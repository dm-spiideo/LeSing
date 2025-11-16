# Tasks: 3D Model Pipeline

**Input**: Design documents from `/specs/002-3d-model-pipeline/`
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/formats.md

**Tests**: This feature mandates TDD approach (FR-037 to FR-042, SC-011: >90% coverage). Test tasks are included and MUST be completed BEFORE implementation tasks.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3, US4)
- Include exact file paths in descriptions

## Path Conventions

Based on plan.md structure:
- Backend components: `backend/model-converter/`, `backend/slicer/`, `backend/shared/`
- Tests: `backend/model-converter/tests/`, `backend/slicer/tests/`
- Fixtures: `backend/model-converter/tests/fixtures/`

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure per plan.md

- [ ] T001 Create backend directory structure (backend/model-converter, backend/slicer, backend/shared)
- [ ] T002 [P] Create requirements.txt in backend/model-converter with vtracer, build123d, trimesh, manifold3d, scikit-image, opencv-python, pydantic
- [ ] T003 [P] Create requirements-dev.txt in backend/model-converter with pytest, pytest-cov, pytest-benchmark
- [ ] T004 [P] Create requirements.txt in backend/slicer with pydantic
- [ ] T005 [P] Create requirements-dev.txt in backend/slicer with pytest, pytest-cov
- [ ] T006 [P] Create pyproject.toml in backend/model-converter with ruff configuration per CODE_GUIDELINES.md
- [ ] T007 [P] Create pyproject.toml in backend/slicer with ruff configuration
- [ ] T008 [P] Create README.md in backend/model-converter documenting component purpose
- [ ] T009 [P] Create README.md in backend/slicer documenting component purpose
- [ ] T010 Create __init__.py files for all Python package directories (src/, tests/, metrics/)

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T011 [P] Create shared Pydantic models in backend/shared/models.py (ConversionJob, QualityMetrics, VectorFile, MeshFile, GCodeFile, ValidationReport, PrinterProfile, MaterialProfile, TestFixture per data-model.md)
- [ ] T012 [P] Create custom exception hierarchy in backend/shared/exceptions.py (ValidationError, RepairError, TimeoutError, FileFormatError)
- [ ] T013 [P] Create file I/O utilities in backend/shared/file_io.py (image loading, SVG reading, 3MF loading, G-code validation)
- [ ] T014 [P] Create structured logging configuration in backend/shared/logging_config.py with timestamps and performance metrics (FR-036)
- [ ] T015 Create test fixtures directory structure (backend/model-converter/tests/fixtures/golden, backend/model-converter/tests/fixtures/synthetic)
- [ ] T016 [P] Create synthetic test image generator in backend/model-converter/tests/fixtures/generate_test_images.py (FR-037: text, resolution, color count parametrization)
- [ ] T017 Generate baseline test images (simple text 1024x1024, thin lines 1024x1024, high res 2048x2048, extreme aspect 2560x256) using generator from T016
- [ ] T018 [P] Create printer profiles in backend/slicer/src/config/bambu_h2d_pla.ini with 256x256x256mm build volume, 190-220°C nozzle, 60°C bed (FR-024)
- [ ] T019 [P] Create printer profile in backend/slicer/src/config/bambu_h2d_petg.ini with 220-250°C nozzle, 70°C bed (FR-025)

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Basic Image-to-3D Conversion (Priority: P1) 🎯 MVP

**Goal**: Transform AI-generated images into valid, printable 3D model files (3MF format) with watertight/manifold guarantees

**Independent Test**: Provide a known good AI-generated image, run conversion, verify output is valid 3MF that passes watertight/manifold checks and fits build volume

### Contract Tests for User Story 1 (TDD - Write FIRST, ensure FAIL)

- [ ] T020 [P] [US1] Write contract test for PNG/JPEG input validation in backend/model-converter/tests/contract/test_image_schema.py (RGB, ≥512x512, ≤20MB per contracts/formats.md)
- [ ] T021 [P] [US1] Write contract test for SVG output schema in backend/model-converter/tests/contract/test_svg_schema.py (well-formed XML, viewBox, ≤5MB, ≤1000 paths, ≤8 colors per FR-004, FR-005)
- [ ] T022 [P] [US1] Write contract test for 3MF output schema in backend/model-converter/tests/contract/test_3mf_schema.py (watertight, manifold, ≤256mm build volume, ≤10MB per FR-013, FR-014, FR-015)

### Unit Tests for User Story 1 (TDD - Write FIRST, ensure FAIL)

- [ ] T023 [P] [US1] Write unit tests for vectorizer in backend/model-converter/tests/unit/test_vectorizer.py (VTracer wrapper, 8-color quantization, file size limits per FR-001, FR-005)
- [ ] T024 [P] [US1] Write unit tests for SVG→3D converter in backend/model-converter/tests/unit/test_converter.py (Build123d extrusion, 2-10mm depth, FR-008)
- [ ] T025 [P] [US1] Write unit tests for mesh validator in backend/model-converter/tests/unit/test_validator.py (watertight check, manifold check, build volume check per FR-013, FR-014, FR-015)
- [ ] T026 [P] [US1] Write unit tests for mesh repairer in backend/model-converter/tests/unit/test_repairer.py (Manifold3D wrapper, success/failure reporting per FR-019, FR-020)

### Integration Tests for User Story 1 (TDD - Write FIRST, ensure FAIL)

- [ ] T027 [P] [US1] Write integration test for image→vector pipeline in backend/model-converter/tests/integration/test_image_to_vector.py (PNG→SVG with quality validation)
- [ ] T028 [P] [US1] Write integration test for vector→3D pipeline in backend/model-converter/tests/integration/test_vector_to_3d.py (SVG→3MF with validation)
- [ ] T029 [US1] Write integration test for mesh validation→repair workflow in backend/model-converter/tests/integration/test_mesh_validation.py (detect non-watertight, attempt repair, validate result)
- [ ] T030 [US1] Write end-to-end test for full image→3D pipeline in backend/model-converter/tests/integration/test_end_to_end.py (PNG→3MF, all stages, acceptance scenario 1 from spec.md)

### Implementation for User Story 1

- [ ] T031 [US1] Implement image→SVG vectorizer in backend/model-converter/src/vectorizer.py (VTracer wrapper with color_mode=8, timeout handling per FR-001, FR-046)
- [ ] T032 [US1] Implement SVG structure validator in backend/model-converter/src/vectorizer.py (XML parsing, viewBox check, geometry check per FR-004)
- [ ] T033 [US1] Implement SVG→3D converter in backend/model-converter/src/converter.py (Build123d import_svg + extrude with configurable depth 2-10mm per FR-008)
- [ ] T034 [US1] Implement 3MF metadata export in backend/model-converter/src/converter.py (source SVG reference, extrusion depth per FR-009)
- [ ] T035 [US1] Implement mesh validator in backend/model-converter/src/validator.py (trimesh is_watertight, is_volume, bounds check per FR-013, FR-014, FR-015)
- [ ] T036 [US1] Implement mesh property calculator in backend/model-converter/src/validator.py (volume, surface area, vertex/face counts per FR-016)
- [ ] T037 [US1] Implement face count warnings/rejection in backend/model-converter/src/validator.py (warn >50K, reject >100K per FR-017, FR-018)
- [ ] T038 [US1] Implement mesh repairer in backend/model-converter/src/repairer.py (Manifold3D automatic repair with before/after status per FR-019, FR-020, FR-021)
- [ ] T039 [US1] Implement extrusion depth accuracy validation in backend/model-converter/src/converter.py (measure actual depth, ±5% tolerance per FR-010)
- [ ] T040 [US1] Add error handling for corrupted images in backend/model-converter/src/vectorizer.py (detect and reject with clear message per FR-043)
- [ ] T041 [US1] Add error handling for empty/malformed SVG in backend/model-converter/src/converter.py (no paths error, XML parsing error per FR-044, FR-045)
- [ ] T042 [US1] Add retry logic with exponential backoff in backend/model-converter/src/vectorizer.py (max 3 retries per FR-047)
- [ ] T043 [US1] Add logging for US1 operations in all modules (timestamps, file sizes, performance metrics per FR-036)

**Checkpoint**: At this point, User Story 1 should be fully functional - can convert images to valid, printable 3D models

---

## Phase 4: User Story 2 - Automated Quality Validation (Priority: P1)

**Goal**: Automatic quality validation at each stage with clear pass/fail feedback and actionable error messages

**Independent Test**: Feed known good and bad inputs, verify system correctly identifies quality issues with specific metric scores and error details

### Unit Tests for User Story 2 (TDD - Write FIRST, ensure FAIL)

- [ ] T044 [P] [US2] Write unit tests for SSIM metric in backend/model-converter/tests/unit/metrics/test_ssim.py (structural similarity ≥0.85 threshold per FR-002)
- [ ] T045 [P] [US2] Write unit tests for Edge IoU metric in backend/model-converter/tests/unit/metrics/test_edge_iou.py (edge preservation ≥0.75 threshold per FR-003)
- [ ] T046 [P] [US2] Write unit tests for color fidelity metric in backend/model-converter/tests/unit/metrics/test_color_fidelity.py (histogram correlation ≥0.90 per FR-006)
- [ ] T047 [P] [US2] Write unit tests for overall quality score calculation (weighted combination per FR-032: SSIM 25%, edge IoU 20%, color 15%, coverage 10%, quantization 10%)

### Integration Tests for User Story 2 (TDD - Write FIRST, ensure FAIL)

- [ ] T048 [US2] Write integration test for quality validation workflow in backend/model-converter/tests/integration/test_quality_validation.py (calculate metrics, generate report, pass/fail decision per FR-031, FR-033)
- [ ] T049 [US2] Write integration test for automatic retry on low quality in backend/model-converter/tests/integration/test_quality_retry.py (SSIM 0.75-0.84 triggers retry per FR-007, acceptance scenario 4)

### Implementation for User Story 2

- [ ] T050 [P] [US2] Implement SSIM calculator in backend/model-converter/src/metrics/ssim.py (scikit-image SSIM, re-rasterize SVG for comparison per FR-002)
- [ ] T051 [P] [US2] Implement Edge IoU calculator in backend/model-converter/src/metrics/edge_iou.py (OpenCV Canny edge detection, intersection-over-union per FR-003)
- [ ] T052 [P] [US2] Implement color fidelity calculator in backend/model-converter/src/metrics/color_fidelity.py (RGB histogram correlation using NumPy/SciPy per FR-006)
- [ ] T053 [P] [US2] Implement coverage ratio calculator in backend/model-converter/src/metrics/ssim.py (non-background pixel ratio for overall score)
- [ ] T054 [P] [US2] Implement color quantization error calculator in backend/model-converter/src/metrics/color_fidelity.py (palette accuracy for overall score)
- [ ] T055 [US2] Implement overall quality score calculator in backend/model-converter/src/metrics/__init__.py (weighted combination per FR-032, return QualityMetrics Pydantic model)
- [ ] T056 [US2] Implement quality report generator in backend/model-converter/src/validator.py (all metrics, pass/fail status, warnings/errors per FR-031)
- [ ] T057 [US2] Implement automatic retry logic in backend/model-converter/src/vectorizer.py (adjust parameters when 0.75 ≤ quality < 0.85 per FR-007)
- [ ] T058 [US2] Implement edge preservation validation for 3D models in backend/model-converter/src/converter.py (top-view rendering, IoU ≥0.85 per FR-011)
- [ ] T059 [US2] Add clear error messages for validation failures (distinguish user-fixable vs system issues per FR-048)
- [ ] T060 [US2] Add specific dimension reporting for build volume violations (show actual vs max 256mm per acceptance scenario 3)

**Checkpoint**: At this point, User Stories 1 AND 2 work together - conversions have automated quality gates with clear feedback

---

## Phase 5: User Story 3 - G-code Generation for Bambu Lab H2D (Priority: P2)

**Goal**: Generate printer-ready G-code optimized for Bambu Lab H2D with material profiles (PLA/PETG) and accurate print estimates

**Independent Test**: Provide known good 3MF model, generate G-code, verify contains correct temperature commands and produces reasonable time/material estimates

### Contract Tests for User Story 3 (TDD - Write FIRST, ensure FAIL)

- [ ] T061 [P] [US3] Write contract test for G-code output schema in backend/slicer/tests/contract/test_gcode_schema.py (non-empty, temperature commands, metadata extraction per contracts/formats.md, FR-030)
- [ ] T062 [P] [US3] Write contract test for printer profile schema in backend/slicer/tests/contract/test_profile_schema.py (build volume, nozzle diameter, material support per FR-023)

### Unit Tests for User Story 3 (TDD - Write FIRST, ensure FAIL)

- [ ] T063 [P] [US3] Write unit tests for PrusaSlicer CLI wrapper in backend/slicer/tests/unit/test_slicer.py (subprocess calls, profile loading, timeout handling per FR-022, FR-046)
- [ ] T064 [P] [US3] Write unit tests for G-code metadata extraction in backend/slicer/tests/unit/test_slicer.py (parse comments for print time, filament usage, layer count per FR-028)
- [ ] T065 [P] [US3] Write unit tests for profile validation in backend/slicer/tests/unit/test_slicer.py (Bambu Lab H2D, PLA temps 190-220°C, PETG 220-250°C per FR-024, FR-025)

### Integration Tests for User Story 3 (TDD - Write FIRST, ensure FAIL)

- [ ] T066 [US3] Write integration test for 3D→G-code pipeline in backend/slicer/tests/integration/test_3d_to_gcode.py (3MF input, G-code output, estimate accuracy per acceptance scenario 1, 2)
- [ ] T067 [US3] Write integration test for profile loading in backend/slicer/tests/integration/test_profile_loading.py (load PLA profile, load PETG profile, validate settings)

### Implementation for User Story 3

- [ ] T068 [US3] Implement PrusaSlicer CLI wrapper in backend/slicer/src/slicer.py (subprocess.run with printer/material profiles, timeout 5 minutes per FR-022, FR-046)
- [ ] T069 [US3] Implement profile loader in backend/slicer/src/slicer.py (read .ini files from config/, validate against PrinterProfile/MaterialProfile per FR-023, FR-024, FR-025)
- [ ] T070 [US3] Implement layer height configuration in backend/slicer/src/slicer.py (0.2mm standard, 0.1mm high quality per FR-026)
- [ ] T071 [US3] Implement infill configuration in backend/slicer/src/slicer.py (20% lightweight, 100% solid per FR-027)
- [ ] T072 [US3] Implement G-code metadata extractor in backend/slicer/src/slicer.py (parse comments for print time, filament usage, layer count, cost per FR-028)
- [ ] T073 [US3] Implement G-code validator in backend/slicer/src/slicer.py (non-empty check, temperature command check per FR-030)
- [ ] T074 [US3] Implement support structure detection in backend/slicer/src/slicer.py (automatic supports when needed per FR-029)
- [ ] T075 [US3] Add error handling for missing printer profile in backend/slicer/src/slicer.py (list available profiles per edge case)
- [ ] T076 [US3] Add logging for G-code generation operations (timestamps, file sizes, estimates per FR-036)

**Checkpoint**: At this point, User Stories 1, 2, AND 3 work together - full pipeline from image to printer-ready G-code

---

## Phase 6: User Story 4 - Visual Subjective Quality Testing (Priority: P3)

**Goal**: Visual comparison tools for side-by-side quality assessment beyond automated metrics (original image, vector, 3D rendering)

**Independent Test**: Generate comparison visualizations for known test cases, verify displays correctly and aids quality assessment

### Unit Tests for User Story 4 (TDD - Write FIRST, ensure FAIL)

- [ ] T077 [P] [US4] Write unit tests for re-rasterization in backend/model-converter/tests/unit/test_visualization.py (SVG→PNG at matching resolution)
- [ ] T078 [P] [US4] Write unit tests for 3D top-view rendering in backend/model-converter/tests/unit/test_visualization.py (trimesh rendering, matching scale)
- [ ] T079 [P] [US4] Write unit tests for HTML report generation in backend/model-converter/tests/unit/test_visualization.py (side-by-side layout, metrics overlay per FR-035)

### Integration Tests for User Story 4 (TDD - Write FIRST, ensure FAIL)

- [ ] T080 [US4] Write integration test for visual comparison workflow in backend/model-converter/tests/integration/test_visual_comparison.py (generate comparison, save HTML, validate content per acceptance scenario 1, 3)

### Implementation for User Story 4

- [ ] T081 [P] [US4] Implement SVG re-rasterizer in backend/model-converter/src/visualization.py (cairosvg or similar, match original resolution per FR-034)
- [ ] T082 [P] [US4] Implement 3D top-view renderer in backend/model-converter/src/visualization.py (trimesh scene, camera positioning, matching scale per FR-034)
- [ ] T083 [US4] Implement side-by-side comparison generator in backend/model-converter/src/visualization.py (original, re-rasterized SVG, 3D top-view per FR-034)
- [ ] T084 [US4] Implement HTML report generator in backend/model-converter/src/visualization.py (batch support, metrics overlays, pass/fail indicators per FR-035)
- [ ] T085 [P] [US4] Implement PDF export for visual comparisons in backend/model-converter/src/visualization.py (suitable for archival/approval per acceptance scenario 4)
- [ ] T086 [US4] Integrate visual comparison into quality validation workflow (generate on completion, include in ValidationReport)

**Checkpoint**: All user stories complete - full pipeline with comprehensive quality validation and visual review tools

---

## Phase 7: Testing & Quality Assurance

**Purpose**: Golden file baselines, regression detection, performance benchmarking per FR-038 through FR-042

- [ ] T087 [P] Generate golden file baselines in backend/model-converter/tests/fixtures/golden/ (reference SVG files, expected metric scores per FR-038)
- [ ] T088 [P] Write regression tests in backend/model-converter/tests/integration/test_regression.py (compare outputs to baselines, 5% tolerance per FR-039)
- [ ] T089 [P] Write performance benchmarks in backend/model-converter/tests/integration/test_performance.py (measure each stage, enforce <60s total per FR-040, FR-041)
- [ ] T090 [P] Write parametrized edge case tests in backend/model-converter/tests/integration/test_edge_cases.py (low res, high res, extreme aspect, thin lines, complex paths, empty/malformed per FR-042)
- [ ] T091 Validate test coverage >90% using pytest-cov (SC-011 requirement)
- [ ] T092 Run performance benchmarks and verify SLA compliance (<30s vectorization, <10s 3D conversion, <10s validation, <60s total per plan.md)
- [ ] T093 Run batch conversion test with 100 images (verify <5% failure rate per SC-009, plan.md)

---

## Phase 8: Polish & Cross-Cutting Concerns

**Purpose**: Documentation, cleanup, and final validation

- [ ] T094 [P] Update backend/model-converter/README.md with usage examples from quickstart.md
- [ ] T095 [P] Update backend/slicer/README.md with G-code generation examples
- [ ] T096 [P] Create example scripts in backend/model-converter/examples/ demonstrating image→3D→G-code workflow
- [ ] T097 Code cleanup and refactoring (apply ruff formatting per CLAUDE.md)
- [ ] T098 Security review of file handling (validate paths, prevent directory traversal)
- [ ] T099 Run full quickstart.md validation (setup from scratch, run all examples)
- [ ] T100 Final integration test with real AI-generated name sign images (validate end-to-end quality)

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Story 1 (Phase 3)**: Depends on Foundational (Phase 2) - Core MVP functionality
- **User Story 2 (Phase 4)**: Depends on Foundational (Phase 2) + integrates with US1 - Quality validation layer
- **User Story 3 (Phase 5)**: Depends on Foundational (Phase 2) + requires US1 output (3MF files) - G-code generation
- **User Story 4 (Phase 6)**: Depends on Foundational (Phase 2) + integrates with US1/US2 - Visual quality tools
- **Testing & QA (Phase 7)**: Depends on US1/US2 complete (minimum), ideally all user stories
- **Polish (Phase 8)**: Depends on all desired user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories - CORE MVP
- **User Story 2 (P1)**: Can start after Foundational (Phase 2) - Integrates with US1 but independently testable (can validate metrics without full pipeline)
- **User Story 3 (P2)**: Can start after Foundational (Phase 2) - Requires 3MF files from US1 for testing, but independently testable with fixture 3MF files
- **User Story 4 (P3)**: Can start after Foundational (Phase 2) - Uses outputs from US1/US2 but independently testable with fixture files

### Within Each User Story (TDD Discipline)

1. **Contract Tests** (if applicable) - Write FIRST, ensure FAIL
2. **Unit Tests** - Write FIRST, ensure FAIL
3. **Integration Tests** - Write FIRST, ensure FAIL
4. **Implementation** - Minimal code to make tests PASS
5. **Refactor** - Clean up implementation while keeping tests GREEN
6. **Story Checkpoint** - Validate independently before next story

### Parallel Opportunities

- **Phase 1 (Setup)**: All T002-T010 can run in parallel (different files)
- **Phase 2 (Foundational)**: All T011-T019 can run in parallel (different modules)
- **User Story 1**:
  - Contract tests T020-T022 in parallel
  - Unit tests T023-T026 in parallel
  - Integration tests T027-T028 in parallel
  - Implementation: T031-T032 parallel, T050-T054 parallel (metrics)
- **User Story 2**:
  - Unit tests T044-T047 in parallel
  - Implementation: T050-T054 parallel (all metrics)
- **User Story 3**:
  - Contract tests T061-T062 in parallel
  - Unit tests T063-T065 in parallel
- **User Story 4**:
  - Unit tests T077-T079 in parallel
  - Implementation: T081-T082 parallel
- **Phase 7 (Testing)**: T087-T090 can run in parallel
- **Phase 8 (Polish)**: T094-T096 can run in parallel

---

## Parallel Example: User Story 1

Launch all contract tests together (TDD - write FIRST):
```bash
Task T020: "Write contract test for PNG/JPEG input validation in backend/model-converter/tests/contract/test_image_schema.py"
Task T021: "Write contract test for SVG output schema in backend/model-converter/tests/contract/test_svg_schema.py"
Task T022: "Write contract test for 3MF output schema in backend/model-converter/tests/contract/test_3mf_schema.py"
```

Launch all unit tests together (TDD - write FIRST):
```bash
Task T023: "Write unit tests for vectorizer in backend/model-converter/tests/unit/test_vectorizer.py"
Task T024: "Write unit tests for SVG→3D converter in backend/model-converter/tests/unit/test_converter.py"
Task T025: "Write unit tests for mesh validator in backend/model-converter/tests/unit/test_validator.py"
Task T026: "Write unit tests for mesh repairer in backend/model-converter/tests/unit/test_repairer.py"
```

Launch core implementation modules together (after tests written and failing):
```bash
Task T031: "Implement image→SVG vectorizer in backend/model-converter/src/vectorizer.py"
Task T033: "Implement SVG→3D converter in backend/model-converter/src/converter.py"
Task T035: "Implement mesh validator in backend/model-converter/src/validator.py"
Task T038: "Implement mesh repairer in backend/model-converter/src/repairer.py"
```

---

## Parallel Example: User Story 2

Launch all metric calculators together (after tests written and failing):
```bash
Task T050: "Implement SSIM calculator in backend/model-converter/src/metrics/ssim.py"
Task T051: "Implement Edge IoU calculator in backend/model-converter/src/metrics/edge_iou.py"
Task T052: "Implement color fidelity calculator in backend/model-converter/src/metrics/color_fidelity.py"
Task T053: "Implement coverage ratio calculator in backend/model-converter/src/metrics/ssim.py"
Task T054: "Implement color quantization error calculator in backend/model-converter/src/metrics/color_fidelity.py"
```

---

## Implementation Strategy

### MVP First (User Stories 1 + 2 Only)

**Rationale**: Both are P1 priority, and quality validation (US2) is essential for production reliability per spec.md

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL - blocks all stories)
3. Complete Phase 3: User Story 1 (Basic conversion)
4. Complete Phase 4: User Story 2 (Quality validation)
5. **STOP and VALIDATE**: Test US1+US2 together independently
6. Run batch test with 100 images (verify <5% failure, quality gates work)
7. Deploy/demo MVP - Operators can now convert images with confidence

**MVP Capabilities**:
- ✅ Convert PNG/JPEG → valid 3D models (3MF)
- ✅ Automated quality validation (SSIM, Edge IoU, color fidelity)
- ✅ Watertight/manifold guarantees
- ✅ Automatic mesh repair
- ✅ Clear error messages
- ⏸️ Manual G-code slicing required (US3 not in MVP)
- ⏸️ No visual comparison tools yet (US4 not in MVP)

### Incremental Delivery

1. **Foundation** (Phases 1-2) → Core infrastructure ready
2. **MVP Release** (Phases 3-4: US1+US2) → Image→3D conversion with quality gates
   - Test independently with 100 images
   - Deploy/Demo to operators
3. **Full Automation** (Phase 5: US3) → Add G-code generation
   - Test independently with fixture 3MF files
   - Integrate with US1/US2
   - Deploy/Demo complete pipeline
4. **Quality Tools** (Phase 6: US4) → Add visual comparison
   - Test independently
   - Integrate with US1/US2
   - Deploy/Demo final feature set
5. **Production Ready** (Phases 7-8) → Regression tests, performance validation, polish

### Parallel Team Strategy

With multiple developers after Foundational phase completes:

**Option 1: Sequential Focus (Recommended for MVP)**
- Team collaborates on US1 (T020-T043) → Validate independently
- Team collaborates on US2 (T044-T060) → Validate US1+US2 together
- **STOP**: Deploy MVP
- Team collaborates on US3 → Validate and deploy
- Team collaborates on US4 → Validate and deploy

**Option 2: Parallel Stories (If team has 3+ developers)**
- Developer A: User Story 1 (T020-T043)
- Developer B: User Story 2 (T044-T060) in parallel with A
- Once A+B complete: Integrate and validate together
- Developer C: User Story 3 (T061-T076) - can start early with fixture 3MF files
- Developer D: User Story 4 (T077-T086) - can start early with fixture files
- Final integration and testing

---

## Notes

- **TDD Discipline**: ALL test tasks (T020-T030, T044-T049, T061-T067, T077-T080) MUST be written FIRST and FAIL before implementation
- **Coverage Target**: >90% per SC-011 - validate with pytest-cov after Phase 7
- **Performance SLA**: <60s total pipeline (target <30s) - validate with pytest-benchmark in Phase 7
- **Quality Gates**: SSIM ≥0.85, Edge IoU ≥0.75, Color ≥0.90, Overall ≥0.85 per FR-002, FR-003, FR-006, FR-033
- **Watertight Guarantee**: 100% of output meshes MUST be watertight/manifold (SC-001, SC-006) - use automatic repair (FR-019)
- **[P] tasks**: Different files, no dependencies, can run truly in parallel
- **[Story] labels**: Map tasks to user stories for traceability and independent validation
- **File paths**: All exact paths included per task generation rules
- **Checkpoints**: Stop after each user story phase to validate independently
- **Commit strategy**: Commit after each task or logical group (e.g., all metrics together)
- **Ruff linting**: Run `./run_ruff.sh` per CLAUDE.md before committing

---

## Success Criteria Mapping

Tasks are designed to satisfy all 12 success criteria from spec.md:

- **SC-001** (100% watertight): T035, T038 (mesh validation + repair)
- **SC-002** (95% quality ≥0.85): T055, T056 (overall quality score)
- **SC-003** (<60s pipeline): T089, T092 (performance benchmarks)
- **SC-004** (SSIM ≥0.85): T050, T056 (SSIM metric + reporting)
- **SC-005** (Edge IoU ≥0.75): T051, T058 (Edge IoU for vector and 3D)
- **SC-006** (100% unprintable catch): T035, T037 (validation + face count checks)
- **SC-007** (80% repair success): T038 (Manifold3D repair)
- **SC-008** (±10% estimate accuracy): T072 (G-code metadata extraction)
- **SC-009** (<5% failure in batch): T093 (batch test with 100 images)
- **SC-010** (<10s quality assessment): T084 (HTML visual comparison)
- **SC-011** (>90% coverage): T091 (pytest-cov validation)
- **SC-012** (Performance regression detection): T089 (benchmarks with SLA enforcement)
