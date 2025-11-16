"""Main AIImageGenerator class.

This module provides the public API for generating images from text prompts.
"""

import io
import time
from pathlib import Path

import httpx
from PIL import Image

from .api.openai_client import OpenAIClient
from .exceptions import ValidationError
from .logging_config import configure_logging, get_logger
from .models import GenerationMetadata, ImageRequest, ImageResult, QualityValidation
from .storage.manager import StorageManager
from .validation.quality_validator import QualityValidator
from .validation.validator import PromptValidator
from config.settings import Settings


class AIImageGenerator:
    """Main class for AI-powered image generation.

    This class provides the public API for generating name sign images from
    text prompts using OpenAI's DALL-E 3 API.

    Example:
        ```python
        generator = AIImageGenerator()
        result = generator.generate_image("SARAH")
        if result.status == "success":
            print(f"Image saved to: {result.image_path}")
        ```
    """

    def __init__(self, settings: Settings | None = None) -> None:
        """Initialize the image generator.

        Args:
            settings: Optional settings instance. If not provided,
                     settings will be loaded from environment variables.
        """
        # Load settings
        if settings is None:
            settings = Settings()
        self.settings = settings

        # Configure logging
        configure_logging(log_level=settings.log_level)
        self.logger = get_logger(__name__)

        # Initialize components
        self.openai_client = OpenAIClient(
            api_key=settings.get_api_key(),
            settings=settings,
        )
        self.storage_manager = StorageManager(settings=settings)
        self.prompt_validator = PromptValidator()
        self.quality_validator = QualityValidator()

        self.logger.info(
            "ai_image_generator_initialized",
            log_level=settings.log_level,
            storage_path=str(settings.storage_path),
        )

    def generate_image(
        self,
        prompt: str,
        style: str | None = None,
        size: str | None = None,
        quality: str | None = None,
    ) -> ImageResult:
        """Generate an image from a text prompt.

        Args:
            prompt: Text to convert to image (1-50 characters)
            style: Optional design style (not implemented in US1)
            size: Optional image size (defaults to settings)
            quality: Optional quality level (defaults to settings)

        Returns:
            ImageResult with status, image path, and metadata
        """
        # Create request
        try:
            # Validate prompt
            validated_prompt = self.prompt_validator.validate_prompt(prompt)

            # Create image request
            request = ImageRequest(
                prompt=validated_prompt,
                style=style,  # type: ignore[arg-type]
                size=size or self.settings.image_size,  # type: ignore[arg-type]
                quality=quality or self.settings.image_quality,  # type: ignore[arg-type]
            )

            self.logger.info(
                "generation_started",
                request_id=str(request.request_id),
                prompt=validated_prompt,
                size=request.size,
                quality=request.quality,
            )

            # Track generation time
            start_time = time.time()

            # Generate image via OpenAI
            api_response = self.openai_client.generate_image_from_prompt(
                prompt=validated_prompt,
                size=request.size,
                quality=request.quality,
            )

            # Download image
            image = self._download_image(api_response["url"])

            # Save image
            image_path = self.storage_manager.save_image(
                image=image,
                request_id=request.request_id,
                prompt=validated_prompt,
            )

            self.logger.info(
                "image_saved",
                request_id=str(request.request_id),
                image_path=str(image_path),
            )

            # Validate quality
            quality_validation = self.quality_validator.validate_image(
                image_path=image_path,
                request_id=request.request_id,
            )

            # Calculate generation time
            generation_time_ms = int((time.time() - start_time) * 1000)

            # Create metadata
            metadata = GenerationMetadata(
                model="dall-e-3",
                original_prompt=validated_prompt,
                optimized_prompt=api_response["revised_prompt"],
                generation_time_ms=generation_time_ms,
                image_size=request.size,
                image_format=quality_validation.image_format,
                file_size_bytes=quality_validation.file_size_bytes,
                quality_validation=quality_validation,
            )

            # Save metadata
            self.storage_manager.save_metadata_json(
                metadata=metadata.model_dump(mode="json"),
                image_path=image_path,
            )

            self.logger.info(
                "generation_completed",
                request_id=str(request.request_id),
                generation_time_ms=generation_time_ms,
                quality_score=quality_validation.quality_score,
            )

            # Return success result
            return ImageResult(
                request_id=request.request_id,
                status="success",
                image_path=image_path,
                metadata=metadata,
            )

        except ValidationError as e:
            # Validation errors should return failed status
            self.logger.error(
                "validation_error",
                error=e.message,
                details=e.details,
            )
            from uuid import uuid4
            return ImageResult(
                request_id=request.request_id if 'request' in locals() else uuid4(),
                status="failed",
                error=e.message,
            )

        except Exception as e:
            # All other errors should return failed status
            error_message = f"{type(e).__name__}: {str(e)}"
            self.logger.error(
                "generation_failed",
                error=error_message,
                error_type=type(e).__name__,
            )
            from uuid import uuid4
            return ImageResult(
                request_id=request.request_id if 'request' in locals() else uuid4(),
                status="failed",
                error=error_message,
            )

    def validate_image(self, image_path: Path) -> QualityValidation:
        """Validate an existing image file.

        Args:
            image_path: Path to image file

        Returns:
            QualityValidation with results
        """
        # Generate a temporary request ID for validation
        from uuid import uuid4
        request_id = uuid4()

        return self.quality_validator.validate_image(
            image_path=image_path,
            request_id=request_id,
        )

    def _download_image(self, url: str) -> Image.Image:
        """Download image from URL.

        Args:
            url: Image URL from OpenAI API

        Returns:
            PIL Image object

        Raises:
            Exception: If download fails
        """
        response = httpx.get(url, timeout=30.0)
        response.raise_for_status()

        image = Image.open(io.BytesIO(response.content))
        return image
