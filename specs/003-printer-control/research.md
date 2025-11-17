# Research: Printer Control Implementation

**Date**: 2025-11-16
**Feature**: Printer Control (003-printer-control)
**Purpose**: Resolve technical unknowns and establish implementation approach

## Research Questions

### 1. Primary Library Choice: bambulabs-api vs Direct Implementation

**Decision**: Use `bambulabs-api` with H2D validation and abstraction layer

**Rationale**:
- **Maturity**: Most actively maintained Bambu Lab library (229 stars, 42 forks, regular updates)
- **Documentation**: Comprehensive docs and examples at https://bambutools.github.io/bambulabs_api/
- **Testing**: Includes automated testing (flake8, pytest), quality assurance
- **Community**: Largest user base provides support and bug reports
- **API Design**: Clean, Pythonic interface following best practices
- **Compatibility**: Python 3.10+ (compatible with our 3.12 requirement)
- **Risk Mitigation**: Abstract HardwareInterface layer allows library swap if H2D issues found

**Alternatives Considered**:

| Alternative | Pros | Cons | Rejected Because |
|-------------|------|------|------------------|
| paho-mqtt + ftplib (direct) | Full control, no 3rd-party deps | More implementation work, protocol details, error handling complexity | Reinventing well-tested wheel, increases development time for POC |
| bambu-connect | Clean API, camera support | Smaller community, less documentation, only tested on P1S | Lower confidence, less community support for troubleshooting |
| pybambu | Battle-tested in Home Assistant | Currently not up-to-date (acknowledged by maintainers) | May lack recent protocol updates, maintenance concerns |

**Caveat**: H2D printer is **untested** with bambulabs-api according to documentation. Mitigation:
1. Early hardware validation testing (Phase 1, Week 1) before full implementation
2. Abstract `HardwareInterface` as thin wrapper enabling library substitution
3. Document H2D-specific behaviors/quirks
4. Contribute fixes back to bambulabs-api if issues found

**Dependencies**:
```
bambulabs-api>=1.0.0  # Main printer control library
pydantic>=2.0.0       # Data models and validation
pydantic-settings>=2.0.0  # Environment configuration
```

### 2. File Format Handling: G-code vs 3MF

**Decision**: Convert G-code to 3MF using ZIP wrapper approach

**Rationale**:
- **Wireless Control**: Bambu printers prefer 3MF for full MQTT control (start/pause/resume/stop)
- **G-code Limitation**: Raw G-code can be uploaded but requires manual button press to start
- **Automation Goal**: 3MF enables zero-touch printing per spec requirement (SC-007)
- **Simplicity**: ZIP wrapper approach is lightweight and testable

**Implementation Approach**:
```python
import zipfile
from pathlib import Path

def gcode_to_3mf(gcode_path: Path, output_path: Path) -> Path:
    """Wrap G-code in 3MF container for Bambu printer."""
    gcode_content = gcode_path.read_bytes()

    with zipfile.ZipFile(output_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        # Add G-code to 3MF structure
        zipf.writestr("Metadata/plate_1.gcode", gcode_content)

        # Add required 3MF manifest
        manifest = '''<?xml version="1.0" encoding="UTF-8"?>
<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">
  <Default Extension="gcode" ContentType="text/plain"/>
</Types>'''
        zipf.writestr("[Content_Types].xml", manifest)

    return output_path
```

**Alternatives Considered**:
- **Option A**: Use `to-3mf` library for proper 3MF packaging
  - Pro: Spec-compliant 3MF structure
  - Con: Additional dependency, may be overkill for POC
  - Rejected: ZIP wrapper sufficient for POC, can upgrade later

- **Option B**: Switch to Bambu Studio for slicing (native 3MF output)
  - Pro: Native format compatibility guaranteed
  - Con: Adds proprietary software dependency, breaks PrusaSlicer pipeline
  - Rejected: Violates local-first principle, complicates pipeline

**Testing Strategy**: Create minimal test 3MF files in Phase 1, validate printer acceptance early

### 3. Communication Protocols: MQTT + FTP

**Decision**: Use standard protocols with TLS encryption

**MQTT (Control & Status)**:
- **Protocol**: MQTT v3.1.1 over TLS
- **Port**: 8883 (TLS encrypted)
- **Library**: paho-mqtt (included with bambulabs-api)
- **Topics**:
  - Subscribe: `device/{SERIAL}/report` (status updates from printer)
  - Publish: `device/{SERIAL}/request` (commands to printer)
- **Message Format**: JSON with sequence IDs
- **Reconnection**: Auto-reconnect via paho-mqtt `loop_start()` + `on_connect` callback

**FTP (File Transfer)**:
- **Protocol**: FTPS (FTP over TLS)
- **Port**: 990 (implicit TLS)
- **Library**: Python ftplib with TLS support (standard library)
- **Credentials**: Username `bblp`, password is printer access code
- **Upload Directory**: `/` or `/gcodes/`
- **Validation**: Check FTP response code 226 for success

**Security**:
- All communication encrypted (TLS for MQTT, FTPS for file transfer)
- Credentials stored in environment variables (never hardcoded)
- Access code masked in logs (first 7 chars + "***")

### 4. Queue Persistence Strategy

**Decision**: File-based JSON queue with atomic writes

**Rationale**:
- **Simplicity**: Aligns with local-first POC principle
- **Reliability**: Atomic file operations prevent corruption
- **Inspection**: Human-readable JSON for debugging
- **No Dependencies**: No database or message queue infrastructure needed

**Implementation Pattern**:
```python
import json
from pathlib import Path
import tempfile

class PrintJobQueue:
    def __init__(self, queue_file: Path):
        self.queue_file = queue_file

    def save(self, jobs: list):
        """Atomic write: temp file + rename."""
        temp_fd, temp_path = tempfile.mkstemp(dir=self.queue_file.parent)
        try:
            with os.fdopen(temp_fd, 'w') as f:
                json.dump([job.dict() for job in jobs], f, indent=2)
            os.replace(temp_path, self.queue_file)  # Atomic on POSIX
        except Exception:
            os.unlink(temp_path)
            raise
```

**Validation on Startup**:
- Check file integrity (valid JSON)
- Reconcile with printer state (mark stale jobs as failed)
- Remove invalid entries
- Log recovery actions

**Alternatives Considered**:
- **SQLite**: More structure, ACID guarantees
  - Rejected: Adds dependency, overkill for POC scale (<100 jobs)
- **Redis**: Fast, rich data structures
  - Rejected: Requires external service, violates local-first

### 5. Error Code Translation

**Decision**: Build HMS error code lookup table from official documentation

**Source**: Bambu Lab Wiki HMS error code reference (https://wiki.bambulab.com/en/hms/error-code)

**Implementation**:
```python
# src/utils/hms_errors.py
HMS_ERROR_CODES = {
    "0500-0500-0001-0007": {
        "message": "MQTT command verification failed",
        "cause": "Invalid command format or parameters",
        "resolution": "Check command structure and retry"
    },
    # ... more mappings
}

def translate_hms_error(code: str) -> str:
    """Convert HMS error code to human-readable message."""
    if code in HMS_ERROR_CODES:
        error = HMS_ERROR_CODES[code]
        return f"{error['message']}. Cause: {error['cause']}. Resolution: {error['resolution']}"
    return f"Unknown error code: {code}. Check printer display for details."
```

**Population Strategy**: Start with common errors from investigation, expand based on actual POC testing

### 6. Connection Health Monitoring

**Decision**: Watchdog thread + keepalive + timeout detection

**Pattern**:
```python
import threading
import time

class ConnectionMonitor:
    def __init__(self, hardware_interface, check_interval=30):
        self.interface = hardware_interface
        self.check_interval = check_interval
        self.last_message = time.time()
        self.running = False

    def start(self):
        self.running = True
        self.thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self.thread.start()

    def _monitor_loop(self):
        while self.running:
            time.sleep(self.check_interval)
            if time.time() - self.last_message > self.check_interval * 2:
                logger.warning("Connection appears stale, reconnecting...")
                self.interface.reconnect()
```

**Metrics**:
- Track `last_message` timestamp on every MQTT message received
- Alert if no messages for 2x check_interval (default 60s)
- Automatic reconnect on timeout

### 7. Testing Infrastructure

**Decision**: Three-tier testing strategy (contract/integration/unit)

**Contract Tests** (Validate Interfaces):
```python
# tests/contract/test_print_request.py
from pydantic import ValidationError
import pytest

def test_print_request_schema():
    """Validate PrintRequest matches slicer contract."""
    request = PrintRequest(
        job_id="job_001",
        gcode_file_path=Path("/path/to/file.gcode"),
        material="PLA",
        estimated_time_minutes=45,
        estimated_filament_grams=75.0
    )
    assert request.job_id == "job_001"

def test_print_request_rejects_invalid():
    """Ensure validation catches bad inputs."""
    with pytest.raises(ValidationError):
        PrintRequest(job_id="", gcode_file_path=Path("/missing"))
```

**Integration Tests** (Mock MQTT/FTP):
```python
# tests/integration/test_mqtt_integration.py
from unittest.mock import Mock, patch

@patch('paho.mqtt.client.Client')
def test_mqtt_status_subscription(mock_mqtt):
    """Verify MQTT topic subscription and message parsing."""
    interface = BambuHardwareInterface(settings)
    interface.connect()

    # Simulate status message from printer
    mock_mqtt.return_value.on_message(None, None,
        MQTTMessage(topic=b"device/ABC123/report",
                   payload=b'{"gcode_state":"printing","mc_percent":50}'))

    status = interface.get_status()
    assert status.state == "printing"
    assert status.progress_percent == 50
```

**Unit Tests** (Isolated Components):
```python
# tests/unit/test_printer_agent.py
def test_submit_job_when_printer_idle(mocker):
    """Job starts immediately when printer available."""
    mock_hardware = mocker.Mock(spec=BambuHardwareInterface)
    mock_hardware.get_status.return_value = PrinterStatus(state="idle")

    agent = PrinterAgent(hardware=mock_hardware)
    result = agent.submit_job(Path("test.gcode"), "job_001")

    assert result.status == "printing"
    mock_hardware.upload_file.assert_called_once()
    mock_hardware.start_print.assert_called_once()
```

**Coverage Target**: >90% (exceeds 80% constitution requirement)

**Mocking Strategy**:
- MQTT: Mock paho.mqtt.client.Client
- FTP: Mock ftplib.FTP_TLS
- Printer hardware: Mock entire BambuHardwareInterface for agent/queue tests
- File I/O: Use tmp_path pytest fixture

## Implementation Approach Summary

### Phase 1 (Week 1-2): Hardware Interface MVP
1. Install bambulabs-api and dependencies
2. Implement BambuHardwareInterface wrapper:
   - `connect()` / `disconnect()`
   - `upload_file()` with FTPS
   - `start_print()` / `stop_print()` via MQTT
   - `get_status()` with status parsing
3. Implement G-code→3MF conversion utility
4. Write contract tests validating interfaces
5. Manual H2D testing to validate library compatibility
6. Document any H2D-specific quirks

### Phase 2 (Week 2-3): Printer Agent & Integration
1. Implement PrinterAgent orchestration:
   - `submit_job()` (single job, no queue)
   - `get_job_status()`
   - `cancel_job()`
2. Implement Pydantic models (PrintRequest, JobResult, JobStatus, PrinterStatus)
3. Implement exception hierarchy
4. Write unit tests (agent, converter)
5. Write integration tests (MQTT, FTP mocked)
6. Test end-to-end: G-code → 3MF → Upload → Print

### Phase 3 (Week 3-4): End-to-End POC
1. Integrate with slicer component
2. Run complete pipeline test (text "SARAH" → physical print)
3. Validate success criteria (SC-001: <2 hours, SC-008: quality match)
4. Document performance metrics
5. Fix any integration issues

### Phase 4 (Week 4-5+): Queue & Hardening
1. Implement PrintJobQueue with file persistence
2. Automatic job dispatch on printer idle
3. Connection health monitoring (watchdog)
4. Comprehensive error recovery
5. HMS error code mapping
6. Performance optimization
7. Production deployment docs

## Open Questions for Implementation

None at this stage. All research questions resolved. Ready to proceed to Phase 1 (Data Model & Contracts).
