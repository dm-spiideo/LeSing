"""Contract tests for validation method.

Tests verify the validate_image method contracts are met.
"""

from pathlib import Path

import pytest

from src.generator import AIImageGenerator
from src.models import QualityValidation


class TestValidationContract:
    """Contract tests for validate_image method."""

    @pytest.fixture
    def generator(self, test_settings, temp_output_dir: Path):  # type: ignore[no-untyped-def]
        """Provide an AIImageGenerator instance."""
        test_settings.storage_path = temp_output_dir
        return AIImageGenerator(settings=test_settings)

    def test_validate_image_exists(self, generator: AIImageGenerator) -> None:
        """Test that validate_image method exists on AIImageGenerator."""
        assert hasattr(generator, "validate_image")
        assert callable(generator.validate_image)

    def test_validate_image_accepts_path(self, generator: AIImageGenerator, sample_image_path: Path) -> None:
        """Test that validate_image accepts a Path parameter."""
        result = generator.validate_image(sample_image_path)
        assert result is not None

    def test_validate_image_returns_quality_validation(
        self, generator: AIImageGenerator, sample_image_path: Path
    ) -> None:
        """Test that validate_image returns QualityValidation."""
        result = generator.validate_image(sample_image_path)
        assert isinstance(result, QualityValidation)

    def test_quality_validation_has_required_fields(self, generator: AIImageGenerator, sample_image_path: Path) -> None:
        """Test that QualityValidation has all required fields."""
        result = generator.validate_image(sample_image_path)

        # Check all required fields exist
        assert hasattr(result, "request_id")
        assert hasattr(result, "image_path")
        assert hasattr(result, "file_exists")
        assert hasattr(result, "file_readable")
        assert hasattr(result, "format_valid")
        assert hasattr(result, "resolution_met")
        assert hasattr(result, "width")
        assert hasattr(result, "height")
        assert hasattr(result, "file_size_bytes")
        assert hasattr(result, "quality_score")
        assert hasattr(result, "validation_passed")

    def test_quality_score_is_between_zero_and_one(self, generator: AIImageGenerator, sample_image_path: Path) -> None:
        """Test that quality_score is always between 0.0 and 1.0."""
        result = generator.validate_image(sample_image_path)
        assert 0.0 <= result.quality_score <= 1.0

    def test_validation_passed_is_boolean(self, generator: AIImageGenerator, sample_image_path: Path) -> None:
        """Test that validation_passed is a boolean."""
        result = generator.validate_image(sample_image_path)
        assert isinstance(result.validation_passed, bool)

    def test_validate_nonexistent_file(self, generator: AIImageGenerator) -> None:
        """Test that validate_image handles non-existent files gracefully."""
        non_existent = Path("/tmp/does_not_exist_12345.png")
        result = generator.validate_image(non_existent)

        assert isinstance(result, QualityValidation)
        assert result.file_exists is False
        assert result.validation_passed is False
        assert result.quality_score == 0.0

    def test_validate_image_with_valid_png(self, generator: AIImageGenerator, sample_image_path: Path) -> None:
        """Test validation of a valid PNG image."""
        result = generator.validate_image(sample_image_path)

        assert result.file_exists is True
        assert result.file_readable is True
        assert result.format_valid is True
        assert result.validation_passed is True
        assert result.quality_score > 0.0

    def test_validate_image_with_low_resolution(self, generator: AIImageGenerator, tmp_path: Path) -> None:
        """Test validation fails for low-resolution images."""
        from PIL import Image

        # Create a low-res image (512x512, below minimum 1024x1024)
        low_res = Image.new("RGB", (512, 512), color="red")
        low_res_path = tmp_path / "low_res.png"
        low_res.save(low_res_path, "PNG")

        result = generator.validate_image(low_res_path)

        assert result.file_exists is True
        assert result.file_readable is True
        assert result.resolution_met is False
        assert result.validation_passed is False
        assert result.width == 512
        assert result.height == 512
