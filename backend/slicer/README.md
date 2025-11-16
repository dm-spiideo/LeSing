# Slicer

**Component**: 3D Model Pipeline - G-code Generation
**Version**: 0.1.0
**Python**: 3.12+

## Overview

The Slicer component generates printer-ready G-code from validated 3D models using PrusaSlicer CLI with Bambu Lab H2D printer profiles. It provides accurate print time and material estimates.

## Features

- **G-code Generation**: Convert 3MF to G-code using PrusaSlicer CLI
- **Printer Profiles**: Bambu Lab H2D configuration (256×256×256mm build volume)
- **Material Profiles**: PLA (190-220°C) and PETG (220-250°C) support
- **Print Estimates**: Time, filament usage, layer count, and cost calculation
- **Configurable Settings**: Layer height, infill percentage, support generation

## Prerequisites

**PrusaSlicer CLI** must be installed on your system:

```bash
# macOS (Homebrew)
brew install --cask prusaslicer

# Linux - Download from official site
# https://github.com/prusa3d/PrusaSlicer/releases

# Verify installation
prusa-slicer --version
```

## Installation

```bash
cd backend/slicer

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

# Integration tests (requires PrusaSlicer installed)
pytest tests/integration/
```

### Code Quality

```bash
# Run linter
ruff check .

# Type checking
mypy src/
```

## Project Structure

```
backend/slicer/
├── src/
│   ├── slicer.py           # PrusaSlicer CLI wrapper
│   ├── config/             # Printer/material profiles
│   │   ├── bambu_h2d_pla.ini
│   │   └── bambu_h2d_petg.ini
│   └── models.py           # Pydantic data models
├── tests/
│   ├── contract/           # G-code format validation
│   ├── integration/        # End-to-end slicing tests
│   └── unit/               # Component unit tests
├── requirements.txt
├── requirements-dev.txt
└── pyproject.toml
```

## Printer Configuration

### Bambu Lab H2D Specifications

- **Build Volume**: 256×256×256mm
- **Nozzle Diameter**: 0.4mm
- **Layer Height**: 0.2mm (standard), 0.1mm (high quality)
- **Infill**: 20% (lightweight), 100% (solid)

### Material Profiles

**PLA**:
- Nozzle Temperature: 190-220°C
- Bed Temperature: 60°C
- Print Speed: Standard
- Cooling: Full fan after layer 1

**PETG**:
- Nozzle Temperature: 220-250°C
- Bed Temperature: 70°C
- Print Speed: Reduced
- Cooling: Reduced fan speed

## G-code Metadata

Generated G-code includes:

- Estimated print time (minutes)
- Filament usage (grams)
- Layer count
- Estimated cost
- Temperature settings
- Support structure status

## Performance Requirements

- G-code generation: <5 minutes (timeout)
- Estimate accuracy: ±10% of actual print time/material

## Related Documentation

- [Feature Specification](../../specs/002-3d-model-pipeline/spec.md)
- [Implementation Plan](../../specs/002-3d-model-pipeline/plan.md)
- [Quickstart Guide](../../specs/002-3d-model-pipeline/quickstart.md)
