"""Exception hierarchy for printer control."""

from datetime import datetime


class PrinterControlError(Exception):
    """Base exception for all printer control errors."""

    def __init__(self, message: str, details: dict[str, any] | None = None):
        """Initialize exception with message and optional details.

        Args:
            message: Human-readable error description
            details: Additional context (printer_id, job_id, error_code, etc.)
        """
        super().__init__(message)
        self.message = message
        self.details = details or {}
        self.timestamp = datetime.utcnow()

    def __str__(self) -> str:
        """Format error message with details."""
        if self.details:
            details_str = ", ".join(f"{k}={v}" for k, v in self.details.items())
            return f"{self.message} ({details_str})"
        return self.message


class ConnectionError(PrinterControlError):
    """Network or MQTT/FTP connection failures."""

    pass


class AuthenticationError(PrinterControlError):
    """Invalid credentials (access code, serial number)."""

    pass


class UploadError(PrinterControlError):
    """FTP file upload failures."""

    pass


class CommandError(PrinterControlError):
    """MQTT command execution failures."""

    pass


class QueueError(PrinterControlError):
    """Queue operation failures."""

    pass


class ValidationError(PrinterControlError):
    """Input validation failures."""

    pass
