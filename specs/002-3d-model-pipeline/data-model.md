# Data Models: 3D Model Pipeline

**Feature**: 002-3d-model-pipeline
**Created**: 2025-11-16
**Status**: Design Complete
**Implementation**: Pydantic v2 models

## Overview

This document defines the data models for the 3D Model Pipeline using Pydantic v2 schemas. All models provide runtime validation, type safety, and JSON serialization for file-based communication between pipeline stages.

## Core Entities

### 1. ConversionJob

Represents a complete image-to-G-code conversion with all pipeline stages.

```python
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Optional
from pydantic import BaseModel, Field, ConfigDict

class ConversionStage(str, Enum):
    """Pipeline stages for conversion tracking."""
    SUBMITTED = "submitted"
    VECTORIZING = "vectorizing"
    VECTOR_VALIDATION = "vector_validation"
    EXTRUDING = "extruding"
    MESH_VALIDATION = "mesh_validation"
    MESH_REPAIR = "mesh_repair"
    SLICING = "slicing"
    COMPLETED = "completed"
    FAILED = "failed"

class ConversionJob(BaseModel):
    """
    Tracks a single image-to-G-code conversion through all pipeline stages.

    Satisfies spec requirements:
    - FR-036: Logging with timestamps and file sizes
    - FR-031: Quality report generation
    - FR-048: Clear error messages
    """
    model_config = ConfigDict(frozen=False)

    job_id: str = Field(..., description="Unique identifier for this conversion")

    # Input
    input_image_path: Path = Field(..., description="Path to source PNG/JPEG image")
    input_image_size_bytes: int = Field(..., gt=0, description="Input file size in bytes")

    # Pipeline stage tracking
    current_stage: ConversionStage = Field(default=ConversionStage.SUBMITTED)
    stage_timestamps: dict[ConversionStage, datetime] = Field(default_factory=dict)

    # Output file paths
    svg_path: Optional[Path] = None
    mesh_3mf_path: Optional[Path] = None
    gcode_path: Optional[Path] = None

    # Quality metrics (populated as stages complete)
    quality_metrics: Optional["QualityMetrics"] = None
    mesh_properties: Optional["MeshProperties"] = None
    gcode_metadata: Optional["GCodeMetadata"] = None

    # Error handling
    error_message: Optional[str] = None
    retry_count: int = Field(default=0, ge=0, le=3)

    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = None

    def mark_stage_complete(self, stage: ConversionStage) -> None:
        """Update current stage and record timestamp."""
        self.current_stage = stage
        self.stage_timestamps[stage] = datetime.utcnow()

    def total_processing_time_seconds(self) -> Optional[float]:
        """Calculate total time from submission to completion."""
        if self.completed_at is None:
            return None
        return (self.completed_at - self.created_at).total_seconds()
```

---

### 2. QualityMetrics

Aggregates all quality measurements for vectorization validation (FR-031, FR-032).

```python
from pydantic import BaseModel, Field, field_validator

class QualityMetrics(BaseModel):
    """
    Quality assessment results for image→vector conversion.

    Satisfies spec requirements:
    - FR-002: SSIM ≥ 0.85
    - FR-003: Edge IoU ≥ 0.75
    - FR-006: Color correlation ≥ 0.90
    - FR-032: Overall quality score calculation
    - FR-033: Pass only when overall ≥ 0.85
    """
    model_config = ConfigDict(frozen=True)

    # Tier 1 metrics (required)
    ssim_score: float = Field(..., ge=0.0, le=1.0, description="Structural similarity (FR-002)")
    edge_iou: float = Field(..., ge=0.0, le=1.0, description="Edge preservation IoU (FR-003)")
    color_correlation: float = Field(..., ge=-1.0, le=1.0, description="Histogram correlation (FR-006)")
    coverage_ratio: float = Field(..., ge=0.0, le=1.0, description="Non-background pixel ratio")
    color_quantization_error: float = Field(..., ge=0.0, le=1.0, description="Color palette accuracy")

    # Tier 2 metrics (optional)
    lpips_score: Optional[float] = Field(None, ge=0.0, le=1.0, description="Perceptual similarity (optional)")

    # Overall assessment
    overall_score: float = Field(..., ge=0.0, le=1.0, description="Weighted combination (FR-032)")
    passed: bool = Field(..., description="True if overall_score ≥ 0.85 (FR-033)")

    # Thresholds for individual metrics
    ssim_passed: bool = Field(..., description="True if SSIM ≥ 0.85")
    edge_iou_passed: bool = Field(..., description="True if IoU ≥ 0.75")
    color_passed: bool = Field(..., description="True if correlation ≥ 0.90")

    @field_validator("overall_score")
    @classmethod
    def calculate_overall_score(cls, v: float, info) -> float:
        """
        Calculate weighted overall score per FR-032:
        - SSIM: 25%
        - Perceptual similarity (LPIPS): 20%
        - Edge IoU: 20%
        - Color correlation: 15%
        - Coverage: 10%
        - Color quantization: 10%
        """
        values = info.data
        score = (
            0.25 * values.get("ssim_score", 0.0) +
            0.20 * (1.0 - values.get("lpips_score", 0.2)) +  # LPIPS lower is better
            0.20 * values.get("edge_iou", 0.0) +
            0.15 * values.get("color_correlation", 0.0) +
            0.10 * values.get("coverage_ratio", 0.0) +
            0.10 * (1.0 - values.get("color_quantization_error", 0.1))
        )
        return round(score, 3)

    @classmethod
    def from_raw_metrics(
        cls,
        ssim: float,
        edge_iou: float,
        color_corr: float,
        coverage: float,
        color_quant_err: float,
        lpips: Optional[float] = None
    ) -> "QualityMetrics":
        """Factory method to create validated metrics."""
        overall = (
            0.25 * ssim +
            0.20 * (1.0 - (lpips or 0.2)) +
            0.20 * edge_iou +
            0.15 * color_corr +
            0.10 * coverage +
            0.10 * (1.0 - color_quant_err)
        )

        return cls(
            ssim_score=ssim,
            edge_iou=edge_iou,
            color_correlation=color_corr,
            coverage_ratio=coverage,
            color_quantization_error=color_quant_err,
            lpips_score=lpips,
            overall_score=overall,
            passed=overall >= 0.85,
            ssim_passed=ssim >= 0.85,
            edge_iou_passed=edge_iou >= 0.75,
            color_passed=color_corr >= 0.90
        )
```

---

### 3. VectorFile

SVG file metadata with validation status (FR-004, FR-005).

```python
from pydantic import BaseModel, Field

class VectorFile(BaseModel):
    """
    Metadata for vectorized SVG files.

    Satisfies spec requirements:
    - FR-004: SVG structure validation
    - FR-005: File size ≤ 5MB, path count ≤ 1000
    """
    model_config = ConfigDict(frozen=True)

    file_path: Path = Field(..., description="Path to SVG file")
    file_size_bytes: int = Field(..., gt=0, le=5_242_880, description="File size (≤5MB per FR-005)")

    # SVG structure validation (FR-004)
    is_valid_xml: bool = Field(..., description="Well-formed XML")
    has_root_element: bool = Field(..., description="Valid SVG root element")
    has_viewbox: bool = Field(..., description="viewBox or width/height defined")
    has_geometry: bool = Field(..., description="At least one shape/path present")

    # Complexity metrics (FR-005)
    path_count: int = Field(..., ge=1, le=1000, description="Number of paths (≤1000 per FR-005)")
    color_count: int = Field(..., ge=1, le=8, description="Distinct colors (≤8 per FR-001)")

    # Dimensions
    viewbox_width: float = Field(..., gt=0, description="SVG viewBox width")
    viewbox_height: float = Field(..., gt=0, description="SVG viewBox height")
    aspect_ratio: float = Field(..., gt=0, description="Width/height ratio")

    # Overall validation
    is_valid: bool = Field(..., description="All validation checks passed")

    @field_validator("is_valid")
    @classmethod
    def validate_overall(cls, v: bool, info) -> bool:
        """Overall validation requires all structure checks to pass."""
        values = info.data
        return (
            values.get("is_valid_xml", False) and
            values.get("has_root_element", False) and
            values.get("has_viewbox", False) and
            values.get("has_geometry", False)
        )
```

---

### 4. MeshFile

3D model metadata with printability validation (FR-013 through FR-021).

```python
from pydantic import BaseModel, Field

class MeshProperties(BaseModel):
    """
    Geometric properties of 3D mesh (FR-016).
    """
    model_config = ConfigDict(frozen=True)

    volume_mm3: float = Field(..., gt=0, description="Mesh volume in cubic millimeters")
    surface_area_mm2: float = Field(..., gt=0, description="Surface area in square millimeters")
    vertex_count: int = Field(..., gt=0, description="Number of vertices")
    face_count: int = Field(..., gt=0, description="Number of triangular faces")

    # Bounding box
    bbox_min: tuple[float, float, float] = Field(..., description="Minimum corner (x, y, z)")
    bbox_max: tuple[float, float, float] = Field(..., description="Maximum corner (x, y, z)")

    # Derived properties
    bbox_dimensions_mm: tuple[float, float, float] = Field(..., description="Bounding box dimensions")

    def fits_build_volume(self, max_x: float = 256, max_y: float = 256, max_z: float = 256) -> bool:
        """Check if mesh fits within printer build volume (FR-015)."""
        dims = self.bbox_dimensions_mm
        return dims[0] <= max_x and dims[1] <= max_y and dims[2] <= max_z


class MeshFile(BaseModel):
    """
    3D mesh file with printability validation.

    Satisfies spec requirements:
    - FR-013: Watertight validation (NON-NEGOTIABLE)
    - FR-014: Manifold validation (NON-NEGOTIABLE)
    - FR-015: Build volume validation (NON-NEGOTIABLE)
    - FR-016: Mesh properties calculation
    - FR-017: Warning at 50K faces
    - FR-018: Rejection at 100K faces
    - FR-019: Automatic repair attempt
    - FR-020: Repair success reporting
    """
    model_config = ConfigDict(frozen=True)

    file_path: Path = Field(..., description="Path to 3MF file")
    file_size_bytes: int = Field(..., gt=0, le=10_485_760, description="File size (≤10MB)")

    # Critical printability checks (NON-NEGOTIABLE)
    is_watertight: bool = Field(..., description="No holes/gaps (FR-013)")
    is_manifold: bool = Field(..., description="Valid solid volume (FR-014)")
    fits_build_volume: bool = Field(..., description="Within 256×256×256mm (FR-015)")

    # Mesh properties
    properties: MeshProperties = Field(..., description="Geometric properties (FR-016)")

    # Extrusion metadata
    extrusion_depth_mm: float = Field(..., ge=2.0, le=10.0, description="Configured depth (FR-008)")
    actual_depth_mm: float = Field(..., gt=0, description="Measured depth from mesh")
    depth_accuracy_pct: float = Field(..., description="Accuracy within ±5% (FR-010)")

    # Quality checks
    face_count_warning: bool = Field(..., description="True if faces > 50K (FR-017)")
    face_count_reject: bool = Field(..., description="True if faces > 100K (FR-018)")

    # Repair tracking (FR-019, FR-020)
    repair_attempted: bool = Field(default=False, description="Whether repair was attempted")
    repair_succeeded: bool = Field(default=False, description="Repair success status")
    repair_details: Optional[str] = None

    # Overall printability (FR-013, FR-014, FR-015)
    is_printable: bool = Field(..., description="All critical checks passed")

    @field_validator("is_printable")
    @classmethod
    def validate_printability(cls, v: bool, info) -> bool:
        """Printable requires watertight AND manifold AND fits build volume."""
        values = info.data
        return (
            values.get("is_watertight", False) and
            values.get("is_manifold", False) and
            values.get("fits_build_volume", False) and
            not values.get("face_count_reject", True)
        )

    @field_validator("depth_accuracy_pct")
    @classmethod
    def calculate_depth_accuracy(cls, v: float, info) -> float:
        """Calculate depth accuracy percentage (FR-010)."""
        values = info.data
        target = values.get("extrusion_depth_mm", 5.0)
        actual = values.get("actual_depth_mm", 0.0)
        if target == 0:
            return 0.0
        error_pct = abs(actual - target) / target * 100
        return round(100 - error_pct, 2)
```

---

### 5. GCodeFile

G-code file with print estimates (FR-022 through FR-030).

```python
from pydantic import BaseModel, Field

class GCodeMetadata(BaseModel):
    """
    Print estimates and metadata from G-code generation (FR-028).
    """
    model_config = ConfigDict(frozen=True)

    estimated_print_time_minutes: int = Field(..., gt=0, description="Estimated print duration")
    filament_usage_grams: float = Field(..., gt=0, description="Filament weight")
    layer_count: int = Field(..., gt=0, description="Number of layers")
    estimated_cost_usd: float = Field(..., ge=0, description="Material cost estimate")

    # Print settings
    layer_height_mm: float = Field(..., gt=0, description="Layer height (FR-026)")
    infill_percent: int = Field(..., ge=0, le=100, description="Infill density (FR-027)")
    has_supports: bool = Field(..., description="Support structures included (FR-029)")


class GCodeFile(BaseModel):
    """
    Printer-ready G-code with metadata.

    Satisfies spec requirements:
    - FR-022: G-code generation from 3MF
    - FR-023: Bambu Lab H2D profile
    - FR-024: PLA material profile
    - FR-025: PETG material profile
    - FR-026: Configurable layer height
    - FR-027: Configurable infill
    - FR-028: Print estimates
    - FR-029: Support generation
    - FR-030: G-code validation
    """
    model_config = ConfigDict(frozen=True)

    file_path: Path = Field(..., description="Path to G-code file")
    file_size_bytes: int = Field(..., gt=0, description="File size in bytes")

    # Printer and material profiles
    printer_profile: str = Field(..., description="Bambu Lab H2D (FR-023)")
    material_profile: str = Field(..., description="PLA or PETG (FR-024, FR-025)")

    # Temperature settings
    nozzle_temp_celsius: int = Field(..., ge=190, le=250, description="Nozzle temperature")
    bed_temp_celsius: int = Field(..., ge=60, le=70, description="Bed temperature")

    # Print metadata
    metadata: GCodeMetadata = Field(..., description="Print estimates (FR-028)")

    # Validation (FR-030)
    is_valid: bool = Field(..., description="Non-empty with expected structure")
    has_temperature_commands: bool = Field(..., description="Contains M104/M140 commands")

    # Timestamps
    generated_at: datetime = Field(default_factory=datetime.utcnow)

    @field_validator("is_valid")
    @classmethod
    def validate_gcode(cls, v: bool, info) -> bool:
        """Valid G-code must be non-empty and contain temperature commands."""
        values = info.data
        return (
            values.get("file_size_bytes", 0) > 0 and
            values.get("has_temperature_commands", False)
        )
```

---

### 6. ValidationReport

Comprehensive quality assessment results (FR-031, FR-034, FR-035).

```python
from pydantic import BaseModel, Field
from typing import Optional

class ValidationReport(BaseModel):
    """
    Quality assessment results for each pipeline stage.

    Satisfies spec requirements:
    - FR-031: Quality report generation
    - FR-034: Visual comparison output
    - FR-035: HTML quality report
    """
    model_config = ConfigDict(frozen=False)

    job_id: str = Field(..., description="Associated conversion job ID")

    # Vectorization stage
    vectorization_metrics: Optional[QualityMetrics] = None
    vectorization_passed: bool = False
    vectorization_warnings: list[str] = Field(default_factory=list)
    vectorization_errors: list[str] = Field(default_factory=list)

    # 3D conversion stage
    extrusion_passed: bool = False
    extrusion_edge_iou: Optional[float] = None
    extrusion_warnings: list[str] = Field(default_factory=list)
    extrusion_errors: list[str] = Field(default_factory=list)

    # Mesh validation stage
    mesh_validation_passed: bool = False
    mesh_properties: Optional[MeshProperties] = None
    mesh_warnings: list[str] = Field(default_factory=list)
    mesh_errors: list[str] = Field(default_factory=list)

    # G-code generation stage
    gcode_generation_passed: bool = False
    gcode_metadata: Optional[GCodeMetadata] = None
    gcode_warnings: list[str] = Field(default_factory=list)
    gcode_errors: list[str] = Field(default_factory=list)

    # Visual comparison paths (FR-034)
    original_image_path: Optional[Path] = None
    rasterized_svg_path: Optional[Path] = None
    rendered_3d_top_view_path: Optional[Path] = None
    comparison_html_path: Optional[Path] = None  # FR-035

    # Overall assessment
    overall_passed: bool = Field(..., description="All stages passed")
    total_warnings: int = Field(default=0, description="Total warning count")
    total_errors: int = Field(default=0, description="Total error count")

    generated_at: datetime = Field(default_factory=datetime.utcnow)

    def add_warning(self, stage: str, message: str) -> None:
        """Add warning to appropriate stage."""
        if stage == "vectorization":
            self.vectorization_warnings.append(message)
        elif stage == "extrusion":
            self.extrusion_warnings.append(message)
        elif stage == "mesh":
            self.mesh_warnings.append(message)
        elif stage == "gcode":
            self.gcode_warnings.append(message)
        self.total_warnings += 1

    def add_error(self, stage: str, message: str) -> None:
        """Add error to appropriate stage."""
        if stage == "vectorization":
            self.vectorization_errors.append(message)
        elif stage == "extrusion":
            self.extrusion_errors.append(message)
        elif stage == "mesh":
            self.mesh_errors.append(message)
        elif stage == "gcode":
            self.gcode_errors.append(message)
        self.total_errors += 1
```

---

### 7. PrinterProfile

Printer-specific configuration (FR-023).

```python
from pydantic import BaseModel, Field

class PrinterProfile(BaseModel):
    """
    Printer hardware specifications.

    Satisfies spec requirements:
    - FR-023: Bambu Lab H2D profile
    """
    model_config = ConfigDict(frozen=True)

    profile_name: str = Field(..., description="Profile identifier (e.g., 'bambu_h2d')")
    manufacturer: str = Field(..., description="Printer manufacturer")
    model: str = Field(..., description="Printer model")

    # Build volume (FR-023)
    build_volume_x_mm: float = Field(..., gt=0, description="X-axis build volume")
    build_volume_y_mm: float = Field(..., gt=0, description="Y-axis build volume")
    build_volume_z_mm: float = Field(..., gt=0, description="Z-axis build volume")

    # Nozzle specifications
    nozzle_diameter_mm: float = Field(..., gt=0, description="Nozzle diameter (e.g., 0.4mm)")

    # Default settings
    default_layer_height_mm: float = Field(default=0.2, gt=0)
    default_infill_percent: int = Field(default=20, ge=0, le=100)

    # Supported materials
    supported_materials: list[str] = Field(..., description="Supported material types")


# Predefined Bambu Lab H2D profile
BAMBU_H2D_PROFILE = PrinterProfile(
    profile_name="bambu_h2d",
    manufacturer="Bambu Lab",
    model="H2D",
    build_volume_x_mm=256.0,
    build_volume_y_mm=256.0,
    build_volume_z_mm=256.0,
    nozzle_diameter_mm=0.4,
    default_layer_height_mm=0.2,
    default_infill_percent=20,
    supported_materials=["PLA", "PETG"]
)
```

---

### 8. MaterialProfile

Material-specific slicing settings (FR-024, FR-025).

```python
from pydantic import BaseModel, Field

class MaterialProfile(BaseModel):
    """
    Material-specific print settings.

    Satisfies spec requirements:
    - FR-024: PLA profile
    - FR-025: PETG profile
    """
    model_config = ConfigDict(frozen=True)

    material_name: str = Field(..., description="Material type (e.g., 'PLA', 'PETG')")

    # Temperature ranges (FR-024, FR-025)
    nozzle_temp_min_celsius: int = Field(..., gt=0)
    nozzle_temp_max_celsius: int = Field(..., gt=0)
    nozzle_temp_default_celsius: int = Field(..., gt=0)

    bed_temp_celsius: int = Field(..., ge=0)

    # Print speeds
    print_speed_mm_s: int = Field(..., gt=0, description="Standard print speed")
    first_layer_speed_mm_s: int = Field(..., gt=0, description="First layer speed")

    # Retraction
    retraction_distance_mm: float = Field(..., ge=0)
    retraction_speed_mm_s: int = Field(..., gt=0)

    # Cooling
    fan_speed_percent: int = Field(..., ge=0, le=100)

    # Cost estimation
    cost_per_kg_usd: float = Field(..., gt=0, description="Material cost for estimates")


# Predefined material profiles
PLA_PROFILE = MaterialProfile(
    material_name="PLA",
    nozzle_temp_min_celsius=190,
    nozzle_temp_max_celsius=220,
    nozzle_temp_default_celsius=200,
    bed_temp_celsius=60,
    print_speed_mm_s=60,
    first_layer_speed_mm_s=30,
    retraction_distance_mm=0.8,
    retraction_speed_mm_s=40,
    fan_speed_percent=100,
    cost_per_kg_usd=20.0
)

PETG_PROFILE = MaterialProfile(
    material_name="PETG",
    nozzle_temp_min_celsius=220,
    nozzle_temp_max_celsius=250,
    nozzle_temp_default_celsius=235,
    bed_temp_celsius=70,
    print_speed_mm_s=50,
    first_layer_speed_mm_s=25,
    retraction_distance_mm=1.0,
    retraction_speed_mm_s=35,
    fan_speed_percent=50,
    cost_per_kg_usd=25.0
)
```

---

### 9. TestFixture

Synthetic test image with known properties (FR-037).

```python
from pydantic import BaseModel, Field
from enum import Enum

class FixtureComplexity(str, Enum):
    """Complexity levels for test fixtures."""
    SIMPLE = "simple"
    MODERATE = "moderate"
    COMPLEX = "complex"


class TestFixture(BaseModel):
    """
    Synthetic test image specification for automated testing.

    Satisfies spec requirements:
    - FR-037: Test image generation
    - FR-042: Parametrized test suite
    """
    model_config = ConfigDict(frozen=True)

    fixture_id: str = Field(..., description="Unique test fixture identifier")

    # Image properties
    text_content: str = Field(..., description="Text to render in test image")
    resolution_width: int = Field(..., ge=512, le=2048, description="Image width")
    resolution_height: int = Field(..., ge=512, le=2048, description="Image height")
    color_count: int = Field(..., ge=1, le=8, description="Number of distinct colors")

    # Complexity characteristics
    complexity: FixtureComplexity = Field(..., description="Fixture complexity level")
    line_thickness_px: int = Field(..., ge=1, le=10, description="Text stroke width")
    path_count_estimate: int = Field(..., ge=1, description="Expected path count after vectorization")

    # Edge case flags
    is_low_resolution: bool = Field(default=False, description="Resolution < 1024×1024")
    is_high_resolution: bool = Field(default=False, description="Resolution > 1536×1536")
    is_extreme_aspect_ratio: bool = Field(default=False, description="Aspect ratio > 10:1")
    has_thin_lines: bool = Field(default=False, description="Line thickness < 2px")
    is_high_complexity: bool = Field(default=False, description="Path count > 500")

    # Expected quality ranges (for golden file baselines FR-038)
    expected_ssim_min: float = Field(..., ge=0.0, le=1.0)
    expected_edge_iou_min: float = Field(..., ge=0.0, le=1.0)

    # File path
    generated_image_path: Optional[Path] = None

    @classmethod
    def create_simple_text_fixture(cls, text: str = "TEST") -> "TestFixture":
        """Factory for simple text fixture (baseline test case)."""
        return cls(
            fixture_id=f"simple_text_{text}",
            text_content=text,
            resolution_width=1024,
            resolution_height=1024,
            color_count=2,
            complexity=FixtureComplexity.SIMPLE,
            line_thickness_px=5,
            path_count_estimate=len(text) * 10,
            is_low_resolution=False,
            is_high_resolution=False,
            is_extreme_aspect_ratio=False,
            has_thin_lines=False,
            is_high_complexity=False,
            expected_ssim_min=0.90,
            expected_edge_iou_min=0.85
        )

    @classmethod
    def create_thin_line_fixture(cls) -> "TestFixture":
        """Factory for thin line edge case (FR-042)."""
        return cls(
            fixture_id="thin_lines_edge_case",
            text_content="THIN",
            resolution_width=1024,
            resolution_height=1024,
            color_count=2,
            complexity=FixtureComplexity.MODERATE,
            line_thickness_px=1,
            path_count_estimate=100,
            has_thin_lines=True,
            expected_ssim_min=0.75,
            expected_edge_iou_min=0.65
        )
```

---

## Model Relationships

```
ConversionJob (orchestrates entire pipeline)
    ├── QualityMetrics (vectorization quality)
    ├── MeshProperties (3D model properties)
    └── GCodeMetadata (print estimates)

ValidationReport (comprehensive quality assessment)
    ├── QualityMetrics (vectorization stage)
    ├── MeshProperties (mesh validation stage)
    └── GCodeMetadata (G-code generation stage)

VectorFile (SVG metadata)
    └── referenced by ConversionJob.svg_path

MeshFile (3MF metadata)
    ├── MeshProperties (geometric data)
    └── referenced by ConversionJob.mesh_3mf_path

GCodeFile (G-code metadata)
    ├── GCodeMetadata (print estimates)
    ├── PrinterProfile (printer configuration)
    └── MaterialProfile (material settings)

TestFixture (synthetic test data)
    └── used to generate test images for golden file baselines
```

## Implementation Notes

### File Storage

All models support JSON serialization for file-based storage:

```python
# Save conversion job to disk
job = ConversionJob(...)
job_json = job.model_dump_json(indent=2)
Path("jobs/job_123.json").write_text(job_json)

# Load from disk
job_data = Path("jobs/job_123.json").read_text()
job = ConversionJob.model_validate_json(job_data)
```

### Validation Errors

Pydantic provides clear error messages (FR-048):

```python
try:
    mesh = MeshFile(
        file_path=Path("model.3mf"),
        file_size_bytes=15_000_000,  # Exceeds 10MB limit!
        ...
    )
except ValidationError as e:
    print(e.json())
    # Output: {"file_size_bytes": ["ensure this value is less than or equal to 10485760"]}
```

### Shared Models Location

All models defined in `backend/shared/models.py` for cross-component usage:

```python
# In model-converter/src/converter.py
from backend.shared.models import ConversionJob, QualityMetrics, MeshFile

# In slicer/src/slicer.py
from backend.shared.models import GCodeFile, PrinterProfile, MaterialProfile
```

## Next Steps

1. ✅ Data models complete - all 9 entities defined with Pydantic schemas
2. ➡️ Generate API contracts for file formats and validation (contracts/)
3. ➡️ Create developer quickstart guide (quickstart.md)
