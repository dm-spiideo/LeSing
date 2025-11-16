"""Configuration management for printer control."""

import os
from pathlib import Path
from typing import Any

import yaml
from pydantic import ValidationError as PydanticValidationError
from pydantic_settings import BaseSettings, SettingsConfigDict

from printer_control.exceptions import ValidationError
from printer_control.models import (
    FTPConfig,
    MQTTConfig,
    PrinterCapabilities,
    PrinterConfig,
)


class Settings(BaseSettings):
    """Environment-based settings for printer control."""

    # Printer connection
    printer_ip: str
    access_code: str
    serial: str

    # Optional overrides
    printer_id: str = "bambu_h2d_01"
    printer_name: str = "Bambu Lab H2D #1"
    printer_model: str = "Bambu Lab H2D"

    # Queue settings
    queue_path: Path = Path("./data/print_queue.json")
    max_retries: int = 3
    retry_base_delay: float = 2.0

    # Monitoring
    status_poll_interval: float = 5.0
    timeout: int = 30

    # Logging
    log_level: str = "INFO"

    model_config = SettingsConfigDict(
        env_prefix="PRINTER_CONTROL_", env_file=".env", env_file_encoding="utf-8"
    )


def load_config_from_yaml(yaml_path: Path) -> PrinterConfig:
    """Load printer configuration from YAML file.

    Args:
        yaml_path: Path to YAML configuration file

    Returns:
        PrinterConfig object

    Raises:
        ValidationError: If YAML is invalid or missing required fields
    """
    if not yaml_path.exists():
        raise ValidationError(
            f"Configuration file not found: {yaml_path}",
            details={"path": str(yaml_path)},
        )

    try:
        with open(yaml_path, "r") as f:
            data = yaml.safe_load(f)
    except yaml.YAMLError as e:
        raise ValidationError(
            f"Invalid YAML in configuration file",
            details={"path": str(yaml_path), "error": str(e)},
        ) from e

    try:
        return PrinterConfig(**data)
    except PydanticValidationError as e:
        raise ValidationError(
            f"Invalid printer configuration",
            details={"path": str(yaml_path), "errors": e.errors()},
        ) from e


def load_config_from_env() -> PrinterConfig:
    """Load printer configuration from environment variables.

    Environment variables:
        PRINTER_CONTROL_PRINTER_IP: Printer IP address
        PRINTER_CONTROL_ACCESS_CODE: Printer access code
        PRINTER_CONTROL_SERIAL: Printer serial number
        ... (see Settings class for full list)

    Returns:
        PrinterConfig object

    Raises:
        ValidationError: If required environment variables missing
    """
    try:
        settings = Settings()  # type: ignore[call-arg]
    except PydanticValidationError as e:
        raise ValidationError(
            "Missing or invalid environment variables",
            details={"errors": e.errors()},
        ) from e

    # Build printer config from settings
    return PrinterConfig(
        printer_id=settings.printer_id,
        name=settings.printer_name,
        model=settings.printer_model,
        ip=settings.printer_ip,
        access_code=settings.access_code,
        serial=settings.serial,
        capabilities=PrinterCapabilities(
            build_volume={"x": 256, "y": 256, "z": 256},
            materials=["PLA", "PETG", "ABS", "TPU"],
            max_temp_nozzle=300,
            max_temp_bed=110,
            has_filament_sensor=True,
            has_camera=True,
        ),
        mqtt=MQTTConfig(),
        ftp=FTPConfig(),
        status_poll_interval=settings.status_poll_interval,
    )


def load_config(config_path: Path | None = None) -> PrinterConfig:
    """Load printer configuration from YAML file or environment variables.

    Args:
        config_path: Optional path to YAML config file. If None, loads from env vars.

    Returns:
        PrinterConfig object

    Raises:
        ValidationError: If configuration is invalid or missing

    Example:
        >>> # Load from environment variables
        >>> config = load_config()
        >>>
        >>> # Load from YAML file
        >>> config = load_config(Path("config/printer_config.yaml"))
    """
    if config_path is not None:
        return load_config_from_yaml(config_path)
    else:
        return load_config_from_env()


def save_config_to_yaml(config: PrinterConfig, yaml_path: Path) -> None:
    """Save printer configuration to YAML file.

    Args:
        config: PrinterConfig object to save
        yaml_path: Destination YAML file path

    Raises:
        ValidationError: If unable to write file
    """
    try:
        yaml_path.parent.mkdir(parents=True, exist_ok=True)
        with open(yaml_path, "w") as f:
            # Convert Pydantic model to dict, handle IP address serialization
            config_dict = config.model_dump(mode="json")
            yaml.dump(config_dict, f, default_flow_style=False, sort_keys=False)
    except (OSError, yaml.YAMLError) as e:
        raise ValidationError(
            f"Failed to save configuration to file",
            details={"path": str(yaml_path), "error": str(e)},
        ) from e
