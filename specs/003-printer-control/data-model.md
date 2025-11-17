# Data Model: Printer Control

**Feature**: 003-printer-control
**Date**: 2025-11-16
**Source**: Extracted from [spec.md](./spec.md) Key Entities section

## Overview

The Printer Control component manages three primary entities: Print Jobs (work requests), Printer Status (hardware state), and Job Queue (pending work). These models define the data contracts between the printer control component and its consumers (slicer component) and dependencies (printer hardware).

## Entity Relationships

```
┌─────────────────┐
│  Slicer         │
│  Component      │
└────────┬────────┘
         │ PrintRequest
         ▼
┌─────────────────┐       ┌──────────────────┐
│  Printer Agent  │◄─────►│  Job Queue       │
│  (Orchestrator) │       │  (Persistence)   │
└────────┬────────┘       └──────────────────┘
         │                         │
         │ JobResult              │ List[PrintJob]
         │ JobStatus              │
         ▼                         │
┌─────────────────┐               │
│  Hardware       │               │
│  Interface      │               │
└────────┬────────┘               │
         │                         │
         │ PrinterStatus          │
         ▼                         │
┌─────────────────┐               │
│  Bambu Lab H2D  │               │
│  Printer        │               │
└─────────────────┘               │
                                  │
         Print Job instances ─────┘
```

## Core Entities

### 1. Print Job

**Description**: Represents a request to produce a physical object from a digital file. Tracks the entire lifecycle from submission through completion or failure.

**Source**: Spec Key Entities, FR-029 (accept requests), FR-030 (report results)

**Attributes**:

| Field | Type | Required | Validation | Description |
|-------|------|----------|------------|-------------|
| `job_id` | str | Yes | Non-empty, unique | Unique identifier for the print job |
| `gcode_file_path` | Path | Yes | File exists | Absolute path to G-code file from slicer |
| `material` | Literal["PLA", "PETG", "ABS"] | Yes | Enum | Filament material type |
| `estimated_time_minutes` | int | Yes | >= 1 | Estimated print duration from slicer |
| `estimated_filament_grams` | float | Yes | >= 0.0 | Estimated filament consumption |
| `priority` | int | No (default: 0) | >= 0 | Job priority (higher = print sooner) |
| `submission_timestamp` | datetime | Yes | Auto-generated | When job was submitted |
| `status` | Literal["queued", "uploading", "printing", "completed", "failed", "cancelled"] | Yes | State machine | Current job state |
| `progress_percent` | int | No | 0-100 | Print progress percentage |
| `current_layer` | int | No | >= 0 | Current layer being printed |
| `total_layers` | int | No | >= 0 | Total layers in model |
| `nozzle_temp` | float | No | >= 0.0 | Current nozzle temperature (°C) |
| `bed_temp` | float | No | >= 0.0 | Current bed temperature (°C) |
| `chamber_temp` | float | No | >= 0.0 | Current chamber temperature (°C) |
| `remaining_time_minutes` | int | No | >= 0 | Estimated time remaining |
| `started_at` | datetime | No | | When print actually started |
| `completed_at` | datetime | No | | When print finished (success or failure) |
| `actual_print_time_minutes` | int | No | >= 0 | Actual duration (completed_at - started_at) |
| `error_code` | str | No | | HMS error code if failed |
| `error_message` | str | No | | Human-readable error explanation |

**State Transitions**:

```
                    ┌──────────────────┐
                    │                  │
        Submit ────►│  queued          │
                    │                  │
                    └────────┬─────────┘
                             │
                     Printer available
                             │
                    ┌────────▼─────────┐
                    │                  │
                    │  uploading       │
                    │                  │
                    └────────┬─────────┘
                             │
                       Upload success
                             │
                    ┌────────▼─────────┐
                    │                  │
                    │  printing        │◄───┐
                    │                  │    │
                    └────┬─────────┬───┘    │
                         │         │        │
                    Success    Error/Cancel │
                         │         │        │
                ┌────────▼─┐  ┌───▼──────┐ │
                │          │  │          │ │
                │completed │  │  failed  │ │
                │          │  │cancelled │ │
                └──────────┘  └──────────┘ │
                                           │
                                         Retry
                                           │
                                           └───┘
```

**Validation Rules** (from Requirements):
- FR-005: Accept files from slicing component
- FR-013: Prevent starting new jobs when printer busy
- FR-020: Queue jobs when printer unavailable
- FR-021: Persist across restarts
- FR-024: Allow cancellation

**Relationships**:
- Input from: Slicer Component (via PrintRequest)
- Managed by: PrinterAgent, JobQueue
- Output to: Slicer Component (via JobResult, JobStatus)

---

### 2. Printer Status

**Description**: Snapshot of the physical printer's current operational state. Reflects real-time hardware conditions received via MQTT messages.

**Source**: Spec Key Entities, FR-014 through FR-019 (status monitoring requirements)

**Attributes**:

| Field | Type | Required | Validation | Description |
|-------|------|----------|------------|-------------|
| `state` | Literal["idle", "printing", "paused", "error", "offline"] | Yes | Enum | Primary operational state |
| `connection_state` | Literal["connected", "disconnected"] | Yes | Enum | Network connection status |
| `current_job_id` | str | No | | Job ID if printer is printing |
| `progress_percent` | int | Yes | 0-100 | Print completion percentage |
| `current_layer` | int | Yes | >= 0 | Layer currently being printed |
| `total_layers` | int | Yes | >= 0 | Total layers in current job |
| `nozzle_temp` | float | Yes | >= 0.0 | Nozzle temperature (°C) |
| `bed_temp` | float | Yes | >= 0.0 | Bed temperature (°C) |
| `chamber_temp` | float | No | >= 0.0 | Chamber temperature (°C) - H2D has active chamber |
| `remaining_time_minutes` | int | Yes | >= 0 | Estimated time to completion |
| `error_code` | str | No | | HMS error code if state="error" |
| `last_update` | datetime | Yes | Auto-generated | When status was last refreshed |

**Data Source**: MQTT messages from printer on topic `device/{SERIAL}/report`

**Update Frequency**: FR-019 requires updates at least every 5 seconds during printing

**Validation Rules** (from Requirements):
- FR-014: Report progress (percentage, layers)
- FR-015: Report temperatures (nozzle, bed, chamber)
- FR-016: Report remaining time
- FR-017: Detect completion within 30 seconds
- FR-018: Detect failures and error codes
- FR-003: Verify availability before job submission

**Relationships**:
- Populated by: HardwareInterface (from MQTT)
- Consumed by: PrinterAgent (for job orchestration)
- Used for: Job status updates, queue dispatch decisions

---

### 3. Job Queue

**Description**: Ordered collection of print jobs awaiting execution. Provides persistence across system restarts and manages job priority ordering.

**Source**: Spec Key Entities, FR-020 through FR-024 (queue management requirements)

**Attributes**:

| Field | Type | Required | Validation | Description |
|-------|------|----------|------------|-------------|
| `jobs` | List[PrintJob] | Yes | Max 100 items | Ordered list of queued jobs |
| `max_size` | int | Yes | Const 100 | Maximum queue capacity |
| `persistence_file` | Path | Yes | Writable | JSON file for persistence |

**Operations**:

| Method | Input | Output | Description |
|--------|-------|--------|-------------|
| `enqueue(job)` | PrintJob | None | Add job to queue, sorted by priority desc then submission time asc |
| `dequeue()` | None | PrintJob \| None | Remove and return highest priority job, or None if empty |
| `get_position(job_id)` | str | int | Return 1-indexed position, or -1 if not queued |
| `remove(job_id)` | str | bool | Remove specific job, return True if found |
| `save()` | None | None | Persist queue to JSON file (atomic write) |
| `load()` | None | None | Restore queue from JSON file (validation + reconciliation) |
| `get_all()` | None | List[PrintJob] | Return all queued jobs (for status queries) |

**Ordering Rules**:
1. Higher priority jobs first (descending `priority`)
2. Same priority: older submission first (ascending `submission_timestamp`)

**Persistence Format** (JSON):
```json
{
  "version": "1.0",
  "queue": [
    {
      "job_id": "job_20251116_001",
      "gcode_file_path": "/path/to/file.gcode",
      "material": "PLA",
      "estimated_time_minutes": 45,
      "estimated_filament_grams": 75.0,
      "priority": 0,
      "submission_timestamp": "2025-11-16T10:30:00Z",
      "status": "queued"
    }
  ],
  "last_saved": "2025-11-16T10:30:05Z"
}
```

**Validation Rules** (from Requirements):
- FR-020: Queue jobs when printer busy
- FR-021: Persist across restarts
- FR-022: Auto-dispatch when printer available
- FR-023: Report queue position
- FR-024: Allow cancellation
- Constraint: Max 100 jobs to prevent resource exhaustion

**Startup Reconciliation**:
1. Load queue from JSON file
2. Validate JSON structure and job fields
3. Check for jobs with status="printing" or "uploading"
4. If found, query printer status:
   - Printer idle → mark as failed (stale)
   - Printer printing different job → mark as failed
   - Printer printing this job → update status from printer
5. Remove invalid entries
6. Log recovery actions
7. Save corrected queue

**Relationships**:
- Manages: List of PrintJob instances
- Used by: PrinterAgent (for job dispatch)
- Persists to: Local filesystem (JSON file)

---

## Validation Summary

All entities align with functional requirements:

| Entity | FR Coverage | Spec Section |
|--------|-------------|--------------|
| Print Job | FR-005, FR-013, FR-020, FR-021, FR-024, FR-029, FR-030 | Key Entities, User Stories 1-4 |
| Printer Status | FR-003, FR-014, FR-015, FR-016, FR-017, FR-018, FR-019 | Key Entities, User Story 1 |
| Job Queue | FR-020, FR-021, FR-022, FR-023, FR-024 | Key Entities, User Story 2 |

All success criteria (SC-001 through SC-014) are measurable using these entities.
