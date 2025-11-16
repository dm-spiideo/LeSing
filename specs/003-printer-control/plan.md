# Implementation Plan: Printer Control

**Feature**: 003-printer-control
**Created**: 2025-11-16
**Status**: Draft → Implementation
**Timeline**: 2-3 days for MVP

---

## Implementation Phases

### Phase 1: Foundation (MVP)
**Goal**: Single printer support with basic print job submission and monitoring
**Duration**: 1 day
**Priority**: P1

#### Tasks

1. **Project Setup** (1 hour)
   - [ ] Create `backend/printer-control/` directory structure
   - [ ] Initialize `pyproject.toml` with dependencies
   - [ ] Create `requirements.txt`
   - [ ] Set up test directory structure
   - [ ] Create README.md and symlink CODE_GUIDELINES.md

2. **Data Models** (2 hours)
   - [ ] Implement `models.py` with Pydantic schemas:
     - `PrintJob`, `PrintJobStatus`, `PrintJobUpdate`
     - `PrinterConfig`, `PrinterCapabilities`, `MQTTConfig`, `FTPConfig`
     - `PrinterStatus`, `PrinterState`, `TemperatureReading`
     - `QueueState`
     - `PrintCommand`, `CommandType`
   - [ ] Write unit tests for model validation
   - [ ] Test serialization/deserialization

3. **Configuration** (1 hour)
   - [ ] Implement `config.py` with pydantic-settings
   - [ ] Create `config/printer_profiles/bambu_h2d.json` template
   - [ ] Environment variable loading (.env support)
   - [ ] Write config validation tests

4. **Exceptions** (30 min)
   - [ ] Implement `exceptions.py` with custom exception hierarchy:
     - `PrinterControlError` (base)
     - `ConnectionError`, `AuthenticationError`
     - `UploadError`, `CommandError`
     - `QueueError`, `ValidationError`

5. **Printer Abstraction** (4 hours)
   - [ ] Implement `printer.py` with `BambuLabPrinter` class:
     - `connect()` / `disconnect()` - MQTT connection management
     - `upload_file()` - FTP G-code upload
     - `start_print()` / `pause_print()` / `cancel_print()` - MQTT commands
     - `get_status()` - MQTT status polling
   - [ ] Wrap bambulabs_api library
   - [ ] Handle authentication and TLS
   - [ ] Implement retry logic with tenacity
   - [ ] Write unit tests with mocked MQTT/FTP

6. **Integration Testing** (2 hours)
   - [ ] Test with actual H2D printer (if available) OR mock MQTT broker
   - [ ] Verify upload, start, status, cancel operations
   - [ ] Test error handling and reconnection
   - [ ] Document H2D-specific quirks if discovered

**Deliverables**:
- ✅ Printer class can connect to H2D printer
- ✅ Can upload G-code file via FTP
- ✅ Can start print and receive acknowledgment
- ✅ Can monitor status and detect completion
- ✅ >80% test coverage for Phase 1 code

---

### Phase 2: Queue Management
**Goal**: Local job queue with persistence and retry logic
**Duration**: 0.5 day
**Priority**: P1

#### Tasks

1. **Job Queue** (3 hours)
   - [ ] Implement `queue.py` with `PrintQueue` class:
     - `enqueue()` / `dequeue()` - Job queue operations
     - `save()` / `load()` - Persistent state (JSON file)
     - `get_next_job()` - FIFO job selection
     - `update_job_status()` - Job state transitions
   - [ ] Implement priority support (optional for MVP)
   - [ ] Write queue tests (empty, single, multiple jobs)

2. **Printer Agent** (3 hours)
   - [ ] Implement `agent.py` with `PrinterAgent` class:
     - `submit_job()` - Accept job from upstream
     - `process_queue()` - Main event loop
     - `assign_job_to_printer()` - Job assignment
     - `monitor_active_jobs()` - Status polling
     - `handle_job_completion()` - Cleanup
     - `handle_job_failure()` - Retry logic
   - [ ] State machine for job lifecycle
   - [ ] Automatic retry with exponential backoff
   - [ ] Write agent orchestration tests

3. **Integration** (2 hours)
   - [ ] End-to-end test: submit job → queue → upload → print → complete
   - [ ] Test retry logic with simulated failures
   - [ ] Test queue persistence (agent restart)
   - [ ] Test edge cases (network failures, printer offline)

**Deliverables**:
- ✅ Jobs queued and processed automatically
- ✅ Queue state survives agent restart
- ✅ Automatic retry on transient failures (max 3)
- ✅ >85% test coverage for Phase 2 code

---

### Phase 3: Production Hardening
**Goal**: Monitoring, logging, error handling
**Duration**: 0.5 day
**Priority**: P2

#### Tasks

1. **Logging** (2 hours)
   - [ ] Configure structlog for JSON logging
   - [ ] Add structured logging to all components
   - [ ] Log job lifecycle events (submit, start, complete, fail)
   - [ ] Log printer status changes (idle → printing → idle)
   - [ ] Mask sensitive data (access codes)

2. **Monitoring** (2 hours)
   - [ ] Implement health check endpoint (for future orchestrator)
   - [ ] Expose metrics (queue depth, success rate, error rate)
   - [ ] Add watchdog for stuck jobs (timeout detection)

3. **Documentation** (2 hours)
   - [ ] Complete README.md with setup instructions
   - [ ] Document Bambu Lab Developer Mode setup
   - [ ] Create quickstart guide
   - [ ] API reference documentation
   - [ ] Troubleshooting guide

4. **CI/CD** (1 hour)
   - [ ] GitHub Actions workflow for tests
   - [ ] Linting and formatting checks
   - [ ] Coverage reporting (>90% target)

**Deliverables**:
- ✅ Structured JSON logging
- ✅ Production-ready error handling
- ✅ Complete documentation
- ✅ >90% test coverage

---

### Phase 4: Multi-Printer Support (Future)
**Goal**: Load balancing across multiple printers
**Duration**: 1 day
**Priority**: P3

#### Tasks

1. **Multi-Printer Configuration**
   - [ ] Support multiple printer configs
   - [ ] Printer pool management
   - [ ] Load balancing algorithm (round-robin or least-busy)

2. **Job Routing**
   - [ ] Job requirements matching (material, build volume)
   - [ ] Printer capability checking
   - [ ] Failover when printer offline

3. **Testing**
   - [ ] Multi-printer integration tests
   - [ ] Load balancing verification
   - [ ] Failover testing

**Deliverables**:
- ✅ Support 2+ printers in parallel
- ✅ Automatic load balancing
- ✅ Failover when printer goes offline

---

## Testing Strategy

### Unit Tests (>90% coverage)

**File**: `tests/unit/test_models.py`
- Model validation (valid/invalid inputs)
- Serialization/deserialization
- Model methods (is_terminal, can_retry, etc.)

**File**: `tests/unit/test_printer.py`
- Mocked MQTT/FTP communication
- Command execution (start, pause, cancel)
- Status parsing
- Error handling

**File**: `tests/unit/test_queue.py`
- Queue operations (enqueue, dequeue)
- Persistence (save/load)
- State transitions
- Priority ordering

**File**: `tests/unit/test_agent.py`
- Job submission
- Queue processing
- Retry logic
- Job lifecycle state machine

**File**: `tests/unit/test_config.py`
- Configuration loading
- Environment variable parsing
- Validation

### Integration Tests

**File**: `tests/integration/test_mqtt_integration.py`
- Real MQTT connection (requires test broker or printer)
- Command execution
- Status updates

**File**: `tests/integration/test_ftp_integration.py`
- Real FTP upload (requires test server or printer)
- File transfer
- Error handling

**File**: `tests/integration/test_end_to_end.py`
- Full workflow: submit → upload → print → complete
- Error scenarios (network failure, printer error)
- Queue persistence across restarts

### Contract Tests

**File**: `tests/contract/test_printer_contract.py`
- API contract verification
- Input/output validation
- Error contract compliance

---

## Dependencies

### External Dependencies

```toml
[project.dependencies]
python = "^3.12"
bambulabs-api = "^0.1.0"  # Bambu Lab printer control
pydantic = "^2.0"         # Data validation
pydantic-settings = "^2.0"  # Settings management
tenacity = "^8.0"         # Retry logic
structlog = "^24.0"       # Structured logging
```

### Development Dependencies

```toml
[project.dev-dependencies]
pytest = "^8.0"
pytest-cov = "^5.0"
pytest-asyncio = "^0.23"
pytest-mock = "^3.14"
ruff = "^0.7.0"
mypy = "^1.7"
```

### Potential Issues

1. **bambulabs_api H2D support**: Library untested with H2D
   - **Mitigation**: Test early, prepare to patch or use direct MQTT/FTP if needed
   - **Fallback**: Use paho-mqtt + ftplib directly

2. **Developer Mode requirement**: Bambu printers require Developer Mode for local API
   - **Mitigation**: Document setup in README, provide screenshots
   - **Risk**: Users may not enable it (security concern)

3. **Network reliability**: Production deployment needs stable network
   - **Mitigation**: Retry logic, queue persistence, offline buffering

---

## Success Criteria

### Phase 1 (MVP)
- [x] Successfully connect to H2D printer
- [x] Upload G-code file via FTP
- [x] Start print job via MQTT
- [x] Monitor status and detect completion
- [x] >80% test coverage

### Phase 2 (Queue)
- [x] Queue jobs persistently
- [x] Automatic retry on failure (max 3)
- [x] Queue survives agent restart
- [x] >85% test coverage

### Phase 3 (Production)
- [x] Structured logging
- [x] Complete documentation
- [x] >90% test coverage
- [x] CI/CD pipeline

### Phase 4 (Multi-Printer)
- [x] Support 2+ printers
- [x] Load balancing
- [x] Failover

---

## Risks & Mitigations

| Risk | Impact | Probability | Mitigation |
|------|--------|-------------|------------|
| bambulabs_api doesn't support H2D | High | Medium | Test early, prepare direct MQTT/FTP fallback |
| Network unreliability in production | Medium | High | Retry logic, queue persistence, monitoring |
| Printer firmware updates break API | Medium | Low | Version testing, graceful degradation |
| Multiple concurrent jobs to same printer | Low | Low | Queue prevents duplicates, printer validates |

---

## Timeline

**Total Estimated Time**: 2-3 days

- **Day 1**: Phase 1 (Foundation) - 8 hours
- **Day 2 AM**: Phase 2 (Queue Management) - 4 hours
- **Day 2 PM**: Phase 3 (Production Hardening) - 4 hours
- **Day 3**: Testing, documentation, cleanup - 4 hours

**MVP Completion**: End of Day 2
**Production Ready**: End of Day 3

---

## Next Steps

1. ✅ Complete spec review
2. ⏳ Set up project structure
3. ⏳ Implement Phase 1 (Foundation)
4. ⏳ Test with H2D printer (or mock)
5. ⏳ Implement Phase 2 (Queue)
6. ⏳ Production hardening
7. ⏳ Documentation
8. ⏳ Integration with Job Orchestration (Feature 004)
