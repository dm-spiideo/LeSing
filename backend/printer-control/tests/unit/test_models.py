"""Unit tests for Pydantic models."""

from pathlib import Path

import pytest
from pydantic import ValidationError

from printer_control.models import (
    PrinterCapabilities,
    PrinterConfig,
    PrinterState,
    PrinterStatus,
    PrintJob,
    PrintJobStatus,
    QueueState,
    TemperatureReading,
)


class TestPrintJob:
    """Tests for PrintJob model."""

    def test_create_valid_job(self, test_gcode_file):
        """Test creating a valid print job."""
        job = PrintJob(
            job_id="job_001",
            gcode_path=test_gcode_file,
            name="Test Job",
            priority=0,
        )

        assert job.job_id == "job_001"
        assert job.gcode_path == test_gcode_file
        assert job.status == PrintJobStatus.PENDING
        assert job.progress == 0.0
        assert job.retry_count == 0

    def test_invalid_gcode_path(self):
        """Test that non-existent G-code file raises error."""
        with pytest.raises(ValidationError, match="G-code file not found"):
            PrintJob(
                job_id="job_001",
                gcode_path=Path("/nonexistent/file.gcode"),
            )

    def test_invalid_gcode_extension(self, tmp_path):
        """Test that invalid extension raises error."""
        bad_file = tmp_path / "test.txt"
        bad_file.write_text("not gcode")

        with pytest.raises(ValidationError, match="Invalid G-code file extension"):
            PrintJob(job_id="job_001", gcode_path=bad_file)

    def test_is_terminal(self, test_print_job):
        """Test terminal state detection."""
        test_print_job.status = PrintJobStatus.PENDING
        assert not test_print_job.is_terminal()

        test_print_job.status = PrintJobStatus.PRINTING
        assert not test_print_job.is_terminal()

        test_print_job.status = PrintJobStatus.COMPLETED
        assert test_print_job.is_terminal()

        test_print_job.status = PrintJobStatus.FAILED
        assert test_print_job.is_terminal()

    def test_can_retry(self, test_print_job):
        """Test retry eligibility."""
        test_print_job.status = PrintJobStatus.FAILED
        test_print_job.retry_count = 0
        test_print_job.max_retries = 3
        assert test_print_job.can_retry()

        test_print_job.retry_count = 3
        assert not test_print_job.can_retry()

        test_print_job.status = PrintJobStatus.COMPLETED
        assert not test_print_job.can_retry()


class TestPrinterConfig:
    """Tests for PrinterConfig model."""

    def test_create_valid_config(self):
        """Test creating valid printer configuration."""
        config = PrinterConfig(
            printer_id="printer_01",
            name="Test Printer",
            model="Bambu Lab H2D",
            ip="192.168.1.100",
            access_code="abc12345",
            serial="01P00A000TEST",
            capabilities=PrinterCapabilities(
                build_volume={"x": 256, "y": 256, "z": 256},
                materials=["PLA"],
                max_temp_nozzle=300,
                max_temp_bed=110,
            ),
        )

        assert config.printer_id == "printer_01"
        assert str(config.ip) == "192.168.1.100"
        assert config.access_code == "abc12345"

    def test_invalid_access_code(self):
        """Test that non-alphanumeric access code raises error."""
        with pytest.raises(ValidationError, match="Access code must be alphanumeric"):
            PrinterConfig(
                printer_id="printer_01",
                name="Test",
                ip="192.168.1.100",
                access_code="abc-123!",  # Invalid characters
                serial="01P00A000TEST",
                capabilities=PrinterCapabilities(
                    build_volume={"x": 256, "y": 256, "z": 256},
                    materials=["PLA"],
                    max_temp_nozzle=300,
                    max_temp_bed=110,
                ),
            )


class TestPrinterStatus:
    """Tests for PrinterStatus model."""

    def test_create_valid_status(self):
        """Test creating valid printer status."""
        status = PrinterStatus(
            printer_id="printer_01",
            state=PrinterState.IDLE,
            online=True,
            nozzle_temp=TemperatureReading(current=25.0, target=0.0),
            bed_temp=TemperatureReading(current=25.0, target=0.0),
        )

        assert status.printer_id == "printer_01"
        assert status.state == PrinterState.IDLE
        assert status.online

    def test_can_accept_job(self):
        """Test job acceptance logic."""
        status = PrinterStatus(
            printer_id="printer_01", state=PrinterState.IDLE, online=True
        )
        assert status.can_accept_job()

        status.state = PrinterState.PRINTING
        assert not status.can_accept_job()

        status.state = PrinterState.IDLE
        status.online = False
        assert not status.can_accept_job()


class TestTemperatureReading:
    """Tests for TemperatureReading model."""

    def test_is_stable(self):
        """Test temperature stability detection."""
        temp = TemperatureReading(current=215.0, target=215.0)
        assert temp.is_stable(tolerance=2.0)

        temp = TemperatureReading(current=216.5, target=215.0)
        assert temp.is_stable(tolerance=2.0)

        temp = TemperatureReading(current=218.0, target=215.0)
        assert not temp.is_stable(tolerance=2.0)


class TestQueueState:
    """Tests for QueueState model."""

    def test_queue_operations(self):
        """Test queue state operations."""
        state = QueueState()

        # Add job
        state.add_job("job_001")
        assert "job_001" in state.pending
        assert state.total_jobs() == 1

        # Move to active
        state.move_to_active("job_001")
        assert "job_001" not in state.pending
        assert "job_001" in state.active

        # Move to completed
        state.move_to_completed("job_001")
        assert "job_001" not in state.active
        assert "job_001" in state.completed

    def test_next_job(self):
        """Test next job retrieval."""
        state = QueueState()
        assert state.next_job() is None

        state.add_job("job_001")
        assert state.next_job() == "job_001"

        state.add_job("job_002")
        assert state.next_job() == "job_001"  # FIFO
