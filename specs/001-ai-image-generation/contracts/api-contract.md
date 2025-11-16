# API Contract: AI Image Generation Component

**Feature**: 001-ai-image-generation
**Date**: 2025-11-16
**Version**: 1.0.0

---

## Overview

This document defines the public API contract for the AI Image Generation component. This is a Python library interface (not a REST API) designed to be called by other components in the LeSign pipeline, specifically the 3D Model Pipeline.

---

## Public Interface

### AIImageGenerator Class

The primary interface for all image generation operations.

#### Constructor

```python
class AIImageGenerator:
    def __init__(self, settings: Settings | None = None):
        """
        Initialize the AI Image Generator.

        Args:
            settings: Optional Settings object. If None, loads from environment.

        Raises:
            ConfigurationError: If required configuration (API key) is missing
        """
```

---

### Method: generate_image

Generate a name sign image from a text prompt.

**Signature**:
```python
def generate_image(
    self,
    prompt: str,
    style: Literal["modern", "classic", "playful"] | None = None,
    size: Literal["1024x1024", "1792x1024", "1024x1792"] = "1024x1024",
    quality: Literal["standard", "hd"] = "standard"
) -> ImageResult:
```

**Input Contract**:

| Parameter | Type | Required | Constraints | Description |
|-----------|------|----------|-------------|-------------|
| `prompt` | `str` | Yes | 1-50 chars, non-empty | Text to render in name sign |
| `style` | `str \| None` | No | "modern", "classic", or "playful" | Design aesthetic |
| `size` | `str` | No | "1024x1024", "1792x1024", "1024x1792" | Image dimensions |
| `quality` | `str` | No | "standard" or "hd" | Quality level |

**Output Contract**:

Returns `ImageResult` object with the following structure:

```python
@dataclass
class ImageResult:
    request_id: str                    # UUID tracking identifier
    image_path: Path | None            # Path to generated image (None if failed)
    status: Literal["success", "failed", "retry"]  # Generation outcome
    error: str | None                  # Error message if failed
    metadata: GenerationMetadata | None  # Generation details (None if failed)
    timestamp: datetime                # Result creation time
```

**Success Case** (`status == "success"`):
- `image_path`: Valid Path object pointing to PNG/JPEG file
- `metadata`: GenerationMetadata object with full details
- `error`: None

**Failure Case** (`status == "failed"`):
- `image_path`: None
- `metadata`: None
- `error`: Descriptive error message

**Example Usage**:
```python
from ai_generation import AIImageGenerator

generator = AIImageGenerator()

# Basic usage
result = generator.generate_image("SARAH")
if result.status == "success":
    print(f"Image saved to: {result.image_path}")
else:
    print(f"Generation failed: {result.error}")

# With style
result = generator.generate_image("Welcome Home", style="modern")

# Full options
result = generator.generate_image(
    prompt="The Smiths",
    style="classic",
    size="1792x1024",
    quality="hd"
)
```

**Exceptions**:

| Exception | When Raised | Recovery |
|-----------|-------------|----------|
| `ValidationError` | Invalid input (empty prompt, invalid style/size/quality) | Fix input and retry |
| `AuthenticationError` | Invalid OpenAI API key | Check API key configuration |
| `RateLimitError` | OpenAI rate limit exceeded (after retries) | Wait and retry later |
| `ServiceError` | OpenAI service unavailable (after retries) | Wait and retry later |
| `QualityError` | Generated image fails validation (after retry) | Try different prompt or parameters |
| `StorageError` | Cannot save image file (disk full, permissions) | Fix storage issue |

**Performance Guarantees**:
- **Target**: <30 seconds (90th percentile)
- **Timeout**: 60 seconds maximum
- **Retries**: Automatic for transient failures (rate limits, service errors)

---

### Method: validate_image

Validate an existing image file meets quality requirements.

**Signature**:
```python
def validate_image(self, image_path: Path) -> QualityValidation:
```

**Input Contract**:

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `image_path` | `Path` | Yes | Path to image file to validate |

**Output Contract**:

Returns `QualityValidation` object:

```python
@dataclass
class QualityValidation:
    request_id: str           # Tracking identifier
    image_path: Path          # Path to validated image
    file_exists: bool         # File exists on disk
    file_readable: bool       # File can be opened
    format_valid: bool        # Valid PNG or JPEG format
    resolution_met: bool      # ≥ 1024x1024 pixels
    width: int                # Image width in pixels
    height: int               # Image height in pixels
    file_size_bytes: int      # File size
    quality_score: float      # 0.0-1.0 overall score
    validation_passed: bool   # True if all checks pass
    timestamp: datetime       # Validation execution time
```

**Example Usage**:
```python
validation = generator.validate_image(Path("output/image.png"))

if validation.validation_passed:
    print(f"Image is valid: {validation.width}x{validation.height}")
else:
    print(f"Validation failed. Score: {validation.quality_score}")
```

**Exceptions**:
- `FileNotFoundError`: Image file does not exist
- `ValidationError`: Invalid file path provided

---

## Error Handling Contract

### Exception Hierarchy

```
AIGenerationError (base exception)
├── ValidationError         # Input validation failures
├── APIError                # OpenAI API errors
│   ├── AuthenticationError # Invalid API key
│   ├── RateLimitError      # Rate limit exceeded
│   └── ServiceError        # Service unavailable
├── QualityError            # Quality validation failure
└── StorageError            # File I/O errors
```

### Error Response Format

All exceptions include:
- **message**: Human-readable error description
- **request_id**: Tracking identifier (if applicable)
- **details**: Additional context (if applicable)

**Example**:
```python
try:
    result = generator.generate_image("SARAH")
except RateLimitError as e:
    print(f"Rate limited: {e.message}")
    print(f"Request ID: {e.request_id}")
    # Recommended: Wait and retry
except QualityError as e:
    print(f"Quality check failed: {e.message}")
    print(f"Details: {e.details}")
    # Recommended: Try different prompt
```

---

## Integration Contract with 3D Model Pipeline

### Handoff Mechanism (POC)

**Directory**: `output/generated/`

**File Pairs**:
- Image file: `{timestamp}_{request_id}_{prompt_slug}.png`
- Metadata file: `{timestamp}_{request_id}_{prompt_slug}.json`

**Example**:
```
output/generated/
├── 20251116_123456_a1b2c3_sarah.png
└── 20251116_123456_a1b2c3_sarah.json
```

### Metadata JSON Schema

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "title": "AI Generation Metadata",
  "type": "object",
  "required": ["request", "result", "metadata", "quality_validation"],
  "properties": {
    "request": {
      "type": "object",
      "required": ["request_id", "prompt", "timestamp"],
      "properties": {
        "request_id": {"type": "string", "format": "uuid"},
        "prompt": {"type": "string", "minLength": 1, "maxLength": 50},
        "style": {"type": "string", "enum": ["modern", "classic", "playful"]},
        "size": {"type": "string", "enum": ["1024x1024", "1792x1024", "1024x1792"]},
        "quality": {"type": "string", "enum": ["standard", "hd"]},
        "timestamp": {"type": "string", "format": "date-time"}
      }
    },
    "result": {
      "type": "object",
      "required": ["request_id", "image_path", "status", "timestamp"],
      "properties": {
        "request_id": {"type": "string", "format": "uuid"},
        "image_path": {"type": "string"},
        "status": {"type": "string", "enum": ["success", "failed", "retry"]},
        "error": {"type": ["string", "null"]},
        "timestamp": {"type": "string", "format": "date-time"}
      }
    },
    "metadata": {
      "type": "object",
      "required": ["model", "original_prompt", "optimized_prompt", "generation_time_ms"],
      "properties": {
        "model": {"type": "string"},
        "original_prompt": {"type": "string"},
        "optimized_prompt": {"type": "string"},
        "generation_time_ms": {"type": "integer", "minimum": 0},
        "image_size": {"type": "string"},
        "image_format": {"type": "string"},
        "file_size_bytes": {"type": "integer", "minimum": 1}
      }
    },
    "quality_validation": {
      "type": "object",
      "required": ["validation_passed", "quality_score"],
      "properties": {
        "file_exists": {"type": "boolean"},
        "file_readable": {"type": "boolean"},
        "format_valid": {"type": "boolean"},
        "resolution_met": {"type": "boolean"},
        "width": {"type": "integer"},
        "height": {"type": "integer"},
        "quality_score": {"type": "number", "minimum": 0, "maximum": 1},
        "validation_passed": {"type": "boolean"},
        "timestamp": {"type": "string", "format": "date-time"}
      }
    }
  }
}
```

---

## Backwards Compatibility

**Version**: 1.0.0 (initial release)

**Future Changes**:
- **Breaking changes**: Will increment major version (e.g., 2.0.0)
- **New features**: Will increment minor version (e.g., 1.1.0)
- **Bug fixes**: Will increment patch version (e.g., 1.0.1)

**Deprecation Policy**:
- Deprecated features will be marked in documentation
- Deprecated features will remain functional for at least 2 minor versions
- Users will be warned via logs when using deprecated features

---

## Testing Contract

### Contract Tests

All contract tests are located in `tests/contract/test_generator_contract.py`

**Required Tests**:
1. **Input Validation**: Verify all input constraints enforced
2. **Output Structure**: Verify ImageResult structure matches contract
3. **Exception Types**: Verify correct exceptions raised for error cases
4. **Metadata Format**: Verify JSON metadata matches schema

**Example Contract Test**:
```python
def test_generate_image_returns_valid_contract():
    """Verify generate_image returns ImageResult matching contract."""
    generator = AIImageGenerator()
    result = generator.generate_image("TEST")

    # Verify required fields
    assert hasattr(result, 'request_id')
    assert hasattr(result, 'image_path')
    assert hasattr(result, 'status')
    assert hasattr(result, 'error')
    assert hasattr(result, 'metadata')
    assert hasattr(result, 'timestamp')

    # Verify status is valid
    assert result.status in ["success", "failed", "retry"]

    # Verify success case contract
    if result.status == "success":
        assert result.image_path is not None
        assert result.metadata is not None
        assert result.error is None
```

---

## Configuration Contract

### Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `AI_GEN_OPENAI_API_KEY` | Yes | - | OpenAI API key (sk-...) |
| `AI_GEN_IMAGE_SIZE` | No | "1024x1024" | Default image size |
| `AI_GEN_IMAGE_QUALITY` | No | "standard" | Default quality level |
| `AI_GEN_STORAGE_PATH` | No | "./output/generated" | Output directory |
| `AI_GEN_LOG_LEVEL` | No | "INFO" | Logging level |
| `AI_GEN_MAX_RETRIES` | No | 3 | Maximum retry attempts |

**Example `.env` file**:
```bash
AI_GEN_OPENAI_API_KEY=sk-proj-xxx...xxx
AI_GEN_IMAGE_SIZE=1024x1024
AI_GEN_IMAGE_QUALITY=standard
AI_GEN_STORAGE_PATH=./output/generated
AI_GEN_LOG_LEVEL=INFO
```

---

## Summary

This contract defines:
- ✅ Public API methods (`generate_image`, `validate_image`)
- ✅ Input/output data structures (ImageResult, QualityValidation)
- ✅ Error handling hierarchy (exceptions and recovery)
- ✅ Integration format (file pairs, JSON schema)
- ✅ Configuration requirements (environment variables)
- ✅ Testing expectations (contract tests)

Adherence to this contract ensures reliable integration with downstream components in the LeSign pipeline.
