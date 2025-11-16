# Data Model: Printer Control

**Feature**: 003-printer-control
**Last Updated**: 2025-11-16

## Overview

This document defines all Pydantic data models used in the Printer Control component. Models provide type-safe data validation, serialization, and clear contracts between subsystems.

---

## Core Models

### PrintJob

Represents a print job throughout its lifecycle.

```python
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Optional
from pydantic import BaseModel, Field, field_validator


class PrintJobStatus(str, Enum):
    """Print job lifecycle states."""
    PENDING = "pending"        # Queued, waiting for printer
    UPLOADING = "uploading"    # FTP upload in progress
    STARTING = "starting"      # MQTT start command sent
    PRINTING = "printing"      # Active print
    RETRYING = "retrying"      # Failed, retrying
    COMPLETED = "completed"    # Successfully finished
    FAILED = "failed"          # Terminal failure
    CANCELLED = "cancelled"    # User cancelled
    ERROR = "error"            # Printer error (requires intervention)


class PrintJob(BaseModel):
    """Print job metadata and state."""

    # Identity
    job_id: str = Field(..., description="Unique job identifier (UUID)")
    gcode_path: Path = Field(..., description="Local path to G-code file")
    printer_id: str | None = Field(None, description="Assigned printer ID")

    # Metadata
    name: str | None = Field(None, description="Human-readable job name")
    description: str | None = Field(None, description="Job description")
    priority: int = Field(0, description="Priority (higher = more urgent)")
    design_id: str | None = Field(None, description="Reference to design library")
    customer_id: str | None = Field(None, description="Customer identifier")

    # Status
    status: PrintJobStatus = Field(PrintJobStatus.PENDING, description="Current job state")
    progress: float = Field(0.0, ge=0.0, le=100.0, description="Progress percentage (0-100)")
    current_layer: int | None = Field(None, ge=0, description="Current layer being printed")
    total_layers: int | None = Field(None, ge=0, description="Total layers in model")

    # Timing
    created_at: datetime = Field(default_factory=datetime.utcnow, description="Job creation timestamp")
    started_at: datetime | None = Field(None, description="Print start timestamp")
    completed_at: datetime | None = Field(None, description="Print completion timestamp")
    estimated_duration_seconds: int | None = Field(None, ge=0, description="Estimated print time")
    actual_duration_seconds: int | None = Field(None, ge=0, description="Actual print time")

    # Error handling
    retry_count: int = Field(0, ge=0, description="Number of retry attempts")
    max_retries: int = Field(3, ge=0, description="Maximum retry attempts")
    error_message: str | None = Field(None, description="Last error message")
    error_code: str | None = Field(None, description="Error code (if available)")

    # Material estimates
    estimated_filament_grams: float | None = Field(None, ge=0, description="Estimated filament usage (g)")
    actual_filament_grams: float | None = Field(None, ge=0, description="Actual filament usage (g)")

    @field_validator('gcode_path')
    @classmethod
    def validate_gcode_path(cls, v: Path) -> Path:
        """Ensure G-code file exists and has .gcode extension."""
        if not v.exists():
            raise ValueError(f"G-code file not found: {v}")
        if v.suffix.lower() not in ['.gcode', '.gco', '.g']:
            raise ValueError(f"Invalid G-code file extension: {v.suffix}")
        return v

    def is_terminal(self) -> bool:
        """Check if job is in terminal state."""
        return self.status in {
            PrintJobStatus.COMPLETED,
            PrintJobStatus.FAILED,
            PrintJobStatus.CANCELLED,
            PrintJobStatus.ERROR
        }

    def can_retry(self) -> bool:
        """Check if job can be retried."""
        return (
            self.status in {PrintJobStatus.FAILED, PrintJobStatus.ERROR} and
            self.retry_count < self.max_retries
        )


class PrintJobUpdate(BaseModel):
    """Partial update for print job (used for status updates)."""

    status: PrintJobStatus | None = None
    progress: float | None = Field(None, ge=0.0, le=100.0)
    current_layer: int | None = Field(None, ge=0)
    error_message: str | None = None
    error_code: str | None = None
    actual_filament_grams: float | None = Field(None, ge=0)
```

---

### PrinterConfig

Printer connection configuration and capabilities.

```python
from pydantic import BaseModel, Field, IPvAnyAddress


class PrinterCapabilities(BaseModel):
    """Printer hardware capabilities."""

    build_volume: dict[str, int] = Field(
        ...,
        description="Build volume in mm (x, y, z)",
        example={"x": 256, "y": 256, "z": 256}
    )
    materials: list[str] = Field(
        ...,
        description="Supported materials",
        example=["PLA", "PETG", "ABS"]
    )
    max_temp_nozzle: int = Field(..., ge=0, le=500, description="Max nozzle temp (°C)")
    max_temp_bed: int = Field(..., ge=0, le=200, description="Max bed temp (°C)")
    has_filament_sensor: bool = Field(True, description="Filament runout sensor")
    has_camera: bool = Field(True, description="Built-in camera")


class MQTTConfig(BaseModel):
    """MQTT connection configuration."""

    port: int = Field(8883, ge=1, le=65535, description="MQTT port")
    use_tls: bool = Field(True, description="Use TLS encryption")
    keepalive: int = Field(60, ge=10, le=3600, description="Keepalive interval (s)")
    timeout: int = Field(30, ge=5, le=300, description="Connection timeout (s)")


class FTPConfig(BaseModel):
    """FTP connection configuration."""

    port: int = Field(990, ge=1, le=65535, description="FTP port")
    use_tls: bool = Field(True, description="Use TLS encryption")
    timeout: int = Field(30, ge=5, le=300, description="Upload timeout (s)")


class PrinterConfig(BaseModel):
    """Printer connection and configuration."""

    # Identity
    printer_id: str = Field(..., description="Unique printer identifier")
    name: str = Field(..., description="Human-readable printer name")
    model: str = Field("Bambu Lab H2D", description="Printer model")

    # Connection
    ip: IPvAnyAddress = Field(..., description="Printer IP address")
    access_code: str = Field(..., min_length=8, max_length=16, description="Printer access code")
    serial: str = Field(..., min_length=10, max_length=20, description="Printer serial number")

    # Capabilities
    capabilities: PrinterCapabilities

    # Protocol config
    mqtt: MQTTConfig = Field(default_factory=MQTTConfig)
    ftp: FTPConfig = Field(default_factory=FTPConfig)

    # Monitoring
    status_poll_interval: float = Field(5.0, ge=1.0, le=60.0, description="Status poll interval (s)")

    @field_validator('access_code')
    @classmethod
    def validate_access_code(cls, v: str) -> str:
        """Validate access code format (alphanumeric)."""
        if not v.isalnum():
            raise ValueError("Access code must be alphanumeric")
        return v
```

---

### PrinterStatus

Real-time printer state and metrics.

```python
from enum import Enum
from pydantic import BaseModel, Field
from datetime import datetime


class PrinterState(str, Enum):
    """Printer operational states."""
    IDLE = "idle"              # Ready for jobs
    PRINTING = "printing"      # Active print
    PAUSED = "paused"          # Print paused
    ERROR = "error"            # Error state
    OFFLINE = "offline"        # Not reachable
    MAINTENANCE = "maintenance"  # Firmware update, calibration, etc.


class TemperatureReading(BaseModel):
    """Temperature sensor reading."""

    current: float = Field(..., description="Current temperature (°C)")
    target: float = Field(..., description="Target temperature (°C)")

    def is_stable(self, tolerance: float = 2.0) -> bool:
        """Check if temperature is stable (within tolerance of target)."""
        return abs(self.current - self.target) <= tolerance


class PrinterStatus(BaseModel):
    """Real-time printer status."""

    # Identity
    printer_id: str = Field(..., description="Printer identifier")

    # State
    state: PrinterState = Field(..., description="Current printer state")
    online: bool = Field(..., description="Printer reachable via network")

    # Current job (if any)
    current_job_id: str | None = Field(None, description="Active job ID")
    progress: float | None = Field(None, ge=0.0, le=100.0, description="Print progress %")
    current_layer: int | None = Field(None, ge=0, description="Current layer")
    total_layers: int | None = Field(None, ge=0, description="Total layers")
    time_remaining_seconds: int | None = Field(None, ge=0, description="Estimated time remaining")

    # Temperatures
    nozzle_temp: TemperatureReading | None = None
    bed_temp: TemperatureReading | None = None
    chamber_temp: TemperatureReading | None = None

    # Errors
    error_code: str | None = Field(None, description="Error code (if in error state)")
    error_message: str | None = Field(None, description="Human-readable error")

    # Metadata
    firmware_version: str | None = Field(None, description="Printer firmware version")
    last_updated: datetime = Field(default_factory=datetime.utcnow, description="Last status update")

    def can_accept_job(self) -> bool:
        """Check if printer can accept new job."""
        return self.state == PrinterState.IDLE and self.online
```

---

### QueueState

Persistent queue state for job management.

```python
from pydantic import BaseModel, Field
from typing import List


class QueueState(BaseModel):
    """Persistent print queue state."""

    # Job lists
    pending: list[str] = Field(default_factory=list, description="Pending job IDs (FIFO)")
    active: list[str] = Field(default_factory=list, description="Currently printing job IDs")
    completed: list[str] = Field(default_factory=list, description="Completed job IDs")
    failed: list[str] = Field(default_factory=list, description="Failed job IDs")

    # Metadata
    version: int = Field(1, description="Queue state schema version")
    last_modified: datetime = Field(default_factory=datetime.utcnow)

    def total_jobs(self) -> int:
        """Total number of jobs in queue."""
        return len(self.pending) + len(self.active) + len(self.completed) + len(self.failed)

    def next_job(self) -> str | None:
        """Get next pending job ID (FIFO)."""
        return self.pending[0] if self.pending else None

    def add_job(self, job_id: str) -> None:
        """Add job to pending queue."""
        if job_id not in self.pending:
            self.pending.append(job_id)
            self.last_modified = datetime.utcnow()

    def move_to_active(self, job_id: str) -> bool:
        """Move job from pending to active."""
        if job_id in self.pending:
            self.pending.remove(job_id)
            self.active.append(job_id)
            self.last_modified = datetime.utcnow()
            return True
        return False

    def move_to_completed(self, job_id: str) -> bool:
        """Move job from active to completed."""
        if job_id in self.active:
            self.active.remove(job_id)
            self.completed.append(job_id)
            self.last_modified = datetime.utcnow()
            return True
        return False

    def move_to_failed(self, job_id: str) -> bool:
        """Move job to failed list."""
        if job_id in self.active:
            self.active.remove(job_id)
        elif job_id in self.pending:
            self.pending.remove(job_id)

        if job_id not in self.failed:
            self.failed.append(job_id)
            self.last_modified = datetime.utcnow()
            return True
        return False
```

---

## Supporting Models

### PrintCommand

Command wrapper for printer operations.

```python
from enum import Enum
from pydantic import BaseModel, Field


class CommandType(str, Enum):
    """Printer command types."""
    START_PRINT = "start_print"
    PAUSE_PRINT = "pause_print"
    RESUME_PRINT = "resume_print"
    CANCEL_PRINT = "cancel_print"
    GET_STATUS = "get_status"


class PrintCommand(BaseModel):
    """Printer command wrapper."""

    command_type: CommandType = Field(..., description="Command to execute")
    job_id: str | None = Field(None, description="Associated job ID")
    filename: str | None = Field(None, description="G-code filename (for start_print)")
    parameters: dict[str, any] | None = Field(None, description="Additional parameters")

    # Execution metadata
    issued_at: datetime = Field(default_factory=datetime.utcnow)
    executed_at: datetime | None = None
    acknowledged: bool = Field(False, description="Printer acknowledged command")
```

---

## Model Relationships

```
QueueState
├── pending: List[job_id] ──────────┐
├── active: List[job_id] ───────────┤
├── completed: List[job_id] ────────┤
└── failed: List[job_id] ───────────┤
                                    │
                                    │ references
                                    ▼
                                PrintJob
                                ├── job_id
                                ├── gcode_path
                                ├── printer_id ─────────┐
                                ├── status              │
                                └── ...                 │
                                                        │ assigned to
                                                        ▼
                                                    PrinterConfig
                                                    ├── printer_id
                                                    ├── ip
                                                    ├── access_code
                                                    └── capabilities
                                                        │
                                                        │ monitors
                                                        ▼
                                                    PrinterStatus
                                                    ├── printer_id
                                                    ├── state
                                                    ├── current_job_id ──┐
                                                    └── ...              │
                                                                         │ references
                                                                         ▼
                                                                    PrintJob
```

---

## Serialization Examples

### PrintJob JSON

```json
{
  "job_id": "job_20251116_123456_abc123",
  "gcode_path": "/data/gcode/welcome_home.gcode",
  "printer_id": "bambu_h2d_01",
  "name": "Welcome Home Sign",
  "description": "Customer order #12345",
  "priority": 0,
  "status": "printing",
  "progress": 45.5,
  "current_layer": 128,
  "total_layers": 280,
  "created_at": "2025-11-16T12:34:56Z",
  "started_at": "2025-11-16T12:35:30Z",
  "estimated_duration_seconds": 3600,
  "retry_count": 0,
  "max_retries": 3
}
```

### PrinterStatus JSON

```json
{
  "printer_id": "bambu_h2d_01",
  "state": "printing",
  "online": true,
  "current_job_id": "job_20251116_123456_abc123",
  "progress": 45.5,
  "current_layer": 128,
  "total_layers": 280,
  "time_remaining_seconds": 1980,
  "nozzle_temp": {
    "current": 215.0,
    "target": 215.0
  },
  "bed_temp": {
    "current": 59.5,
    "target": 60.0
  },
  "firmware_version": "01.09.00.00",
  "last_updated": "2025-11-16T12:40:00Z"
}
```

### QueueState JSON

```json
{
  "pending": ["job_002", "job_003"],
  "active": ["job_001"],
  "completed": ["job_000"],
  "failed": [],
  "version": 1,
  "last_modified": "2025-11-16T12:40:00Z"
}
```

---

## Validation Rules

### PrintJob
- ✅ `gcode_path` must exist and have valid extension (.gcode, .gco, .g)
- ✅ `progress` must be 0.0-100.0
- ✅ `priority` defaults to 0 (normal), higher = more urgent
- ✅ `retry_count` cannot exceed `max_retries`

### PrinterConfig
- ✅ `ip` must be valid IP address (IPv4 or IPv6)
- ✅ `access_code` must be 8-16 alphanumeric characters
- ✅ `serial` must be 10-20 characters
- ✅ `status_poll_interval` must be 1.0-60.0 seconds

### PrinterStatus
- ✅ `progress` must be 0.0-100.0 if set
- ✅ `current_layer` <= `total_layers` if both set
- ✅ Temperature readings must have non-negative values

### QueueState
- ✅ No duplicate job IDs across pending/active/completed/failed lists
- ✅ `version` must match schema version (1)
- ✅ `last_modified` auto-updated on queue changes
