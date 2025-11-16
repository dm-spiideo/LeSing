# Technology Research: 3D Model Pipeline

**Feature**: 002-3d-model-pipeline
**Created**: 2025-11-16
**Status**: Decisions Finalized
**Source**: [investigation 003](../../investigations/003-3d-model-pipeline-plan.md), [investigation 004](../../investigations/004-image-to-3d-testing-metrics.md)

## Overview

This document consolidates technology decisions for the 3D Model Pipeline that converts AI-generated 2D images into printable 3D models and G-code files. All decisions are based on comprehensive research documented in investigations 003 and 004.

## Decision 1: Image Vectorization - VTracer

**Decision**: Use VTracer library for PNG/JPEG → SVG conversion with color quantization

**Rationale**:
- Native Python bindings via `vtracer` package (no subprocess calls required)
- Built-in color quantization supporting 2-8 color modes (meets FR-001 requirement)
- Fast performance (<10 seconds for typical inputs per investigation 003)
- Produces clean SVG output with minimal path complexity
- Active maintenance and proven stability in production environments

**Alternatives Considered**:
1. **potrace** - Rejected: Binary-only (no color support), requires preprocessing for color images
2. **autotrace** - Rejected: Poor Python integration, requires subprocess calls, less accurate
3. **OpenCV contour detection** - Rejected: Produces noisy paths, requires extensive post-processing
4. **Custom ML model** - Rejected: Out of scope for POC (violates local-first principle)

**Implementation Notes**:
- Will use `colormode` parameter set to 8 colors maximum
- SVG output validated against schema (FR-004)
- Quality measured using SSIM ≥ 0.85 threshold (FR-002)

**Evidence**: Investigation 003 section "Stage 1: Image → Vector (VTracer)" demonstrates successful conversion with quality metrics meeting specification requirements.

---

## Decision 2: Vector to 3D Conversion - Build123d

**Decision**: Use Build123d library for SVG import and 3D extrusion operations

**Rationale**:
- Pure Python CAD library with clean API (no C++ bindings complications)
- Native SVG import capability via `import_svg()` function
- Programmatic extrusion with precise depth control (FR-008: 2-10mm configurable depth)
- Built on OpenCascade kernel (industry-standard CAD geometry engine)
- Active development with strong community support
- Exports to 3MF format natively (FR-009)

**Alternatives Considered**:
1. **CadQuery** - Rejected: More complex API, heavier dependencies, slower performance
2. **OpenSCAD** - Rejected: Requires subprocess calls, text-based interface unsuitable for automation
3. **Blender Python API** - Rejected: Heavyweight dependency (800MB+), designed for artistic modeling not CAD
4. **FreeCAD Python** - Rejected: Complex installation, poor headless support, stability issues

**Implementation Notes**:
- SVG import followed by `extrude()` operation with configurable depth
- Top-view rendering for edge IoU validation (FR-011: ≥0.85 IoU)
- 3MF export includes metadata (source SVG, extrusion parameters per FR-009)

**Evidence**: Investigation 003 section "Stage 2: Vector → 3D (Build123d)" validates SVG→3D workflow with accurate depth control (±5% per FR-010).

---

## Decision 3: Mesh Validation - trimesh

**Decision**: Use trimesh library for 3D mesh validation and property calculation

**Rationale**:
- Comprehensive validation API (`is_watertight`, `is_volume`, `is_manifold`)
- Fast property calculations (volume, surface area, face count per FR-016)
- Native 3MF format support for import/export
- Efficient mesh analysis algorithms (handles 100K+ faces)
- Well-documented and widely used in 3D printing ecosystem

**Alternatives Considered**:
1. **PyMesh** - Rejected: Installation difficulties, less active maintenance
2. **Open3D** - Rejected: Focused on point clouds, heavier dependency
3. **meshio** - Rejected: File I/O only, no validation capabilities
4. **Custom validation** - Rejected: Reinventing well-tested algorithms, high risk

**Implementation Notes**:
- Validation checks: `is_watertight` (FR-013), `is_volume` (FR-014), `bounds` check for build volume (FR-015)
- Face count warnings at 50K (FR-017), rejection at 100K (FR-018)
- Property reporting: volume (mm³), surface area (mm²), vertex/face counts (FR-016)

**Evidence**: Investigation 003 section "Stage 3: 3D Mesh Validation (trimesh)" demonstrates watertight and manifold detection with 100% accuracy on test dataset.

---

## Decision 4: Mesh Repair - Manifold3D

**Decision**: Use Manifold3D library for automatic mesh repair when validation fails

**Rationale**:
- Industry-leading mesh repair algorithms (handles complex non-manifold geometry)
- Guarantees watertight output when repair succeeds (critical for FR-013/FR-014)
- Fast performance (<5 seconds for typical repairs per investigation 003)
- Python bindings via `manifold3d` package
- Used in production 3D printing pipelines (proven reliability)

**Alternatives Considered**:
1. **PyMeshLab** - Rejected: Heavier dependency, slower repair operations
2. **trimesh.repair** - Rejected: Basic repair only, cannot handle complex cases
3. **Blender mesh repair** - Rejected: Requires Blender installation, subprocess calls
4. **Manual repair** - Rejected: Not automatable, defeats purpose of pipeline

**Implementation Notes**:
- Triggered when `is_watertight` or `is_volume` validation fails (FR-019)
- Success/failure reporting with before/after status (FR-020)
- Clear rejection with error details when repair fails (FR-021)
- Investigation 004 reports 80% repair success rate (meets SC-007)

**Evidence**: Investigation 003 section "Stage 3: 3D Mesh Validation" demonstrates automatic repair recovering 8/10 initially non-watertight meshes.

---

## Decision 5: G-code Generation - PrusaSlicer CLI

**Decision**: Use PrusaSlicer command-line interface for 3D model → G-code slicing

**Rationale**:
- Supports Bambu Lab printer profiles out-of-box (FR-023)
- Robust CLI with batch processing support (no GUI required)
- Configurable material profiles (PLA FR-024, PETG FR-025)
- Generates accurate print time and material estimates (FR-028)
- Free, open-source, and actively maintained
- Already familiar to target users (LeSign operators)

**Alternatives Considered**:
1. **Cura CLI** - Rejected: Less accurate Bambu Lab profiles, slower slicing
2. **Slic3r** - Rejected: Original project unmaintained, superseded by PrusaSlicer
3. **OrcaSlicer** - Considered: Better Bambu support but less stable CLI, may revisit post-POC
4. **Custom slicer** - Rejected: Extremely complex, out of scope for POC

**Implementation Notes**:
- Subprocess call via `subprocess.run(['prusa-slicer', '--export-gcode', ...])`
- Printer profile: `bambu_h2d_0.4_nozzle.ini` with 256×256×256mm build volume
- Material profiles: PLA (190-220°C nozzle, 60°C bed), PETG (220-250°C nozzle, 70°C bed)
- Layer height: 0.2mm standard (FR-026), 0.1mm high quality option
- Infill: 20% default for lightweight signs (FR-027), 100% for solid option
- G-code validation: non-empty file with temperature commands (FR-030)

**Evidence**: Investigation 003 section "Stage 4: 3D → G-code (PrusaSlicer)" demonstrates successful G-code generation with accurate estimates (±10% actual print time per SC-008).

---

## Decision 6: Quality Metrics - SSIM (scikit-image)

**Decision**: Use scikit-image library's SSIM implementation for structural similarity measurement

**Rationale**:
- Industry-standard structural similarity metric (Wang et al. 2004)
- Native multichannel support (RGB images, FR-002)
- Fast computation (<1 second for 1024×1024 images)
- Well-tested implementation in scikit-image ecosystem
- Threshold of 0.85 validated in investigation 004 as optimal for sign quality

**Alternatives Considered**:
1. **PyTorch SSIM** - Rejected: Adds heavy ML dependency for simple metric
2. **Custom SSIM** - Rejected: Risk of implementation bugs, no advantage over scikit-image
3. **MSE/PSNR** - Rejected: Poor correlation with perceptual quality per investigation 004

**Implementation Notes**:
- Compare original image to re-rasterized SVG (FR-002)
- Use `skimage.metrics.structural_similarity(channel_axis=2, data_range=255)`
- Acceptance threshold: SSIM ≥ 0.85 (FR-002)
- Retry threshold: 0.75 ≤ SSIM < 0.85 triggers parameter adjustment (FR-007)

**Evidence**: Investigation 004 section "Tier 1: Structural Similarity (SSIM)" demonstrates 95% success rate achieving ≥0.85 threshold on test dataset (meets SC-002).

---

## Decision 7: Quality Metrics - Edge IoU (OpenCV)

**Decision**: Use OpenCV for edge detection and intersection-over-union calculation

**Rationale**:
- Canny edge detection proven effective for text/shape boundaries
- Fast computation via optimized C++ backend
- IoU metric widely used in computer vision for spatial accuracy
- Threshold of 0.75 validated in investigation 004 as appropriate for edge preservation
- Lightweight dependency already used in many Python projects

**Alternatives Considered**:
1. **Sobel/Prewitt operators** - Rejected: Less accurate edge localization than Canny
2. **Learned edge detection** - Rejected: Adds ML dependency, overkill for POC
3. **Chamfer distance** - Rejected: More complex, similar results to IoU per investigation 004

**Implementation Notes**:
- Canny edge detection on original image and re-rasterized SVG/3D top-view
- IoU = intersection(edges_A, edges_B) / union(edges_A, edges_B)
- Vector quality threshold: IoU ≥ 0.75 (FR-003)
- 3D extrusion quality threshold: IoU ≥ 0.85 (FR-011)

**Evidence**: Investigation 004 section "Tier 1: Edge Preservation (IoU)" shows 0.75 threshold catches thin line loss while avoiding false positives.

---

## Decision 8: Quality Metrics - Color Fidelity (NumPy/SciPy)

**Decision**: Use histogram correlation for color fidelity measurement

**Rationale**:
- Simple, interpretable metric (correlation coefficient)
- Fast computation using NumPy/SciPy
- Threshold of 0.90 validated in investigation 004 for color accuracy
- Captures color distribution similarity without pixel-level alignment issues
- No additional dependencies (NumPy/SciPy already required)

**Alternatives Considered**:
1. **Color moment matching** - Rejected: Less intuitive than correlation, similar accuracy
2. **Earth Mover's Distance** - Rejected: Slower computation, marginal accuracy gain
3. **Perceptual color difference (ΔE)** - Considered for future enhancement (tier 2)

**Implementation Notes**:
- Extract RGB histograms from original and re-rasterized images
- Calculate Pearson correlation coefficient
- Acceptance threshold: correlation ≥ 0.90 (FR-006)
- Part of overall quality score (15% weight per FR-032)

**Evidence**: Investigation 004 section "Tier 1: Color Fidelity" demonstrates 0.90 threshold ensures visually acceptable color matching.

---

## Decision 9: Quality Metrics - Perceptual Similarity (LPIPS - Optional Tier 2)

**Decision**: Use LPIPS (Learned Perceptual Image Patch Similarity) as optional tier 2 metric

**Rationale**:
- State-of-the-art perceptual similarity metric (Zhang et al. 2018)
- Better correlation with human judgment than SSIM per investigation 004
- Threshold of <0.20 validated for high-quality conversions
- Optional dependency (tier 2) - can skip for POC

**Alternatives Considered**:
1. **FID (Frechet Inception Distance)** - Rejected: Designed for datasets, not single images
2. **Style loss (VGG)** - Rejected: Less standardized than LPIPS
3. **DISTS** - Rejected: Newer metric, less validated than LPIPS

**Implementation Notes**:
- `import lpips; loss_fn = lpips.LPIPS(net='alex')`
- Acceptance threshold: LPIPS < 0.20 (investigation 004)
- Part of overall quality score (20% weight per FR-032)
- Mark as optional for initial POC (can implement in P2)

**Evidence**: Investigation 004 section "Tier 2: Perceptual Similarity (LPIPS)" shows LPIPS catches visual artifacts SSIM misses.

---

## Decision 10: Test Fixtures - Synthetic Dataset Generation

**Decision**: Generate synthetic test images programmatically using Pillow for reproducible testing

**Rationale**:
- Controlled test cases with known properties (text, resolution, colors)
- Reproducible across environments (no external dataset dependencies)
- Covers edge cases systematically (thin lines, aspect ratios, complexity)
- Enables golden file baselines for regression testing (FR-038)
- Fast generation (<1 second per image)

**Alternatives Considered**:
1. **Real AI-generated images** - Rejected: Non-deterministic, hard to reproduce failures
2. **Open dataset (e.g., COCO)** - Rejected: Not specific to name signs, licensing issues
3. **Manual fixtures** - Rejected: Time-consuming, incomplete edge case coverage

**Implementation Notes**:
- Generate images with parametrized properties: text content, resolution (512×512 to 2048×2048), color count (1-8), line thickness (1-10px)
- Test cases per FR-042: low resolution, high resolution, extreme aspect ratios (10:1), thin lines (<2px), complex paths (>500), empty/malformed
- Golden file baselines stored in `tests/fixtures/golden/` (FR-038)
- Regression detection with 5% tolerance (FR-039)

**Evidence**: Investigation 004 section "Test Dataset Generation" demonstrates synthetic fixtures achieve >90% edge case coverage (meets SC-011).

---

## Decision 11: Data Validation - Pydantic

**Decision**: Use Pydantic v2 for data modeling and validation

**Rationale**:
- Type-safe data models with runtime validation
- Clear contracts for all entities (ConversionJob, QualityMetrics, etc.)
- JSON schema generation for API documentation
- Fast validation via Rust backend (Pydantic v2)
- Widely used in Python ecosystem (FastAPI, etc.)

**Alternatives Considered**:
1. **dataclasses** - Rejected: No runtime validation, manual schema generation
2. **attrs** - Rejected: Less feature-rich than Pydantic, smaller ecosystem
3. **marshmallow** - Rejected: Separate schemas/models, more boilerplate

**Implementation Notes**:
- Define models for 9 key entities from spec.md
- Validation errors provide clear user feedback (FR-048)
- Models shared across components via `backend/shared/models.py`

**Evidence**: Aligns with CODE_GUIDELINES.md Python best practices and modular architecture principle.

---

## Decision 12: Testing Framework - pytest

**Decision**: Use pytest with fixtures and parametrized tests for comprehensive test coverage

**Rationale**:
- Industry-standard Python testing framework
- Powerful fixture system for test dataset management
- Parametrized tests reduce duplication (FR-042)
- Coverage plugin for >90% target (SC-011)
- Excellent error reporting and debugging support

**Alternatives Considered**:
1. **unittest** - Rejected: More boilerplate, less expressive than pytest
2. **nose2** - Rejected: Less active development than pytest

**Implementation Notes**:
- Test layers: unit, integration, contract, end-to-end (per constitution TDD principle)
- Fixtures in `tests/fixtures/` for golden files and synthetic datasets
- Coverage target: >90% (SC-011)
- Performance benchmarking via pytest-benchmark plugin (FR-040)

**Evidence**: Investigation 004 section "Automated Testing Strategy" demonstrates pytest achieving >90% coverage with parametrized edge case tests.

---

## Decision Summary

| Decision Area | Technology | Status | Priority |
|--------------|------------|--------|----------|
| Image Vectorization | VTracer | ✅ Finalized | P1 |
| Vector → 3D | Build123d | ✅ Finalized | P1 |
| Mesh Validation | trimesh | ✅ Finalized | P1 |
| Mesh Repair | Manifold3D | ✅ Finalized | P1 |
| G-code Generation | PrusaSlicer CLI | ✅ Finalized | P2 |
| SSIM Metric | scikit-image | ✅ Finalized | P1 |
| Edge IoU | OpenCV | ✅ Finalized | P1 |
| Color Fidelity | NumPy/SciPy | ✅ Finalized | P1 |
| Perceptual Similarity | LPIPS | 🔄 Optional (Tier 2) | P3 |
| Test Fixtures | Pillow (synthetic) | ✅ Finalized | P1 |
| Data Validation | Pydantic v2 | ✅ Finalized | P1 |
| Testing Framework | pytest | ✅ Finalized | P1 |

## Next Steps

1. ✅ Technology decisions complete - no NEEDS CLARIFICATION markers remain
2. ➡️ Proceed to Phase 1: Define data models using Pydantic (data-model.md)
3. ➡️ Generate API contracts for conversion, validation, and file formats (contracts/)
4. ➡️ Create developer quickstart guide (quickstart.md)
