# API Contract: Printer Control

**Feature**: 003-printer-control
**Last Updated**: 2025-11-16

## Overview

This document defines the public API contracts for the Printer Control component. All APIs use type-safe Pydantic models for validation and return structured responses.

---

## Printer Agent API

The `PrinterAgent` is the primary interface for upstream components (Job Orchestrator) to interact with printer hardware.

### Constructor

```python
from printer_control import PrinterAgent, PrinterConfig

agent = PrinterAgent(
    config: PrinterConfig,
    queue_path: Path = Path("./data/print_queue.json")
)
```

**Parameters**:
- `config`: Printer configuration (IP, access code, capabilities)
- `queue_path`: Path to persistent queue state file (optional)

**Raises**:
- `ValidationError`: Invalid configuration
- `ConnectionError`: Cannot connect to printer on initialization

---

### submit_job

Submit a new print job to the queue.

```python
def submit_job(
    gcode_path: Path,
    name: str | None = None,
    priority: int = 0,
    metadata: dict[str, any] | None = None
) -> PrintJob
```

**Parameters**:
- `gcode_path`: Path to G-code file (must exist, .gcode/.gco/.g extension)
- `name`: Human-readable job name (optional)
- `priority`: Job priority (higher = more urgent, default 0)
- `metadata`: Additional metadata (customer_id, design_id, etc.)

**Returns**: `PrintJob` object with `job_id` and initial state `PENDING`

**Raises**:
- `ValidationError`: Invalid G-code path or file doesn't exist
- `QueueError`: Queue is full or corrupted

**Example**:
```python
job = agent.submit_job(
    gcode_path=Path("/data/gcode/welcome_home.gcode"),
    name="Welcome Home Sign",
    priority=0,
    metadata={"customer_id": "cust_12345", "design_id": "design_001"}
)
print(f"Job submitted: {job.job_id}")
```

**Contract**:
- ✅ Job ID is unique UUID
- ✅ Initial status is `PENDING`
- ✅ `created_at` timestamp is set to current UTC time
- ✅ Job is added to queue immediately
- ✅ Returns within 100ms (queue operation only, no printer communication)

---

### get_job_status

Retrieve current status of a print job.

```python
def get_job_status(job_id: str) -> PrintJob
```

**Parameters**:
- `job_id`: Job identifier (UUID string)

**Returns**: `PrintJob` object with current state

**Raises**:
- `ValueError`: Job ID not found

**Example**:
```python
job = agent.get_job_status("job_20251116_123456_abc123")
print(f"Status: {job.status}, Progress: {job.progress}%")
```

**Contract**:
- ✅ Returns current job state (may be stale up to `status_poll_interval` seconds)
- ✅ Raises `ValueError` if job_id doesn't exist
- ✅ Returns within 50ms (in-memory lookup)

---

### cancel_job

Cancel a pending or active print job.

```python
def cancel_job(job_id: str) -> bool
```

**Parameters**:
- `job_id`: Job identifier

**Returns**: `True` if cancelled successfully, `False` if job not found or already terminal

**Raises**:
- `CommandError`: Printer communication failure during cancellation

**Example**:
```python
success = agent.cancel_job("job_20251116_123456_abc123")
if success:
    print("Job cancelled")
else:
    print("Job not found or already completed")
```

**Contract**:
- ✅ If job is `PENDING`: removed from queue, status → `CANCELLED`
- ✅ If job is `UPLOADING`/`STARTING`/`PRINTING`: MQTT cancel command sent, status → `CANCELLED`
- ✅ If job is terminal (`COMPLETED`/`FAILED`/`ERROR`): no-op, returns `False`
- ✅ Returns within 5s (includes MQTT command roundtrip)

---

### get_printer_status

Get current printer status (state, temperature, current job).

```python
def get_printer_status(printer_id: str | None = None) -> PrinterStatus
```

**Parameters**:
- `printer_id`: Printer identifier (optional for single-printer setups)

**Returns**: `PrinterStatus` object with real-time printer state

**Raises**:
- `ValueError`: Printer ID not found (multi-printer setups)
- `ConnectionError`: Printer offline or unreachable

**Example**:
```python
status = agent.get_printer_status()
print(f"State: {status.state}")
print(f"Nozzle: {status.nozzle_temp.current}°C / {status.nozzle_temp.target}°C")
if status.current_job_id:
    print(f"Printing: {status.current_job_id} ({status.progress}%)")
```

**Contract**:
- ✅ Polls printer via MQTT and returns fresh status
- ✅ Returns within `mqtt.timeout` seconds (default 30s)
- ✅ Raises `ConnectionError` if printer unreachable
- ✅ `last_updated` timestamp reflects actual poll time

---

### get_queue_state

Get current queue state (pending, active, completed jobs).

```python
def get_queue_state() -> QueueState
```

**Returns**: `QueueState` object with job ID lists

**Example**:
```python
queue = agent.get_queue_state()
print(f"Pending: {len(queue.pending)} jobs")
print(f"Active: {len(queue.active)} jobs")
print(f"Completed: {len(queue.completed)} jobs")
```

**Contract**:
- ✅ Returns current in-memory queue state
- ✅ Returns within 10ms (in-memory lookup)
- ✅ Job IDs can be used with `get_job_status()`

---

### start (Lifecycle)

Start the printer agent event loop (background processing).

```python
def start() -> None
```

**Behavior**:
- Loads queue state from persistent storage
- Connects to printer
- Starts background thread/task for queue processing
- Begins status monitoring

**Raises**:
- `ConnectionError`: Cannot connect to printer
- `QueueError`: Cannot load queue state

**Example**:
```python
agent = PrinterAgent(config)
agent.start()  # Runs in background
# ... submit jobs ...
agent.stop()
```

---

### stop (Lifecycle)

Stop the printer agent gracefully.

```python
def stop() -> None
```

**Behavior**:
- Stops queue processing loop
- Waits for active uploads to complete (up to 60s)
- Saves queue state to persistent storage
- Disconnects from printer

**Example**:
```python
agent.stop()  # Waits for graceful shutdown
```

**Contract**:
- ✅ Blocks until shutdown complete (max 60s)
- ✅ Saves queue state before exit
- ✅ Does NOT cancel active prints (printer continues)

---

## Printer API (Low-Level)

The `BambuLabPrinter` class provides direct hardware interface. Most users should use `PrinterAgent` instead.

### Constructor

```python
from printer_control import BambuLabPrinter, PrinterConfig

printer = BambuLabPrinter(config: PrinterConfig)
```

---

### connect

Establish MQTT connection to printer.

```python
def connect() -> bool
```

**Returns**: `True` if connected, `False` if failed

**Raises**:
- `AuthenticationError`: Invalid access code or serial
- `ConnectionError`: Network unreachable or timeout

**Contract**:
- ✅ Establishes TLS-encrypted MQTT connection (port 8883)
- ✅ Authenticates with access code
- ✅ Subscribes to status topics
- ✅ Returns within `mqtt.timeout` seconds

---

### disconnect

Close MQTT connection.

```python
def disconnect() -> None
```

**Contract**:
- ✅ Gracefully closes MQTT connection
- ✅ Unsubscribes from topics
- ✅ Returns within 5s

---

### upload_file

Upload G-code file to printer via FTP.

```python
def upload_file(
    local_path: Path,
    remote_name: str | None = None
) -> bool
```

**Parameters**:
- `local_path`: Local G-code file path
- `remote_name`: Remote filename (optional, defaults to local filename)

**Returns**: `True` if uploaded successfully

**Raises**:
- `ValidationError`: File doesn't exist or invalid format
- `UploadError`: FTP transfer failed
- `AuthenticationError`: FTP authentication failed

**Contract**:
- ✅ Uses TLS-encrypted FTP (port 990)
- ✅ Uploads to printer's internal storage
- ✅ Verifies file size after upload
- ✅ Returns within `ftp.timeout` * file_size_mb seconds

**Example**:
```python
printer.connect()
printer.upload_file(Path("/data/welcome.gcode"))
printer.disconnect()
```

---

### start_print

Start printing uploaded G-code file.

```python
def start_print(filename: str) -> bool
```

**Parameters**:
- `filename`: G-code filename on printer (from `upload_file`)

**Returns**: `True` if print started, `False` if failed

**Raises**:
- `CommandError`: MQTT command failed
- `ValidationError`: File not found on printer

**Contract**:
- ✅ Sends MQTT start command
- ✅ Waits for printer acknowledgment (max 30s)
- ✅ Returns `True` only if printer confirms start
- ✅ Raises `CommandError` if printer rejects (e.g., busy, error state)

---

### pause_print

Pause active print.

```python
def pause_print() -> bool
```

**Returns**: `True` if paused, `False` if no active print

**Contract**:
- ✅ Sends MQTT pause command
- ✅ Only works if printer state is `PRINTING`
- ✅ Returns `False` if already paused or idle

---

### cancel_print

Cancel active print.

```python
def cancel_print() -> bool
```

**Returns**: `True` if cancelled, `False` if no active print

**Contract**:
- ✅ Sends MQTT cancel command
- ✅ Printer stops immediately and homes axes
- ✅ Returns `True` if printer acknowledges cancellation

---

### get_status

Poll current printer status via MQTT.

```python
def get_status() -> PrinterStatus
```

**Returns**: `PrinterStatus` object

**Raises**:
- `ConnectionError`: MQTT connection lost

**Contract**:
- ✅ Sends MQTT status request
- ✅ Parses printer response into `PrinterStatus` model
- ✅ Returns within 5s (single MQTT roundtrip)
- ✅ Updates `last_updated` timestamp

---

## Error Contracts

All exceptions inherit from `PrinterControlError` base class.

### Exception Hierarchy

```python
PrinterControlError (base)
├── ConnectionError           # Network/MQTT/FTP connection failures
├── AuthenticationError       # Invalid credentials
├── UploadError              # FTP upload failures
├── CommandError             # MQTT command execution failures
├── QueueError               # Queue operations failures
└── ValidationError          # Input validation failures
```

### Error Response Format

All exceptions include:
- `message`: Human-readable error description
- `details`: Dict with additional context (printer_id, job_id, error_code, etc.)
- `timestamp`: When error occurred

**Example**:
```python
try:
    printer.upload_file(Path("/invalid.gcode"))
except UploadError as e:
    print(f"Upload failed: {e.message}")
    print(f"Details: {e.details}")
    # Details: {"printer_id": "bambu_h2d_01", "error_code": "ftp_timeout"}
```

---

## Threading & Concurrency

### Thread Safety

- ✅ `PrinterAgent` is thread-safe for `submit_job()`, `get_job_status()`, `cancel_job()`
- ✅ `BambuLabPrinter` is NOT thread-safe (single connection per instance)
- ✅ Queue operations use locks for concurrent access

### Background Processing

- `PrinterAgent.start()` spawns background thread for queue processing
- Status polling runs in separate thread (every `status_poll_interval` seconds)
- Upstream components can call API methods from any thread

---

## Monitoring & Observability

### Structured Logging

All API calls log structured JSON events:

```json
{
  "event": "job_submitted",
  "timestamp": "2025-11-16T12:34:56Z",
  "job_id": "job_20251116_123456_abc123",
  "gcode_path": "/data/welcome.gcode",
  "priority": 0,
  "queue_depth": 3
}
```

### Metrics (Future)

Exposed via health check endpoint:
- `queue_depth_pending`: Number of pending jobs
- `queue_depth_active`: Number of active jobs
- `jobs_completed_total`: Total completed jobs
- `jobs_failed_total`: Total failed jobs
- `printer_online`: Boolean (1 = online, 0 = offline)
- `current_print_progress`: Current job progress (0-100)

---

## Versioning

**Current Version**: `0.1.0` (MVP)

**Breaking Changes Policy**:
- Major version bump (1.0 → 2.0) for incompatible API changes
- Minor version bump (1.0 → 1.1) for backwards-compatible additions
- Patch version bump (1.0.0 → 1.0.1) for bug fixes

**Deprecation Policy**:
- Deprecated APIs marked with warnings for 2 minor versions before removal
- Migration guide provided for breaking changes

---

## Examples

### End-to-End Workflow

```python
from pathlib import Path
from printer_control import PrinterAgent, PrinterConfig

# Configure printer
config = PrinterConfig(
    printer_id="bambu_h2d_01",
    name="Bambu Lab H2D #1",
    ip="192.168.1.100",
    access_code="12345678",
    serial="01P00A000000000",
    capabilities=PrinterCapabilities(
        build_volume={"x": 256, "y": 256, "z": 256},
        materials=["PLA", "PETG"],
        max_temp_nozzle=300,
        max_temp_bed=110
    )
)

# Initialize agent
agent = PrinterAgent(config)
agent.start()

try:
    # Submit job
    job = agent.submit_job(
        gcode_path=Path("/data/gcode/welcome_home.gcode"),
        name="Welcome Home Sign",
        priority=0
    )
    print(f"Job submitted: {job.job_id}")

    # Monitor progress
    while True:
        status = agent.get_job_status(job.job_id)
        print(f"Status: {status.status}, Progress: {status.progress}%")

        if status.is_terminal():
            break

        time.sleep(5)

    # Check final status
    if status.status == PrintJobStatus.COMPLETED:
        print("Print completed successfully!")
    else:
        print(f"Print failed: {status.error_message}")

finally:
    agent.stop()
```

### Error Handling

```python
from printer_control import PrinterAgent, ConnectionError, QueueError

agent = PrinterAgent(config)

try:
    agent.start()
except ConnectionError as e:
    print(f"Cannot connect to printer: {e.message}")
    print(f"Check printer IP and access code")
    sys.exit(1)

try:
    job = agent.submit_job(Path("/data/invalid.gcode"))
except ValidationError as e:
    print(f"Invalid G-code file: {e.message}")
except QueueError as e:
    print(f"Queue full or corrupted: {e.message}")
```

---

## Testing Contract

All public APIs must have:
- ✅ Unit tests with mocked dependencies
- ✅ Integration tests with real printer (or mock MQTT broker)
- ✅ Contract tests verifying input/output schemas
- ✅ Error scenario tests for all `Raises` cases

See `specs/003-printer-control/plan.md` for detailed test plan.
