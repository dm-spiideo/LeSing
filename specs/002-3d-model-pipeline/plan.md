# Implementation Plan: 3D Model Pipeline

**Branch**: `002-3d-model-pipeline` | **Date**: 2025-11-16 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/002-3d-model-pipeline/spec.md`

## Summary

The 3D Model Pipeline converts AI-generated 2D name sign images into printable 3D models and G-code files for the Bambu Lab H2D printer. The pipeline consists of four stages: (1) Image→Vector conversion using VTracer with quality metrics validation, (2) Vector→3D extrusion using CAD libraries with edge preservation validation, (3) 3D mesh validation and repair ensuring watertight/manifold geometry, and (4) 3D→G-code slicing with printer-specific profiles. The system implements automated quality gates at each stage using metrics like SSIM (≥0.85), edge IoU (≥0.75), and guarantees 100% watertight mesh output through automatic repair capabilities.

## Technical Context

**Language/Version**: Python 3.12 (aligned with project CODE_GUIDELINES.md)
**Primary Dependencies**:
- VTracer (image→vector conversion)
- Build123d (vector→3D CAD/extrusion)
- trimesh (mesh validation)
- Manifold3D (mesh repair)
- PrusaSlicer CLI (3D→G-code slicing)
- scikit-image (SSIM quality metrics)
- opencv-python (edge detection)
- Pydantic (data validation)

**Storage**: File-based (SVG, 3MF, G-code files) - local filesystem for POC, no database
**Testing**: pytest with >90% coverage target, TDD approach with Red-Green-Refactor cycle
**Target Platform**: Linux/macOS development environment, local execution (no cloud dependencies)
**Project Type**: Backend processing pipeline (single project with modular components)
**Performance Goals**:
- Total pipeline: <60 seconds per conversion (target <30s)
- Vectorization: <30 seconds
- 3D conversion: <10 seconds
- Quality validation: <10 seconds per stage

**Constraints**:
- Bambu Lab H2D build volume: 256×256×256mm (hard limit)
- File size limits: SVG <5MB, 3MF <10MB
- Path complexity: <1000 paths per SVG
- Mesh complexity: <100K faces (reject), <50K faces (warn)
- All meshes MUST be watertight and manifold (non-negotiable)

**Scale/Scope**:
- POC target: 100 conversions/day
- Batch processing: 100 images with <5% failure rate
- Test suite: 50+ automated tests covering edge cases
- Golden file baselines for regression detection

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

### ✅ I. Modular Components (PASS)

**Compliance**: The pipeline is explicitly designed as modular components:
- **model-converter** component: Image→Vector→3D conversion with independent operation
- **slicer** component: 3D→G-code generation with printer profiles
- **metrics** module: Quality validation independent of conversion logic
- **fixtures** module: Test dataset generation for reproducible testing

Each component has:
- Clear boundaries (file-based input/output contracts)
- Independent testability (can validate vector conversion without slicing)
- Well-documented contracts (SVG format in, 3MF format out)
- Composability (can orchestrate into automated pipeline: image→vector→3D→gcode)

**Evidence from spec**:
- FR-037 to FR-042 define testing fixtures and quality metrics as independent capabilities
- Key Entities section defines clear contracts (ConversionJob, QualityMetrics, VectorFile, MeshFile, GCodeFile)
- User Story prioritization enables independent delivery (P1: conversion, P2: slicing, P3: visual testing)

### ✅ II. Test-Driven Development (PASS)

**Compliance**: Specification mandates TDD approach:
- FR-037: Test image generation capability for synthetic fixtures
- FR-038: Golden file baselines for regression testing
- FR-039: Quality regression detection with 5% tolerance
- FR-040: Performance benchmarking for each pipeline stage
- FR-041: Performance SLA enforcement (<60s total)
- FR-042: Parametrized test suite covering edge cases
- SC-011: >90% code coverage requirement

**Testing layers planned**:
- Unit tests for metric calculations (SSIM, IoU, color correlation)
- Integration tests for pipeline stages (vector→3D, 3D→gcode)
- End-to-end tests for complete workflow (image→printable gcode)
- Contract tests for file format validation (SVG, 3MF, G-code)
- Regression tests with golden file baselines

**TDD discipline**: Tasks will follow Red-Green-Refactor (write test, fail, implement, pass, refactor)

### ✅ III. Clear Interfaces & Contracts (PASS)

**Compliance**: All component boundaries explicitly defined:

**Input Contracts**:
- Image input: PNG/JPEG, ≥512×512 resolution, RGB color space
- SVG input: Well-formed XML, viewBox defined, ≥1 shape/path
- 3MF input: Watertight mesh, manifold geometry, fits build volume

**Output Contracts**:
- SVG output: ≤8 colors, <5MB file size, <1000 paths, quality score ≥0.85
- 3MF output: Watertight (non-negotiable), manifold (non-negotiable), <10MB, depth accuracy ±5%
- G-code output: Valid structure, temperature commands, estimated print time/materials

**API Boundaries**:
- Conversion API: submit_image(path) → ConversionJob
- Validation API: validate_quality(svg, original) → QualityMetrics
- Mesh API: validate_mesh(3mf) → ValidationReport
- Slicing API: generate_gcode(3mf, profile) → GCodeFile

**Error Handling**:
- Explicit error hierarchy (ValidationError, RepairError, TimeoutError)
- FR-043 to FR-048 define comprehensive error handling
- Retry logic with exponential backoff (max 3 retries)
- Clear user-fixable vs system error distinction

### ✅ IV. Local-First POC (PASS)

**Compliance**: All processing executes locally without cloud dependencies:
- VTracer runs locally (Python bindings, no API calls)
- Build123d CAD operations local (OpenCascade kernel)
- PrusaSlicer CLI local installation (no cloud slicing)
- File-based storage (local filesystem, no cloud storage)
- No authentication/database required for POC
- Minimal dependencies (avoid custom ML infrastructure)

**Evidence**:
- Assumptions section confirms "Network access not required for core pipeline"
- Out of Scope explicitly excludes "Cloud-based processing or distributed pipeline execution"
- Architecture uses direct file-based communication between stages

### ✅ V. Python & Best Practices (PASS)

**Compliance**: Follows Python best practices per CODE_GUIDELINES.md:

**Configuration**:
- Environment variables for printer profiles, material settings
- FR-023 to FR-025 define configurable profiles (no hardcoded values)
- Extrusion depth, layer height, infill configurable (FR-008, FR-026, FR-027)

**Error Handling**:
- Explicit exception hierarchy (FR-043 to FR-048)
- Comprehensive logging (FR-036: timestamps, file sizes, performance metrics)
- Graceful degradation (FR-007: retry on marginal quality, FR-019: attempt mesh repair)

**Logging**:
- Structured format with stage timestamps (FR-036)
- Performance metrics at each stage (FR-040)
- Quality metrics logged for monitoring (FR-031)

**Dependencies**:
- All dependencies pinned in requirements.txt (investigation specifies versions)
- Virtual environment expected (Python 3.12 per CODE_GUIDELINES)
- Clear dependency documentation in investigation docs

**Code Organization**:
- Modular structure (model-converter/, slicer/, metrics/, fixtures/)
- Single Responsibility: each module handles one concern
- Dependency injection for testability (Pydantic models, pluggable validators)

### Constitution Check Summary

**Result**: ✅ **PASS** - All core principles satisfied

No violations requiring justification. The architecture naturally aligns with constitution principles:
- Modular components with clear boundaries enable parallel development
- TDD discipline ensures quality through comprehensive test coverage
- Clear contracts prevent integration failures
- Local-first POC minimizes infrastructure complexity
- Python best practices enforce maintainability and security

## Project Structure

### Documentation (this feature)

```text
specs/002-3d-model-pipeline/
├── spec.md              # Feature specification (completed)
├── plan.md              # This file (/speckit.plan command output)
├── research.md          # Phase 0 output (technology decisions)
├── data-model.md        # Phase 1 output (entity schemas)
├── quickstart.md        # Phase 1 output (developer guide)
├── contracts/           # Phase 1 output (API contracts)
│   ├── conversion.yaml  # ConversionJob API contract (OpenAPI)
│   ├── validation.yaml  # QualityMetrics API contract
│   └── formats.md       # File format specifications (SVG, 3MF, G-code)
├── checklists/          # Quality validation checklists
│   └── requirements.md  # Spec quality checklist (completed)
└── tasks.md             # Phase 2 output (/speckit.tasks command - NOT created by /speckit.plan)
```

### Source Code (repository root)

```text
backend/
├── model-converter/              # Vector → 3D conversion component
│   ├── src/
│   │   ├── __init__.py
│   │   ├── converter.py          # SVG import and 3D extrusion
│   │   ├── vectorizer.py         # Image → SVG using VTracer
│   │   ├── validator.py          # Mesh validation (watertight, manifold)
│   │   ├── repairer.py           # Manifold3D automatic repair
│   │   ├── metrics/              # Quality metric calculations
│   │   │   ├── __init__.py
│   │   │   ├── ssim.py           # Structural similarity
│   │   │   ├── edge_iou.py       # Edge preservation IoU
│   │   │   ├── color_fidelity.py # Histogram correlation
│   │   │   └── perceptual.py     # LPIPS (optional, tier 2)
│   │   └── models.py             # Pydantic data models
│   ├── tests/
│   │   ├── contract/             # File format contract tests
│   │   │   ├── test_svg_schema.py
│   │   │   ├── test_3mf_schema.py
│   │   │   └── test_validation_report.py
│   │   ├── integration/          # Multi-stage integration tests
│   │   │   ├── test_image_to_vector.py
│   │   │   ├── test_vector_to_3d.py
│   │   │   ├── test_mesh_validation.py
│   │   │   └── test_end_to_end.py
│   │   ├── unit/                 # Component unit tests
│   │   │   ├── test_converter.py
│   │   │   ├── test_vectorizer.py
│   │   │   ├── test_validator.py
│   │   │   ├── test_repairer.py
│   │   │   └── metrics/
│   │   │       ├── test_ssim.py
│   │   │       ├── test_edge_iou.py
│   │   │       └── test_color_fidelity.py
│   │   └── fixtures/             # Test data generation
│   │       ├── test_dataset_generator.py
│   │       ├── golden/           # Golden file baselines
│   │       │   ├── simple_text.svg
│   │       │   ├── simple_text_metrics.json
│   │       │   └── ...
│   │       └── synthetic/        # Generated test images
│   │           ├── text_TEST_1024x1024.png
│   │           └── ...
│   ├── requirements.txt          # Production dependencies
│   ├── requirements-dev.txt      # Development/testing dependencies
│   ├── pyproject.toml            # Build configuration, tool settings
│   └── README.md                 # Component documentation
│
├── slicer/                       # 3D → G-code generation component
│   ├── src/
│   │   ├── __init__.py
│   │   ├── slicer.py             # PrusaSlicer CLI wrapper
│   │   ├── config/               # Printer/material profiles
│   │   │   ├── bambu_h2d_pla.ini
│   │   │   ├── bambu_h2d_petg.ini
│   │   │   └── profile_schema.py # Profile validation
│   │   ├── post_process.py       # G-code post-processing (optional)
│   │   └── models.py             # Pydantic data models
│   ├── tests/
│   │   ├── contract/
│   │   │   ├── test_gcode_schema.py
│   │   │   └── test_profile_schema.py
│   │   ├── integration/
│   │   │   ├── test_3d_to_gcode.py
│   │   │   └── test_profile_loading.py
│   │   └── unit/
│   │       ├── test_slicer.py
│   │       └── test_post_process.py
│   ├── requirements.txt
│   ├── requirements-dev.txt
│   ├── pyproject.toml
│   └── README.md
│
└── shared/                       # Shared utilities and models
    ├── __init__.py
    ├── models.py                 # Shared Pydantic models (ConversionJob, etc.)
    ├── file_io.py                # File handling utilities
    ├── exceptions.py             # Custom exception hierarchy
    └── logging_config.py         # Structured logging setup

investigations/                   # Research and planning artifacts
├── 003-3d-model-pipeline-plan.md        # Pipeline architecture research
└── 004-image-to-3d-testing-metrics.md   # Quality metrics research
```

**Structure Decision**: Backend processing pipeline (single project structure) selected because:
1. All components are Python-based processing modules (no frontend/mobile)
2. Modular organization enables independent component development (model-converter vs slicer)
3. Shared utilities reduce duplication (Pydantic models, exceptions, logging)
4. File-based communication between modules (SVG, 3MF, G-code files)
5. Aligns with existing backend/ai-generation structure in repository

## Complexity Tracking

No violations requiring justification - all constitution principles satisfied by design.

## Implementation Workflow

### Phase 0: Research ✅ COMPLETE

**Output**: [research.md](./research.md)

**Summary**: All technology decisions finalized based on investigations 003 and 004:

- **Image Vectorization**: VTracer (color quantization, fast performance)
- **Vector → 3D**: Build123d (pure Python CAD, SVG import, 3MF export)
- **Mesh Validation**: trimesh (watertight/manifold checks, property calculation)
- **Mesh Repair**: Manifold3D (automatic repair, 80% success rate)
- **G-code Generation**: PrusaSlicer CLI (Bambu Lab profiles, accurate estimates)
- **Quality Metrics**: SSIM (scikit-image), Edge IoU (OpenCV), Color Correlation (NumPy/SciPy), LPIPS optional (tier 2)
- **Test Fixtures**: Synthetic dataset generation using Pillow
- **Data Validation**: Pydantic v2
- **Testing**: pytest with >90% coverage target

**Outcome**: Zero "NEEDS CLARIFICATION" markers remain in Technical Context. All dependencies documented with rationale and alternatives considered.

---

### Phase 1: Design & Contracts ✅ COMPLETE

**Outputs**:
- [data-model.md](./data-model.md) - Pydantic schemas for all 9 key entities
- [contracts/formats.md](./contracts/formats.md) - File format specifications with validation rules
- [quickstart.md](./quickstart.md) - Developer setup and workflow guide

**Data Models Defined**:
1. **ConversionJob** - Pipeline orchestration with stage tracking, timestamps, error handling
2. **QualityMetrics** - Vectorization quality with weighted overall score calculation
3. **VectorFile** - SVG metadata with structure validation and complexity limits
4. **MeshFile** - 3D mesh with printability validation (watertight, manifold, build volume)
5. **GCodeFile** - G-code with print estimates and temperature settings
6. **ValidationReport** - Comprehensive quality assessment across all stages
7. **PrinterProfile** - Bambu Lab H2D specifications (256×256×256mm build volume)
8. **MaterialProfile** - PLA and PETG temperature/speed settings
9. **TestFixture** - Synthetic test image specifications with expected quality ranges

**File Format Contracts**:
- **Input Images**: PNG/JPEG, RGB, ≥512×512, ≤20MB
- **SVG**: Well-formed XML, viewBox, ≥1 shape, ≤5MB, ≤1000 paths, ≤8 colors
- **3MF**: Watertight (required), manifold (required), ≤256mm build volume, ≤10MB, ≤100K faces
- **G-code**: Non-empty, temperature commands required, metadata extraction for estimates
- **JSON**: ConversionJob and QualityMetrics serialization contracts

**Developer Resources**:
- Environment setup instructions (Python 3.12, venv, PrusaSlicer CLI)
- TDD workflow (Red-Green-Refactor cycle)
- Common tasks (run tests, generate fixtures, validate formats)
- Debugging tips (logging, intermediate files, visualization)
- Performance profiling guidance (benchmarks, targets)

**Agent Context Updated**: ✅ New technologies added to CLAUDE.md

---

### Phase 2: Task Generation

**Status**: ⏳ PENDING - Use `/speckit.tasks` command to generate tasks.md

This phase is NOT part of `/speckit.plan`. To proceed with implementation planning:

```bash
/speckit.tasks
```

This will generate:
- **tasks.md**: Dependency-ordered implementation tasks with test-first approach
- Task breakdown for each component (model-converter, slicer, shared utilities)
- Quality gates and acceptance criteria per task
- Estimated effort and dependencies

---

## Plan Completion Summary

✅ **Phase 0 Complete**: All technology decisions finalized in research.md
✅ **Phase 1 Complete**: Data models, contracts, and developer guide created
✅ **Agent Context Updated**: CLAUDE.md updated with new technologies

**Next Action**: Run `/speckit.tasks` to generate implementation task breakdown.

**Artifacts Created**:
- `plan.md` (this file) - Implementation plan with technical context and constitution check
- `research.md` - Technology decisions with rationale
- `data-model.md` - Pydantic v2 schemas for all entities
- `contracts/formats.md` - File format specifications
- `quickstart.md` - Developer quickstart guide
- Updated `CLAUDE.md` - Agent context with new technologies

**Ready for**: Task generation and implementation execution.
