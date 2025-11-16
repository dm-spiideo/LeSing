"""Printer Control - Bambu Lab printer interface for LeSign."""

from printer_control.agent import PrinterAgent
from printer_control.config import PrinterConfig, load_config
from printer_control.exceptions import (
    AuthenticationError,
    CommandError,
    ConnectionError,
    PrinterControlError,
    QueueError,
    UploadError,
    ValidationError,
)
from printer_control.models import (
    PrintCommand,
    PrinterState,
    PrinterStatus,
    PrintJob,
    PrintJobStatus,
    QueueState,
)
from printer_control.printer import BambuLabPrinter
from printer_control.queue import PrintQueue

__version__ = "0.1.0"

__all__ = [
    # Main interfaces
    "PrinterAgent",
    "BambuLabPrinter",
    "PrintQueue",
    # Configuration
    "PrinterConfig",
    "load_config",
    # Models
    "PrintJob",
    "PrintJobStatus",
    "PrinterStatus",
    "PrinterState",
    "QueueState",
    "PrintCommand",
    # Exceptions
    "PrinterControlError",
    "ConnectionError",
    "AuthenticationError",
    "UploadError",
    "CommandError",
    "QueueError",
    "ValidationError",
]
