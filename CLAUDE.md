# lesign Development Guidelines

Auto-generated from all feature plans. Last updated: 2025-11-16

## Active Technologies

### 001-ai-image-generation
- Python 3.11+
- openai (DALL-E 3 API client)
- pydantic (data validation)
- pillow (image processing)
- pytest (testing)
- ruff (linting)
- mypy (type checking)

### 002-3d-model-pipeline
- Python 3.12
- VTracer (image→vector conversion)
- Build123d (vector→3D CAD/extrusion)
- trimesh (mesh validation)
- Manifold3D (mesh repair)
- PrusaSlicer CLI (3D→G-code slicing)
- scikit-image (SSIM quality metrics)
- opencv-python (edge detection)
- pydantic (data validation)
- pytest (testing, >90% coverage)
- ruff (linting)

## Project Structure

```text
backend/
├── ai-generation/      # Feature 001: AI image generation
├── model-converter/    # Feature 002: Vector and 3D conversion
├── slicer/            # Feature 002: G-code generation
└── shared/            # Feature 002: Shared utilities

specs/
├── 001-ai-image-generation/
└── 002-3d-model-pipeline/
```

## Commands

### AI Image Generation (backend/ai-generation)
```bash
cd backend/ai-generation
pytest                    # Run tests with coverage
ruff check src/ tests/    # Lint code
mypy src/                 # Type check
```

### 3D Model Pipeline (backend/model-converter, backend/slicer)
```bash
cd backend/model-converter
pytest                    # Run tests (>90% coverage target)
ruff check src/ tests/    # Lint code

cd backend/slicer
pytest                    # Run tests
ruff check src/ tests/    # Lint code
```

## Code Style

- Python 3.11+ (ai-generation): Follow standard conventions
- Python 3.12 (3d-model-pipeline): Follow backend/CODE_GUIDELINES.md
- All Python: ruff for linting, mypy for type checking

## Recent Changes

- 002-3d-model-pipeline: Added 3D conversion pipeline with VTracer, Build123d, Manifold3D, PrusaSlicer
- 001-ai-image-generation: Added DALL-E 3 integration with comprehensive testing

<!-- MANUAL ADDITIONS START -->
<!-- MANUAL ADDITIONS END -->
