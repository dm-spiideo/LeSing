# Data Model: AI Image Generation

**Feature**: 001-ai-image-generation
**Date**: 2025-11-16
**Purpose**: Define data structures, entities, and relationships for AI Image Generation component

---

## Overview

The AI Image Generation component manages four primary entities that track the lifecycle of name sign image generation requests: ImageRequest (input), ImageResult (output), QualityValidation (assessment), and GenerationMetadata (detailed information).

---

## Entity Definitions

### 1. ImageRequest

**Purpose**: Represents a user's request to generate a name sign image

**Attributes**:

| Field | Type | Required | Constraints | Description |
|-------|------|----------|-------------|-------------|
| `request_id` | `str` | Yes | UUID format | Unique identifier for tracking |
| `prompt` | `str` | Yes | 1-50 chars | User text to render in name sign |
| `style` | `str \| None` | No | Enum: "modern", "classic", "playful" | Design aesthetic preference |
| `size` | `str` | No | Enum: "1024x1024", "1792x1024", "1024x1792" | Image dimensions (default: "1024x1024") |
| `quality` | `str` | No | Enum: "standard", "hd" | Quality level (default: "standard") |
| `timestamp` | `datetime` | Yes | ISO 8601 | Request creation time |

**Validation Rules**:
- `prompt`: Non-empty, 1-50 characters, no special control characters
- `style`: If provided, must be one of enum values
- `size`: If provided, must be one of enum values
- `quality`: If provided, must be one of enum values

**Pydantic Model**:
```python
from pydantic import BaseModel, Field, field_validator
from datetime import datetime
from typing import Literal
from uuid import uuid4

class ImageRequest(BaseModel):
    request_id: str = Field(default_factory=lambda: str(uuid4()))
    prompt: str = Field(min_length=1, max_length=50)
    style: Literal["modern", "classic", "playful"] | None = None
    size: Literal["1024x1024", "1792x1024", "1024x1792"] = "1024x1024"
    quality: Literal["standard", "hd"] = "standard"
    timestamp: datetime = Field(default_factory=datetime.utcnow)

    @field_validator("prompt")
    @classmethod
    def validate_prompt(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("Prompt cannot be empty or whitespace only")
        return v.strip()
```

---

### 2. ImageResult

**Purpose**: Represents the outcome of an image generation attempt

**Attributes**:

| Field | Type | Required | Constraints | Description |
|-------|------|----------|-------------|-------------|
| `request_id` | `str` | Yes | UUID format | Links to originating ImageRequest |
| `image_path` | `Path \| None` | Conditional | Valid file path | Path to generated image (None if failed) |
| `status` | `str` | Yes | Enum: "success", "failed", "retry" | Generation outcome |
| `error` | `str \| None` | Conditional | - | Error message if status is "failed" |
| `metadata` | `GenerationMetadata \| None` | Conditional | - | Detailed generation info (None if failed) |
| `timestamp` | `datetime` | Yes | ISO 8601 | Result creation time |

**State Transitions**:
```
[Initial] → "retry" → "success" | "failed"
```

**Validation Rules**:
- If `status == "success"`: `image_path` and `metadata` must be present, `error` must be None
- If `status == "failed"`: `error` must be present, `image_path` and `metadata` should be None
- If `status == "retry"`: intermediate state, `error` may describe retry reason

**Pydantic Model**:
```python
from pathlib import Path

class ImageResult(BaseModel):
    request_id: str
    image_path: Path | None = None
    status: Literal["success", "failed", "retry"]
    error: str | None = None
    metadata: "GenerationMetadata | None" = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)

    @model_validator(mode="after")
    def validate_status_consistency(self):
        if self.status == "success":
            if self.image_path is None or self.metadata is None:
                raise ValueError("Success status requires image_path and metadata")
            if self.error is not None:
                raise ValueError("Success status cannot have error message")
        elif self.status == "failed":
            if self.error is None:
                raise ValueError("Failed status requires error message")
        return self
```

---

### 3. QualityValidation

**Purpose**: Assessment of whether a generated image meets printability standards

**Attributes**:

| Field | Type | Required | Constraints | Description |
|-------|------|----------|-------------|-------------|
| `request_id` | `str` | Yes | UUID format | Links to ImageResult being validated |
| `image_path` | `Path` | Yes | Valid file path | Path to image being validated |
| `file_exists` | `bool` | Yes | - | File exists on disk |
| `file_readable` | `bool` | Yes | - | File can be opened |
| `format_valid` | `bool` | Yes | - | Valid PNG or JPEG |
| `resolution_met` | `bool` | Yes | - | Meets minimum 1024x1024 |
| `width` | `int` | Yes | ≥ 0 | Image width in pixels |
| `height` | `int` | Yes | ≥ 0 | Image height in pixels |
| `file_size_bytes` | `int` | Yes | > 0 | File size |
| `quality_score` | `float` | Yes | 0.0 - 1.0 | Overall quality score |
| `validation_passed` | `bool` | Yes | - | True if all checks pass |
| `timestamp` | `datetime` | Yes | ISO 8601 | Validation execution time |

**Quality Score Calculation**:
```
quality_score = (
    file_exists * 0.25 +
    file_readable * 0.25 +
    format_valid * 0.25 +
    resolution_met * 0.25
)
```
All checks must pass for `validation_passed = True`

**Pydantic Model**:
```python
class QualityValidation(BaseModel):
    request_id: str
    image_path: Path
    file_exists: bool
    file_readable: bool
    format_valid: bool
    resolution_met: bool
    width: int = Field(ge=0)
    height: int = Field(ge=0)
    file_size_bytes: int = Field(gt=0)
    quality_score: float = Field(ge=0.0, le=1.0)
    validation_passed: bool
    timestamp: datetime = Field(default_factory=datetime.utcnow)

    @computed_field
    @property
    def all_checks_passed(self) -> bool:
        return all([
            self.file_exists,
            self.file_readable,
            self.format_valid,
            self.resolution_met
        ])
```

---

### 4. GenerationMetadata

**Purpose**: Detailed information about the generation process

**Attributes**:

| Field | Type | Required | Constraints | Description |
|-------|------|----------|-------------|-------------|
| `model` | `str` | Yes | - | AI model used (e.g., "dall-e-3") |
| `original_prompt` | `str` | Yes | - | User's original prompt |
| `optimized_prompt` | `str` | Yes | - | Final prompt sent to API |
| `generation_time_ms` | `int` | Yes | ≥ 0 | API call duration in milliseconds |
| `image_size` | `str` | Yes | - | Actual image dimensions |
| `image_format` | `str` | Yes | - | File format (PNG, JPEG) |
| `file_size_bytes` | `int` | Yes | > 0 | File size |
| `quality_validation` | `QualityValidation` | Yes | - | Embedded validation results |

**Pydantic Model**:
```python
class GenerationMetadata(BaseModel):
    model: str
    original_prompt: str
    optimized_prompt: str
    generation_time_ms: int = Field(ge=0)
    image_size: str
    image_format: str
    file_size_bytes: int = Field(gt=0)
    quality_validation: QualityValidation
```

---

## Relationships

```
ImageRequest (1) ──generates──> (1) ImageResult
                                     │
                                     │ has
                                     ▼
                                (0..1) GenerationMetadata
                                     │
                                     │ contains
                                     ▼
                                (1) QualityValidation
```

**Cardinality**:
- One `ImageRequest` produces exactly one `ImageResult`
- One `ImageResult` may have zero or one `GenerationMetadata` (None if failed)
- One `GenerationMetadata` contains exactly one `QualityValidation`

---

## File Storage Format

### Image Files

**Format**: PNG (preferred) or JPEG
**Naming**: `{yyyymmdd}_{hhmmss}_{request_id}_{prompt_slug}.png`
**Location**: `output/generated/`

**Example**: `20251116_123456_a1b2c3d4_sarah.png`

### Metadata JSON Files

**Format**: JSON sidecar file (same name as image, .json extension)
**Naming**: `{yyyymmdd}_{hhmmss}_{request_id}_{prompt_slug}.json`
**Location**: `output/generated/`

**Example Structure**:
```json
{
  "request": {
    "request_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
    "prompt": "SARAH",
    "style": "modern",
    "size": "1024x1024",
    "quality": "standard",
    "timestamp": "2025-11-16T12:34:56Z"
  },
  "result": {
    "request_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
    "image_path": "20251116_123456_a1b2c3d4_sarah.png",
    "status": "success",
    "error": null,
    "timestamp": "2025-11-16T12:35:01Z"
  },
  "metadata": {
    "model": "dall-e-3",
    "original_prompt": "SARAH",
    "optimized_prompt": "A modern name sign design with the text 'SARAH' in a clean, readable sans-serif font, suitable for 3D printing. Minimalist, clean lines, contemporary. Professional product photography, high contrast, white background.",
    "generation_time_ms": 2340,
    "image_size": "1024x1024",
    "image_format": "PNG",
    "file_size_bytes": 245678
  },
  "quality_validation": {
    "request_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
    "image_path": "20251116_123456_a1b2c3d4_sarah.png",
    "file_exists": true,
    "file_readable": true,
    "format_valid": true,
    "resolution_met": true,
    "width": 1024,
    "height": 1024,
    "file_size_bytes": 245678,
    "quality_score": 1.0,
    "validation_passed": true,
    "timestamp": "2025-11-16T12:35:01Z"
  }
}
```

---

## Data Flow

```
1. User provides prompt
   ↓
2. Create ImageRequest
   ↓
3. Optimize prompt
   ↓
4. Call OpenAI API
   ↓
5. Save image file
   ↓
6. Run QualityValidation
   ↓
7. Create GenerationMetadata
   ↓
8. Create ImageResult
   ↓
9. Write JSON metadata file
   ↓
10. Return ImageResult to caller
```

**Error Scenarios**:
- **API Failure**: ImageResult with status="failed", error populated
- **Quality Failure**: ImageResult with status="retry" → retry → eventual success or failed
- **Storage Failure**: ImageResult with status="failed", error="Failed to save image file"

---

## Validation Summary

| Entity | Validation | Enforcement |
|--------|------------|-------------|
| ImageRequest | Pydantic validators | At construction |
| ImageResult | Status consistency | Model validator |
| QualityValidation | Score calculation | Computed property |
| GenerationMetadata | Type constraints | Pydantic fields |

All entities use Pydantic for automatic validation, ensuring data integrity throughout the component lifecycle.
