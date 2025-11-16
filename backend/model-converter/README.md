# Model Converter

**Component**: 3D Model Pipeline - Image to 3D Conversion
**Version**: 0.1.0
**Python**: 3.12+

## Overview

The Model Converter transforms AI-generated 2D name sign images into printable 3D models with automated quality validation. It provides a complete pipeline from raster images to validated 3D mesh files ready for slicing.

## Features

- **Image Vectorization**: Convert PNG/JPEG to SVG using VTracer with 8-color quantization
- **Quality Metrics**: SSIM, edge IoU, color fidelity validation (≥0.85 overall score required)
- **3D Extrusion**: SVG to 3D model conversion using Build123d CAD library
- **Mesh Validation**: Watertight and manifold guarantees for printability
- **Automatic Repair**: Manifold3D mesh repair for non-watertight geometry
- **Test Fixtures**: Synthetic test image generation for automated testing

## Pipeline Stages

```
PNG/JPEG → [Vectorize] → SVG → [Validate Quality] → [Extrude] → 3MF → [Validate Mesh] → [Repair if needed] → Valid 3MF
```

## Installation

```bash
cd backend/model-converter

# Create virtual environment
python3.12 -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -r requirements-dev.txt
```

## Development

### Run Tests

```bash
# All tests with coverage
pytest

# Unit tests only
pytest tests/unit/

# Integration tests
pytest tests/integration/

# Specific test file
pytest tests/unit/test_vectorizer.py
```

### Code Quality

```bash
# Run linter
ruff check .

# Auto-fix issues
ruff check --fix .

# Type checking
mypy src/
```

## Project Structure

```
backend/model-converter/
├── src/
│   ├── vectorizer.py       # Image → SVG conversion
│   ├── converter.py        # SVG → 3D model conversion
│   ├── validator.py        # Mesh validation
│   ├── repairer.py         # Mesh repair
│   └── metrics/            # Quality metrics
│       ├── ssim.py         # Structural similarity
│       ├── edge_iou.py     # Edge preservation
│       └── color_fidelity.py
├── tests/
│   ├── contract/           # File format validation tests
│   ├── integration/        # Multi-stage pipeline tests
│   ├── unit/               # Component unit tests
│   └── fixtures/           # Test data and baselines
├── requirements.txt
├── requirements-dev.txt
└── pyproject.toml
```

## Quality Requirements

- **Overall Quality Score**: ≥0.85 (weighted combination of all metrics)
- **SSIM**: ≥0.85 (structural similarity between original and vectorized)
- **Edge IoU**: ≥0.75 (edge preservation accuracy)
- **Color Fidelity**: ≥0.90 (histogram correlation)
- **Watertight**: 100% (non-negotiable for printability)
- **Manifold**: 100% (non-negotiable for printability)
- **Build Volume**: Must fit within 256×256×256mm (Bambu Lab H2D)

## Dependencies

See [research.md](../../specs/002-3d-model-pipeline/research.md) for technology decisions and rationale.

- **VTracer**: Image vectorization with color quantization
- **Build123d**: CAD library for SVG import and 3D extrusion
- **trimesh**: Mesh validation and property calculation
- **Manifold3D**: Automatic mesh repair
- **scikit-image**: SSIM quality metric
- **OpenCV**: Edge detection for IoU metric
- **Pydantic**: Data validation

## Related Documentation

- [Feature Specification](../../specs/002-3d-model-pipeline/spec.md)
- [Implementation Plan](../../specs/002-3d-model-pipeline/plan.md)
- [Data Models](../../specs/002-3d-model-pipeline/data-model.md)
- [Quickstart Guide](../../specs/002-3d-model-pipeline/quickstart.md)
