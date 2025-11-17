# Feature Specification: Printer Control

**Feature Branch**: `003-printer-control`
**Created**: 2025-11-16
**Status**: Draft
**Input**: User description: "Printer control component to execute G-code files on Bambu Lab H2D printer, completing the LeSign POC pipeline: Text Prompt → AI Image → 3D Model → G-code → Physical Print"

## Overview

Enable automated physical printing of name signs by establishing communication with the 3D printer and orchestrating print jobs from digital files. This completes the final stage of the LeSign proof-of-concept pipeline, transforming digital designs into physical products without manual intervention.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Basic Print Execution (Priority: P1) 🎯 MVP

A system operator submits a prepared print file and the system autonomously uploads it to the printer, initiates the print, and monitors progress until completion.

**Why this priority**: This is the minimal functionality needed to complete the end-to-end POC pipeline. Without this, the system cannot produce physical output.

**Independent Test**: Provide a valid print file, submit it to the system, and verify a physical name sign is produced without any manual printer interaction.

**Acceptance Scenarios**:

1. **Given** a valid print file is available, **When** the operator submits it for printing, **Then** the file is uploaded to the printer and the print job starts automatically
2. **Given** a print job is running, **When** the operator requests status, **Then** the system reports current progress (percentage complete, estimated time remaining, temperatures)
3. **Given** a print job completes successfully, **When** the operator checks the final status, **Then** the system reports completion with actual print time
4. **Given** a print job is running, **When** the operator requests cancellation, **Then** the printer stops and the job is marked as cancelled
5. **Given** a print file has been submitted, **When** the printer connection is lost temporarily, **Then** the system automatically reconnects and continues monitoring

---

### User Story 2 - Print Queue Management (Priority: P2)

A system operator can submit multiple print jobs which are queued when the printer is busy, with automatic dispatching as the printer becomes available.

**Why this priority**: Enables batch processing and unattended operation for multiple name signs, but not required for initial POC validation.

**Independent Test**: Submit three print jobs when the printer is idle. Verify the first prints immediately while the second and third queue, then automatically start when each prior job completes.

**Acceptance Scenarios**:

1. **Given** the printer is currently printing, **When** a new job is submitted, **Then** the job is queued and its position in the queue is reported
2. **Given** multiple jobs are queued, **When** the current print completes, **Then** the next queued job starts automatically without operator intervention
3. **Given** jobs are queued, **When** the operator requests queue status, **Then** all queued jobs are listed with their positions and estimated start times
4. **Given** a job is in the queue, **When** the operator cancels it, **Then** the job is removed and queue positions are recalculated

---

### User Story 3 - Error Recovery (Priority: P2)

When a print fails due to printer errors, the system detects the failure, reports a clear error message, and allows the operator to decide whether to retry or cancel.

**Why this priority**: Improves reliability and reduces manual monitoring requirements, but initial POC can rely on operator supervision.

**Independent Test**: Simulate a printer error (e.g., filament runout), verify the system detects it within 30 seconds, reports the specific error, and allows retry after the issue is resolved.

**Acceptance Scenarios**:

1. **Given** a print is running, **When** the printer encounters an error (e.g., filament runout, nozzle temperature issue), **Then** the system detects the error within 30 seconds and reports the specific error code with a human-readable explanation
2. **Given** a print has failed with an error, **When** the operator resolves the issue and requests retry, **Then** the print job resumes or restarts from the beginning
3. **Given** a print job upload fails, **When** the upload fails due to temporary network issues, **Then** the system automatically retries up to 3 times with exponential backoff
4. **Given** the printer is unreachable, **When** attempting to submit a job, **Then** the system reports the connection failure immediately rather than appearing to hang

---

### User Story 4 - End-to-End Pipeline Integration (Priority: P1) 🎯 MVP

The system accepts print files from the preceding pipeline stage (3D slicing), automatically converts them to the printer's preferred format, and produces physical output without operator involvement in the printing process.

**Why this priority**: This validates the complete automation goal - text prompt input resulting in physical product output.

**Independent Test**: Run complete pipeline starting with text input "SARAH", verify AI image generation → 3D conversion → slicing → printing all execute automatically and produce a physical name sign within 2 hours.

**Acceptance Scenarios**:

1. **Given** the slicing component produces a print file, **When** it passes the file to the printer control component, **Then** the file is automatically converted to the printer's preferred format and uploaded
2. **Given** the end-to-end pipeline is initiated, **When** all stages complete successfully, **Then** a physical name sign is produced that matches the original text input
3. **Given** any pipeline stage fails, **When** the failure occurs, **Then** the system reports which stage failed with specific error details to aid debugging

---

### Edge Cases

- What happens when the printer is turned off or unreachable at job submission time?
- How does the system handle partial upload failures (network interruption mid-transfer)?
- What happens if the printer's storage is full and cannot accept new files?
- How does the system respond when printer authentication credentials are incorrect or have changed?
- What happens when a print file format is incompatible with the printer?
- How does the system handle printer state transitions (idle → warming up → ready)?
- What happens when the operator submits a job while the system is reconnecting to the printer?
- How does the system respond to print jobs that would exceed printer physical dimensions?

## Requirements *(mandatory)*

### Functional Requirements

#### Connection & Authentication

- **FR-001**: System MUST establish secure authenticated connection to the printer on the local network
- **FR-002**: System MUST automatically reconnect when printer connection is temporarily lost
- **FR-003**: System MUST verify printer availability before accepting job submissions
- **FR-004**: System MUST maintain connection for the duration of print jobs (potentially several hours)

#### File Handling

- **FR-005**: System MUST accept print files from the slicing pipeline component
- **FR-006**: System MUST convert print files to the printer's preferred format before upload
- **FR-007**: System MUST validate file size constraints before upload (printer storage limits)
- **FR-008**: System MUST upload files securely to the printer over encrypted connection

#### Print Job Control

- **FR-009**: System MUST initiate print jobs remotely without requiring physical printer interaction
- **FR-010**: System MUST pause running print jobs on operator request
- **FR-011**: System MUST resume paused print jobs on operator request
- **FR-012**: System MUST stop print jobs on operator request
- **FR-013**: System MUST prevent starting new jobs when printer is already printing

#### Status Monitoring

- **FR-014**: System MUST report current print progress (percentage complete, current layer, total layers)
- **FR-015**: System MUST report printer temperatures (nozzle, bed, chamber)
- **FR-016**: System MUST report estimated time remaining for active print jobs
- **FR-017**: System MUST detect print completion within 30 seconds
- **FR-018**: System MUST detect print failures and report specific error codes
- **FR-019**: System MUST provide status updates at least every 5 seconds during active printing

#### Queue Management (P2)

- **FR-020**: System MUST queue jobs when printer is busy
- **FR-021**: System MUST persist queued jobs across system restarts
- **FR-022**: System MUST automatically dispatch queued jobs when printer becomes available
- **FR-023**: System MUST report queue position for submitted jobs
- **FR-024**: System MUST allow operators to cancel queued jobs

#### Error Handling

- **FR-025**: System MUST retry transient upload failures up to 3 times with exponential backoff
- **FR-026**: System MUST translate printer error codes to human-readable messages
- **FR-027**: System MUST preserve error information for failed jobs to aid troubleshooting
- **FR-028**: System MUST fail immediately with clear messages for permanent errors (invalid credentials, unreachable printer)

#### Integration

- **FR-029**: System MUST accept print requests from the slicing component matching the defined interface contract
- **FR-030**: System MUST report job results back to the requesting component with completion status and timing

### Key Entities

- **Print Job**: A request to produce a physical object from a digital file. Includes the file location, unique identifier, estimated print time, material type, submission timestamp, current status (queued/uploading/printing/completed/failed/cancelled), progress metrics, and error information if failed.

- **Printer Status**: Current operational state of the physical printer. Includes connection state (connected/disconnected), current activity (idle/printing/paused/error), active job identifier if printing, progress metrics (percentage, layers, temperatures), remaining time estimate, and error code if in error state.

- **Job Queue**: Ordered collection of print jobs awaiting execution. Includes all queued jobs with their positions, priority values, estimated start times based on current queue state, and persistence across system restarts.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Complete end-to-end pipeline (text input → AI image → 3D model → slicing → physical print) executes in under 2 hours for a simple name sign
- **SC-002**: Print job uploads complete within 30 seconds for typical file sizes (5MB)
- **SC-003**: Print jobs start automatically within 10 seconds of successful file upload
- **SC-004**: Status updates reflect printer state within 5 seconds of changes
- **SC-005**: Print failures are detected within 30 seconds of occurrence
- **SC-006**: System successfully reconnects within 15 seconds after temporary connection loss
- **SC-007**: Zero manual printer interactions required from job submission to physical output
- **SC-008**: Physical print quality matches AI-generated image (recognizable text, structural integrity)
- **SC-009**: Queue correctly dispatches jobs with zero missed jobs (100% dispatch rate)
- **SC-010**: All error messages include specific actionable information (error code, likely cause, suggested resolution)

### Quality Metrics

- **SC-011**: Print completion detection accuracy of 100% (no false positives or missed completions)
- **SC-012**: Connection uptime of 95% or higher over continuous 8-hour operation
- **SC-013**: Successful retry rate of 90% or higher for transient upload failures
- **SC-014**: Error message clarity validated by operator comprehension test (operator can identify root cause from message alone in 90% of cases)

## Assumptions *(mandatory)*

- The Bambu Lab H2D printer is configured for local network operation (LAN mode) and is reachable on the same network as the system
- Printer network credentials (IP address, access code, serial number) are provided via environment variables
- The printer is the H2D model specifically; compatibility with other Bambu Lab models is not guaranteed
- The slicing component produces standard G-code files that can be packaged for the printer
- A single printer is available for POC; multi-printer support is not required initially
- The printer's internal file storage has sufficient space for job files (validation only, not space management)
- Print material (filament) is loaded and properly configured by the operator before job submission
- The printer's build plate is cleared between jobs by the operator
- Network connectivity between the system and printer is reliable (home/office LAN, not public WiFi)
- Printer firmware is up-to-date and supports standard communication protocols (MQTT for control, FTP for file transfer)

## Out of Scope

- Web-based user interface for job management (POC uses programmatic API only)
- Multi-printer fleet management and load balancing
- Camera integration for print monitoring
- Print time optimization or parameter tuning
- Filament management and automatic material changes
- Post-processing instructions or automation
- Print quality validation beyond basic success/failure detection
- Custom printer profiles or support for non-Bambu Lab printers
- Cloud-based operation or remote printer access outside local network
- Historical job analytics or reporting dashboards
- User access control or multi-user job management
- Print cost calculation or filament consumption tracking
- Integration with external print services or marketplaces

## Dependencies

- **Slicer Component** (Feature 002): Must produce G-code files that match the defined interface contract
- **Printer Hardware**: Bambu Lab H2D printer must be available, powered on, and network-accessible
- **Local Network**: Reliable LAN connectivity between system and printer
- **Environment Configuration**: Printer credentials (IP, serial number, access code) must be provided

## Constraints

- **Printer Model**: Implementation must support Bambu Lab H2D specifically
- **Network Mode**: Printer must operate in LAN-only mode (no cloud dependency)
- **File Format**: Printer prefers 3MF format; G-code must be packaged accordingly
- **Connection Security**: All printer communication must use encrypted protocols (TLS for MQTT, FTPS for file transfer)
- **Storage**: Print files must not exceed printer's available storage capacity
- **Timing**: Status polling must not exceed printer's rate limits (minimum 5-second intervals recommended)
- **Queue Size**: Job queue limited to 100 pending jobs maximum to prevent resource exhaustion

## Risks & Mitigations

- **Risk**: H2D printer compatibility with existing integration libraries is untested
  - **Mitigation**: Early hardware validation testing in Phase 1; maintain abstraction layer allowing library substitution if needed

- **Risk**: G-code packaging in 3MF format may not be compatible with Bambu Lab firmware
  - **Mitigation**: Test early with small files; multiple conversion approaches available (ZIP wrapper, specialized library, or switch to Bambu Studio for slicing)

- **Risk**: Network reliability issues may cause connection drops during multi-hour prints
  - **Mitigation**: Automatic reconnection logic; print continues on printer even if monitoring connection is lost

- **Risk**: Printer error codes may be cryptic and difficult to troubleshoot
  - **Mitigation**: Build error code mapping from official documentation; comprehensive logging of all printer communication

- **Risk**: Queue state corruption could result in lost or duplicate jobs
  - **Mitigation**: Atomic file operations for queue persistence; validation on startup; idempotent job identifiers
