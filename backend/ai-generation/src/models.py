"""Data models for AI Image Generation component.

This module defines all Pydantic models used for request/response handling,
validation, and metadata tracking.
"""

from datetime import datetime
from pathlib import Path
from typing import Literal
from uuid import UUID, uuid4

from pydantic import BaseModel, Field, field_validator, model_validator


class ImageRequest(BaseModel):
    """Request model for image generation.

    Attributes:
        request_id: Unique identifier for this request
        prompt: User's text to convert to image (1-50 characters)
        style: Optional design style (modern, classic, playful)
        size: Image dimensions (width x height)
        quality: Quality level (standard or hd)
        timestamp: When the request was created
    """

    request_id: UUID = Field(default_factory=uuid4)
    prompt: str = Field(..., min_length=1, max_length=50)
    style: Literal["modern", "classic", "playful"] | None = None
    size: Literal["1024x1024", "1792x1024", "1024x1792"] = "1024x1024"
    quality: Literal["standard", "hd"] = "standard"
    timestamp: datetime = Field(default_factory=datetime.utcnow)

    @field_validator("prompt")
    @classmethod
    def validate_prompt(cls, v: str) -> str:
        """Validate prompt is non-empty and contains valid characters.

        Args:
            v: Prompt string

        Returns:
            Validated prompt

        Raises:
            ValueError: If prompt is empty or contains invalid characters
        """
        if not v.strip():
            raise ValueError("Prompt cannot be empty or whitespace only")

        # POC limitation: Only Latin characters for reliable 3D conversion
        # Allow alphanumeric, spaces, and common punctuation
        import re

        if not re.match(r'^[a-zA-Z0-9\s\-\'",!.]+$', v):
            raise ValueError(
                "Prompt must contain only Latin characters, numbers, spaces, and basic punctuation"
            )

        return v.strip()


class QualityValidation(BaseModel):
    """Quality validation results for a generated image.

    Attributes:
        request_id: ID of the associated request
        image_path: Path to the validated image
        file_exists: Whether the file exists
        file_readable: Whether the file can be opened
        format_valid: Whether format is PNG or JPEG
        resolution_met: Whether resolution meets minimum (1024x1024)
        width: Image width in pixels
        height: Image height in pixels
        file_size_bytes: File size in bytes
        quality_score: Overall quality score (0.0-1.0)
        validation_passed: Whether validation passed
        timestamp: When validation was performed
    """

    request_id: UUID
    image_path: Path
    file_exists: bool
    file_readable: bool
    format_valid: bool
    resolution_met: bool
    width: int
    height: int
    file_size_bytes: int
    quality_score: float = Field(ge=0.0, le=1.0)
    validation_passed: bool
    timestamp: datetime = Field(default_factory=datetime.utcnow)

    @field_validator("quality_score")
    @classmethod
    def validate_quality_score(cls, v: float) -> float:
        """Ensure quality score is between 0.0 and 1.0.

        Args:
            v: Quality score

        Returns:
            Validated quality score

        Raises:
            ValueError: If score is out of range
        """
        if not 0.0 <= v <= 1.0:
            raise ValueError("Quality score must be between 0.0 and 1.0")
        return v


class GenerationMetadata(BaseModel):
    """Metadata about image generation process.

    Attributes:
        model: AI model used (e.g., "dall-e-3")
        original_prompt: User's original text
        optimized_prompt: Enhanced prompt used for generation
        generation_time_ms: Time taken to generate in milliseconds
        image_size: Image dimensions (WxH)
        image_format: File format (PNG or JPEG)
        file_size_bytes: File size in bytes
        quality_validation: Quality check results
    """

    model: str
    original_prompt: str
    optimized_prompt: str
    generation_time_ms: int = Field(ge=0)
    image_size: str  # e.g., "1024x1024"
    image_format: str  # e.g., "PNG"
    file_size_bytes: int = Field(ge=0)
    quality_validation: QualityValidation | None = None


class ImageResult(BaseModel):
    """Result of an image generation request.

    Attributes:
        request_id: ID of the original request
        status: Generation status (success or failed)
        image_path: Path to generated image (if successful)
        error: Error message (if failed)
        metadata: Generation metadata (if successful)
        timestamp: When the result was created
    """

    request_id: UUID
    status: Literal["success", "failed"]
    image_path: Path | None = None
    error: str | None = None
    metadata: GenerationMetadata | None = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)

    @model_validator(mode="after")
    def validate_status_consistency(self) -> "ImageResult":
        """Ensure status is consistent with other fields.

        For success status:
        - image_path must be set
        - metadata must be set
        - error must be None

        For failed status:
        - error must be set
        - image_path and metadata should be None

        Returns:
            Validated model

        Raises:
            ValueError: If status is inconsistent with other fields
        """
        if self.status == "success":
            if self.image_path is None:
                raise ValueError("Success status requires image_path")
            if self.metadata is None:
                raise ValueError("Success status requires metadata")
            if self.error is not None:
                raise ValueError("Success status should not have error message")
        elif self.status == "failed":
            if self.error is None:
                raise ValueError("Failed status requires error message")
            # Note: We allow image_path/metadata for failed status
            # in case partial data is useful for debugging

        return self
