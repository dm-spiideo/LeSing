"""Contract tests for AIImageGenerator public API.

Tests verify the public interface contracts are met:
- Input/output contracts
- Exception types
- ImageResult structure
"""

from pathlib import Path
from uuid import UUID

import pytest

from src.exceptions import (
    AIGenerationError,
    AuthenticationError,
    ValidationError,
)
from src.generator import AIImageGenerator
from src.models import ImageResult


class TestAIImageGeneratorContract:
    """Contract tests for AIImageGenerator public API."""

    @pytest.fixture
    def generator(self, test_settings, temp_output_dir: Path):  # type: ignore[no-untyped-def]
        """Provide an AIImageGenerator instance."""
        test_settings.storage_path = temp_output_dir
        return AIImageGenerator(settings=test_settings)

    def test_generate_image_accepts_prompt_string(
        self, generator: AIImageGenerator
    ) -> None:
        """Test that generate_image accepts a string prompt."""
        # This will fail until implemented, but tests the contract
        result = generator.generate_image("SARAH")
        assert isinstance(result, ImageResult)

    def test_generate_image_accepts_optional_style(
        self, generator: AIImageGenerator
    ) -> None:
        """Test that generate_image accepts optional style parameter."""
        result = generator.generate_image("SARAH", style="modern")
        assert isinstance(result, ImageResult)

    def test_generate_image_accepts_optional_size(
        self, generator: AIImageGenerator
    ) -> None:
        """Test that generate_image accepts optional size parameter."""
        result = generator.generate_image("SARAH", size="1024x1024")
        assert isinstance(result, ImageResult)

    def test_generate_image_accepts_optional_quality(
        self, generator: AIImageGenerator
    ) -> None:
        """Test that generate_image accepts optional quality parameter."""
        result = generator.generate_image("SARAH", quality="standard")
        assert isinstance(result, ImageResult)

    def test_generate_image_returns_image_result(
        self, generator: AIImageGenerator
    ) -> None:
        """Test that generate_image returns ImageResult."""
        result = generator.generate_image("SARAH")
        assert isinstance(result, ImageResult)
        assert hasattr(result, "status")
        assert hasattr(result, "request_id")
        assert hasattr(result, "image_path")
        assert hasattr(result, "error")
        assert hasattr(result, "metadata")
        assert hasattr(result, "timestamp")

    def test_generate_image_result_has_valid_request_id(
        self, generator: AIImageGenerator
    ) -> None:
        """Test that ImageResult contains a valid UUID request_id."""
        result = generator.generate_image("SARAH")
        assert isinstance(result.request_id, UUID)

    def test_generate_image_success_status_has_image_path(
        self, generator: AIImageGenerator
    ) -> None:
        """Test that success status includes image_path."""
        result = generator.generate_image("SARAH")
        if result.status == "success":
            assert result.image_path is not None
            assert isinstance(result.image_path, Path)

    def test_generate_image_success_status_has_metadata(
        self, generator: AIImageGenerator
    ) -> None:
        """Test that success status includes metadata."""
        result = generator.generate_image("SARAH")
        if result.status == "success":
            assert result.metadata is not None
            assert hasattr(result.metadata, "original_prompt")
            assert hasattr(result.metadata, "optimized_prompt")
            assert hasattr(result.metadata, "generation_time_ms")
            assert hasattr(result.metadata, "quality_validation")

    def test_generate_image_failed_status_has_error(
        self, generator: AIImageGenerator
    ) -> None:
        """Test that failed status includes error message."""
        # Force failure with invalid prompt
        result = generator.generate_image("")
        if result.status == "failed":
            assert result.error is not None
            assert isinstance(result.error, str)
            assert len(result.error) > 0

    def test_generate_image_raises_validation_error_for_invalid_prompt(
        self, generator: AIImageGenerator
    ) -> None:
        """Test that invalid prompt raises ValidationError or returns failed status."""
        # Empty prompt should either raise ValidationError or return failed status
        try:
            result = generator.generate_image("")
            assert result.status == "failed"
            assert "validation" in result.error.lower() if result.error else True  # type: ignore[union-attr]
        except ValidationError:
            pass  # Also acceptable

    def test_generate_image_raises_validation_error_for_invalid_style(
        self, generator: AIImageGenerator
    ) -> None:
        """Test that invalid style raises ValidationError or returns failed status."""
        try:
            result = generator.generate_image("SARAH", style="invalid_style")  # type: ignore[arg-type]
            assert result.status == "failed"
        except (ValidationError, TypeError):
            pass  # Also acceptable

    def test_validate_image_accepts_path(self, generator: AIImageGenerator) -> None:
        """Test that validate_image accepts a Path parameter."""
        from src.models import QualityValidation

        # Create a dummy path
        dummy_path = Path("/tmp/test.png")

        # This should accept a Path and return QualityValidation
        # (may fail validation, but should not error on input type)
        result = generator.validate_image(dummy_path)
        assert isinstance(result, QualityValidation)

    def test_validate_image_returns_quality_validation(
        self, generator: AIImageGenerator, sample_image_path: Path
    ) -> None:
        """Test that validate_image returns QualityValidation."""
        from src.models import QualityValidation

        result = generator.validate_image(sample_image_path)
        assert isinstance(result, QualityValidation)
        assert hasattr(result, "validation_passed")
        assert hasattr(result, "quality_score")
        assert hasattr(result, "file_exists")
        assert hasattr(result, "resolution_met")

    def test_exception_hierarchy(self) -> None:
        """Test that all exceptions inherit from AIGenerationError."""
        assert issubclass(ValidationError, AIGenerationError)
        assert issubclass(AuthenticationError, AIGenerationError)

    def test_exception_has_message(self) -> None:
        """Test that exceptions have message attribute."""
        error = ValidationError("Test error message")
        assert hasattr(error, "message")
        assert error.message == "Test error message"

    def test_exception_has_details(self) -> None:
        """Test that exceptions can have details dict."""
        error = AIGenerationError(
            "Test error", details={"key": "value", "code": 123}
        )
        assert hasattr(error, "details")
        assert error.details["key"] == "value"
        assert error.details["code"] == 123
