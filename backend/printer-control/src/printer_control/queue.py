"""Print job queue management with persistence."""

import json
import threading
from pathlib import Path

import structlog

from printer_control.exceptions import QueueError, ValidationError
from printer_control.models import PrintJob, PrintJobStatus, QueueState

logger = structlog.get_logger()


class PrintQueue:
    """Thread-safe print job queue with persistent state.

    Manages job queue with FIFO ordering, priority support, and persistent
    storage. Queue state survives application restart.

    Example:
        >>> queue = PrintQueue(queue_path=Path("./data/queue.json"))
        >>> job = PrintJob(job_id="job_001", gcode_path=Path("test.gcode"))
        >>> queue.enqueue(job)
        >>> queue.save()
        >>> next_job = queue.dequeue()
    """

    def __init__(self, queue_path: Path):
        """Initialize print queue.

        Args:
            queue_path: Path to persistent queue state file (JSON)

        Raises:
            QueueError: If unable to load existing queue state
        """
        self.queue_path = queue_path
        self._jobs: dict[str, PrintJob] = {}
        self._state = QueueState()
        self._lock = threading.RLock()

        # Create queue directory if it doesn't exist
        self.queue_path.parent.mkdir(parents=True, exist_ok=True)

        # Load existing state if available
        if self.queue_path.exists():
            self.load()

        logger.info(
            "queue_initialized",
            queue_path=str(self.queue_path),
            total_jobs=self._state.total_jobs(),
        )

    def enqueue(self, job: PrintJob) -> None:
        """Add job to queue.

        Jobs are added to the end of the queue (FIFO order). Higher priority
        jobs are inserted at the front.

        Args:
            job: PrintJob to enqueue

        Raises:
            ValidationError: If job already exists in queue
        """
        with self._lock:
            if job.job_id in self._jobs:
                raise ValidationError(
                    f"Job already exists in queue: {job.job_id}",
                    details={"job_id": job.job_id},
                )

            self._jobs[job.job_id] = job

            # Add to appropriate list based on status
            if job.status == PrintJobStatus.PENDING:
                if job.priority > 0:
                    # Insert high-priority jobs at front
                    self._state.pending.insert(0, job.job_id)
                else:
                    # Normal priority: append to end (FIFO)
                    self._state.add_job(job.job_id)
            elif job.status in {
                PrintJobStatus.UPLOADING,
                PrintJobStatus.STARTING,
                PrintJobStatus.PRINTING,
            }:
                if job.job_id not in self._state.active:
                    self._state.active.append(job.job_id)
            elif job.status == PrintJobStatus.COMPLETED:
                if job.job_id not in self._state.completed:
                    self._state.completed.append(job.job_id)
            elif job.status in {
                PrintJobStatus.FAILED,
                PrintJobStatus.ERROR,
                PrintJobStatus.CANCELLED,
            }:
                if job.job_id not in self._state.failed:
                    self._state.failed.append(job.job_id)

            logger.info(
                "job_enqueued",
                job_id=job.job_id,
                status=job.status,
                priority=job.priority,
                queue_depth=len(self._state.pending),
            )

    def dequeue(self) -> PrintJob | None:
        """Remove and return next pending job (FIFO order).

        Returns:
            Next PrintJob from queue, or None if queue empty

        Example:
            >>> job = queue.dequeue()
            >>> if job:
            ...     print(f"Processing job: {job.job_id}")
        """
        with self._lock:
            job_id = self._state.next_job()
            if job_id is None:
                return None

            job = self._jobs.get(job_id)
            if job is None:
                logger.warning(
                    "job_not_found", job_id=job_id, action="removing_from_queue"
                )
                self._state.pending.remove(job_id)
                return None

            # Move to active state
            self._state.move_to_active(job_id)

            logger.info("job_dequeued", job_id=job_id, queue_depth=len(self._state.pending))

            return job

    def get_job(self, job_id: str) -> PrintJob | None:
        """Retrieve job by ID without removing from queue.

        Args:
            job_id: Job identifier

        Returns:
            PrintJob if found, None otherwise
        """
        with self._lock:
            return self._jobs.get(job_id)

    def update_job(self, job: PrintJob) -> None:
        """Update existing job in queue.

        Args:
            job: Updated PrintJob object

        Raises:
            ValidationError: If job not found in queue
        """
        with self._lock:
            if job.job_id not in self._jobs:
                raise ValidationError(
                    f"Job not found in queue: {job.job_id}",
                    details={"job_id": job.job_id},
                )

            self._jobs[job.job_id] = job

            logger.debug(
                "job_updated", job_id=job.job_id, status=job.status, progress=job.progress
            )

    def mark_completed(self, job_id: str) -> bool:
        """Mark job as completed and move to completed list.

        Args:
            job_id: Job identifier

        Returns:
            True if job moved successfully, False if not found or not active
        """
        with self._lock:
            job = self._jobs.get(job_id)
            if job is None:
                return False

            job.status = PrintJobStatus.COMPLETED
            success = self._state.move_to_completed(job_id)

            if success:
                logger.info("job_completed", job_id=job_id)

            return success

    def mark_failed(self, job_id: str, error_message: str | None = None) -> bool:
        """Mark job as failed and move to failed list.

        Args:
            job_id: Job identifier
            error_message: Optional error description

        Returns:
            True if job moved successfully, False if not found
        """
        with self._lock:
            job = self._jobs.get(job_id)
            if job is None:
                return False

            job.status = PrintJobStatus.FAILED
            if error_message:
                job.error_message = error_message

            success = self._state.move_to_failed(job_id)

            if success:
                logger.warning("job_failed", job_id=job_id, error=error_message)

            return success

    def get_state(self) -> QueueState:
        """Get current queue state (snapshot).

        Returns:
            QueueState with current job lists
        """
        with self._lock:
            return QueueState(
                pending=self._state.pending.copy(),
                active=self._state.active.copy(),
                completed=self._state.completed.copy(),
                failed=self._state.failed.copy(),
                version=self._state.version,
                last_modified=self._state.last_modified,
            )

    def save(self) -> None:
        """Persist queue state to disk.

        Saves both queue state (job lists) and job metadata to JSON file.

        Raises:
            QueueError: If unable to write file
        """
        with self._lock:
            try:
                # Serialize state and jobs
                data = {
                    "state": self._state.model_dump(mode="json"),
                    "jobs": {
                        job_id: job.model_dump(mode="json")
                        for job_id, job in self._jobs.items()
                    },
                }

                # Write atomically: write to temp file, then rename
                temp_path = self.queue_path.with_suffix(".tmp")
                with open(temp_path, "w") as f:
                    json.dump(data, f, indent=2)

                temp_path.replace(self.queue_path)

                logger.debug(
                    "queue_saved", queue_path=str(self.queue_path), total_jobs=len(self._jobs)
                )

            except (OSError, json.JSONDecodeError) as e:
                raise QueueError(
                    "Failed to save queue state",
                    details={"path": str(self.queue_path), "error": str(e)},
                ) from e

    def load(self) -> None:
        """Load queue state from disk.

        Restores queue state and job metadata from JSON file.

        Raises:
            QueueError: If unable to read or parse file
        """
        try:
            with open(self.queue_path) as f:
                data = json.load(f)

            # Restore state
            self._state = QueueState(**data["state"])

            # Restore jobs (convert gcode_path string back to Path)
            self._jobs = {}
            for job_id, job_data in data["jobs"].items():
                if "gcode_path" in job_data:
                    job_data["gcode_path"] = Path(job_data["gcode_path"])
                self._jobs[job_id] = PrintJob(**job_data)

            logger.info(
                "queue_loaded",
                queue_path=str(self.queue_path),
                total_jobs=len(self._jobs),
                pending=len(self._state.pending),
                active=len(self._state.active),
            )

        except (OSError, json.JSONDecodeError, KeyError, ValueError) as e:
            raise QueueError(
                "Failed to load queue state",
                details={"path": str(self.queue_path), "error": str(e)},
            ) from e

    def clear_terminal_jobs(self, keep_count: int = 100) -> int:
        """Remove old completed/failed jobs to prevent unbounded growth.

        Args:
            keep_count: Number of recent terminal jobs to keep

        Returns:
            Number of jobs removed
        """
        with self._lock:
            removed = 0

            # Remove old completed jobs (keep most recent)
            if len(self._state.completed) > keep_count:
                old_completed = self._state.completed[:-keep_count]
                for job_id in old_completed:
                    self._jobs.pop(job_id, None)
                    removed += 1
                self._state.completed = self._state.completed[-keep_count:]

            # Remove old failed jobs (keep most recent)
            if len(self._state.failed) > keep_count:
                old_failed = self._state.failed[:-keep_count]
                for job_id in old_failed:
                    self._jobs.pop(job_id, None)
                    removed += 1
                self._state.failed = self._state.failed[-keep_count:]

            if removed > 0:
                logger.info("terminal_jobs_cleared", removed_count=removed)

            return removed
