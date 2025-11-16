# AI Image Generation Component

AI-powered text-to-image generation for name signs using OpenAI's DALL-E 3 API. This component is the first stage of the LeSign POC pipeline, converting user text prompts into 2D design images suitable for 3D printing.

## Features

- **Text-to-Image Generation**: Convert simple text prompts (e.g., "SARAH", "Welcome Home") into name sign designs
- **Style Support**: Generate images with different aesthetic styles (modern, classic, playful)
- **Quality Validation**: Automatic validation of generated images for resolution, format, and printability
- **Retry Logic**: Intelligent retry mechanism for failed generations or quality issues
- **Comprehensive Logging**: Structured logging with sensitive data filtering
- **Type Safety**: Full type hints and mypy strict mode compliance
- **Test Coverage**: 80%+ test coverage with unit, integration, and contract tests

## Quick Start

### Prerequisites

- Python 3.11 or higher
- OpenAI API key ([get one here](https://platform.openai.com/api-keys))
- pip or virtual environment tool

### Installation

```bash
# Navigate to component directory
cd backend/ai-generation

# Create and activate virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
pip install -r requirements-dev.txt  # For development
```

### Configuration

```bash
# Copy example environment file
cp .env.example .env

# Edit .env and add your OpenAI API key
# AI_GEN_OPENAI_API_KEY=sk-proj-YOUR_API_KEY_HERE
```

### Basic Usage

```python
from ai_generation import AIImageGenerator

# Initialize generator
generator = AIImageGenerator()

# Generate a simple name sign
result = generator.generate_image("SARAH")

if result.status == "success":
    print(f"✅ Image generated: {result.image_path}")
    print(f"⏱️  Time: {result.metadata.generation_time_ms}ms")
else:
    print(f"❌ Generation failed: {result.error}")
```

## Project Structure

```
backend/ai-generation/
├── src/                    # Source code
│   ├── generator.py        # Main AIImageGenerator class
│   ├── models.py           # Pydantic models
│   ├── exceptions.py       # Exception hierarchy
│   ├── api/                # OpenAI API client
│   ├── prompt/             # Prompt optimization
│   ├── validation/         # Quality validation
│   └── storage/            # File storage management
├── tests/                  # Test suite
│   ├── unit/               # Unit tests
│   ├── integration/        # Integration tests
│   └── contract/           # Contract tests
├── config/                 # Configuration
│   └── settings.py         # Settings management
├── output/                 # Generated images (gitignored)
├── pyproject.toml          # Project configuration
├── requirements.txt        # Production dependencies
└── requirements-dev.txt    # Development dependencies
```

## Development

### Run Tests

```bash
# All tests
pytest

# Unit tests only
pytest tests/unit/

# With coverage report
pytest --cov=src --cov-report=html
```

### Code Quality

```bash
# Lint code
ruff check src/ tests/

# Auto-fix issues
ruff check --fix src/ tests/

# Format code
ruff format src/ tests/

# Type checking
mypy src/
```

## API Reference

### AIImageGenerator

Main class for generating images from text prompts.

#### Methods

- `generate_image(prompt: str, style: str | None = None, size: str | None = None, quality: str | None = None) -> ImageResult`
  - Generate an image from a text prompt
  - **Parameters**:
    - `prompt`: Text to convert to image (1-50 characters)
    - `style`: Optional design style ("modern", "classic", "playful")
    - `size`: Optional image size ("1024x1024", "1792x1024", "1024x1792")
    - `quality`: Optional quality level ("standard", "hd")
  - **Returns**: `ImageResult` with status, image path, and metadata

- `validate_image(image_path: Path) -> QualityValidation`
  - Validate an existing image file
  - **Parameters**:
    - `image_path`: Path to image file
  - **Returns**: `QualityValidation` with validation results

### Models

#### ImageResult
- `status`: "success" | "failed"
- `image_path`: Path to generated image (if successful)
- `error`: Error message (if failed)
- `metadata`: Generation metadata (if successful)

#### GenerationMetadata
- `model`: AI model used
- `original_prompt`: User's original text
- `optimized_prompt`: Enhanced prompt used for generation
- `generation_time_ms`: Time taken to generate
- `quality_validation`: Quality check results

## Environment Variables

All configuration is done via environment variables with the `AI_GEN_` prefix:

- `AI_GEN_OPENAI_API_KEY`: OpenAI API key (required)
- `AI_GEN_IMAGE_SIZE`: Default image size (default: "1024x1024")
- `AI_GEN_IMAGE_QUALITY`: Default quality level (default: "standard")
- `AI_GEN_STORAGE_PATH`: Path for generated images (default: "./output/generated")
- `AI_GEN_LOG_LEVEL`: Logging level (default: "INFO")
- `AI_GEN_MAX_RETRIES`: Maximum retry attempts (default: 3)

## Error Handling

The component uses a structured exception hierarchy:

- `AIGenerationError`: Base exception
  - `ValidationError`: Invalid input parameters
  - `APIError`: API communication errors
    - `AuthenticationError`: Invalid API key
    - `RateLimitError`: Rate limit exceeded
    - `ServiceError`: OpenAI service error
  - `QualityError`: Generated image failed quality validation
  - `StorageError`: File storage errors

## Performance

- **Generation Time**: <30 seconds (90th percentile)
- **Test Execution**: <10 seconds (unit tests)
- **Coverage**: 80%+ minimum requirement

## Integration with LeSign Pipeline

Generated images are saved to `output/generated/` with accompanying metadata:

```
output/generated/
├── 20251116_123456_abc123_sarah.png   # Image file
└── 20251116_123456_abc123_sarah.json  # Metadata
```

The 3D Model Pipeline component reads these files for further processing.

## License

Part of the LeSign POC project.

## Support

For issues or questions, see the main LeSign documentation or create an issue in the repository.
