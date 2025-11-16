"""Unit tests for print queue."""

import pytest

from printer_control.exceptions import QueueError, ValidationError
from printer_control.models import PrintJobStatus
from printer_control.queue import PrintQueue


class TestPrintQueue:
    """Tests for PrintQueue class."""

    def test_queue_initialization(self, temp_queue_path):
        """Test queue initialization."""
        queue = PrintQueue(temp_queue_path)
        assert queue.queue_path == temp_queue_path
        assert queue.get_state().total_jobs() == 0

    def test_enqueue_dequeue(self, temp_queue_path, test_print_job):
        """Test basic enqueue and dequeue operations."""
        queue = PrintQueue(temp_queue_path)

        # Enqueue job
        queue.enqueue(test_print_job)
        assert queue.get_state().total_jobs() == 1
        assert "test_job_001" in queue.get_state().pending

        # Dequeue job
        job = queue.dequeue()
        assert job is not None
        assert job.job_id == "test_job_001"
        assert "test_job_001" in queue.get_state().active

    def test_priority_queue(self, temp_queue_path, test_gcode_file):
        """Test priority job ordering."""
        from printer_control.models import PrintJob

        queue = PrintQueue(temp_queue_path)

        # Enqueue normal priority job
        job1 = PrintJob(
            job_id="job_001", gcode_path=test_gcode_file, priority=0
        )
        queue.enqueue(job1)

        # Enqueue high priority job
        job2 = PrintJob(
            job_id="job_002", gcode_path=test_gcode_file, priority=10
        )
        queue.enqueue(job2)

        # High priority should be dequeued first
        next_job = queue.dequeue()
        assert next_job.job_id == "job_002"

    def test_duplicate_job(self, temp_queue_path, test_print_job):
        """Test that duplicate job IDs raise error."""
        queue = PrintQueue(temp_queue_path)

        queue.enqueue(test_print_job)

        with pytest.raises(ValidationError, match="Job already exists"):
            queue.enqueue(test_print_job)

    def test_mark_completed(self, temp_queue_path, test_print_job):
        """Test marking job as completed."""
        queue = PrintQueue(temp_queue_path)

        queue.enqueue(test_print_job)
        queue.dequeue()  # Move to active

        success = queue.mark_completed("test_job_001")
        assert success

        state = queue.get_state()
        assert "test_job_001" in state.completed
        assert "test_job_001" not in state.active

    def test_mark_failed(self, temp_queue_path, test_print_job):
        """Test marking job as failed."""
        queue = PrintQueue(temp_queue_path)

        queue.enqueue(test_print_job)
        queue.dequeue()  # Move to active

        success = queue.mark_failed("test_job_001", "Test error")
        assert success

        state = queue.get_state()
        assert "test_job_001" in state.failed
        assert "test_job_001" not in state.active

    def test_persistence(self, temp_queue_path, test_print_job):
        """Test queue state persistence."""
        # Create queue and add job
        queue1 = PrintQueue(temp_queue_path)
        queue1.enqueue(test_print_job)
        queue1.save()

        # Load queue in new instance
        queue2 = PrintQueue(temp_queue_path)
        assert queue2.get_state().total_jobs() == 1

        job = queue2.get_job("test_job_001")
        assert job is not None
        assert job.job_id == "test_job_001"

    def test_clear_terminal_jobs(self, temp_queue_path, test_gcode_file):
        """Test clearing old completed/failed jobs."""
        from printer_control.models import PrintJob

        queue = PrintQueue(temp_queue_path)

        # Add 150 completed jobs
        for i in range(150):
            job = PrintJob(
                job_id=f"job_{i:03d}",
                gcode_path=test_gcode_file,
                status=PrintJobStatus.COMPLETED,
            )
            queue.enqueue(job)

        # Clear, keeping only 100
        removed = queue.clear_terminal_jobs(keep_count=100)
        assert removed == 50
        assert len(queue.get_state().completed) == 100
