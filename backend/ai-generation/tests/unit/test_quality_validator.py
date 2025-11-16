"""Unit tests for QualityValidator.

Tests cover:
- File exists check
- File readable check (with Pillow)
- Format validation (PNG/JPEG)
- Resolution validation (≥1024x1024)
- Quality score calculation
"""

from pathlib import Path
from unittest.mock import Mock, patch
from uuid import uuid4

import pytest
from PIL import Image

from src.models import QualityValidation
from src.validation.quality_validator import QualityValidator


class TestQualityValidator:
    """Test suite for QualityValidator class."""

    @pytest.fixture
    def validator(self) -> QualityValidator:
        """Provide a QualityValidator instance."""
        return QualityValidator()

    def test_validate_image_success(
        self, validator: QualityValidator, sample_image_path: Path
    ) -> None:
        """Test validation of valid image."""
        request_id = uuid4()
        result = validator.validate_image(
            image_path=sample_image_path, request_id=request_id
        )

        assert isinstance(result, QualityValidation)
        assert result.file_exists is True
        assert result.file_readable is True
        assert result.format_valid is True
        assert result.resolution_met is True
        assert result.validation_passed is True
        assert result.quality_score >= 0.0
        assert result.quality_score <= 1.0

    def test_validate_image_file_not_exists(self, validator: QualityValidator) -> None:
        """Test validation when file doesn't exist."""
        request_id = uuid4()
        non_existent_path = Path("/tmp/nonexistent_image.png")

        result = validator.validate_image(
            image_path=non_existent_path, request_id=request_id
        )

        assert result.file_exists is False
        assert result.validation_passed is False
        assert result.quality_score == 0.0

    def test_validate_image_low_resolution(
        self, validator: QualityValidator, tmp_path: Path
    ) -> None:
        """Test validation fails for images below 1024x1024."""
        # Create a low-resolution image (512x512)
        low_res_image = Image.new("RGB", (512, 512), color="white")
        image_path = tmp_path / "low_res.png"
        low_res_image.save(image_path, "PNG")

        request_id = uuid4()
        result = validator.validate_image(image_path=image_path, request_id=request_id)

        assert result.file_exists is True
        assert result.file_readable is True
        assert result.resolution_met is False
        assert result.width == 512
        assert result.height == 512
        assert result.validation_passed is False
        assert result.quality_score < 1.0

    def test_validate_image_invalid_format(
        self, validator: QualityValidator, tmp_path: Path
    ) -> None:
        """Test validation of invalid format (not PNG or JPEG)."""
        # Create a text file with .png extension
        invalid_file = tmp_path / "invalid.png"
        invalid_file.write_text("This is not an image")

        request_id = uuid4()
        result = validator.validate_image(
            image_path=invalid_file, request_id=request_id
        )

        assert result.file_exists is True
        assert result.file_readable is False
        assert result.validation_passed is False

    def test_validate_image_jpeg_format(
        self, validator: QualityValidator, tmp_path: Path
    ) -> None:
        """Test validation accepts JPEG format."""
        # Create a valid JPEG image
        jpeg_image = Image.new("RGB", (1024, 1024), color="blue")
        image_path = tmp_path / "test.jpg"
        jpeg_image.save(image_path, "JPEG")

        request_id = uuid4()
        result = validator.validate_image(image_path=image_path, request_id=request_id)

        assert result.file_exists is True
        assert result.file_readable is True
        assert result.format_valid is True
        assert result.image_format == "JPEG"
        assert result.validation_passed is True

    def test_validate_image_exact_minimum_resolution(
        self, validator: QualityValidator, tmp_path: Path
    ) -> None:
        """Test validation passes for exactly 1024x1024."""
        exact_size_image = Image.new("RGB", (1024, 1024), color="green")
        image_path = tmp_path / "exact_size.png"
        exact_size_image.save(image_path, "PNG")

        request_id = uuid4()
        result = validator.validate_image(image_path=image_path, request_id=request_id)

        assert result.resolution_met is True
        assert result.width == 1024
        assert result.height == 1024
        assert result.validation_passed is True

    def test_validate_image_larger_resolution(
        self, validator: QualityValidator, tmp_path: Path
    ) -> None:
        """Test validation passes for images larger than minimum."""
        large_image = Image.new("RGB", (2048, 2048), color="red")
        image_path = tmp_path / "large.png"
        large_image.save(image_path, "PNG")

        request_id = uuid4()
        result = validator.validate_image(image_path=image_path, request_id=request_id)

        assert result.resolution_met is True
        assert result.width == 2048
        assert result.height == 2048
        assert result.validation_passed is True

    def test_validate_image_quality_score_calculation(
        self, validator: QualityValidator, sample_image_path: Path
    ) -> None:
        """Test quality score calculation logic."""
        request_id = uuid4()
        result = validator.validate_image(
            image_path=sample_image_path, request_id=request_id
        )

        # Quality score should be 1.0 for perfect validation
        if (
            result.file_exists
            and result.file_readable
            and result.format_valid
            and result.resolution_met
        ):
            assert result.quality_score == 1.0

    def test_validate_image_file_size_recorded(
        self, validator: QualityValidator, sample_image_path: Path
    ) -> None:
        """Test that file size is correctly recorded."""
        request_id = uuid4()
        result = validator.validate_image(
            image_path=sample_image_path, request_id=request_id
        )

        assert result.file_size_bytes > 0
        assert result.file_size_bytes == sample_image_path.stat().st_size
