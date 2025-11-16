# Feature Specification: Printer Control

**Feature Branch**: `003-printer-control`
**Created**: 2025-11-16
**Status**: Draft
**Target Printer**: Bambu Lab H2D
**Dependencies**: 3D Model Pipeline (Feature 002)

## Overview

The Printer Control component provides direct communication and control of Bambu Lab 3D printer hardware. It manages G-code execution, print job initiation and monitoring, local job buffering, and real-time status tracking. The system operates locally with the printer, handling both networked (MQTT) and file-based (FTP) communication protocols.

## User Scenarios & Testing

### User Story 1 - Print Job Submission (Priority: P1)

As a LeSign operator, when I have a G-code file from the slicer, I can submit it to a Bambu Lab H2D printer and initiate the print job with appropriate material and quality settings.

**Why this priority**: Core MVP functionality - without this, no physical prints can be produced. Every print job must go through this component.

**Independent Test**: Can be fully tested by providing a valid G-code file, submitting it to the printer, and verifying the job starts successfully with correct settings.

**Acceptance Scenarios**:

1. **Given** a valid G-code file and printer connection details (IP, access code, serial), **When** I submit a print job, **Then** the system uploads the file via FTP and initiates printing via MQTT with confirmation

2. **Given** a print job submission, **When** the file upload completes, **Then** the system sends the start print command and receives acknowledgment from the printer within 30 seconds

3. **Given** multiple G-code files in the queue, **When** the printer becomes available, **Then** the system automatically submits the next job in FIFO order without manual intervention

4. **Given** a printer that is offline or unreachable, **When** I attempt to submit a job, **Then** the system queues the job locally and retries connection with exponential backoff (2s, 4s, 8s, 16s, 32s max)

---

### User Story 2 - Real-time Status Monitoring (Priority: P1)

As a LeSign operator, the system continuously monitors printer status (idle, printing, error) and provides real-time progress updates so I can track job completion and respond to issues immediately.

**Why this priority**: Essential for production reliability - operators need to know printer state, job progress, and error conditions to maintain workflow and prevent waste.

**Independent Test**: Can be tested by connecting to a printer, monitoring status changes, and verifying accurate reporting during idle, printing, and error states.

**Acceptance Scenarios**:

1. **Given** a connected printer, **When** the system polls printer status via MQTT, **Then** it accurately reports current state (idle, printing, paused, error, offline) with timestamps

2. **Given** an active print job, **When** the printer is printing, **Then** the system reports progress percentage, current layer, estimated time remaining, and temperature readings every 5 seconds

3. **Given** a print error occurs (filament runout, bed adhesion failure, etc.), **When** the printer reports the error via MQTT, **Then** the system immediately flags the job as failed with error details and sends notifications

4. **Given** a print job completion, **When** the printer finishes successfully, **Then** the system updates job status to "completed", records actual print time and material used, and readies the printer for the next job

---

### User Story 3 - Local Job Queue Management (Priority: P2)

As a LeSign operator, the system maintains a local queue of pending print jobs and automatically manages job scheduling, retry logic, and queue prioritization without manual intervention.

**Why this priority**: Important for automation and resilience but can be tested after basic print submission works. Initial MVP can use single job submission.

**Independent Test**: Can be tested by submitting multiple jobs, simulating failures, and verifying queue management logic handles jobs correctly.

**Acceptance Scenarios**:

1. **Given** multiple jobs submitted to the printer agent, **When** jobs are queued, **Then** the system maintains persistent queue state (survives agent restart) with job metadata (ID, G-code path, priority, submission time)

2. **Given** a job fails due to transient network error, **When** the failure is detected, **Then** the system automatically retries up to 3 times with exponential backoff before marking as failed

3. **Given** a high-priority job (e.g., rush order), **When** it's submitted to a non-empty queue, **Then** the system inserts it at the front of the queue while preserving FIFO order for same-priority jobs

4. **Given** the printer agent restarts, **When** it initializes, **Then** it recovers the queue state from persistent storage and resumes processing from where it left off

---

### User Story 4 - Multi-Printer Support (Priority: P3)

As a LeSign operator with multiple Bambu Lab printers, I can configure and control multiple printers from a single printer agent instance, with automatic load balancing and failover.

**Why this priority**: Valuable for scaling production but not blocking for MVP - single printer support is sufficient for initial deployment.

**Independent Test**: Can be tested by configuring multiple printer connections and verifying job distribution and failover logic.

**Acceptance Scenarios**:

1. **Given** multiple printers configured in printer agent settings, **When** a job is submitted, **Then** the system selects the first available idle printer and assigns the job

2. **Given** all printers are busy, **When** a new job arrives, **Then** the system queues the job and assigns it to the first printer that becomes available

3. **Given** one printer goes offline, **When** the agent detects the failure, **Then** it redistributes queued jobs to remaining healthy printers without manual intervention

4. **Given** printer-specific settings (different material profiles, build volumes), **When** job requirements are specified, **Then** the system only assigns jobs to compatible printers

---

### Edge Cases

- **Network interruption during file upload**: System should detect incomplete upload, clean up partial file, and retry from beginning

- **Printer power loss mid-print**: System should detect disconnection, mark job as failed, and not automatically retry (requires operator intervention for physical cleanup)

- **Corrupted G-code file**: System should validate G-code file integrity before upload and reject with clear error if invalid

- **Printer firmware updates**: System should detect when printer is in maintenance mode and avoid job submission until ready

## Technology Stack

### Core Dependencies

| Library | Version | Purpose |
|---------|---------|---------|
| `bambulabs_api` | latest | Official-ish Bambu Lab printer control library (MQTT/FTP) |
| `pydantic` | ^2.0 | Data validation and settings management |
| `paho-mqtt` | ^1.6 (via bambulabs_api) | MQTT protocol communication |
| `ftplib` | stdlib | FTP file transfer (part of Python standard library) |
| `structlog` | ^24.0 | Structured JSON logging |
| `tenacity` | ^8.0 | Retry logic with exponential backoff |

### Development Dependencies

| Library | Version | Purpose |
|---------|---------|---------|
| `pytest` | ^8.0 | Testing framework |
| `pytest-cov` | ^5.0 | Coverage reporting |
| `pytest-asyncio` | ^0.23 | Async test support |
| `pytest-mock` | ^3.14 | Mocking utilities |
| `ruff` | ^0.7.0 | Linting and formatting |
| `mypy` | ^1.7 | Type checking |

### Rationale

- **bambulabs_api**: Community-maintained library with active support for Bambu Lab printers, provides MQTT and FTP abstractions
- **paho-mqtt**: Industry-standard MQTT client library, dependency of bambulabs_api
- **tenacity**: Robust retry logic with exponential backoff, essential for network resilience
- **structlog**: JSON logging for production observability and debugging
- **pytest**: Standard Python testing framework, aligns with other LeSign components

**Note**: The bambulabs_api library has not been tested with H2D printers yet. Initial implementation may require testing and potential patches to ensure H2D compatibility.

## Architecture

### Component Structure

```
backend/printer-control/
├── src/
│   └── printer_control/
│       ├── __init__.py
│       ├── agent.py                # Main printer agent (job orchestration)
│       ├── printer.py              # Printer abstraction (MQTT/FTP wrapper)
│       ├── queue.py                # Local job queue management
│       ├── models.py               # Pydantic models (PrintJob, PrinterStatus, etc.)
│       ├── config.py               # Settings and configuration
│       └── exceptions.py           # Custom exceptions
├── tests/
│   ├── unit/
│   │   ├── test_printer.py
│   │   ├── test_queue.py
│   │   ├── test_agent.py
│   │   └── test_models.py
│   ├── integration/
│   │   ├── test_mqtt_integration.py
│   │   └── test_ftp_integration.py
│   └── contract/
│       └── test_printer_contract.py
├── config/
│   ├── printer_profiles/
│   │   └── bambu_h2d.json
│   └── settings.yaml
├── pyproject.toml
├── requirements.txt
├── README.md
└── CODE_GUIDELINES.md (symlink to ../../backend/CODE_GUIDELINES.md)
```

### Data Flow

```
┌─────────────────────────────────────────────────────────────┐
│                     Job Orchestrator                        │
│                 (upstream component)                        │
└────────────────────────┬────────────────────────────────────┘
                         │ submit_print_job(gcode_path, metadata)
                         ▼
┌─────────────────────────────────────────────────────────────┐
│                     Printer Agent                           │
│  - Receives jobs from orchestrator                          │
│  - Manages local queue                                      │
│  - Selects available printer                                │
│  - Handles retry logic                                      │
└────────────────────────┬────────────────────────────────────┘
                         │ enqueue_job()
                         ▼
┌─────────────────────────────────────────────────────────────┐
│                     Job Queue                               │
│  - Persistent queue (JSON file store)                       │
│  - FIFO ordering (with priority support)                    │
│  - Queue state recovery                                     │
└────────────────────────┬────────────────────────────────────┘
                         │ get_next_job()
                         ▼
┌─────────────────────────────────────────────────────────────┐
│                   Printer (Abstraction)                     │
│  - MQTT connection management                               │
│  - FTP file upload                                          │
│  - Status monitoring                                        │
│  - Command execution                                        │
└─────────┬───────────────────────────────────────────────────┘
          │
          ├─────────────────┐
          │                 │
          ▼                 ▼
┌──────────────────┐  ┌──────────────────┐
│  MQTT Protocol   │  │  FTP Protocol    │
│  (port 8883)     │  │  (port 990)      │
│  - Status poll   │  │  - Upload G-code │
│  - Start print   │  │  - File mgmt     │
│  - Pause/cancel  │  │                  │
└────────┬─────────┘  └────────┬─────────┘
         │                     │
         └──────────┬──────────┘
                    ▼
         ┌────────────────────┐
         │  Bambu Lab H2D     │
         │  3D Printer        │
         └────────────────────┘
```

### State Machine: Print Job Lifecycle

```
  ┌─────────┐
  │ PENDING │  (job submitted to queue)
  └────┬────┘
       │
       │ printer available
       ▼
  ┌─────────┐
  │UPLOADING│  (FTP upload in progress)
  └────┬────┘
       │
       ├───────┐ upload failed
       │       ▼
       │  ┌─────────┐
       │  │ RETRYING│  (exponential backoff)
       │  └────┬────┘
       │       │ retry attempts exhausted
       │       ▼
       │  ┌─────────┐
       │  │ FAILED  │  (terminal state)
       │  └─────────┘
       │
       │ upload success
       ▼
  ┌─────────┐
  │STARTING │  (MQTT start command sent)
  └────┬────┘
       │
       │ printer acknowledges
       ▼
  ┌─────────┐
  │PRINTING │  (active print, monitored via MQTT)
  └────┬────┘
       │
       ├───────┐ print completes
       │       ▼
       │  ┌─────────┐
       │  │COMPLETED│  (terminal state)
       │  └─────────┘
       │
       ├───────┐ error detected
       │       ▼
       │  ┌─────────┐
       │  │ ERROR   │  (terminal state, requires operator intervention)
       │  └─────────┘
       │
       └───────┐ cancelled
               ▼
          ┌─────────┐
          │CANCELLED│  (terminal state)
          └─────────┘
```

## Data Models

See `specs/003-printer-control/data-model.md` for complete Pydantic schemas.

**Core Models**:
- `PrintJob`: Job metadata, state, timestamps, retry count
- `PrinterConfig`: Printer connection details (IP, access code, serial, capabilities)
- `PrinterStatus`: Real-time printer state (state, temperature, progress, current_job)
- `PrintCommand`: Command wrapper (start, pause, cancel, status_update)
- `QueueState`: Persistent queue state (pending_jobs, active_jobs, completed_jobs)

## API Contract

See `specs/003-printer-control/contracts/api-contract.md` for complete API specifications.

**Core API**:

```python
# Printer Agent API (main interface)
agent = PrinterAgent(config)
agent.submit_job(gcode_path: Path, metadata: dict) -> PrintJob
agent.get_job_status(job_id: str) -> PrintJobStatus
agent.cancel_job(job_id: str) -> bool
agent.get_printer_status(printer_id: str) -> PrinterStatus
agent.get_queue_state() -> QueueState

# Printer API (low-level hardware interface)
printer = BambuLabPrinter(config)
printer.connect() -> bool
printer.disconnect()
printer.upload_file(local_path: Path, remote_name: str) -> bool
printer.start_print(filename: str) -> bool
printer.get_status() -> PrinterStatus
printer.pause_print() -> bool
printer.cancel_print() -> bool
```

## Configuration

### Environment Variables

```bash
# Printer connection
PRINTER_CONTROL_PRINTER_IP=192.168.1.100
PRINTER_CONTROL_ACCESS_CODE=12345678
PRINTER_CONTROL_SERIAL=01P00A000000000

# Queue management
PRINTER_CONTROL_QUEUE_PATH=./data/print_queue.json
PRINTER_CONTROL_MAX_RETRIES=3
PRINTER_CONTROL_RETRY_BASE_DELAY=2.0

# Monitoring
PRINTER_CONTROL_STATUS_POLL_INTERVAL=5.0
PRINTER_CONTROL_TIMEOUT=30.0

# Logging
PRINTER_CONTROL_LOG_LEVEL=INFO
```

### Printer Profile (JSON)

```json
{
  "printer_id": "bambu_h2d_01",
  "model": "Bambu Lab H2D",
  "ip": "192.168.1.100",
  "access_code": "12345678",
  "serial": "01P00A000000000",
  "capabilities": {
    "build_volume": {"x": 256, "y": 256, "z": 256},
    "materials": ["PLA", "PETG", "ABS", "TPU"],
    "max_temp_nozzle": 300,
    "max_temp_bed": 110
  },
  "mqtt": {
    "port": 8883,
    "use_tls": true,
    "keepalive": 60
  },
  "ftp": {
    "port": 990,
    "use_tls": true,
    "timeout": 30
  }
}
```

## Testing Strategy

### Unit Tests (>90% coverage target)

- `test_printer.py`: Printer class methods with mocked MQTT/FTP
- `test_queue.py`: Queue operations (enqueue, dequeue, persistence, priority)
- `test_agent.py`: Agent orchestration logic with mocked printer
- `test_models.py`: Pydantic model validation and serialization

### Integration Tests

- `test_mqtt_integration.py`: Real MQTT communication (requires test printer or mock broker)
- `test_ftp_integration.py`: Real FTP upload (requires test printer or FTP server)

### Contract Tests

- `test_printer_contract.py`: Verify API contract matches specification
- Input/output validation for all public APIs
- Error handling and exception contracts

### Test Fixtures

- Mock printer responses (MQTT status messages, FTP acknowledgments)
- Sample G-code files (small, large, invalid)
- Queue state fixtures (empty, single job, multiple jobs)
- Printer configuration fixtures (single printer, multi-printer)

## Success Metrics

### Phase 1 (MVP - Single Printer)
- ✅ Successfully submit and start print job on H2D printer
- ✅ Monitor print status and detect completion
- ✅ Handle network failures with retry logic
- ✅ >90% test coverage

### Phase 2 (Production - Queue Management)
- ✅ Persistent queue survives agent restart
- ✅ Automatic retry on transient failures (max 3 attempts)
- ✅ Job priority support (rush orders)
- ✅ Graceful error handling and reporting

### Phase 3 (Scale - Multi-Printer)
- ✅ Load balancing across multiple H2D printers
- ✅ Failover when printer goes offline
- ✅ Printer-specific job routing based on capabilities
- ✅ Production metrics (job throughput, success rate, error rate)

## Security Considerations

1. **Credential Storage**: Access codes stored in environment variables or encrypted config files (not in code)
2. **TLS Encryption**: All MQTT and FTP communication uses TLS encryption
3. **Network Isolation**: Printer control runs on isolated network segment (production deployment)
4. **Input Validation**: G-code file validation before upload to prevent malicious code execution
5. **Developer Mode**: Bambu Lab printers require Developer Mode enabled for local API access (document in setup guide)

## Deployment

### Local Development
```bash
cd backend/printer-control
uv venv --python 3.12
uv sync
uv run pytest
```

### Production Deployment
- Docker container for printer agent
- Persistent volume for queue state
- Environment variables for printer configuration
- Systemd service or Kubernetes deployment for auto-restart
- Monitoring and alerting for printer offline events

## Open Questions

1. **H2D Compatibility**: bambulabs_api library untested with H2D - may require patches or fallback to direct MQTT/FTP
2. **Camera Integration**: Do we need camera feed for quality monitoring? (User Story 5 - future)
3. **Multi-tenancy**: How to handle multiple customers' jobs on shared printers? (future)
4. **Filament Management**: Track filament inventory and auto-pause when low? (future)

## References

- [Bambu Lab Wiki - Third-party Integration](https://wiki.bambulab.com/en/software/third-party-integration)
- [bambulabs_api GitHub](https://github.com/BambuTools/bambulabs_api)
- [Bambu Lab MQTT Protocol](https://forum.bambulab.com/t/mqtt-support/58793)
- LeSign Constitution: `.specify/memory/constitution.md`
- Feature 002 (3D Pipeline): `specs/002-3d-model-pipeline/spec.md`
