"""
Integration test for image→vector pipeline (T027).

Tests complete PNG/JPEG→SVG conversion with quality validation.

Feature: 002-3d-model-pipeline
User Story: US1 - Basic Image-to-3D Conversion
"""

from pathlib import Path

import pytest
from PIL import Image

# Add backend to path for imports
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent.parent))

from backend.shared.file_io import load_image, load_svg


# This will fail until we implement the full pipeline
@pytest.mark.skip(reason="Implementation not yet created - TDD red phase")
@pytest.mark.integration
class TestImageToVectorPipeline:
    """Integration tests for image→SVG conversion pipeline."""

    def test_simple_image_to_svg(self, tmp_path):
        """Simple image should convert to valid SVG."""
        from backend.model_converter.src.vectorizer import vectorize_image

        # Create test image
        img_path = tmp_path / "input.png"
        img = Image.new("RGB", (1024, 1024), color=(255, 0, 0))
        # Draw simple shape
        from PIL import ImageDraw
        draw = ImageDraw.Draw(img)
        draw.rectangle([200, 200, 800, 800], fill=(0, 0, 0))
        img.save(img_path)

        # Vectorize
        svg_path = tmp_path / "output.svg"
        vector_file = vectorize_image(img_path, svg_path)

        # Validate output
        assert svg_path.exists()
        assert vector_file.is_valid
        assert vector_file.color_count <= 8
        assert vector_file.path_count <= 1000

        # Validate SVG loads correctly
        root = load_svg(svg_path)
        assert root is not None

    def test_colorful_image_quantization(self, tmp_path):
        """Image with many colors should quantize to 8 colors."""
        from backend.model_converter.src.vectorizer import vectorize_image

        # Create image with gradient (many colors)
        img_path = tmp_path / "gradient.png"
        img = Image.new("RGB", (1024, 1024))
        from PIL import ImageDraw
        draw = ImageDraw.Draw(img)
        # Draw gradient-like pattern
        for i in range(0, 1024, 100):
            color = (i % 256, (i * 2) % 256, (i * 3) % 256)
            draw.rectangle([i, 0, i + 100, 1024], fill=color)
        img.save(img_path)

        # Vectorize
        svg_path = tmp_path / "output.svg"
        vector_file = vectorize_image(img_path, svg_path, max_colors=8)

        # Should quantize to 8 colors
        assert vector_file.color_count <= 8
        assert vector_file.is_valid

    def test_high_resolution_image(self, tmp_path):
        """High resolution image should convert successfully."""
        from backend.model_converter.src.vectorizer import vectorize_image

        img_path = tmp_path / "high_res.png"
        img = Image.new("RGB", (2048, 2048), color=(100, 100, 100))
        from PIL import ImageDraw
        draw = ImageDraw.Draw(img)
        draw.ellipse([500, 500, 1500, 1500], fill=(255, 255, 255))
        img.save(img_path)

        svg_path = tmp_path / "output.svg"
        vector_file = vectorize_image(img_path, svg_path)

        assert vector_file.is_valid
        assert vector_file.file_size_bytes <= 5_242_880  # 5MB limit

    def test_extreme_aspect_ratio(self, tmp_path):
        """Extreme aspect ratio should preserve ratio in SVG."""
        from backend.model_converter.src.vectorizer import vectorize_image

        img_path = tmp_path / "wide.png"
        img = Image.new("RGB", (2560, 256), color=(200, 200, 200))
        from PIL import ImageDraw
        draw = ImageDraw.Draw(img)
        draw.rectangle([100, 50, 2460, 206], fill=(50, 50, 50))
        img.save(img_path)

        svg_path = tmp_path / "output.svg"
        vector_file = vectorize_image(img_path, svg_path)

        # Aspect ratio should be preserved (10:1)
        assert 9.5 <= vector_file.aspect_ratio <= 10.5
        assert vector_file.is_valid

    def test_text_like_shapes(self, tmp_path):
        """Text-like shapes should vectorize cleanly."""
        from backend.model_converter.src.vectorizer import vectorize_image

        img_path = tmp_path / "text.png"
        img = Image.new("RGB", (1024, 1024), color=(255, 255, 255))
        from PIL import ImageDraw, ImageFont
        draw = ImageDraw.Draw(img)
        # Draw text-like rectangles
        draw.rectangle([100, 400, 200, 600], fill=(0, 0, 0))  # T
        draw.rectangle([250, 400, 450, 500], fill=(0, 0, 0))  # E
        draw.rectangle([500, 400, 700, 500], fill=(0, 0, 0))  # S
        draw.rectangle([750, 400, 950, 500], fill=(0, 0, 0))  # T
        img.save(img_path)

        svg_path = tmp_path / "output.svg"
        vector_file = vectorize_image(img_path, svg_path)

        assert vector_file.is_valid
        assert vector_file.has_geometry
        assert vector_file.path_count > 0

    def test_low_resolution_minimum(self, tmp_path):
        """Minimum resolution (512×512) should convert successfully."""
        from backend.model_converter.src.vectorizer import vectorize_image

        img_path = tmp_path / "low_res.png"
        img = Image.new("RGB", (512, 512), color=(150, 150, 150))
        from PIL import ImageDraw
        draw = ImageDraw.Draw(img)
        draw.rectangle([100, 100, 400, 400], fill=(255, 0, 0))
        img.save(img_path)

        svg_path = tmp_path / "output.svg"
        vector_file = vectorize_image(img_path, svg_path)

        assert vector_file.is_valid
        assert vector_file.viewbox_width > 0
        assert vector_file.viewbox_height > 0

    def test_pipeline_with_quality_check(self, tmp_path):
        """Pipeline should include quality validation."""
        from backend.model_converter.src.vectorizer import vectorize_image

        img_path = tmp_path / "test.png"
        img = Image.new("RGB", (1024, 1024), color=(128, 128, 128))
        from PIL import ImageDraw
        draw = ImageDraw.Draw(img)
        draw.circle([512, 512], 300, fill=(255, 255, 0))
        img.save(img_path)

        svg_path = tmp_path / "output.svg"
        vector_file = vectorize_image(img_path, svg_path)

        # Quality validation (to be implemented in US2)
        # For now, just verify successful conversion
        assert vector_file.is_valid
        assert vector_file.file_size_bytes > 0

    def test_grayscale_to_svg(self, tmp_path):
        """Grayscale image should convert (as RGB)."""
        from backend.model_converter.src.vectorizer import vectorize_image

        img_path = tmp_path / "grayscale.png"
        img = Image.new("L", (1024, 1024), color=200)
        from PIL import ImageDraw
        draw = ImageDraw.Draw(img)
        draw.rectangle([300, 300, 700, 700], fill=50)
        img.save(img_path)

        svg_path = tmp_path / "output.svg"
        vector_file = vectorize_image(img_path, svg_path)

        assert vector_file.is_valid
        # Should have limited colors (grayscale values)
        assert vector_file.color_count <= 8
