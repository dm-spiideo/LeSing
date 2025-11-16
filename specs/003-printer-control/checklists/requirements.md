# Requirements Checklist: Printer Control

**Feature**: 003-printer-control
**Status**: Implementation

---

## Functional Requirements

### Core Functionality

- [ ] **F1.1**: Connect to Bambu Lab H2D printer via MQTT (port 8883, TLS)
- [ ] **F1.2**: Authenticate using access code and serial number
- [ ] **F1.3**: Upload G-code files via FTP (port 990, TLS)
- [ ] **F1.4**: Start print job via MQTT command
- [ ] **F1.5**: Pause active print job
- [ ] **F1.6**: Cancel active print job
- [ ] **F1.7**: Poll printer status (state, temperature, progress)
- [ ] **F1.8**: Detect print completion automatically

### Queue Management

- [ ] **F2.1**: Accept print jobs from upstream (Job Orchestrator)
- [ ] **F2.2**: Queue jobs in FIFO order
- [ ] **F2.3**: Persist queue state to disk (JSON file)
- [ ] **F2.4**: Recover queue state after agent restart
- [ ] **F2.5**: Support job priority (higher priority jumps queue)
- [ ] **F2.6**: Automatic retry on transient failures (max 3 attempts)
- [ ] **F2.7**: Exponential backoff for retries (2s, 4s, 8s, 16s, 32s)
- [ ] **F2.8**: Remove jobs from queue on terminal state (completed/failed/cancelled)

### Monitoring & Status

- [ ] **F3.1**: Real-time printer state tracking (idle, printing, paused, error, offline)
- [ ] **F3.2**: Track print progress (percentage, current layer, time remaining)
- [ ] **F3.3**: Monitor nozzle and bed temperatures
- [ ] **F3.4**: Detect printer errors and report to upstream
- [ ] **F3.5**: Track job lifecycle (pending → uploading → starting → printing → completed/failed)
- [ ] **F3.6**: Expose queue status API (pending, active, completed jobs)

### Error Handling

- [ ] **F4.1**: Retry network failures (connection timeout, FTP timeout)
- [ ] **F4.2**: Do NOT retry fatal errors (authentication failure, invalid G-code)
- [ ] **F4.3**: Mark jobs as failed after max retries exhausted
- [ ] **F4.4**: Detect printer offline and queue jobs until reconnection
- [ ] **F4.5**: Log all errors with structured context (job_id, printer_id, error_code)

---

## Non-Functional Requirements

### Performance

- [ ] **N1.1**: Job submission returns within 100ms (queue operation only)
- [ ] **N1.2**: Status query returns within 50ms (in-memory lookup)
- [ ] **N1.3**: G-code upload completes within timeout (30s + 1s/MB file size)
- [ ] **N1.4**: MQTT commands acknowledged within 5s
- [ ] **N1.5**: Status polling interval configurable (default 5s)

### Reliability

- [ ] **N2.1**: Queue state survives agent crash/restart
- [ ] **N2.2**: No data loss on unexpected shutdown
- [ ] **N2.3**: Automatic reconnection on network failure
- [ ] **N2.4**: Graceful degradation when printer offline (queue buffering)
- [ ] **N2.5**: Active prints continue if agent restarts (printer-side execution)

### Security

- [ ] **N3.1**: Access code stored in environment variables (not in code)
- [ ] **N3.2**: TLS encryption for all MQTT and FTP communication
- [ ] **N3.3**: No logging of sensitive credentials (access codes masked)
- [ ] **N3.4**: G-code file validation before upload (size, format, integrity)
- [ ] **N3.5**: Developer Mode required for printer access (documented in setup)

### Observability

- [ ] **N4.1**: Structured JSON logging for all events
- [ ] **N4.2**: Log job lifecycle events (submit, upload, start, progress, complete)
- [ ] **N4.3**: Log printer status changes (idle → printing → idle)
- [ ] **N4.4**: Log errors with full context (stack traces, request details)
- [ ] **N4.5**: Configurable log level (DEBUG, INFO, WARNING, ERROR)

### Maintainability

- [ ] **N5.1**: Clear separation of concerns (agent, printer, queue)
- [ ] **N5.2**: Type hints for all public APIs (mypy validation)
- [ ] **N5.3**: Pydantic models for all data structures
- [ ] **N5.4**: Comprehensive docstrings (Google style)
- [ ] **N5.5**: >90% test coverage (pytest)

---

## Testing Requirements

### Unit Tests

- [ ] **T1.1**: Model validation tests (valid/invalid inputs)
- [ ] **T1.2**: Printer class tests (mocked MQTT/FTP)
- [ ] **T1.3**: Queue operations tests (enqueue, dequeue, persistence)
- [ ] **T1.4**: Agent orchestration tests (job lifecycle)
- [ ] **T1.5**: Configuration loading tests (env vars, YAML)
- [ ] **T1.6**: Error handling tests (all exception types)

### Integration Tests

- [ ] **T2.1**: Real MQTT connection test (test broker or H2D printer)
- [ ] **T2.2**: Real FTP upload test (test server or H2D printer)
- [ ] **T2.3**: End-to-end workflow test (submit → upload → print → complete)
- [ ] **T2.4**: Network failure recovery test (simulated disconnect)
- [ ] **T2.5**: Queue persistence test (restart agent mid-job)

### Contract Tests

- [ ] **T3.1**: API contract validation (input/output schemas)
- [ ] **T3.2**: Error contract validation (exception types and messages)
- [ ] **T3.3**: Queue state contract (JSON schema validation)

### Coverage Goals

- [ ] **T4.1**: Overall coverage ≥90%
- [ ] **T4.2**: Core modules (printer, queue, agent) ≥95%
- [ ] **T4.3**: Models and config ≥85%
- [ ] **T4.4**: Integration tests cover all happy paths
- [ ] **T4.5**: Integration tests cover all error scenarios

---

## Documentation Requirements

- [ ] **D1**: Complete README.md with setup instructions
- [ ] **D2**: Quickstart guide (15-minute first print)
- [ ] **D3**: API reference documentation (all public methods)
- [ ] **D4**: Bambu Lab Developer Mode setup guide
- [ ] **D5**: Troubleshooting guide (common errors and solutions)
- [ ] **D6**: Configuration reference (env vars, YAML options)
- [ ] **D7**: Example code for common use cases
- [ ] **D8**: Production deployment guide (systemd, Docker)

---

## Dependencies

### Python Libraries

- [ ] **L1**: bambulabs-api (Bambu Lab printer control)
- [ ] **L2**: pydantic (data validation)
- [ ] **L3**: pydantic-settings (configuration management)
- [ ] **L4**: tenacity (retry logic)
- [ ] **L5**: structlog (structured logging)
- [ ] **L6**: pytest (testing framework)
- [ ] **L7**: pytest-cov (coverage reporting)
- [ ] **L8**: pytest-mock (mocking utilities)
- [ ] **L9**: ruff (linting and formatting)
- [ ] **L10**: mypy (type checking)

### Hardware

- [ ] **H1**: Bambu Lab H2D printer (or compatible model)
- [ ] **H2**: Local network connectivity (LAN/Wi-Fi)
- [ ] **H3**: Developer Mode enabled on printer

### Upstream Dependencies

- [ ] **U1**: Feature 002 (3D Model Pipeline) - provides G-code files
- [ ] **U2**: Job Orchestration (Feature 004) - submits print jobs

---

## Compatibility

### Printer Models

- [ ] **C1.1**: Bambu Lab H2D (primary target)
- [ ] **C1.2**: Bambu Lab X1 Series (future)
- [ ] **C1.3**: Bambu Lab P1 Series (future)
- [ ] **C1.4**: Bambu Lab A1 Series (future)

### Python Versions

- [ ] **C2.1**: Python 3.12 (primary)
- [ ] **C2.2**: Python 3.11 (compatible)
- [ ] **C2.3**: Python 3.13 (when released)

### Operating Systems

- [ ] **C3.1**: Linux (Ubuntu 22.04+, production target)
- [ ] **C3.2**: macOS (development)
- [ ] **C3.3**: Windows (development, best-effort)

---

## Acceptance Criteria

### MVP (Phase 1)

- [x] Can connect to H2D printer
- [x] Can upload G-code file
- [x] Can start print job
- [x] Can monitor status and detect completion
- [x] >80% test coverage

### Production (Phase 2)

- [ ] Jobs queued and processed automatically
- [ ] Queue survives agent restart
- [ ] Automatic retry on transient failures
- [ ] >85% test coverage

### Production Ready (Phase 3)

- [ ] Structured logging
- [ ] Complete documentation
- [ ] >90% test coverage
- [ ] CI/CD pipeline

### Scale (Phase 4 - Future)

- [ ] Multi-printer support (2+ printers)
- [ ] Load balancing across printers
- [ ] Failover when printer offline

---

## Risk Mitigation

- [ ] **R1**: Test bambulabs_api with H2D printer early (compatibility unknown)
- [ ] **R2**: Prepare fallback to direct MQTT/FTP if library fails
- [ ] **R3**: Document Developer Mode security implications
- [ ] **R4**: Implement queue persistence early (prevent data loss)
- [ ] **R5**: Add timeout protections to all network operations

---

## Sign-off

### Phase 1 (MVP) Completion Checklist

- [ ] All Phase 1 functional requirements implemented
- [ ] All Phase 1 non-functional requirements met
- [ ] Unit tests written and passing (>80% coverage)
- [ ] Integration tests with H2D printer successful
- [ ] Documentation complete (README, quickstart)
- [ ] Code reviewed and approved
- [ ] No critical bugs or security issues

### Phase 2 (Production) Completion Checklist

- [ ] All Phase 2 functional requirements implemented
- [ ] Queue persistence verified (restart test passed)
- [ ] Retry logic tested with simulated failures
- [ ] Test coverage ≥85%
- [ ] Production deployment guide complete

### Phase 3 (Production Ready) Completion Checklist

- [ ] Structured logging implemented
- [ ] All documentation complete
- [ ] Test coverage ≥90%
- [ ] CI/CD pipeline configured and passing
- [ ] Production deployment successful
- [ ] Monitoring and alerting configured
