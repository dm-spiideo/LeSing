# File Format Specifications

**Feature**: 002-3d-model-pipeline
**Created**: 2025-11-16
**Purpose**: Define contracts for all file formats used in the pipeline

## Overview

This document specifies the file format contracts for the 3D Model Pipeline. Each stage communicates via files, and these contracts ensure compatibility and validation.

---

## 1. Input Image Format

### PNG/JPEG Image Contract

**Purpose**: Source images for vectorization (FR-001)

**File Extensions**: `.png`, `.jpg`, `.jpeg`

**Requirements**:

```yaml
format: PNG or JPEG
color_space: RGB (no CMYK, no grayscale)
bit_depth: 8 bits per channel
min_resolution: 512×512 pixels
max_resolution: 4096×4096 pixels (practical limit)
file_size: ≤ 20MB
```

**Validation Rules**:

1. Must be valid image file (readable by PIL/Pillow)
2. Must have RGB color space (no alpha channel required)
3. Must meet minimum resolution of 512×512 pixels
4. Must not be corrupted (FR-043)

**Example Validation**:

```python
from PIL import Image

def validate_input_image(path: Path) -> tuple[bool, str]:
    """Validate input image meets requirements."""
    try:
        img = Image.open(path)

        if img.mode not in ['RGB', 'RGBA']:
            return False, f"Invalid color mode: {img.mode}, expected RGB"

        width, height = img.size
        if width < 512 or height < 512:
            return False, f"Resolution {width}×{height} below minimum 512×512"

        if path.stat().st_size > 20_000_000:
            return False, f"File size {path.stat().st_size} exceeds 20MB limit"

        return True, "Valid"
    except Exception as e:
        return False, f"Corrupted or invalid image: {e}"
```

---

## 2. SVG Vector Format

### SVG File Contract

**Purpose**: Vectorized representation of input image (FR-004, FR-005)

**File Extension**: `.svg`

**Requirements**:

```yaml
format: SVG 1.1 or 2.0
encoding: UTF-8
structure:
  - well_formed_xml: required
  - root_element: <svg> with namespace
  - viewBox_or_dimensions: required
  - min_geometry: at least one <path>, <rect>, <circle>, or <polygon>

constraints:
  file_size: ≤ 5MB (FR-005)
  path_count: ≤ 1000 paths (FR-005)
  color_count: ≤ 8 distinct colors (FR-001)
```

**Validation Rules**:

1. **Well-formed XML** (FR-004): Must parse without errors
2. **Valid root element**: Must have `<svg>` root with namespace
3. **Dimensions defined**: Must have `viewBox` or `width`/`height` attributes
4. **Contains geometry**: At least one shape element present
5. **File size limit**: ≤ 5MB (FR-005)
6. **Path complexity**: ≤ 1000 paths to avoid performance issues (FR-005)

**Example Valid SVG**:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100">
  <rect x="10" y="10" width="80" height="80" fill="#FF0000"/>
  <path d="M 20,20 L 80,80 L 20,80 Z" fill="#0000FF"/>
</svg>
```

**Example Validation**:

```python
import xml.etree.ElementTree as ET

def validate_svg_structure(path: Path) -> tuple[bool, str]:
    """Validate SVG meets structural requirements (FR-004)."""
    if path.stat().st_size > 5_242_880:
        return False, f"File size {path.stat().st_size} exceeds 5MB limit (FR-005)"

    try:
        tree = ET.parse(path)
        root = tree.getroot()

        # Check root element
        if not root.tag.endswith('svg'):
            return False, f"Invalid root element: {root.tag}"

        # Check viewBox or dimensions
        if 'viewBox' not in root.attrib and ('width' not in root.attrib or 'height' not in root.attrib):
            return False, "Missing viewBox or width/height attributes"

        # Check for geometry
        geometry_tags = ['path', 'rect', 'circle', 'polygon', 'ellipse', 'line']
        has_geometry = any(root.iter(f'{{{root.tag.split("}")[0]}}}}{tag}') for tag in geometry_tags)

        if not has_geometry:
            return False, "No geometry elements found (FR-004)"

        # Check path count
        paths = list(root.iter(f'{{{root.tag.split("}")[0]}}}path'))
        if len(paths) > 1000:
            return False, f"Path count {len(paths)} exceeds limit of 1000 (FR-005)"

        return True, "Valid SVG structure"

    except ET.ParseError as e:
        return False, f"XML parsing error: {e} (FR-045)"
```

---

## 3. 3MF Mesh Format

### 3MF File Contract

**Purpose**: 3D model representation for slicing (FR-009)

**File Extension**: `.3mf`

**Requirements**:

```yaml
format: 3MF (3D Manufacturing Format) version 1.x
structure:
  - zip_container: 3MF is a zip archive
  - 3d_model_xml: /3D/3dmodel.model XML file required
  - valid_mesh: Triangular mesh in <mesh> element

constraints:
  file_size: ≤ 10MB
  watertight: REQUIRED (NON-NEGOTIABLE, FR-013)
  manifold: REQUIRED (NON-NEGOTIABLE, FR-014)
  build_volume: Must fit 256×256×256mm (FR-015)
  face_count: ≤ 100,000 triangles (FR-018)

metadata:
  source_svg: Original SVG file reference
  extrusion_depth_mm: Configured depth value
  generated_by: "lesign-model-converter"
  generated_at: ISO 8601 timestamp
```

**Validation Rules**:

1. **File format**: Must be valid ZIP archive containing 3D/3dmodel.model
2. **Mesh structure**: Must contain valid triangular mesh
3. **Watertight** (FR-013): No holes or gaps - CRITICAL for printability
4. **Manifold** (FR-014): Valid solid volume - CRITICAL for printability
5. **Build volume** (FR-015): Bounding box ≤ 256×256×256mm
6. **Face count** (FR-017, FR-018): Warn > 50K, reject > 100K
7. **Positive volume**: Mesh must have volume > 0 (FR-012)

**Example 3MF Metadata** (in 3dmodel.model):

```xml
<?xml version="1.0" encoding="UTF-8"?>
<model unit="millimeter" xmlns="http://schemas.microsoft.com/3dmanufacturing/core/2015/02">
  <metadata name="source_svg">name_sign_vector.svg</metadata>
  <metadata name="extrusion_depth_mm">5.0</metadata>
  <metadata name="generated_by">lesign-model-converter</metadata>
  <metadata name="generated_at">2025-11-16T10:30:00Z</metadata>

  <resources>
    <object id="1" type="model">
      <mesh>
        <vertices>
          <vertex x="0.0" y="0.0" z="0.0"/>
          <!-- ... more vertices ... -->
        </vertices>
        <triangles>
          <triangle v1="0" v2="1" v3="2"/>
          <!-- ... more triangles ... -->
        </triangles>
      </mesh>
    </object>
  </resources>

  <build>
    <item objectid="1"/>
  </build>
</model>
```

**Example Validation**:

```python
import trimesh

def validate_3mf_mesh(path: Path) -> tuple[bool, list[str]]:
    """
    Validate 3MF mesh meets printability requirements.

    Returns: (is_valid, error_messages)
    """
    errors = []

    # Check file size
    if path.stat().st_size > 10_485_760:
        errors.append(f"File size {path.stat().st_size} exceeds 10MB limit")

    try:
        mesh = trimesh.load(path)

        # CRITICAL: Watertight check (FR-013 NON-NEGOTIABLE)
        if not mesh.is_watertight:
            errors.append("CRITICAL: Mesh is not watertight (has holes/gaps) - UNPRINTABLE")

        # CRITICAL: Manifold check (FR-014 NON-NEGOTIABLE)
        if not mesh.is_volume:
            errors.append("CRITICAL: Mesh is not manifold (invalid solid) - UNPRINTABLE")

        # CRITICAL: Build volume check (FR-015)
        bounds = mesh.bounds
        dimensions = bounds[1] - bounds[0]
        if any(d > 256 for d in dimensions):
            errors.append(f"CRITICAL: Mesh dimensions {dimensions} exceed build volume 256×256×256mm")

        # Face count checks (FR-017, FR-018)
        face_count = len(mesh.faces)
        if face_count > 100_000:
            errors.append(f"CRITICAL: Face count {face_count} exceeds limit of 100,000 (FR-018)")
        elif face_count > 50_000:
            errors.append(f"WARNING: Face count {face_count} > 50,000 may impact slicing performance (FR-017)")

        # Volume check (FR-012)
        if mesh.volume <= 0:
            errors.append("CRITICAL: Mesh has zero or negative volume - UNPRINTABLE")

        return len(errors) == 0 or all("WARNING" in e for e in errors), errors

    except Exception as e:
        errors.append(f"Failed to load 3MF file: {e}")
        return False, errors
```

---

## 4. G-code Format

### G-code File Contract

**Purpose**: Printer-ready instructions for Bambu Lab H2D (FR-022 through FR-030)

**File Extension**: `.gcode` or `.g`

**Requirements**:

```yaml
format: Text-based G-code (Marlin/RepRap dialect)
encoding: UTF-8 or ASCII

required_sections:
  - header_comment: Slicer metadata
  - temperature_commands: M104 (nozzle), M140 (bed)
  - homing: G28 (home all axes)
  - printing_commands: G1 movement commands
  - end_commands: M104 S0, M140 S0 (turn off heaters)

metadata_comments:
  - estimated_print_time: "; estimated printing time = XXX"
  - filament_usage: "; filament used = XXX g"
  - layer_height: "; layer_height = 0.2"
  - generated_by: "; generated by = PrusaSlicer"
```

**Validation Rules**:

1. **Non-empty file** (FR-030): Must contain G-code commands
2. **Temperature commands** (FR-030): Must include M104/M109 (nozzle) and M140/M190 (bed)
3. **Valid structure**: Should contain homing, printing moves, and end commands
4. **Metadata extraction**: Parse comments for estimates (FR-028)

**Temperature Requirements**:

Per FR-024 and FR-025:

```yaml
PLA:
  nozzle_temp: 190-220°C
  bed_temp: 60°C

PETG:
  nozzle_temp: 220-250°C
  bed_temp: 70°C
```

**Example Valid G-code**:

```gcode
; generated by = PrusaSlicer 2.7.0
; printer_model = Bambu Lab H2D
; filament_type = PLA
; layer_height = 0.2
; estimated printing time = 1h 23m
; filament used = 15.4 g

M104 S200 ; set nozzle temp
M140 S60  ; set bed temp
M109 S200 ; wait for nozzle temp
M190 S60  ; wait for bed temp

G28 ; home all axes
G1 Z0.2 F1200 ; move to first layer height

; Begin printing
G1 X10 Y10 E0.5 F1800
G1 X50 Y10 E1.2 F1800
; ... more printing moves ...

; End G-code
M104 S0 ; turn off nozzle
M140 S0 ; turn off bed
G28 X0 Y0 ; home X/Y
M84 ; disable motors
```

**Example Validation**:

```python
import re

def validate_gcode(path: Path) -> tuple[bool, dict]:
    """
    Validate G-code structure and extract metadata (FR-030, FR-028).

    Returns: (is_valid, metadata_dict)
    """
    content = path.read_text()

    if not content or len(content) < 100:
        return False, {"error": "G-code file is empty or too short (FR-030)"}

    # Check for required temperature commands (FR-030)
    has_nozzle_temp = bool(re.search(r'M10[49]\s+S\d+', content))
    has_bed_temp = bool(re.search(r'M1[49]0\s+S\d+', content))

    if not (has_nozzle_temp and has_bed_temp):
        return False, {"error": "Missing temperature commands M104/M140 (FR-030)"}

    # Extract metadata from comments (FR-028)
    metadata = {}

    time_match = re.search(r';\s*estimated printing time[=:]\s*(.+)', content, re.IGNORECASE)
    if time_match:
        metadata['estimated_print_time'] = time_match.group(1).strip()

    filament_match = re.search(r';\s*filament used[=:]\s*([\d.]+)\s*g', content, re.IGNORECASE)
    if filament_match:
        metadata['filament_usage_grams'] = float(filament_match.group(1))

    layer_match = re.search(r';\s*layer_height[=:]\s*([\d.]+)', content, re.IGNORECASE)
    if layer_match:
        metadata['layer_height_mm'] = float(layer_match.group(1))

    # Count layers
    layer_count = len(re.findall(r';LAYER:\d+', content))
    if layer_count > 0:
        metadata['layer_count'] = layer_count

    metadata['file_size_bytes'] = path.stat().st_size
    metadata['has_temperature_commands'] = True

    return True, metadata
```

---

## 5. Quality Metrics JSON

### QualityMetrics JSON Contract

**Purpose**: Serialize quality validation results between stages

**File Extension**: `.json`

**Schema**:

```json
{
  "ssim_score": 0.87,
  "edge_iou": 0.79,
  "color_correlation": 0.92,
  "coverage_ratio": 0.85,
  "color_quantization_error": 0.05,
  "lpips_score": 0.15,
  "overall_score": 0.88,
  "passed": true,
  "ssim_passed": true,
  "edge_iou_passed": true,
  "color_passed": true
}
```

**Validation**:

All fields match the `QualityMetrics` Pydantic model from data-model.md. Use Pydantic for automatic validation:

```python
from backend.shared.models import QualityMetrics

# Load and validate
metrics_json = Path("quality_report.json").read_text()
metrics = QualityMetrics.model_validate_json(metrics_json)

# Save validated metrics
Path("quality_report.json").write_text(metrics.model_dump_json(indent=2))
```

---

## 6. Conversion Job JSON

### ConversionJob JSON Contract

**Purpose**: Track pipeline state and results

**File Extension**: `.json`

**Schema**:

```json
{
  "job_id": "job_20251116_103045",
  "input_image_path": "/data/input/name_sign.png",
  "input_image_size_bytes": 245678,
  "current_stage": "completed",
  "stage_timestamps": {
    "submitted": "2025-11-16T10:30:45Z",
    "vectorizing": "2025-11-16T10:30:46Z",
    "vector_validation": "2025-11-16T10:30:55Z",
    "extruding": "2025-11-16T10:30:56Z",
    "mesh_validation": "2025-11-16T10:31:02Z",
    "slicing": "2025-11-16T10:31:03Z",
    "completed": "2025-11-16T10:31:25Z"
  },
  "svg_path": "/data/output/name_sign.svg",
  "mesh_3mf_path": "/data/output/name_sign.3mf",
  "gcode_path": "/data/output/name_sign.gcode",
  "quality_metrics": { "overall_score": 0.88, "passed": true, ... },
  "error_message": null,
  "retry_count": 0,
  "created_at": "2025-11-16T10:30:45Z",
  "completed_at": "2025-11-16T10:31:25Z"
}
```

**Validation**: Use `ConversionJob` Pydantic model from data-model.md

---

## Contract Testing

All file format contracts should have automated tests:

```python
# tests/contract/test_svg_schema.py
def test_valid_svg_passes_validation():
    """Valid SVG with required structure passes validation."""
    svg_path = Path("tests/fixtures/valid_simple.svg")
    is_valid, message = validate_svg_structure(svg_path)
    assert is_valid, message

def test_oversized_svg_fails():
    """SVG exceeding 5MB limit fails validation (FR-005)."""
    # Generate large SVG
    large_svg = Path("tests/fixtures/oversized.svg")
    is_valid, message = validate_svg_structure(large_svg)
    assert not is_valid
    assert "5MB limit" in message

# tests/contract/test_3mf_schema.py
def test_non_watertight_mesh_fails():
    """Non-watertight mesh fails critical validation (FR-013)."""
    mesh_path = Path("tests/fixtures/non_watertight.3mf")
    is_valid, errors = validate_3mf_mesh(mesh_path)
    assert not is_valid
    assert any("watertight" in e.lower() for e in errors)

# tests/contract/test_gcode_schema.py
def test_gcode_without_temps_fails():
    """G-code missing temperature commands fails (FR-030)."""
    gcode_path = Path("tests/fixtures/no_temps.gcode")
    is_valid, metadata = validate_gcode(gcode_path)
    assert not is_valid
```

## Summary

All file formats have explicit contracts with:

1. **Structure requirements** - What must be present
2. **Validation rules** - How to verify compliance
3. **Constraints** - Size limits, complexity limits
4. **Example code** - Reference implementations
5. **Test cases** - Contract validation tests

These contracts ensure reliable file-based communication between pipeline stages.
