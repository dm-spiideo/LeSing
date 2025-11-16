"""Quality validation for generated images.

This module validates that generated images meet minimum quality requirements
for 3D printing suitability.
"""

from pathlib import Path
from uuid import UUID

from PIL import Image

from ..models import QualityValidation


class QualityValidator:
    """Validator for image quality.

    Checks:
    - File exists and is readable
    - Image format is PNG or JPEG
    - Resolution meets minimum (1024x1024)
    - Calculates overall quality score
    """

    MIN_WIDTH = 1024
    MIN_HEIGHT = 1024
    VALID_FORMATS = {"PNG", "JPEG"}

    def validate_image(self, image_path: Path, request_id: UUID) -> QualityValidation:
        """Validate image quality.

        Args:
            image_path: Path to image file
            request_id: Associated request ID

        Returns:
            QualityValidation with results
        """
        # Initialize validation results
        file_exists = image_path.exists()
        file_readable = False
        format_valid = False
        resolution_met = False
        width = 0
        height = 0
        file_size_bytes = 0
        image_format = ""

        if file_exists:
            # Get file size
            try:
                file_size_bytes = image_path.stat().st_size
            except OSError:
                file_size_bytes = 0

            # Try to open and validate image
            try:
                with Image.open(image_path) as img:
                    file_readable = True
                    image_format = img.format or ""
                    format_valid = image_format in self.VALID_FORMATS
                    width, height = img.size
                    resolution_met = width >= self.MIN_WIDTH and height >= self.MIN_HEIGHT
            except Exception:
                # Image not readable or invalid format
                file_readable = False

        # Calculate quality score
        quality_score = self._calculate_quality_score(
            file_exists=file_exists,
            file_readable=file_readable,
            format_valid=format_valid,
            resolution_met=resolution_met,
        )

        # Overall validation passed?
        validation_passed = all([
            file_exists,
            file_readable,
            format_valid,
            resolution_met,
        ])

        return QualityValidation(
            request_id=request_id,
            image_path=image_path,
            file_exists=file_exists,
            file_readable=file_readable,
            format_valid=format_valid,
            resolution_met=resolution_met,
            width=width,
            height=height,
            file_size_bytes=file_size_bytes,
            quality_score=quality_score,
            validation_passed=validation_passed,
            image_format=image_format,
        )

    def _calculate_quality_score(
        self,
        file_exists: bool,
        file_readable: bool,
        format_valid: bool,
        resolution_met: bool,
    ) -> float:
        """Calculate overall quality score (0.0-1.0).

        Args:
            file_exists: File exists on disk
            file_readable: File can be opened as image
            format_valid: Format is PNG or JPEG
            resolution_met: Resolution meets minimum

        Returns:
            Quality score between 0.0 and 1.0
        """
        # Each criterion contributes equally to the score
        criteria = [file_exists, file_readable, format_valid, resolution_met]
        passed_count = sum(1 for c in criteria if c)
        return passed_count / len(criteria)
