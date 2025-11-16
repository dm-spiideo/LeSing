"""
Unit tests for vectorizer module (T023).

Tests VTracer wrapper with:
- 8-color quantization (FR-001)
- File size limits (FR-005)
- Timeout handling (FR-046)
- SVG structure validation (FR-004)

Feature: 002-3d-model-pipeline
User Story: US1 - Basic Image-to-3D Conversion
"""

from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

import pytest
from PIL import Image

# Add backend to path for imports
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent.parent))

from backend.shared.exceptions import VectorizationError, TimeoutError as PipelineTimeoutError


# This will fail until we implement vectorizer.py
@pytest.mark.skip(reason="Implementation not yet created - TDD red phase")
class TestVectorizer:
    """Unit tests for image→SVG vectorization."""

    def test_vectorize_simple_image(self, tmp_path):
        """Vectorize a simple test image."""
        from backend.model_converter.src.vectorizer import vectorize_image

        # Create test image
        img_path = tmp_path / "test.png"
        img = Image.new("RGB", (1024, 1024), color=(255, 0, 0))
        img.save(img_path)

        output_path = tmp_path / "output.svg"
        result = vectorize_image(img_path, output_path, max_colors=8)

        assert output_path.exists()
        assert result.file_path == output_path
        assert result.color_count <= 8  # FR-001

    def test_color_quantization_8_colors(self, tmp_path):
        """Color quantization should limit to 8 colors max."""
        from backend.model_converter.src.vectorizer import vectorize_image

        img_path = tmp_path / "colorful.png"
        img = Image.new("RGB", (512, 512))
        # Draw with multiple colors (will be quantized to 8)
        img.save(img_path)

        output_path = tmp_path / "output.svg"
        result = vectorize_image(img_path, output_path, max_colors=8)

        assert result.color_count <= 8

    def test_svg_structure_validation(self, tmp_path):
        """Generated SVG should pass structure validation."""
        from backend.model_converter.src.vectorizer import vectorize_image

        img_path = tmp_path / "test.png"
        img = Image.new("RGB", (1024, 1024), color=(0, 0, 255))
        img.save(img_path)

        output_path = tmp_path / "output.svg"
        result = vectorize_image(img_path, output_path)

        assert result.is_valid_xml
        assert result.has_root_element
        assert result.has_viewbox or result.has_geometry
        assert result.is_valid

    def test_file_size_within_limit(self, tmp_path):
        """Generated SVG should be under 5MB limit."""
        from backend.model_converter.src.vectorizer import vectorize_image

        img_path = tmp_path / "test.png"
        img = Image.new("RGB", (1024, 1024))
        img.save(img_path)

        output_path = tmp_path / "output.svg"
        result = vectorize_image(img_path, output_path)

        assert result.file_size_bytes <= 5_242_880  # 5MB

    @patch("backend.model_converter.src.vectorizer.subprocess.run")
    def test_timeout_handling(self, mock_run, tmp_path):
        """Vectorization should timeout after configured limit."""
        from backend.model_converter.src.vectorizer import vectorize_image
        import subprocess

        # Simulate timeout
        mock_run.side_effect = subprocess.TimeoutExpired("vtracer", 120)

        img_path = tmp_path / "test.png"
        img = Image.new("RGB", (1024, 1024))
        img.save(img_path)

        output_path = tmp_path / "output.svg"

        with pytest.raises(PipelineTimeoutError, match="120 seconds"):
            vectorize_image(img_path, output_path, timeout_seconds=120)

    def test_path_count_within_limit(self, tmp_path):
        """Path count should be under 1000 limit."""
        from backend.model_converter.src.vectorizer import vectorize_image

        img_path = tmp_path / "simple.png"
        img = Image.new("RGB", (512, 512), color=(100, 100, 100))
        img.save(img_path)

        output_path = tmp_path / "output.svg"
        result = vectorize_image(img_path, output_path)

        assert result.path_count <= 1000  # FR-005

    def test_vectorize_with_custom_parameters(self, tmp_path):
        """Vectorization should accept custom parameters."""
        from backend.model_converter.src.vectorizer import vectorize_image

        img_path = tmp_path / "test.png"
        img = Image.new("RGB", (1024, 1024))
        img.save(img_path)

        output_path = tmp_path / "output.svg"
        result = vectorize_image(
            img_path,
            output_path,
            max_colors=4,  # Custom color count
            timeout_seconds=60,
        )

        assert result.color_count <= 4

    def test_invalid_image_raises_error(self, tmp_path):
        """Invalid image should raise VectorizationError."""
        from backend.model_converter.src.vectorizer import vectorize_image

        img_path = tmp_path / "invalid.png"
        img_path.write_text("not an image")

        output_path = tmp_path / "output.svg"

        with pytest.raises(Exception):  # Could be ImageValidationError or VectorizationError
            vectorize_image(img_path, output_path)

    def test_aspect_ratio_preserved(self, tmp_path):
        """Aspect ratio should be preserved in SVG."""
        from backend.model_converter.src.vectorizer import vectorize_image

        img_path = tmp_path / "wide.png"
        img = Image.new("RGB", (2048, 512))  # 4:1 aspect ratio
        img.save(img_path)

        output_path = tmp_path / "output.svg"
        result = vectorize_image(img_path, output_path)

        # Aspect ratio should be approximately 4.0
        assert 3.9 <= result.aspect_ratio <= 4.1
