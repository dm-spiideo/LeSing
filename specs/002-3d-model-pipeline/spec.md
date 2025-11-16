# Feature Specification: 3D Model Pipeline

**Feature Branch**: `002-3d-model-pipeline`
**Created**: 2025-11-16
**Status**: Draft
**Target Printer**: Bambu Lab H2D
**Dependencies**: AI Image Generation (Feature 001)

## Overview

The 3D Model Pipeline transforms AI-generated 2D name sign images into printable 3D models and printer-ready G-code files. The system validates quality at each transformation stage to ensure physical printability and visual fidelity to the original design.

## User Scenarios & Testing

### User Story 1 - Basic Image-to-3D Conversion (Priority: P1)

As a LeSign operator, when I have an approved AI-generated name sign image, I can transform it into a printable 3D model file that accurately represents the design and is guaranteed to be physically printable.

**Why this priority**: Core MVP functionality - without this, no signs can be manufactured. Every sign must go through this conversion.

**Independent Test**: Can be fully tested by providing a known good AI-generated image, running the conversion, and verifying the output is a valid, printable 3D model that passes all quality checks.

**Acceptance Scenarios**:

1. **Given** an AI-generated name sign image (PNG/JPEG), **When** I submit it to the conversion pipeline, **Then** I receive a valid 3D model file (3MF format) that is watertight, manifold, and fits within printer build volume (256×256×256mm)

2. **Given** a vectorized image (SVG) with 8 colors, **When** the system performs 3D extrusion, **Then** the resulting model maintains at least 85% edge preservation accuracy compared to the original vector

3. **Given** a completed 3D model, **When** quality validation runs, **Then** the system confirms the model is watertight (no holes), manifold (valid solid), and has positive volume

4. **Given** a 3D model that passes all validation checks, **When** I request the model file, **Then** I receive a 3MF file under 10MB that opens successfully in standard 3D software

---

### User Story 2 - Automated Quality Validation (Priority: P1)

As a LeSign operator, the system automatically validates quality at each conversion stage and provides clear feedback about what passed or failed, so I can quickly identify and address issues without manual inspection.

**Why this priority**: Essential for production reliability - manual quality checking is time-consuming and error-prone. Automated validation ensures consistent quality and reduces waste.

**Independent Test**: Can be tested by feeding known good and bad inputs through the pipeline and verifying the system correctly identifies quality issues with actionable error messages.

**Acceptance Scenarios**:

1. **Given** an image is vectorized, **When** quality metrics are calculated, **Then** I receive scores for SSIM (≥0.85), edge accuracy (≥0.75), and color fidelity (≥0.90) with clear pass/fail status

2. **Given** a 3D model fails watertight validation, **When** automatic repair is attempted, **Then** the system either fixes the mesh and reports success, or provides a clear error explaining why repair failed

3. **Given** a model exceeds printer build volume (256×256×256mm), **When** validation runs, **Then** the system rejects the model immediately with specific dimension measurements and required maximum

4. **Given** vectorization produces low quality (SSIM < 0.75), **When** validation detects this, **Then** the system automatically retries with adjusted parameters before failing

---

### User Story 3 - G-code Generation for Bambu Lab H2D (Priority: P2)

As a LeSign operator, when I have a validated 3D model, I can generate printer-ready G-code optimized for the Bambu Lab H2D printer with appropriate material settings (PLA/PETG) and print estimates.

**Why this priority**: Required for actual printing but can be tested later once 3D models are reliably produced. Initial MVP can use manual slicing.

**Independent Test**: Can be tested by providing a known good 3D model, generating G-code, and verifying it contains correct printer commands and produces reasonable time/material estimates.

**Acceptance Scenarios**:

1. **Given** a valid 3D model file (3MF), **When** I request G-code generation with PLA material profile, **Then** I receive a G-code file with appropriate temperature settings (190-220°C nozzle, 60°C bed) and infill (20% for lightweight signs)

2. **Given** G-code generation completes, **When** I review the metadata, **Then** I see estimated print time, filament usage (grams), layer count, and estimated cost

3. **Given** a generated G-code file, **When** I load it in printer preview software, **Then** the visualization shows no errors and the model is correctly positioned on the build plate

4. **Given** a complex sign requiring supports, **When** G-code is generated, **Then** support structures are automatically included and removable without damaging the sign

---

### User Story 4 - Visual Subjective Quality Testing (Priority: P3)

As a LeSign operator or quality reviewer, I can visually compare the original image, vector, and 3D model renderings side-by-side to subjectively assess quality beyond automated metrics.

**Why this priority**: Important for quality assurance but not blocking - automated metrics provide baseline quality. Visual review catches aesthetic issues metrics might miss.

**Independent Test**: Can be tested by generating comparison visualizations for known test cases and verifying they display correctly and aid in quality assessment.

**Acceptance Scenarios**:

1. **Given** a conversion has completed all stages, **When** I request a quality comparison view, **Then** I see the original image, re-rasterized SVG, and top-view rendering of the 3D model arranged side-by-side at matching scales

2. **Given** automated quality metrics indicate marginal scores (0.75-0.85), **When** I review the visual comparison, **Then** I can make an informed decision whether to accept or regenerate based on visual assessment

3. **Given** multiple test images in a test suite, **When** I run batch visual comparison, **Then** I receive an HTML report with all comparisons, metrics overlays, and pass/fail indicators

4. **Given** a visual comparison for a specific sign, **When** I export the comparison, **Then** I receive a PDF report suitable for archiving or customer approval

---

### Edge Cases

- **Very thin text/lines (< 2px width)**: What happens when original image has features below printable resolution? System should warn if features may disappear or merge during vectorization.

- **Extreme aspect ratios (> 10:1)**: How does system handle very elongated signs? Should validate they still fit build volume after extrusion.

- **Color gradients in source image**: What happens when AI generates smooth gradients instead of distinct colors? Vectorization should quantize to 8 colors maximum, may lose gradient smoothness.

- **Mesh repair failures**: When Manifold3D cannot repair non-watertight mesh, how does system respond? Should reject and recommend regenerating with different AI parameters.

- **Build volume edge cases**: What if sign dimensions are exactly at limits (256×256×256mm)? System should apply small safety margin (e.g., 254×254×254mm maximum).

- **File corruption during conversion**: How does system detect and handle corrupted intermediate files (SVG, 3MF)? Should validate file integrity at each stage.

- **Non-manifold geometry that cannot be fixed**: When complex overlapping shapes create unfixable topology, system should provide specific feedback about which regions are problematic.

- **Extremely high poly count (> 100K faces)**: What happens when vectorization produces overly complex SVG? System should simplify or reject before 3D conversion to avoid performance issues.

- **Zero volume meshes**: When extrusion produces invalid geometry with no interior volume, system should fail fast with clear error rather than proceeding to slicing.

- **Missing printer profile**: What if Bambu Lab H2D configuration is not found during G-code generation? System should fail with clear error listing available profiles.

## Requirements

### Functional Requirements - Image to Vector Conversion

- **FR-001**: System MUST convert PNG/JPEG input images to SVG vector format using color quantization to maximum 8 distinct colors

- **FR-002**: System MUST measure structural similarity (SSIM) between original image and re-rasterized vector, requiring minimum score of 0.85 for acceptance

- **FR-003**: System MUST measure edge preservation accuracy using edge detection comparison, requiring minimum 0.75 IoU score

- **FR-004**: System MUST validate SVG file structure is well-formed XML with valid root element, viewBox or dimensions, and contains at least one shape/path

- **FR-005**: System MUST limit SVG file size to maximum 5MB and path count to maximum 1000 for performance

- **FR-006**: System MUST measure color fidelity using histogram correlation requiring minimum 0.90 correlation score

- **FR-007**: System MUST automatically retry vectorization with adjusted parameters when initial quality scores fall between 0.75-0.84

### Functional Requirements - Vector to 3D Conversion

- **FR-008**: System MUST import SVG files and extrude to 3D models with configurable depth between 2-10mm (default 5mm)

- **FR-009**: System MUST export 3D models in 3MF format with metadata including source SVG reference and extrusion parameters

- **FR-010**: System MUST validate extrusion depth accuracy within 5% of target depth (e.g., 5mm ± 0.25mm)

- **FR-011**: System MUST measure edge preservation between SVG and 3D model top-view rendering requiring minimum 0.85 IoU

- **FR-012**: System MUST detect and report when SVG import fails to produce valid geometry (zero faces)

### Functional Requirements - 3D Mesh Validation

- **FR-013**: System MUST validate all 3D meshes are watertight (no holes or gaps) - this is NON-NEGOTIABLE for printability

- **FR-014**: System MUST validate all 3D meshes are manifold (valid solid volume) - this is NON-NEGOTIABLE for printability

- **FR-015**: System MUST validate all 3D meshes fit within printer build volume of 256×256×256mm - this is NON-NEGOTIABLE

- **FR-016**: System MUST calculate and report mesh properties including volume (mm³), surface area (mm²), vertex count, and face count

- **FR-017**: System MUST warn when face count exceeds 50,000 faces due to potential slicing performance impact

- **FR-018**: System MUST reject meshes when face count exceeds 100,000 faces

- **FR-019**: System MUST attempt automatic mesh repair when watertight or manifold validation fails

- **FR-020**: System MUST validate repaired meshes and report success/failure of repair attempt with before/after status

- **FR-021**: System MUST reject meshes that fail repair with specific error describing the issue

### Functional Requirements - G-code Generation

- **FR-022**: System MUST generate G-code from valid 3MF files using printer-specific configuration profiles

- **FR-023**: System MUST support Bambu Lab H2D printer profile with build volume 256×256×256mm and 0.4mm nozzle

- **FR-024**: System MUST support PLA material profile with nozzle temperature 190-220°C and bed temperature 60°C

- **FR-025**: System MUST support PETG material profile with nozzle temperature 220-250°C and bed temperature 70°C

- **FR-026**: System MUST generate G-code with configurable layer height (0.2mm standard, 0.1mm high quality)

- **FR-027**: System MUST generate G-code with configurable infill percentage (20% for lightweight, 100% for solid)

- **FR-028**: System MUST calculate and report estimated print time (minutes), filament usage (grams), layer count, and cost

- **FR-029**: System MUST generate G-code that includes appropriate supports when model geometry requires them

- **FR-030**: System MUST validate generated G-code file is non-empty and contains expected structure

### Functional Requirements - Quality Reporting & Metrics

- **FR-031**: System MUST generate quality report for each conversion including all metric scores, pass/fail status, and any warnings/errors

- **FR-032**: System MUST calculate overall quality score as weighted combination of SSIM (25%), perceptual similarity (20%), edge IoU (20%), color correlation (15%), coverage (10%), color quantization (10%)

- **FR-033**: System MUST pass conversions only when overall quality score ≥ 0.85

- **FR-034**: System MUST provide visual comparison output showing original image, re-rasterized SVG, and 3D model top-view rendering side-by-side

- **FR-035**: System MUST generate HTML quality report with all metrics, visualizations, and pass/fail indicators for batch testing

- **FR-036**: System MUST log all conversion stages with timestamps, file sizes, and performance metrics for monitoring

### Functional Requirements - Testing & Fixtures

- **FR-037**: System MUST provide test image generation capability creating synthetic name signs with known characteristics (text, resolution, color count)

- **FR-038**: System MUST maintain golden file baselines for regression testing including reference SVG files and expected metric scores

- **FR-039**: System MUST detect quality regressions by comparing current outputs to baseline with 5% tolerance threshold

- **FR-040**: System MUST provide performance benchmarking capability measuring time for each pipeline stage

- **FR-041**: System MUST enforce performance SLA requiring total pipeline completion under 60 seconds for standard inputs

- **FR-042**: System MUST provide parametrized test suite covering edge cases including low resolution, high resolution, extreme aspect ratios, thin lines, complex paths, and empty/malformed inputs

### Functional Requirements - Error Handling

- **FR-043**: System MUST detect and reject corrupted input images with clear error message describing the issue

- **FR-044**: System MUST detect and handle empty SVG files (no paths) with clear error indicating geometry is required

- **FR-045**: System MUST detect and handle malformed SVG XML with parsing error details

- **FR-046**: System MUST timeout vectorization operations exceeding 2 minutes and timeout slicing operations exceeding 5 minutes

- **FR-047**: System MUST provide retry logic with exponential backoff for transient failures (max 3 retries)

- **FR-048**: System MUST provide clear error messages distinguishing between user-fixable issues and system issues

### Key Entities

- **ConversionJob**: Represents a single image-to-G-code conversion with stages (vectorization, 3D conversion, validation, slicing), current status, quality metrics, output file paths, timestamps, and error messages

- **QualityMetrics**: Aggregates all quality measurements including SSIM score, perceptual similarity score, edge IoU, color correlation, coverage ratio, overall score, and pass/fail status

- **VectorFile**: SVG file with metadata including path count, color count, file size, viewBox dimensions, and validation status

- **MeshFile**: 3D model file (3MF) with metadata including watertight status, manifold status, volume, surface area, face count, extrusion depth, build volume fit, and printability status

- **GCodeFile**: Printer-ready G-code with metadata including target printer, material profile, estimated print time, filament usage, layer count, and generation timestamp

- **ValidationReport**: Quality assessment results for each pipeline stage with metric scores, warnings, errors, and visual comparisons

- **PrinterProfile**: Printer-specific configuration including build volume, nozzle diameter, supported materials, temperature ranges, and default settings

- **MaterialProfile**: Material-specific settings including temperature ranges, bed temperature, print speeds, retraction settings, and cooling requirements

- **TestFixture**: Synthetic test image with known properties (text content, resolution, color count, expected complexity) used for automated testing and regression detection

## Success Criteria

### Measurable Outcomes

- **SC-001**: System can convert AI-generated name sign images to valid 3D models with 100% watertight guarantee (no failed prints due to mesh issues)

- **SC-002**: 95% of conversions achieve quality score ≥ 0.85 without requiring retry or manual intervention

- **SC-003**: Total conversion time from image to G-code remains under 60 seconds for 90% of inputs (under 30 seconds target)

- **SC-004**: Visual fidelity between original image and 3D model achieves minimum 85% structural similarity (SSIM ≥ 0.85)

- **SC-005**: Edge preservation accuracy between original and 3D model achieves minimum 75% intersection-over-union (IoU ≥ 0.75)

- **SC-006**: Automated quality validation catches 100% of unprintable meshes before G-code generation (zero failed prints due to missed validation)

- **SC-007**: Mesh repair successfully fixes 80% of initially non-watertight meshes using automatic repair

- **SC-008**: G-code generation produces accurate time/material estimates within 10% of actual print time and filament usage

- **SC-009**: System processes batch conversions of 100 images with less than 5% failure rate requiring human intervention

- **SC-010**: Visual quality reports enable operators to assess quality within 10 seconds per sign without detailed metric analysis

- **SC-011**: Test suite with fixtures and edge cases achieves >90% code coverage and catches regressions before production deployment

- **SC-012**: Performance benchmarks detect degradation when any pipeline stage exceeds SLA by more than 20%

## Assumptions

- AI-generated images are pre-validated and meet minimum quality standards (resolution ≥ 512×512, clear text/shapes)
- Bambu Lab H2D printer profile is accurate and tested with actual hardware
- Slicing software is installed and accessible on the system running the pipeline
- Sufficient disk space (minimum 2GB) available for storing intermediate files (SVG, 3MF, G-code)
- Network access not required for core pipeline (all processing local)
- Runtime environment with required libraries installed
- File-based communication between pipeline stages is acceptable (no streaming processing initially)
- Default extrusion depth of 5mm produces physically printable signs that meet quality expectations
- 8-color quantization provides sufficient detail for typical name sign designs
- Standard 0.2mm layer height and 20% infill are acceptable for initial POC
- Operators have basic familiarity with 3D printing concepts (watertight, manifold, G-code)

## Out of Scope

The following are explicitly excluded from this feature:

- Multi-color 3D printing support (single material per print)
- Custom font rendering or text editing capabilities
- Real-time preview or interactive editing of 3D models
- Automatic scaling or orientation optimization for build plate
- Advanced slicing optimizations (tree supports, variable layer height, ironing)
- Integration with printer control systems (sending G-code to printer)
- Material inventory tracking or cost estimation beyond basic filament usage
- Post-processing instructions (support removal, sanding, painting)
- Alternative 3D printer support beyond Bambu Lab H2D
- Cloud-based processing or distributed pipeline execution
- User authentication or access control for conversion jobs
- Database persistence of conversion history (file-based storage only for MVP)
