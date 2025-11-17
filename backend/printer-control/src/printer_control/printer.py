"""Bambu Lab printer hardware interface."""

import time
from ftplib import FTP, FTP_TLS
from pathlib import Path
from typing import Any

import structlog
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from printer_control.exceptions import (
    AuthenticationError,
    CommandError,
    ConnectionError,
    UploadError,
    ValidationError,
)
from printer_control.models import (
    PrinterConfig,
    PrinterState,
    PrinterStatus,
    TemperatureReading,
)

logger = structlog.get_logger()


class BambuLabPrinter:
    """Bambu Lab printer interface via MQTT and FTP.

    Provides low-level printer control operations: connection management,
    file upload, print commands, and status monitoring.

    Note:
        Requires Bambu Lab Developer Mode enabled on printer.
        bambulabs_api library may not be tested with H2D printers yet.

    Example:
        >>> config = PrinterConfig(...)
        >>> printer = BambuLabPrinter(config)
        >>> printer.connect()
        >>> printer.upload_file(Path("test.gcode"))
        >>> printer.start_print("test.gcode")
        >>> status = printer.get_status()
        >>> printer.disconnect()
    """

    def __init__(self, config: PrinterConfig):
        """Initialize printer interface.

        Args:
            config: Printer configuration (IP, credentials, capabilities)
        """
        self.config = config
        self._connected = False
        self._mqtt_client: Any | None = None  # bambulabs_api.Printer or mock

        logger.info(
            "printer_initialized",
            printer_id=config.printer_id,
            ip=str(config.ip),
            model=config.model,
        )

    def connect(self) -> bool:
        """Establish MQTT connection to printer.

        Returns:
            True if connected successfully

        Raises:
            ConnectionError: Network unreachable or timeout
            AuthenticationError: Invalid access code or serial

        Example:
            >>> if printer.connect():
            ...     print("Connected successfully")
        """
        try:
            # Import bambulabs_api here to allow mocking in tests
            import bambulabs_api as bl

            # Create printer client
            self._mqtt_client = bl.Printer(
                str(self.config.ip), self.config.access_code, self.config.serial
            )

            # Connect with timeout
            self._mqtt_client.connect()

            # Wait for connection to establish
            time.sleep(2)

            self._connected = True

            logger.info(
                "printer_connected",
                printer_id=self.config.printer_id,
                ip=str(self.config.ip),
            )

            return True

        except ImportError as e:
            raise ConnectionError(
                "bambulabs_api library not installed",
                details={"error": str(e)},
            ) from e

        except Exception as e:
            # bambulabs_api may raise various exceptions
            if "authentication" in str(e).lower() or "access code" in str(e).lower():
                raise AuthenticationError(
                    "Invalid access code or serial number",
                    details={
                        "printer_id": self.config.printer_id,
                        "error": str(e),
                    },
                ) from e
            else:
                raise ConnectionError(
                    "Failed to connect to printer",
                    details={
                        "printer_id": self.config.printer_id,
                        "ip": str(self.config.ip),
                        "error": str(e),
                    },
                ) from e

    def disconnect(self) -> None:
        """Close MQTT connection.

        Example:
            >>> printer.disconnect()
        """
        if self._mqtt_client and self._connected:
            try:
                self._mqtt_client.disconnect()
                self._connected = False

                logger.info(
                    "printer_disconnected", printer_id=self.config.printer_id
                )

            except Exception as e:
                logger.warning(
                    "disconnect_failed",
                    printer_id=self.config.printer_id,
                    error=str(e),
                )

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=2, min=2, max=32),
        retry=retry_if_exception_type(UploadError),
        reraise=True,
    )
    def upload_file(self, local_path: Path, remote_name: str | None = None) -> bool:
        """Upload G-code file to printer via FTP.

        Automatically retries on transient failures (up to 3 attempts).

        Args:
            local_path: Local G-code file path
            remote_name: Remote filename (optional, defaults to local filename)

        Returns:
            True if uploaded successfully

        Raises:
            ValidationError: File doesn't exist or invalid format
            UploadError: FTP transfer failed
            AuthenticationError: FTP authentication failed

        Example:
            >>> printer.upload_file(Path("/data/test.gcode"))
        """
        # Validate file
        if not local_path.exists():
            raise ValidationError(
                f"G-code file not found: {local_path}",
                details={"path": str(local_path)},
            )

        if local_path.suffix.lower() not in [".gcode", ".gco", ".g"]:
            raise ValidationError(
                f"Invalid G-code file extension: {local_path.suffix}",
                details={"path": str(local_path)},
            )

        if remote_name is None:
            remote_name = local_path.name

        file_size_mb = local_path.stat().st_size / (1024 * 1024)

        logger.info(
            "file_upload_started",
            printer_id=self.config.printer_id,
            filename=remote_name,
            size_mb=f"{file_size_mb:.2f}",
        )

        try:
            # Determine FTP class based on TLS setting
            ftp_class = FTP_TLS if self.config.ftp.use_tls else FTP

            # Connect to FTP server
            ftp = ftp_class(timeout=self.config.ftp.timeout)
            ftp.connect(str(self.config.ip), self.config.ftp.port)

            # Login (Bambu Lab uses access code as password)
            ftp.login(user="bblp", passwd=self.config.access_code)

            if self.config.ftp.use_tls:
                ftp.prot_p()  # Enable TLS for data channel

            # Upload file
            with open(local_path, "rb") as f:
                ftp.storbinary(f"STOR {remote_name}", f)

            # Verify upload (check file size)
            ftp.voidcmd("TYPE I")
            remote_size = ftp.size(remote_name)
            local_size = local_path.stat().st_size

            if remote_size != local_size:
                raise UploadError(
                    "File size mismatch after upload",
                    details={
                        "expected": local_size,
                        "actual": remote_size,
                        "filename": remote_name,
                    },
                )

            ftp.quit()

            logger.info(
                "file_upload_completed",
                printer_id=self.config.printer_id,
                filename=remote_name,
                size_mb=f"{file_size_mb:.2f}",
            )

            return True

        except Exception as e:
            if "530" in str(e) or "authentication" in str(e).lower():
                raise AuthenticationError(
                    "FTP authentication failed",
                    details={
                        "printer_id": self.config.printer_id,
                        "error": str(e),
                    },
                ) from e
            else:
                raise UploadError(
                    "FTP upload failed",
                    details={
                        "printer_id": self.config.printer_id,
                        "filename": remote_name,
                        "error": str(e),
                    },
                ) from e

    def start_print(self, filename: str) -> bool:
        """Start printing uploaded G-code file.

        Args:
            filename: G-code filename on printer (from upload_file)

        Returns:
            True if print started successfully

        Raises:
            CommandError: MQTT command failed
            ConnectionError: Not connected to printer

        Example:
            >>> printer.start_print("test.gcode")
        """
        if not self._connected or not self._mqtt_client:
            raise ConnectionError(
                "Not connected to printer",
                details={"printer_id": self.config.printer_id},
            )

        try:
            # Send start print command via MQTT
            # Note: bambulabs_api interface may vary
            self._mqtt_client.start_print(filename)

            logger.info(
                "print_started",
                printer_id=self.config.printer_id,
                filename=filename,
            )

            return True

        except Exception as e:
            raise CommandError(
                "Failed to start print",
                details={
                    "printer_id": self.config.printer_id,
                    "filename": filename,
                    "error": str(e),
                },
            ) from e

    def pause_print(self) -> bool:
        """Pause active print.

        Returns:
            True if paused successfully

        Raises:
            CommandError: MQTT command failed
            ConnectionError: Not connected to printer
        """
        if not self._connected or not self._mqtt_client:
            raise ConnectionError(
                "Not connected to printer",
                details={"printer_id": self.config.printer_id},
            )

        try:
            self._mqtt_client.pause_print()

            logger.info("print_paused", printer_id=self.config.printer_id)

            return True

        except Exception as e:
            raise CommandError(
                "Failed to pause print",
                details={"printer_id": self.config.printer_id, "error": str(e)},
            ) from e

    def cancel_print(self) -> bool:
        """Cancel active print.

        Returns:
            True if cancelled successfully

        Raises:
            CommandError: MQTT command failed
            ConnectionError: Not connected to printer
        """
        if not self._connected or not self._mqtt_client:
            raise ConnectionError(
                "Not connected to printer",
                details={"printer_id": self.config.printer_id},
            )

        try:
            self._mqtt_client.cancel_print()

            logger.info("print_cancelled", printer_id=self.config.printer_id)

            return True

        except Exception as e:
            raise CommandError(
                "Failed to cancel print",
                details={"printer_id": self.config.printer_id, "error": str(e)},
            ) from e

    def get_status(self) -> PrinterStatus:
        """Poll current printer status via MQTT.

        Returns:
            PrinterStatus object with current state

        Raises:
            ConnectionError: Not connected or MQTT timeout

        Example:
            >>> status = printer.get_status()
            >>> print(f"State: {status.state}, Progress: {status.progress}%")
        """
        if not self._connected or not self._mqtt_client:
            raise ConnectionError(
                "Not connected to printer",
                details={"printer_id": self.config.printer_id},
            )

        try:
            # Get state from bambulabs_api
            state_data = self._mqtt_client.get_state()

            # Parse state into PrinterStatus model
            # Note: bambulabs_api response format may vary
            return self._parse_printer_status(state_data)

        except Exception as e:
            raise ConnectionError(
                "Failed to get printer status",
                details={"printer_id": self.config.printer_id, "error": str(e)},
            ) from e

    def _parse_printer_status(self, state_data: dict[str, Any]) -> PrinterStatus:
        """Parse bambulabs_api state data into PrinterStatus model.

        Args:
            state_data: Raw state data from bambulabs_api

        Returns:
            PrinterStatus object
        """
        # Map bambulabs_api state to our PrinterState enum
        raw_state = state_data.get("print_status", "unknown").lower()
        state_mapping = {
            "idle": PrinterState.IDLE,
            "running": PrinterState.PRINTING,
            "paused": PrinterState.PAUSED,
            "error": PrinterState.ERROR,
            "finish": PrinterState.IDLE,
        }
        state = state_mapping.get(raw_state, PrinterState.OFFLINE)

        # Extract temperatures
        nozzle_temp = None
        bed_temp = None

        if "nozzle_temp" in state_data and "nozzle_target" in state_data:
            nozzle_temp = TemperatureReading(
                current=float(state_data.get("nozzle_temp", 0)),
                target=float(state_data.get("nozzle_target", 0)),
            )

        if "bed_temp" in state_data and "bed_target" in state_data:
            bed_temp = TemperatureReading(
                current=float(state_data.get("bed_temp", 0)),
                target=float(state_data.get("bed_target", 0)),
            )

        # Extract progress
        progress = float(state_data.get("print_percentage", 0.0))
        current_layer = state_data.get("layer_num")
        total_layers = state_data.get("total_layer_num")
        time_remaining = state_data.get("mc_remaining_time")

        return PrinterStatus(
            printer_id=self.config.printer_id,
            state=state,
            online=True,
            current_job_id=state_data.get("subtask_name"),
            progress=progress,
            current_layer=current_layer,
            total_layers=total_layers,
            time_remaining_seconds=time_remaining,
            nozzle_temp=nozzle_temp,
            bed_temp=bed_temp,
            firmware_version=state_data.get("sw_ver"),
        )

    def is_connected(self) -> bool:
        """Check if printer is connected.

        Returns:
            True if MQTT connection active
        """
        return self._connected
