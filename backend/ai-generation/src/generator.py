"""Main AIImageGenerator class.

This module provides the public API for generating images from text prompts.
"""

import io
import time
from pathlib import Path

import httpx
from PIL import Image

from config.settings import Settings

from .api.openai_client import OpenAIClient
from .exceptions import ValidationError
from .logging_config import configure_logging, get_logger
from .models import GenerationMetadata, ImageRequest, ImageResult, QualityValidation
from .prompt.optimizer import PromptOptimizer
from .storage.manager import StorageManager
from .validation.quality_validator import QualityValidator
from .validation.validator import PromptValidator


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
        self.prompt_optimizer = PromptOptimizer()
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
            style: Optional design style (modern, classic, playful)
            size: Optional image size (defaults to settings)
            quality: Optional quality level (defaults to settings)

        Returns:
            ImageResult with status, image path, and metadata

        Note:
            This method implements automatic retry logic for:
            - Quality validation failures (up to max_retries)
            - API rate limit errors (handled by OpenAI client)
            - Service errors (handled by OpenAI client)

            Non-retryable errors (return immediately):
            - Validation errors (invalid input)
            - Authentication errors (invalid API key)
            - Storage errors (disk/permission issues)
        """
        # Create request
        try:
            # Validate prompt
            validated_prompt = self.prompt_validator.validate_prompt(prompt)

            # Create image request
            request = ImageRequest(
                prompt=validated_prompt,
                style=style,
                size=size or self.settings.image_size,
                quality=quality or self.settings.image_quality,
            )

            # Try generation with retry logic for quality failures
            max_attempts = self.settings.max_retries + 1  # Initial attempt + retries
            for attempt in range(1, max_attempts + 1):
                try:
                    result = self._generate_with_quality_check(
                        request=request,
                        validated_prompt=validated_prompt,
                        optimized_prompt_base=validated_prompt,
                        style=style,
                        attempt=attempt,
                    )

                    # Success - return result
                    return result

                except Exception as e:
                    # Check if this is the last attempt
                    if attempt >= max_attempts:
                        # Final attempt failed - return error
                        self.logger.error(
                            "generation_failed_after_max_retries",
                            request_id=str(request.request_id),
                            attempt=attempt,
                            max_retries=self.settings.max_retries,
                            error=str(e),
                        )
                        from uuid import uuid4

                        return ImageResult(
                            request_id=request.request_id,
                            status="failed",
                            error=f"Generation failed after {self.settings.max_retries} retries: {str(e)}",
                        )

                    # Not the last attempt - check if retryable
                    if self._is_retryable_error(e):
                        backoff_seconds = 2**attempt  # Exponential backoff: 2, 4, 8
                        self.logger.warning(
                            "retry_attempt",
                            request_id=str(request.request_id),
                            attempt_number=attempt,
                            max_retries=self.settings.max_retries,
                            error_type=type(e).__name__,
                            error_message=str(e),
                            backoff_seconds=backoff_seconds,
                        )

                        # Wait before retry
                        import time

                        time.sleep(backoff_seconds)
                        continue
                    else:
                        # Non-retryable error - fail immediately
                        self.logger.error(
                            "generation_failed_non_retryable",
                            request_id=str(request.request_id),
                            error_type=type(e).__name__,
                            error_message=str(e),
                        )
                        raise

            # This line should never be reached (loop always returns or raises)
            # but is required to satisfy mypy's return checking
            from uuid import uuid4

            return ImageResult(
                request_id=request.request_id,
                status="failed",
                error="Unexpected: retry loop completed without returning",
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
                request_id=request.request_id if "request" in locals() else uuid4(),
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
                request_id=request.request_id if "request" in locals() else uuid4(),
                status="failed",
                error=error_message,
            )

    def _is_retryable_error(self, error: Exception) -> bool:
        """Check if an error is retryable.

        Args:
            error: Exception to check

        Returns:
            True if error should trigger retry, False otherwise
        """
        from .exceptions import (
            AuthenticationError,
            QualityError,
            RateLimitError,
            ServiceError,
            StorageError,
            ValidationError,
        )

        # Retryable errors
        retryable_types = (
            QualityError,
            RateLimitError,
            ServiceError,
        )

        # Non-retryable errors
        non_retryable_types = (
            ValidationError,
            AuthenticationError,
            StorageError,
        )

        if isinstance(error, retryable_types):
            return True
        if isinstance(error, non_retryable_types):
            return False

        # Unknown errors - don't retry by default
        return False

    def _generate_with_quality_check(
        self,
        request: ImageRequest,
        validated_prompt: str,
        optimized_prompt_base: str,
        style: str | None,
        attempt: int,
    ) -> ImageResult:
        """Generate image and validate quality.

        This is an internal method that performs one generation attempt.

        Args:
            request: ImageRequest with generation parameters
            validated_prompt: Validated user prompt
            optimized_prompt_base: Base prompt for optimization
            style: Optional design style
            attempt: Current attempt number (1-indexed)

        Returns:
            ImageResult with generated image

        Raises:
            QualityError: If generated image fails quality validation
            Other exceptions: From API or storage operations
        """
        # Optimize prompt with style keywords if style is provided
        if style:
            optimized_prompt = self.prompt_optimizer.optimize(
                validated_prompt,
                style=style,  # type: ignore[arg-type]
            )
        else:
            optimized_prompt = validated_prompt

        self.logger.info(
            "generation_started",
            request_id=str(request.request_id),
            prompt=validated_prompt,
            optimized_prompt=optimized_prompt,
            style=style,
            size=request.size,
            quality=request.quality,
            attempt=attempt,
        )

        # Track generation time
        start_time = time.time()

        # Generate image via OpenAI using optimized prompt
        api_response = self.openai_client.generate_image_from_prompt(
            prompt=optimized_prompt,
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

        # Check if quality validation passed
        if not quality_validation.validation_passed:
            from .exceptions import QualityError

            raise QualityError(
                f"Generated image failed quality validation (score: {quality_validation.quality_score})",
                details={
                    "quality_score": quality_validation.quality_score,
                    "resolution_met": quality_validation.resolution_met,
                    "format_valid": quality_validation.format_valid,
                    "width": quality_validation.width,
                    "height": quality_validation.height,
                },
            )

        # Create metadata
        metadata = GenerationMetadata(
            model="dall-e-3",
            original_prompt=validated_prompt,
            optimized_prompt=optimized_prompt,  # Our prompt with style keywords
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
            attempt=attempt,
        )

        # Return success result
        return ImageResult(
            request_id=request.request_id,
            status="success",
            image_path=image_path,
            metadata=metadata,
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
