# Implementation Tasks: Printer Control

**Feature**: 003-printer-control
**Branch**: `003-printer-control`
**Generated**: 2025-11-16
**Source**: [spec.md](./spec.md), [plan.md](./plan.md), [data-model.md](./data-model.md), [research.md](./research.md)

## Task Overview

**Total Tasks**: 89
**MVP Scope**: Phase 1-4 (User Stories 1 & 4) = 54 tasks
**Enhancement Scope**: Phase 5-7 (User Stories 2 & 3, polish) = 35 tasks

**Parallel Execution Opportunities**:
- Phase 1 Setup: Tasks T001-T007 (all independent)
- Phase 2 Contract Tests: Tasks T008-T015 (all independent)
- Phase 3 Unit Tests: Tasks per module can run in parallel
- Phase 4 Integration Tests: Tasks T040-T045 (independent test files)

**Dependency Summary**:
- Phase 2 (Contracts) → Phase 3 (Implementation)
- Phase 3 (Core modules) → Phase 4 (Integration)
- Phase 4 (MVP) → Phase 5 (Queue), Phase 6 (Error Recovery)

---

## Phase 1: Project Setup (7 tasks)

**Purpose**: Establish development environment and directory structure

- [ ] T001 [P1] [Setup] Create backend/printer-control directory structure per plan.md
- [ ] T002 [P1] [Setup] Create pyproject.toml with Python 3.12, UV configuration
- [ ] T003 [P1] [Setup] Create requirements.txt with bambulabs-api>=1.0.0, pydantic>=2.0.0, pydantic-settings>=2.0.0
- [ ] T004 [P1] [Setup] Create requirements-dev.txt with pytest, pytest-cov, pytest-mock, ruff, mypy
- [ ] T005 [P1] [Setup] Create .env.example with PRINTER_IP, PRINTER_SERIAL, PRINTER_ACCESS_CODE template
- [ ] T006 [P1] [Setup] Create backend/printer-control/README.md with quickstart content from specs/003-printer-control/quickstart.md
- [ ] T007 [P1] [Setup] Symlink backend/CODE_GUIDELINES.md to backend/printer-control/CODE_GUIDELINES.md

---

## Phase 2: Contract Tests (TDD Foundation) (8 tasks)

**Purpose**: Define interfaces via tests before implementation per constitution principle II

- [ ] T008 [P1] [US1] Write contract test for PrintRequest schema in tests/contract/test_print_request.py
- [ ] T009 [P1] [US1] Write contract test for JobResult schema in tests/contract/test_job_result.py
- [ ] T010 [P1] [US1] Write contract test for JobStatus schema in tests/contract/test_job_status.py
- [ ] T011 [P1] [US1] Write contract test for PrinterStatus schema in tests/contract/test_printer_status.py
- [ ] T012 [P1] [US1] Write contract test validating PrintRequest rejects invalid inputs in tests/contract/test_print_request.py
- [ ] T013 [P1] [US1] Write contract test for PrinterAgent.submit_job() interface in tests/contract/test_interfaces.py
- [ ] T014 [P1] [US1] Write contract test for HardwareInterface.connect() interface in tests/contract/test_interfaces.py
- [ ] T015 [P1] [US1] Write contract test for JobQueue.enqueue() interface in tests/contract/test_interfaces.py

---

## Phase 3: Core Implementation (User Story 1 - Basic Print Execution) (32 tasks)

### 3.1 Data Models (5 tasks)

- [ ] T016 [P1] [US1] Implement PrintRequest Pydantic model in src/models.py matching print-request.schema.json
- [ ] T017 [P1] [US1] Implement JobResult Pydantic model in src/models.py matching job-result.schema.json
- [ ] T018 [P1] [US1] Implement JobStatus Pydantic model in src/models.py matching job-status.schema.json
- [ ] T019 [P1] [US1] Implement PrinterStatus Pydantic model in src/models.py matching printer-status.schema.json
- [ ] T020 [P1] [US1] Verify contract tests T008-T012 pass with models implementation

### 3.2 Exception Hierarchy (3 tasks)

- [ ] T021 [P1] [US1] Implement PrinterControlError base exception in src/exceptions.py
- [ ] T022 [P1] [US1] Implement specific exceptions (ConnectionError, AuthenticationError, FileUploadError, PrintJobError) in src/exceptions.py
- [ ] T023 [P2] [US2] Implement QueueFullError exception in src/exceptions.py

### 3.3 Configuration (2 tasks)

- [ ] T024 [P1] [US1] Implement Settings class with pydantic-settings in src/config/settings.py for PRINTER_IP, PRINTER_SERIAL, PRINTER_ACCESS_CODE
- [ ] T025 [P1] [US1] Write unit test for Settings loading from .env in tests/unit/test_settings.py

### 3.4 File Conversion Utility (4 tasks)

- [ ] T026 [P1] [US4] Write unit test for gcode_to_3mf() conversion in tests/unit/test_file_converter.py
- [ ] T027 [P1] [US4] Implement gcode_to_3mf() in src/utils/file_converter.py using ZIP wrapper per research.md decision 2
- [ ] T028 [P1] [US4] Write unit test for 3MF manifest structure validation in tests/unit/test_file_converter.py
- [ ] T029 [P1] [US4] Verify T026-T028 tests pass with file_converter implementation

### 3.5 Hardware Interface (12 tasks)

- [ ] T030 [P1] [US1] Write unit test for BambuHardwareInterface.connect() in tests/unit/test_hardware_interface.py (mock bambulabs-api)
- [ ] T031 [P1] [US1] Write unit test for BambuHardwareInterface.disconnect() in tests/unit/test_hardware_interface.py
- [ ] T032 [P1] [US1] Implement BambuHardwareInterface.__init__() and connect() in src/hardware_interface.py using bambulabs-api
- [ ] T033 [P1] [US1] Implement BambuHardwareInterface.disconnect() in src/hardware_interface.py
- [ ] T034 [P1] [US1] Write unit test for upload_file() with FTP mocking in tests/unit/test_hardware_interface.py
- [ ] T035 [P1] [US1] Implement upload_file() with FTPS in src/hardware_interface.py per research.md decision 3
- [ ] T036 [P1] [US1] Write unit test for start_print() with MQTT mocking in tests/unit/test_hardware_interface.py
- [ ] T037 [P1] [US1] Implement start_print() via MQTT in src/hardware_interface.py
- [ ] T038 [P1] [US1] Write unit test for get_status() parsing MQTT messages in tests/unit/test_hardware_interface.py
- [ ] T039 [P1] [US1] Implement get_status() with MQTT subscription in src/hardware_interface.py mapping to PrinterStatus model
- [ ] T040 [P1] [US1] Write unit test for stop_print() in tests/unit/test_hardware_interface.py
- [ ] T041 [P1] [US1] Implement stop_print() via MQTT in src/hardware_interface.py

### 3.6 Printer Agent (6 tasks)

- [ ] T042 [P1] [US1] Write unit test for PrinterAgent.submit_job() when printer idle in tests/unit/test_printer_agent.py (mock HardwareInterface)
- [ ] T043 [P1] [US1] Implement PrinterAgent.submit_job() in src/printer_agent.py coordinating upload + start_print
- [ ] T044 [P1] [US1] Write unit test for PrinterAgent.get_job_status() in tests/unit/test_printer_agent.py
- [ ] T045 [P1] [US1] Implement PrinterAgent.get_job_status() in src/printer_agent.py querying printer status
- [ ] T046 [P1] [US1] Write unit test for PrinterAgent.cancel_job() in tests/unit/test_printer_agent.py
- [ ] T047 [P1] [US1] Implement PrinterAgent.cancel_job() in src/printer_agent.py calling stop_print

---

## Phase 4: Integration & End-to-End (User Story 4) (7 tasks)

**Purpose**: Validate component interactions and complete pipeline

- [ ] T048 [P1] [US4] Write integration test for MQTT connection and message handling in tests/integration/test_mqtt_integration.py (mock MQTT broker)
- [ ] T049 [P1] [US4] Write integration test for FTP upload workflow in tests/integration/test_ftp_integration.py (mock FTP server)
- [ ] T050 [P1] [US4] Write integration test for complete print flow (convert → upload → start) in tests/integration/test_e2e_print.py
- [ ] T051 [P1] [US4] Create manual H2D validation script in tests/manual/test_h2d_hardware.py for real printer testing
- [ ] T052 [P1] [US4] Execute manual H2D test and document any printer-specific quirks in backend/printer-control/README.md
- [ ] T053 [P1] [US4] Run complete pipeline test (text "SARAH" → AI → 3D → slice → print) and validate SC-001 (<2 hours)
- [ ] T054 [P1] [US4] Verify MVP success criteria SC-002 through SC-008 with metrics logging

---

## Phase 5: Queue Management (User Story 2) (15 tasks)

**Purpose**: Enable batch processing and unattended operation

### 5.1 Job Queue Implementation (8 tasks)

- [ ] T055 [P2] [US2] Write unit test for JobQueue.enqueue() in tests/unit/test_job_queue.py
- [ ] T056 [P2] [US2] Write unit test for JobQueue.dequeue() prioritization in tests/unit/test_job_queue.py
- [ ] T057 [P2] [US2] Implement JobQueue class with enqueue/dequeue in src/job_queue.py per data-model.md
- [ ] T058 [P2] [US2] Write unit test for JobQueue.get_position() in tests/unit/test_job_queue.py
- [ ] T059 [P2] [US2] Implement JobQueue.get_position() in src/job_queue.py
- [ ] T060 [P2] [US2] Write unit test for JobQueue.remove() in tests/unit/test_job_queue.py
- [ ] T061 [P2] [US2] Implement JobQueue.remove() in src/job_queue.py
- [ ] T062 [P2] [US2] Verify T055-T061 tests pass and queue operations work correctly

### 5.2 Queue Persistence (4 tasks)

- [ ] T063 [P2] [US2] Write unit test for JobQueue.save() atomic file write in tests/unit/test_job_queue.py (use tmp_path fixture)
- [ ] T064 [P2] [US2] Implement JobQueue.save() with atomic writes per research.md decision 4
- [ ] T065 [P2] [US2] Write unit test for JobQueue.load() with validation in tests/unit/test_job_queue.py
- [ ] T066 [P2] [US2] Implement JobQueue.load() with startup reconciliation per data-model.md

### 5.3 Automatic Dispatch (3 tasks)

- [ ] T067 [P2] [US2] Write unit test for PrinterAgent.submit_job() queuing when printer busy in tests/unit/test_printer_agent.py
- [ ] T068 [P2] [US2] Update PrinterAgent.submit_job() to enqueue jobs when printer not idle in src/printer_agent.py
- [ ] T069 [P2] [US2] Write unit test for automatic job dispatch in tests/unit/test_printer_agent.py and implement dispatch loop

---

## Phase 6: Error Recovery (User Story 3) (12 tasks)

**Purpose**: Robust error handling and automatic recovery

### 6.1 Connection Monitoring (4 tasks)

- [ ] T070 [P2] [US3] Write unit test for ConnectionMonitor watchdog in tests/unit/test_reconnection.py
- [ ] T071 [P2] [US3] Implement ConnectionMonitor class in src/utils/reconnection.py per research.md decision 6
- [ ] T072 [P2] [US3] Write unit test for automatic reconnection on timeout in tests/unit/test_reconnection.py
- [ ] T073 [P2] [US3] Integrate ConnectionMonitor into HardwareInterface in src/hardware_interface.py

### 6.2 HMS Error Translation (3 tasks)

- [ ] T074 [P2] [US3] Create HMS error code lookup table in src/utils/hms_errors.py per research.md decision 5
- [ ] T075 [P2] [US3] Write unit test for translate_hms_error() in tests/unit/test_hms_errors.py
- [ ] T076 [P2] [US3] Implement translate_hms_error() function in src/utils/hms_errors.py

### 6.3 Retry Logic (3 tasks)

- [ ] T077 [P2] [US3] Write unit test for upload retry with exponential backoff in tests/unit/test_hardware_interface.py
- [ ] T078 [P2] [US3] Implement retry logic in upload_file() per FR-025 (3 retries, exponential backoff)
- [ ] T079 [P2] [US3] Write integration test for transient failure recovery in tests/integration/test_error_recovery.py

### 6.4 Error Detection (2 tasks)

- [ ] T080 [P2] [US3] Write unit test for print failure detection within 30s in tests/unit/test_printer_agent.py
- [ ] T081 [P2] [US3] Implement error polling in PrinterAgent monitoring loop per FR-018

---

## Phase 7: Polish & Production Readiness (8 tasks)

**Purpose**: Cross-cutting concerns and deployment preparation

### 7.1 Logging Infrastructure (2 tasks)

- [ ] T082 [P2] [Polish] Implement structured logging with credential masking in src/utils/logging.py per research.md
- [ ] T083 [P2] [Polish] Add logging statements to all modules (connection events, job lifecycle, errors)

### 7.2 Coverage & Quality (3 tasks)

- [ ] T084 [P2] [Polish] Run pytest --cov=src --cov-report=html and verify >90% coverage per constitution
- [ ] T085 [P2] [Polish] Run ruff check and fix any linting issues
- [ ] T086 [P2] [Polish] Run mypy src/ and fix any type errors

### 7.3 Documentation (3 tasks)

- [ ] T087 [P2] [Polish] Document H2D-specific behaviors and quirks in backend/printer-control/README.md from T052 findings
- [ ] T088 [P2] [Polish] Create connection validation script per quickstart.md in src/validate_connection.py
- [ ] T089 [P2] [Polish] Update CLAUDE.md with printer control tech stack via update-agent-context.sh

---

## Task Execution Guide

### MVP Implementation (Phases 1-4)

**Objective**: Deliver User Stories 1 & 4 (complete text→print pipeline)

**Week 1-2**: Phases 1-3 (Setup + Core Implementation)
1. Setup environment (T001-T007) - Run in parallel
2. Write all contract tests (T008-T015) - TDD foundation, run in parallel
3. Implement models, exceptions, config (T016-T025) - Sequential per test
4. Implement file converter (T026-T029) - TDD cycle
5. Implement hardware interface (T030-T041) - TDD cycle per method
6. Implement printer agent (T042-T047) - TDD cycle

**Week 2-3**: Phase 4 (Integration & E2E)
7. Integration tests (T048-T050) - Run in parallel
8. Manual H2D validation (T051-T052) - Real hardware testing
9. Complete pipeline test (T053-T054) - Success criteria validation

**MVP Completion Gate**:
- ✅ Contract tests T008-T015 all pass
- ✅ Unit tests coverage >90%
- ✅ Integration tests T048-T050 pass
- ✅ Manual H2D test T052 passes
- ✅ End-to-end test T053 completes in <2 hours (SC-001)
- ✅ Physical print matches AI image (SC-008)

### Enhancement Implementation (Phases 5-6)

**Objective**: Deliver User Stories 2 & 3 (queue management + error recovery)

**Week 3-4**: Phase 5 (Queue Management)
1. Queue implementation (T055-T062) - TDD cycle
2. Persistence (T063-T066) - Atomic operations
3. Auto-dispatch (T067-T069) - Integration with agent

**Week 4-5**: Phase 6 (Error Recovery)
4. Connection monitoring (T070-T073) - Watchdog implementation
5. HMS errors (T074-T076) - Error translation
6. Retry logic (T077-T079) - Resilience
7. Error detection (T080-T081) - Failure handling

**Enhancement Completion Gate**:
- ✅ Queue tests T055-T066 pass
- ✅ Dispatch test T069 validates automatic job start
- ✅ Reconnection test T072 passes within 15s (SC-006)
- ✅ Error detection test T080 detects failures within 30s (SC-005)

### Polish & Deployment (Phase 7)

**Week 5+**: Final polish
1. Logging (T082-T083) - Observability
2. Coverage/Quality (T084-T086) - >90% coverage, zero lint errors
3. Documentation (T087-T089) - Deployment readiness

**Production Readiness Gate**:
- ✅ Test coverage >90% (T084)
- ✅ Zero lint errors (T085)
- ✅ Zero type errors (T086)
- ✅ All success criteria SC-001 through SC-014 validated
- ✅ Documentation complete (T087-T089)

---

## Parallel Execution Examples

### Example 1: Setup Phase
```bash
# All setup tasks are independent, run in parallel
git checkout 003-printer-control
mkdir -p backend/printer-control/{src/{config,utils},tests/{contract,integration,unit,manual}}
# T001-T007 can execute simultaneously
```

### Example 2: Contract Tests
```bash
# All contract tests are independent
cd backend/printer-control
# T008-T015 can be written/run in parallel
uv run pytest tests/contract/test_print_request.py &
uv run pytest tests/contract/test_job_result.py &
uv run pytest tests/contract/test_job_status.py &
# ...
wait
```

### Example 3: Unit Test Modules
```bash
# Unit tests per module are independent
uv run pytest tests/unit/test_file_converter.py &
uv run pytest tests/unit/test_hardware_interface.py &
uv run pytest tests/unit/test_printer_agent.py &
wait
```

---

## Success Criteria Mapping

Each task contributes to specific success criteria from spec.md:

| Task Range | Success Criteria | Validation Method |
|------------|------------------|-------------------|
| T016-T020, T042-T047, T053 | SC-001: <2 hours end-to-end | Timer during T053 execution |
| T034-T035 | SC-002: Upload <30s for 5MB | Timer during upload in T049 |
| T037, T043 | SC-003: Print start <10s | Timer in T050 |
| T038-T039 | SC-004: Status updates <5s | Polling interval validation in T048 |
| T080-T081 | SC-005: Failure detection <30s | Timer in error detection test |
| T070-T073 | SC-006: Reconnect <15s | Timer in reconnection test T072 |
| T042-T047, T053 | SC-007: Zero manual interactions | Validate in T053 e2e test |
| T053 | SC-008: Print quality match | Visual inspection in T053 |
| T067-T069 | SC-009: 100% dispatch rate | Queue dispatch test validation |
| T074-T076 | SC-010: Actionable error messages | HMS translation test validation |
| T038-T039, T080 | SC-011: 100% completion detection | Test false positive/negative rates |
| T070-T073 | SC-012: 95% uptime over 8h | Long-running connection test |
| T077-T078 | SC-013: 90% retry success | Transient failure simulation |
| T074-T076 | SC-014: 90% operator comprehension | Error message clarity review |

---

## Dependency Graph

```
Setup (T001-T007)
    ↓
Contract Tests (T008-T015)
    ↓
Models (T016-T020) + Exceptions (T021-T023) + Config (T024-T025)
    ↓
    ├─→ File Converter (T026-T029) ──────────────┐
    │                                            │
    ├─→ Hardware Interface (T030-T041) ─────────┤
    │                                            ↓
    └─→ Printer Agent (T042-T047) ──→ Integration (T048-T054) ─→ MVP DONE
                │
                │
                ├─→ Queue (T055-T066) ──→ Auto-dispatch (T067-T069)
                │
                ├─→ Connection Monitor (T070-T073)
                │
                ├─→ HMS Errors (T074-T076)
                │
                └─→ Retry Logic (T077-T081)
                        ↓
                Polish (T082-T089) ─→ PRODUCTION READY
```

---

## Notes

- **TDD Discipline**: Every implementation task (T016+) has corresponding test task written first (T008-T015, T026, T030, etc.)
- **Constitution Compliance**: >90% coverage target (exceeds 80% requirement), contract-first design, modular architecture
- **MVP Focus**: Phases 1-4 deliver complete pipeline, Phases 5-6 add resilience
- **Real Hardware Validation**: T051-T052 critical for untested H2D printer
- **Atomic Operations**: T063-T064 implement research.md decision 4 for queue persistence
- **Error Translation**: T074-T076 implement research.md decision 5 for HMS codes
- **Abstraction Layer**: T030-T041 wrap bambulabs-api enabling library swap per research.md decision 1
