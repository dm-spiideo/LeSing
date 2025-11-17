"""Printer agent for job orchestration and queue management."""

import threading
import time
import uuid
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import structlog

from printer_control.exceptions import (
    ConnectionError,
    PrinterControlError,
    QueueError,
)
from printer_control.models import (
    PrinterConfig,
    PrinterStatus,
    PrintJob,
    PrintJobStatus,
    QueueState,
)
from printer_control.printer import BambuLabPrinter
from printer_control.queue import PrintQueue

logger = structlog.get_logger()


class PrinterAgent:
    """Printer agent for automated print job management.

    Coordinates job queue, printer communication, and job lifecycle.
    Runs background thread for automatic queue processing.

    Example:
        >>> config = PrinterConfig(...)
        >>> agent = PrinterAgent(config)
        >>> agent.start()
        >>>
        >>> job = agent.submit_job(Path("/data/test.gcode"), name="Test")
        >>> status = agent.get_job_status(job.job_id)
        >>>
        >>> agent.stop()
    """

    def __init__(
        self,
        config: PrinterConfig,
        queue_path: Path = Path("./data/print_queue.json"),
    ):
        """Initialize printer agent.

        Args:
            config: Printer configuration
            queue_path: Path to persistent queue state file
        """
        self.config = config
        self.queue_path = queue_path

        # Initialize components
        self.printer = BambuLabPrinter(config)
        self.queue = PrintQueue(queue_path)

        # Control flags
        self._running = False
        self._thread: threading.Thread | None = None
        self._lock = threading.RLock()

        logger.info(
            "agent_initialized",
            printer_id=config.printer_id,
            queue_path=str(queue_path),
        )

    def submit_job(
        self,
        gcode_path: Path,
        name: str | None = None,
        priority: int = 0,
        metadata: dict[str, Any] | None = None,
    ) -> PrintJob:
        """Submit new print job to queue.

        Args:
            gcode_path: Path to G-code file
            name: Human-readable job name (optional)
            priority: Job priority (higher = more urgent, default 0)
            metadata: Additional metadata (customer_id, design_id, etc.)

        Returns:
            PrintJob object with job_id and initial PENDING status

        Raises:
            ValidationError: Invalid G-code file
            QueueError: Queue operation failed

        Example:
            >>> job = agent.submit_job(
            ...     gcode_path=Path("/data/test.gcode"),
            ...     name="Test Print",
            ...     priority=0
            ... )
            >>> print(f"Job submitted: {job.job_id}")
        """
        # Generate unique job ID
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        job_id = f"job_{timestamp}_{uuid.uuid4().hex[:8]}"

        # Create job object
        job = PrintJob(
            job_id=job_id,
            gcode_path=gcode_path,
            name=name or gcode_path.stem,
            priority=priority,
            status=PrintJobStatus.PENDING,
        )

        # Apply metadata if provided
        if metadata:
            if "customer_id" in metadata:
                job.customer_id = metadata["customer_id"]
            if "design_id" in metadata:
                job.design_id = metadata["design_id"]
            if "description" in metadata:
                job.description = metadata["description"]

        # Enqueue job
        self.queue.enqueue(job)
        self.queue.save()

        logger.info(
            "job_submitted",
            job_id=job.job_id,
            name=job.name,
            priority=job.priority,
            queue_depth=len(self.queue.get_state().pending),
        )

        return job

    def get_job_status(self, job_id: str) -> PrintJob:
        """Get current status of a print job.

        Args:
            job_id: Job identifier

        Returns:
            PrintJob object with current state

        Raises:
            ValueError: Job ID not found
        """
        job = self.queue.get_job(job_id)
        if job is None:
            raise ValueError(f"Job not found: {job_id}")

        return job

    def cancel_job(self, job_id: str) -> bool:
        """Cancel pending or active print job.

        Args:
            job_id: Job identifier

        Returns:
            True if cancelled successfully, False if not found or terminal

        Raises:
            CommandError: Printer communication failure during cancellation
        """
        job = self.queue.get_job(job_id)
        if job is None:
            return False

        # Already terminal - can't cancel
        if job.is_terminal():
            return False

        # If actively printing, send cancel command to printer
        if job.status in {PrintJobStatus.PRINTING, PrintJobStatus.STARTING}:
            try:
                if self.printer.is_connected():
                    self.printer.cancel_print()
            except PrinterControlError as e:
                logger.warning(
                    "cancel_command_failed", job_id=job_id, error=str(e)
                )
                # Continue with marking as cancelled even if command fails

        # Update job status
        job.status = PrintJobStatus.CANCELLED
        self.queue.update_job(job)
        self.queue.mark_failed(job_id, "Cancelled by user")
        self.queue.save()

        logger.info("job_cancelled", job_id=job_id)

        return True

    def get_printer_status(self, printer_id: str | None = None) -> PrinterStatus:
        """Get current printer status.

        Args:
            printer_id: Printer identifier (optional for single-printer setup)

        Returns:
            PrinterStatus object with current printer state

        Raises:
            ConnectionError: Printer offline or unreachable
        """
        if not self.printer.is_connected():
            raise ConnectionError(
                "Printer not connected",
                details={"printer_id": self.config.printer_id},
            )

        return self.printer.get_status()

    def get_queue_state(self) -> QueueState:
        """Get current queue state.

        Returns:
            QueueState with job ID lists
        """
        return self.queue.get_state()

    def start(self) -> None:
        """Start printer agent background processing.

        Loads queue state, connects to printer, and starts queue processing loop.

        Raises:
            ConnectionError: Cannot connect to printer
            QueueError: Cannot load queue state
        """
        with self._lock:
            if self._running:
                logger.warning("agent_already_running")
                return

            # Connect to printer
            logger.info("connecting_to_printer", printer_id=self.config.printer_id)
            self.printer.connect()

            # Start background thread
            self._running = True
            self._thread = threading.Thread(target=self._process_queue, daemon=True)
            self._thread.start()

            logger.info("agent_started", printer_id=self.config.printer_id)

    def stop(self) -> None:
        """Stop printer agent gracefully.

        Stops queue processing, waits for active uploads to complete,
        saves queue state, and disconnects from printer.

        Note: Does NOT cancel active prints (printer continues).
        """
        with self._lock:
            if not self._running:
                return

            logger.info("stopping_agent", printer_id=self.config.printer_id)

            # Signal thread to stop
            self._running = False

            # Wait for thread to finish (max 60s)
            if self._thread and self._thread.is_alive():
                self._thread.join(timeout=60)

            # Save final queue state
            try:
                self.queue.save()
            except QueueError as e:
                logger.error("queue_save_failed_on_shutdown", error=str(e))

            # Disconnect printer
            self.printer.disconnect()

            logger.info("agent_stopped", printer_id=self.config.printer_id)

    def _process_queue(self) -> None:
        """Background thread for queue processing (main event loop)."""
        logger.info("queue_processing_started")

        while self._running:
            try:
                # Process next job if available
                self._process_next_job()

                # Monitor active jobs
                self._monitor_active_jobs()

                # Cleanup old terminal jobs periodically
                if int(time.time()) % 3600 == 0:  # Every hour
                    self.queue.clear_terminal_jobs()

                # Sleep between iterations
                time.sleep(self.config.status_poll_interval)

            except Exception as e:
                logger.error("queue_processing_error", error=str(e), exc_info=True)
                time.sleep(10)  # Back off on errors

        logger.info("queue_processing_stopped")

    def _process_next_job(self) -> None:
        """Process next pending job from queue."""
        # Check if printer available
        try:
            status = self.printer.get_status()
            if not status.can_accept_job():
                return  # Printer busy or offline
        except ConnectionError:
            logger.warning("printer_offline_skipping_job_processing")
            return

        # Get next job
        job = self.queue.dequeue()
        if job is None:
            return  # Queue empty

        logger.info("processing_job", job_id=job.job_id, name=job.name)

        # Execute job workflow
        try:
            self._execute_job(job)
        except Exception as e:
            logger.error(
                "job_execution_failed", job_id=job.job_id, error=str(e), exc_info=True
            )
            self._handle_job_failure(job, str(e))

    def _execute_job(self, job: PrintJob) -> None:
        """Execute complete job workflow: upload → start → monitor.

        Args:
            job: PrintJob to execute

        Raises:
            PrinterControlError: Any step failed
        """
        # Step 1: Upload G-code file
        job.status = PrintJobStatus.UPLOADING
        self.queue.update_job(job)
        self.queue.save()

        remote_filename = f"{job.job_id}.gcode"
        self.printer.upload_file(job.gcode_path, remote_filename)

        # Step 2: Start print
        job.status = PrintJobStatus.STARTING
        self.queue.update_job(job)
        self.queue.save()

        self.printer.start_print(remote_filename)

        # Step 3: Update to printing status
        job.status = PrintJobStatus.PRINTING
        job.started_at = datetime.now(UTC)
        self.queue.update_job(job)
        self.queue.save()

        logger.info("job_printing_started", job_id=job.job_id)

    def _monitor_active_jobs(self) -> None:
        """Monitor active print jobs and update status."""
        queue_state = self.queue.get_state()

        for job_id in queue_state.active:
            job = self.queue.get_job(job_id)
            if job is None or job.status != PrintJobStatus.PRINTING:
                continue

            try:
                # Get printer status
                status = self.printer.get_status()

                # Update job progress
                if status.current_job_id and job_id in status.current_job_id:
                    job.progress = status.progress or 0.0
                    job.current_layer = status.current_layer
                    job.total_layers = status.total_layers
                    self.queue.update_job(job)

                    # Check if completed
                    if status.state.value == "idle" and job.progress >= 99.0:
                        self._handle_job_completion(job)

            except ConnectionError:
                logger.warning("printer_offline_during_monitoring", job_id=job_id)
                continue

    def _handle_job_completion(self, job: PrintJob) -> None:
        """Handle successful job completion.

        Args:
            job: Completed PrintJob
        """
        job.status = PrintJobStatus.COMPLETED
        job.completed_at = datetime.now(UTC)

        if job.started_at:
            duration = job.completed_at - job.started_at
            job.actual_duration_seconds = int(duration.total_seconds())

        self.queue.update_job(job)
        self.queue.mark_completed(job.job_id)
        self.queue.save()

        logger.info(
            "job_completed",
            job_id=job.job_id,
            duration_seconds=job.actual_duration_seconds,
        )

    def _handle_job_failure(self, job: PrintJob, error_message: str) -> None:
        """Handle job failure with retry logic.

        Args:
            job: Failed PrintJob
            error_message: Error description
        """
        job.error_message = error_message
        job.retry_count += 1

        # Check if can retry
        if job.can_retry():
            job.status = PrintJobStatus.RETRYING
            self.queue.update_job(job)

            # Re-enqueue for retry
            job.status = PrintJobStatus.PENDING
            self.queue.enqueue(job)
            self.queue.save()

            logger.warning(
                "job_retry_scheduled",
                job_id=job.job_id,
                retry_count=job.retry_count,
                max_retries=job.max_retries,
            )
        else:
            # Max retries exhausted
            job.status = PrintJobStatus.FAILED
            self.queue.update_job(job)
            self.queue.mark_failed(job.job_id, error_message)
            self.queue.save()

            logger.error(
                "job_failed_permanently",
                job_id=job.job_id,
                error=error_message,
                retry_count=job.retry_count,
            )
