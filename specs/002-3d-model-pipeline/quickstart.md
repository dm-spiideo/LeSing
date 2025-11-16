# Developer Quickstart: 3D Model Pipeline

**Feature**: 002-3d-model-pipeline
**Created**: 2025-11-16
**Audience**: Developers implementing or maintaining the pipeline

## Overview

This guide helps you get started with the 3D Model Pipeline codebase. You'll learn how to set up your development environment, run tests, and understand the architecture.

## Prerequisites

- **Python**: 3.12+ (per CODE_GUIDELINES.md)
- **Operating System**: Linux or macOS (development environment)
- **Disk Space**: Minimum 2GB for dependencies and test fixtures
- **PrusaSlicer**: Installed with CLI access (for G-code generation)

---

## Quick Setup

### 1. Clone and Navigate

```bash
cd /Users/danielmilesson/repos/daniel/lesign
git checkout 002-3d-model-pipeline
```

### 2. Create Virtual Environment

```bash
# Create venv
python3.12 -m venv .venv

# Activate
source .venv/bin/activate  # On macOS/Linux
```

### 3. Install Dependencies

```bash
# Install model-converter dependencies
cd backend/model-converter
pip install -r requirements.txt
pip install -r requirements-dev.txt

# Install slicer dependencies
cd ../slicer
pip install -r requirements.txt
pip install -r requirements-dev.txt

# Return to root
cd ../..
```

### 4. Install PrusaSlicer CLI

**macOS**:
```bash
brew install --cask prusaslicer
# Verify installation
prusa-slicer --help
```

**Linux (Ubuntu/Debian)**:
```bash
# Download from https://github.com/prusa3d/PrusaSlicer/releases
wget https://github.com/prusa3d/PrusaSlicer/releases/download/version_2.7.0/PrusaSlicer-2.7.0+linux-x64.tar.bz2
tar -xjf PrusaSlicer-2.7.0+linux-x64.tar.bz2
sudo mv PrusaSlicer /opt/
sudo ln -s /opt/PrusaSlicer/prusa-slicer /usr/local/bin/prusa-slicer
```

### 5. Verify Installation

```bash
# Run unit tests
cd backend/model-converter
pytest tests/unit -v

# Run integration tests (requires all dependencies)
pytest tests/integration -v
```

---

## Project Structure

```text
backend/
├── model-converter/       # Image → Vector → 3D conversion
│   ├── src/
│   │   ├── vectorizer.py       # VTracer image → SVG
│   │   ├── converter.py        # Build123d SVG → 3D
│   │   ├── validator.py        # trimesh validation
│   │   ├── repairer.py         # Manifold3D mesh repair
│   │   ├── metrics/            # Quality calculations
│   │   │   ├── ssim.py
│   │   │   ├── edge_iou.py
│   │   │   ├── color_fidelity.py
│   │   │   └── perceptual.py   # Optional LPIPS
│   │   └── models.py           # Pydantic schemas
│   ├── tests/
│   │   ├── unit/               # Component tests
│   │   ├── integration/        # Multi-stage tests
│   │   ├── contract/           # File format tests
│   │   └── fixtures/           # Test data
│   └── requirements.txt
│
├── slicer/                # 3D → G-code generation
│   ├── src/
│   │   ├── slicer.py           # PrusaSlicer wrapper
│   │   ├── config/             # Printer profiles
│   │   └── models.py
│   ├── tests/
│   └── requirements.txt
│
└── shared/                # Shared utilities
    ├── models.py               # Pydantic models (all entities)
    ├── exceptions.py           # Custom exceptions
    ├── file_io.py              # File handling
    └── logging_config.py       # Structured logging
```

---

## Key Dependencies

### model-converter Component

```text
vtracer==0.6.0          # Image → SVG vectorization
build123d==0.5.0        # SVG → 3D CAD operations
trimesh==4.0.0          # Mesh validation
manifold3d==2.4.0       # Mesh repair
scikit-image==0.22.0    # SSIM metric
opencv-python==4.8.1    # Edge detection
numpy==1.26.0           # Numerical operations
scipy==1.11.0           # Color correlation
pydantic==2.5.0         # Data validation
pillow==10.1.0          # Image I/O
lpips==0.1.4            # Optional perceptual metric (tier 2)

# Development
pytest==7.4.3
pytest-cov==4.1.0
pytest-benchmark==4.0.0
```

### slicer Component

```text
pydantic==2.5.0         # Data validation
# PrusaSlicer installed separately (CLI tool)
```

---

## Common Tasks

### Run All Tests

```bash
# From backend/model-converter
pytest tests/ -v --cov=src --cov-report=term-missing

# Check coverage (target >90%)
pytest tests/ --cov=src --cov-report=html
open htmlcov/index.html
```

### Run Specific Test Categories

```bash
# Unit tests only (fast)
pytest tests/unit -v

# Integration tests (slower, requires all dependencies)
pytest tests/integration -v

# Contract tests (file format validation)
pytest tests/contract -v

# Performance benchmarks
pytest tests/integration/test_performance.py --benchmark-only
```

### Generate Test Fixtures

```bash
# Generate synthetic test images
cd backend/model-converter
python -m tests.fixtures.generate_test_images

# Output: tests/fixtures/synthetic/*.png
```

### Run Pipeline End-to-End

```python
# Example: Convert image to G-code
from pathlib import Path
from backend.model_converter.src import pipeline

# Initialize pipeline
job = pipeline.convert_image_to_gcode(
    input_image=Path("tests/fixtures/synthetic/test_1024x1024.png"),
    output_dir=Path("output/"),
    extrusion_depth_mm=5.0,
    material_profile="PLA"
)

# Check results
if job.current_stage == "completed":
    print(f"Success! G-code: {job.gcode_path}")
    print(f"Quality score: {job.quality_metrics.overall_score}")
    print(f"Print time: {job.gcode_metadata.estimated_print_time_minutes} minutes")
else:
    print(f"Failed at stage: {job.current_stage}")
    print(f"Error: {job.error_message}")
```

### Validate File Formats

```bash
# Validate SVG
python -m backend.model_converter.src.validator validate-svg input.svg

# Validate 3MF mesh
python -m backend.model_converter.src.validator validate-mesh model.3mf

# Validate G-code
python -m backend.slicer.src.slicer validate-gcode output.gcode
```

---

## Development Workflow

### TDD Cycle (Red-Green-Refactor)

Following the project constitution (Principle II: Test-Driven Development):

```bash
# 1. RED: Write failing test
cat > tests/unit/test_new_feature.py <<EOF
def test_new_feature():
    result = new_feature()
    assert result == expected
EOF

pytest tests/unit/test_new_feature.py  # Should FAIL

# 2. GREEN: Implement minimal code to pass
# Edit src/module.py with implementation

pytest tests/unit/test_new_feature.py  # Should PASS

# 3. REFACTOR: Improve code quality
# Clean up implementation, add documentation

pytest tests/  # All tests should still PASS
```

### Adding a New Metric

1. **Create test** in `tests/unit/metrics/test_new_metric.py`:

```python
import pytest
from backend.model_converter.src.metrics.new_metric import calculate_new_metric

def test_new_metric_perfect_match():
    """New metric returns 1.0 for identical images."""
    score = calculate_new_metric("tests/fixtures/test.png", "tests/fixtures/test.png")
    assert score == pytest.approx(1.0, abs=0.01)

def test_new_metric_no_match():
    """New metric returns 0.0 for completely different images."""
    score = calculate_new_metric("tests/fixtures/test.png", "tests/fixtures/random.png")
    assert score < 0.1
```

2. **Implement** in `src/metrics/new_metric.py`:

```python
from pathlib import Path
import numpy as np
from PIL import Image

def calculate_new_metric(image_a_path: str, image_b_path: str) -> float:
    """
    Calculate new quality metric between two images.

    Args:
        image_a_path: Path to first image
        image_b_path: Path to second image

    Returns:
        Similarity score in [0.0, 1.0] where 1.0 is identical
    """
    img_a = np.array(Image.open(image_a_path).convert('RGB'))
    img_b = np.array(Image.open(image_b_path).convert('RGB'))

    # TODO: Implement metric calculation
    raise NotImplementedError("Implement metric logic")
```

3. **Run tests and iterate**:

```bash
pytest tests/unit/metrics/test_new_metric.py -v
# Iterate until green
```

4. **Add to QualityMetrics model** in `backend/shared/models.py`

---

## Debugging Tips

### Enable Debug Logging

```python
# In your script or test
import logging
logging.basicConfig(level=logging.DEBUG)

# Or use structured logging
from backend.shared.logging_config import setup_logging
setup_logging(level="DEBUG")
```

### Inspect Intermediate Files

Pipeline saves intermediate files for debugging:

```bash
# After running conversion
ls -lh output/
# output/job_123/
#   ├── input.png           # Original image
#   ├── vector.svg          # Vectorized output
#   ├── model.3mf           # 3D mesh
#   ├── model.gcode         # G-code
#   ├── quality_metrics.json
#   └── conversion_job.json
```

### Visualize Quality Metrics

```python
from backend.model_converter.src.metrics.visualization import generate_comparison

# Generate side-by-side comparison
generate_comparison(
    original="tests/fixtures/test.png",
    svg="output/vector.svg",
    mesh_3d="output/model.3mf",
    output_html="output/comparison.html"
)

# Open in browser
open output/comparison.html
```

### Common Issues

#### Issue: `vtracer` import fails

**Solution**: Ensure Rust toolchain is installed for building vtracer bindings:

```bash
curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh
pip install --force-reinstall vtracer
```

#### Issue: PrusaSlicer CLI not found

**Solution**: Add PrusaSlicer to PATH or set environment variable:

```bash
export PRUSA_SLICER_PATH="/opt/PrusaSlicer/prusa-slicer"
```

#### Issue: Tests failing due to missing fixtures

**Solution**: Generate test fixtures:

```bash
cd backend/model-converter
python -m tests.fixtures.generate_test_images
```

#### Issue: Mesh repair fails (Manifold3D)

**Solution**: Check mesh complexity. If face count > 100K, simplify before repair:

```python
import trimesh
mesh = trimesh.load("complex_model.3mf")
simplified = mesh.simplify_quadric_decimation(face_count=50000)
simplified.export("simplified.3mf")
```

---

## Performance Profiling

### Benchmark Pipeline Stages

```bash
# Run performance benchmarks
pytest tests/integration/test_performance.py --benchmark-only --benchmark-autosave

# Compare with baseline
pytest tests/integration/test_performance.py --benchmark-compare
```

### Profile Specific Function

```python
import cProfile
import pstats
from backend.model_converter.src.vectorizer import vectorize_image

# Profile vectorization
cProfile.run('vectorize_image("test.png", "output.svg")', 'profile_stats')

# Analyze results
stats = pstats.Stats('profile_stats')
stats.sort_stats('cumulative')
stats.print_stats(20)  # Top 20 slowest functions
```

### Performance Targets

Per FR-040, FR-041:

```text
Stage                  Target Time
--------------------- ------------
Image → Vector        < 30 seconds
Vector → 3D           < 10 seconds
Mesh Validation       < 10 seconds
3D → G-code           < 15 seconds
--------------------- ------------
Total Pipeline        < 60 seconds (ideally < 30s)
```

---

## Code Style

### Linting

```bash
# From project root
./run_ruff.sh  # Per CLAUDE.md instructions

# Or manually
cd backend/model-converter
ruff check src/ tests/
ruff format src/ tests/
```

### Type Checking (Optional)

```bash
# Install mypy
pip install mypy

# Run type checker
mypy src/ --strict
```

### Pre-commit Hooks (Recommended)

```bash
# Install pre-commit
pip install pre-commit

# Setup hooks
cat > .pre-commit-config.yaml <<EOF
repos:
  - repo: https://github.com/astral-sh/ruff-pre-commit
    rev: v0.1.6
    hooks:
      - id: ruff
        args: [--fix]
      - id: ruff-format
  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v4.5.0
    hooks:
      - id: trailing-whitespace
      - id: end-of-file-fixer
      - id: check-yaml
EOF

pre-commit install
```

---

## Testing Philosophy

Per project constitution (Principle II: Test-Driven Development):

### Test Pyramid

```text
         /\
        /  \  Unit Tests (80%)
       /____\   - Fast, isolated, focused
      /      \  Integration Tests (15%)
     /________\   - Multi-component, realistic
    /          \ End-to-End Tests (5%)
   /____________\  - Full pipeline, slow
```

### Test Coverage Goals

- **Overall**: >90% (SC-011)
- **Critical paths**: 100% (watertight validation, mesh repair, quality gates)
- **Edge cases**: Parametrized tests covering FR-042 scenarios

### Golden File Testing

Use baseline files for regression detection (FR-038, FR-039):

```bash
# Generate golden files (first time)
pytest tests/integration/test_golden_files.py --update-golden

# Run regression tests (5% tolerance per FR-039)
pytest tests/integration/test_golden_files.py
```

---

## API Reference

### Main Pipeline Entry Point

```python
from backend.model_converter.src.pipeline import convert_image_to_gcode
from backend.shared.models import ConversionJob
from pathlib import Path

job: ConversionJob = convert_image_to_gcode(
    input_image=Path("input.png"),
    output_dir=Path("output/"),
    extrusion_depth_mm=5.0,
    material_profile="PLA",
    layer_height_mm=0.2,
    infill_percent=20
)
```

### Stage-by-Stage API

```python
# Stage 1: Image → Vector
from backend.model_converter.src.vectorizer import vectorize_image
svg_path = vectorize_image(
    image_path=Path("input.png"),
    output_path=Path("output.svg"),
    color_mode=8  # Max 8 colors
)

# Stage 2: Vector → 3D
from backend.model_converter.src.converter import extrude_svg_to_3d
mesh_path = extrude_svg_to_3d(
    svg_path=Path("output.svg"),
    output_path=Path("output.3mf"),
    depth_mm=5.0
)

# Stage 3: Validate & Repair
from backend.model_converter.src.validator import validate_and_repair_mesh
from backend.shared.models import MeshFile

mesh: MeshFile = validate_and_repair_mesh(
    mesh_path=Path("output.3mf"),
    attempt_repair=True
)

if not mesh.is_printable:
    raise ValueError("Mesh failed validation and could not be repaired")

# Stage 4: 3D → G-code
from backend.slicer.src.slicer import generate_gcode
from backend.shared.models import GCodeFile

gcode: GCodeFile = generate_gcode(
    mesh_path=Path("output.3mf"),
    output_path=Path("output.gcode"),
    printer_profile="bambu_h2d",
    material_profile="PLA"
)
```

---

## Next Steps

1. **Read the specification**: `specs/002-3d-model-pipeline/spec.md`
2. **Review data models**: `specs/002-3d-model-pipeline/data-model.md`
3. **Check file format contracts**: `specs/002-3d-model-pipeline/contracts/formats.md`
4. **Run the test suite**: Ensure your environment is set up correctly
5. **Implement a task**: Check `specs/002-3d-model-pipeline/tasks.md` (after `/speckit.tasks` generation)

## Resources

- **Spec**: [spec.md](./spec.md)
- **Data Models**: [data-model.md](./data-model.md)
- **Technology Research**: [research.md](./research.md)
- **File Formats**: [contracts/formats.md](./contracts/formats.md)
- **Implementation Plan**: [plan.md](./plan.md)

## Support

For questions or issues:

1. Check existing tests for examples
2. Review investigation documents in `investigations/`
3. Consult constitution principles in `.specify/constitution.md`
4. Ask in project discussion channels

Happy coding!
