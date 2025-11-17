# Implementation Plan: Printer Control

**Branch**: `003-printer-control` | **Date**: 2025-11-16 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/003-printer-control/spec.md`

**Note**: This template is filled in by the `/speckit.plan` command. See `.specify/templates/commands/plan.md` for the execution workflow.

## Summary

Enable automated physical printing of name signs by establishing communication with the Bambu Lab H2D 3D printer and orchestrating print jobs from digital files. The system will accept G-code files from the slicing component, convert them to the printer's preferred format (3MF), upload via secure file transfer, initiate and monitor print jobs via real-time messaging, and handle errors with automatic recovery. This completes the final stage of the LeSign POC pipeline, transforming digital designs into physical products without manual intervention.

## Technical Context

**Language/Version**: Python 3.12
**Primary Dependencies**: bambulabs-api (MQTT/FTP wrapper), pydantic/pydantic-settings (data models), pytest/pytest-mock (testing)
**Storage**: Local file-based queue (JSON), staging directories for G-code and converted 3MF files
**Testing**: pytest with >90% coverage target, pytest-mock for unit tests, contract tests for interfaces
**Target Platform**: Backend processing layer (macOS/Linux for POC, containerized for production)
**Project Type**: Backend module (printer-control component within backend/ directory)
**Performance Goals**: Upload complete <30s for 5MB files, status updates every 5s, print start <10s after upload, reconnect <15s
**Constraints**: Bambu Lab H2D specific, LAN-only operation, encrypted protocols (TLS/FTPS) required, single printer for POC, queue limited to 100 jobs
**Scale/Scope**: Single operator POC, ~10-20 print jobs per session, multi-hour print monitoring, 3 core modules (agent, hardware interface, queue)

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

### I. Modular Components ✅ PASS

**Self-contained**: Printer control is an independent module accepting print files as input and producing job status as output, with no direct dependencies on AI generation or 3D pipeline internals.

**Independently testable**: Component can be tested with mock printer (simulated MQTT/FTP), test files, and contract validation without requiring other pipeline stages.

**Well-documented**: Spec defines clear contracts (PrintRequest → JobResult), acceptance criteria, and integration points with slicer component.

**Composable**: Slots into automation pipeline via defined interface (FR-029/030), enabling end-to-end text→print workflow.

### II. Test-Driven Development ✅ PASS

**Tests FIRST**: Plan includes Phase 1 contract tests, Phase 2 unit tests, Phase 3 integration tests - all before implementation.

**Minimum 80% coverage**: >90% coverage target specified (exceeds 80% requirement).

**All public APIs tested**: PrinterAgent, HardwareInterface, JobQueue all have dedicated test suites planned.

**TDD discipline**: Red-Green-Refactor cycle explicit in Phase 2-4 workflow.

### III. Clear Interfaces & Contracts ✅ PASS

**Input contracts**: PrintRequest model from slicer (job_id, gcode_file_path, material, estimated times) - explicit in spec FR-029.

**Output contracts**: JobResult and JobStatus models with completion status, timing, error info - explicit in spec FR-030.

**API boundaries**: Three clear layers: PrinterAgent (orchestration), HardwareInterface (MQTT/FTP), JobQueue (persistence) with defined responsibilities.

**Error handling**: Exception hierarchy planned (PrinterControlError base, ConnectionError, AuthenticationError, FileUploadError, PrintJobError, QueueFullError) with retry logic (FR-025).

### IV. Local-First POC ✅ PASS

**Local execution**: LAN-only printer communication (no cloud), file-based queue (no database), environment variable configuration.

**Minimize dependencies**: Single external library choice (NEEDS CLARIFICATION between bambulabs-api vs direct implementation), standard Python libraries otherwise.

**Simple solutions**: File-based queue (not Redis/RabbitMQ), single printer (not fleet management), manual filament management.

**Focus on architecture**: Three-layer separation (agent/hardware/queue) establishes clean boundaries for future scaling.

### V. Python & Best Practices ✅ PASS

**Configuration**: Printer credentials via environment variables (PRINTER_IP, PRINTER_SERIAL, PRINTER_ACCESS_CODE) per assumptions section.

**Error Handling**: Explicit exception hierarchy planned, error code translation (FR-026), error preservation (FR-027).

**Logging**: Structured logging required for troubleshooting (risk mitigation), no sensitive data (credentials masked).

**Dependencies**: Python 3.12, versions to be pinned in requirements.txt, virtual environment per backend/CODE_GUIDELINES.md.

**Code Organization**: Clear separation: printer_agent.py (orchestration), hardware_interface.py (communication), job_queue.py (persistence), models.py (contracts).

**All gates PASS** - ready to proceed to Phase 0 research.

---

## Post-Phase 1 Constitution Re-Check

*Phase 0 research and Phase 1 design artifacts completed. Re-validating constitution compliance.*

### I. Modular Components ✅ PASS (Revalidated)

**Self-contained**: Data model confirms three independent modules (PrinterAgent, HardwareInterface, JobQueue) with clear boundaries. Contracts define explicit inputs/outputs (PrintRequest → JobResult).

**Independently testable**: Contract schemas enable validation without implementation. Hardware interface can be mocked for agent tests. Queue can be tested with in-memory state.

**Well-documented**: Quickstart.md provides setup guide, data-model.md defines entities, contracts/ has JSON schemas, research.md documents decisions.

**Composable**: PrintRequest/JobResult schemas match slicer output format, enabling pipeline composition.

### II. Test-Driven Development ✅ PASS (Revalidated)

**Tests FIRST**: Quickstart.md includes TDD cycle workflow. Contract tests defined before implementation begins.

**Minimum 80% coverage**: >90% target maintained in Technical Context.

**All public APIs tested**: Contract schemas enable pre-implementation test writing (test_print_request.py validates schema before PrintRequest class exists).

**TDD discipline**: Quickstart.md explicitly documents Red-Green-Refactor cycle with example.

### III. Clear Interfaces & Contracts ✅ PASS (Revalidated)

**Input contracts**: print-request.schema.json fully defines slicer→printer-control interface with validation rules (required fields, types, patterns, ranges).

**Output contracts**: job-result.schema.json and job-status.schema.json define printer-control→slicer responses with all possible states.

**API boundaries**: Data model clearly separates PrinterAgent (orchestration), HardwareInterface (communication), JobQueue (persistence) with distinct responsibilities.

**Error handling**: Exception hierarchy documented in research.md (PrinterControlError base with 5 specific error types). Error translation (HMS codes) planned.

### IV. Local-First POC ✅ PASS (Revalidated)

**Local execution**: Research decision: file-based JSON queue (not Redis), LAN-only printer (not cloud), environment variables (not cloud secrets service).

**Minimize dependencies**: Research decision: bambulabs-api chosen as single external library (reduces from paho-mqtt + ftplib + custom protocol handling to one mature wrapper).

**Simple solutions**: Research decision: ZIP wrapper for 3MF conversion (not specialized library), atomic file writes (not database transactions).

**Focus on architecture**: Three-layer separation maintained through data model design.

### V. Python & Best Practices ✅ PASS (Revalidated)

**Configuration**: Quickstart.md shows .env file usage with PRINTER_IP, PRINTER_SERIAL, PRINTER_ACCESS_CODE environment variables.

**Error Handling**: Research.md documents exception hierarchy (PrinterControlError, ConnectionError, AuthenticationError, FileUploadError, PrintJobError, QueueFullError) and HMS error code translation.

**Logging**: Research.md includes connection monitoring with structured logging, credential masking pattern shown.

**Dependencies**: Research.md specifies exact libraries (bambulabs-api>=1.0.0, pydantic>=2.0.0, pydantic-settings>=2.0.0) for pinning in requirements.txt.

**Code Organization**: Project structure in plan.md shows clear separation (printer_agent.py, hardware_interface.py, job_queue.py, models.py, exceptions.py) matching design.

**All gates PASS post-Phase 1** - design maintains constitution compliance.

## Project Structure

### Documentation (this feature)

```text
specs/003-printer-control/
├── plan.md              # This file (/speckit.plan command output)
├── research.md          # Phase 0 output (/speckit.plan command)
├── data-model.md        # Phase 1 output (/speckit.plan command)
├── quickstart.md        # Phase 1 output (/speckit.plan command)
├── contracts/           # Phase 1 output (/speckit.plan command)
│   ├── print-request.schema.json
│   ├── job-result.schema.json
│   ├── job-status.schema.json
│   └── printer-status.schema.json
└── tasks.md             # Phase 2 output (/speckit.tasks command - NOT created by /speckit.plan)
```

### Source Code (repository root)

```text
backend/printer-control/
├── src/
│   ├── __init__.py
│   ├── printer_agent.py       # High-level job orchestration (US1, US2, US4)
│   ├── hardware_interface.py  # Low-level MQTT/FTP communication (US1, US3)
│   ├── job_queue.py           # Local queue management (US2)
│   ├── models.py              # Pydantic data models (all contracts)
│   ├── exceptions.py          # Error hierarchy (US3)
│   ├── config/
│   │   └── settings.py        # Environment configuration
│   └── utils/
│       ├── mqtt_client.py     # MQTT connection wrapper
│       ├── ftp_client.py      # FTP upload wrapper
│       ├── reconnection.py    # Connection health monitoring (US3)
│       └── file_converter.py  # G-code → 3MF conversion (US4)
├── tests/
│   ├── conftest.py            # Shared fixtures
│   ├── contract/              # API contract validation
│   │   ├── test_print_request.py
│   │   ├── test_job_result.py
│   │   └── test_interfaces.py
│   ├── integration/           # Component interaction tests
│   │   ├── test_mqtt_integration.py
│   │   ├── test_ftp_integration.py
│   │   └── test_e2e_print.py
│   └── unit/                  # Fast, isolated tests
│       ├── test_printer_agent.py
│       ├── test_hardware_interface.py
│       ├── test_job_queue.py
│       ├── test_file_converter.py
│       └── test_reconnection.py
├── pyproject.toml             # UV/pip configuration
├── requirements.txt           # Production dependencies
├── requirements-dev.txt       # Development dependencies
├── .env.example               # Environment variable template
├── README.md                  # Component documentation
└── CODE_GUIDELINES.md         # Development standards (symlink to backend/)
```

**Structure Decision**: Backend module structure following existing patterns from backend/ai-generation and backend/model-converter. Three-layer architecture (agent/hardware/queue) with clear separation of concerns. Test organization follows contract/integration/unit hierarchy per backend/CODE_GUIDELINES.md.

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

No violations. All constitution principles are met without requiring complexity justifications.
