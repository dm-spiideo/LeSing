"""
Contract tests for PNG/JPEG input validation (T020).

Validates image input requirements per contracts/formats.md:
- RGB color mode (or convertible to RGB)
- Resolution ≥ 512×512 pixels
- File size ≤ 20MB

Feature: 002-3d-model-pipeline
User Story: US1 - Basic Image-to-3D Conversion
"""

import io
from pathlib import Path

import pytest
from PIL import Image

# Add backend to path for imports
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent.parent))

from backend.shared.file_io import load_image
from backend.shared.exceptions import ImageValidationError, FileSizeLimitError


class TestImageInputContract:
    """Contract tests for image input validation."""

    def test_valid_png_rgb(self, tmp_path):
        """Valid PNG with RGB color mode should load successfully."""
        img_path = tmp_path / "valid.png"
        img = Image.new("RGB", (1024, 1024), color=(255, 0, 0))
        img.save(img_path, "PNG")

        loaded = load_image(img_path)
        assert loaded.mode in ("RGB", "RGBA")
        assert loaded.size == (1024, 1024)

    def test_valid_jpeg(self, tmp_path):
        """Valid JPEG should load successfully."""
        img_path = tmp_path / "valid.jpg"
        img = Image.new("RGB", (1024, 1024), color=(0, 255, 0))
        img.save(img_path, "JPEG")

        loaded = load_image(img_path)
        assert loaded.mode == "RGB"
        assert loaded.size == (1024, 1024)

    def test_minimum_resolution_512x512(self, tmp_path):
        """Minimum resolution of 512×512 should be accepted."""
        img_path = tmp_path / "min_res.png"
        img = Image.new("RGB", (512, 512), color=(0, 0, 255))
        img.save(img_path, "PNG")

        loaded = load_image(img_path)
        assert loaded.size == (512, 512)

    def test_below_minimum_resolution_rejected(self, tmp_path):
        """Images below 512×512 should be rejected."""
        img_path = tmp_path / "too_small.png"
        img = Image.new("RGB", (511, 511), color=(255, 255, 0))
        img.save(img_path, "PNG")

        with pytest.raises(ImageValidationError, match="below minimum"):
            load_image(img_path)

    def test_grayscale_converts_to_rgb(self, tmp_path):
        """Grayscale images should convert to RGB."""
        img_path = tmp_path / "grayscale.png"
        img = Image.new("L", (1024, 1024), color=128)
        img.save(img_path, "PNG")

        loaded = load_image(img_path)
        assert loaded.mode == "RGB"

    def test_rgba_accepted(self, tmp_path):
        """RGBA images should be accepted."""
        img_path = tmp_path / "rgba.png"
        img = Image.new("RGBA", (1024, 1024), color=(255, 0, 0, 255))
        img.save(img_path, "PNG")

        loaded = load_image(img_path)
        assert loaded.mode in ("RGB", "RGBA")

    def test_unsupported_format_rejected(self, tmp_path):
        """Unsupported image formats should be rejected."""
        img_path = tmp_path / "image.bmp"
        img = Image.new("RGB", (1024, 1024))
        img.save(img_path, "BMP")

        with pytest.raises(ImageValidationError, match="Unsupported image format"):
            load_image(img_path)

    def test_file_not_found(self, tmp_path):
        """Non-existent files should raise error."""
        img_path = tmp_path / "nonexistent.png"

        with pytest.raises(ImageValidationError, match="not found"):
            load_image(img_path)

    def test_empty_file_rejected(self, tmp_path):
        """Empty files should be rejected."""
        img_path = tmp_path / "empty.png"
        img_path.touch()

        with pytest.raises(ImageValidationError, match="empty"):
            load_image(img_path)

    def test_corrupted_image_rejected(self, tmp_path):
        """Corrupted image files should be rejected."""
        img_path = tmp_path / "corrupted.png"
        img_path.write_bytes(b"Not a valid PNG file")

        with pytest.raises(ImageValidationError, match="Failed to load"):
            load_image(img_path)

    def test_large_resolution_accepted(self, tmp_path):
        """High resolution images should be accepted."""
        img_path = tmp_path / "high_res.png"
        img = Image.new("RGB", (2048, 2048), color=(100, 100, 100))
        img.save(img_path, "PNG")

        loaded = load_image(img_path)
        assert loaded.size == (2048, 2048)

    # Note: Testing 20MB file size limit is difficult without creating large files
    # This would be better tested in integration tests with actual large images
