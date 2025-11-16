"""Shared test fixtures for printer control tests."""

import json
from pathlib import Path
from typing import Generator

import pytest

from printer_control.config import PrinterConfig
from printer_control.models import (
    FTPConfig,
    MQTTConfig,
    PrinterCapabilities,
    PrintJob,
    PrintJobStatus,
)


@pytest.fixture
def test_config() -> PrinterConfig:
    """Test printer configuration."""
    return PrinterConfig(
        printer_id="test_printer_01",
        name="Test Printer",
        model="Bambu Lab H2D",
        ip="192.168.1.100",
        access_code="test12345",
        serial="01P00A000TEST123",
        capabilities=PrinterCapabilities(
            build_volume={"x": 256, "y": 256, "z": 256},
            materials=["PLA", "PETG"],
            max_temp_nozzle=300,
            max_temp_bed=110,
            has_filament_sensor=True,
            has_camera=True,
        ),
        mqtt=MQTTConfig(),
        ftp=FTPConfig(),
        status_poll_interval=5.0,
    )


@pytest.fixture
def test_gcode_file(tmp_path: Path) -> Path:
    """Create temporary test G-code file."""
    gcode_file = tmp_path / "test.gcode"
    gcode_file.write_text(
        "; Test G-code\nG28 ; Home\nG1 X100 Y100 Z10 F3000\n; End\n"
    )
    return gcode_file


@pytest.fixture
def test_print_job(test_gcode_file: Path) -> PrintJob:
    """Test print job."""
    return PrintJob(
        job_id="test_job_001",
        gcode_path=test_gcode_file,
        name="Test Job",
        status=PrintJobStatus.PENDING,
        priority=0,
    )


@pytest.fixture
def temp_queue_path(tmp_path: Path) -> Path:
    """Temporary queue state file path."""
    return tmp_path / "test_queue.json"


@pytest.fixture
def mock_bambulabs_api(monkeypatch):
    """Mock bambulabs_api library."""

    class MockPrinter:
        def __init__(self, ip, access_code, serial):
            self.ip = ip
            self.access_code = access_code
            self.serial = serial
            self.connected = False

        def connect(self):
            self.connected = True

        def disconnect(self):
            self.connected = False

        def start_print(self, filename):
            return True

        def pause_print(self):
            return True

        def cancel_print(self):
            return True

        def get_state(self):
            return {
                "print_status": "idle",
                "print_percentage": 0.0,
                "nozzle_temp": 25.0,
                "nozzle_target": 0.0,
                "bed_temp": 25.0,
                "bed_target": 0.0,
                "layer_num": 0,
                "total_layer_num": 0,
                "mc_remaining_time": 0,
                "sw_ver": "01.09.00.00",
            }

    class MockBambuLabsAPI:
        Printer = MockPrinter

    # Mock the import
    monkeypatch.setattr("printer_control.printer.bl", MockBambuLabsAPI())

    return MockBambuLabsAPI
