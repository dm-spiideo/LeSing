"""
Unit tests for SSIM (Structural Similarity) metric (T044).

Tests structural similarity calculation requiring ≥0.85 threshold (FR-002).

Feature: 002-3d-model-pipeline
User Story: US2 - Automated Quality Validation
"""

from pathlib import Path
from unittest.mock import Mock, patch

import pytest
import numpy as np
from PIL import Image

# Add backend to path for imports
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent.parent.parent))


# This will fail until we implement metrics
@pytest.mark.skip(reason="Implementation not yet created - TDD red phase")
class TestSSIMMetric:
    """Unit tests for SSIM metric calculation."""

    def test_identical_images_perfect_score(self, tmp_path):
        """Identical images should have SSIM = 1.0."""
        from backend.model_converter.src.metrics.ssim import calculate_ssim

        # Create identical images
        img1 = Image.new("RGB", (100, 100), color=(255, 0, 0))
        img2 = Image.new("RGB", (100, 100), color=(255, 0, 0))

        img1_path = tmp_path / "img1.png"
        img2_path = tmp_path / "img2.png"
        img1.save(img1_path)
        img2.save(img2_path)

        ssim_score = calculate_ssim(img1_path, img2_path)

        assert ssim_score == pytest.approx(1.0, abs=0.01)

    def test_different_images_low_score(self, tmp_path):
        """Completely different images should have low SSIM."""
        from backend.model_converter.src.metrics.ssim import calculate_ssim

        img1 = Image.new("RGB", (100, 100), color=(255, 0, 0))
        img2 = Image.new("RGB", (100, 100), color=(0, 255, 0))

        img1_path = tmp_path / "img1.png"
        img2_path = tmp_path / "img2.png"
        img1.save(img1_path)
        img2.save(img2_path)

        ssim_score = calculate_ssim(img1_path, img2_path)

        assert ssim_score < 0.5

    def test_slightly_different_images(self, tmp_path):
        """Similar images should have high SSIM."""
        from backend.model_converter.src.metrics.ssim import calculate_ssim
        from PIL import ImageDraw

        # Create base image
        img1 = Image.new("RGB", (100, 100), color=(255, 255, 255))
        draw1 = ImageDraw.Draw(img1)
        draw1.rectangle([25, 25, 75, 75], fill=(0, 0, 0))

        # Create slightly different version
        img2 = Image.new("RGB", (100, 100), color=(255, 255, 255))
        draw2 = ImageDraw.Draw(img2)
        draw2.rectangle([26, 26, 76, 76], fill=(0, 0, 0))

        img1_path = tmp_path / "img1.png"
        img2_path = tmp_path / "img2.png"
        img1.save(img1_path)
        img2.save(img2_path)

        ssim_score = calculate_ssim(img1_path, img2_path)

        assert ssim_score > 0.9  # Should be very similar

    def test_threshold_check_passes(self, tmp_path):
        """SSIM ≥0.85 should pass threshold check (FR-002)."""
        from backend.model_converter.src.metrics.ssim import calculate_ssim, check_ssim_threshold

        img1 = Image.new("RGB", (100, 100), color=(128, 128, 128))
        img2 = Image.new("RGB", (100, 100), color=(128, 128, 128))

        img1_path = tmp_path / "img1.png"
        img2_path = tmp_path / "img2.png"
        img1.save(img1_path)
        img2.save(img2_path)

        ssim_score = calculate_ssim(img1_path, img2_path)
        passes = check_ssim_threshold(ssim_score, threshold=0.85)

        assert ssim_score >= 0.85
        assert passes is True

    def test_threshold_check_fails(self, tmp_path):
        """SSIM <0.85 should fail threshold check."""
        from backend.model_converter.src.metrics.ssim import calculate_ssim, check_ssim_threshold

        img1 = Image.new("RGB", (100, 100), color=(255, 0, 0))
        img2 = Image.new("RGB", (100, 100), color=(0, 0, 255))

        img1_path = tmp_path / "img1.png"
        img2_path = tmp_path / "img2.png"
        img1.save(img1_path)
        img2.save(img2_path)

        ssim_score = calculate_ssim(img1_path, img2_path)
        passes = check_ssim_threshold(ssim_score, threshold=0.85)

        assert ssim_score < 0.85
        assert passes is False

    def test_grayscale_conversion(self, tmp_path):
        """SSIM should handle grayscale conversion."""
        from backend.model_converter.src.metrics.ssim import calculate_ssim

        # RGB images
        img1 = Image.new("RGB", (100, 100), color=(200, 200, 200))
        img2 = Image.new("RGB", (100, 100), color=(200, 200, 200))

        img1_path = tmp_path / "img1.png"
        img2_path = tmp_path / "img2.png"
        img1.save(img1_path)
        img2.save(img2_path)

        ssim_score = calculate_ssim(img1_path, img2_path)

        assert 0.0 <= ssim_score <= 1.0

    def test_different_sizes_raises_error(self, tmp_path):
        """Images with different sizes should raise error or be resized."""
        from backend.model_converter.src.metrics.ssim import calculate_ssim

        img1 = Image.new("RGB", (100, 100), color=(255, 0, 0))
        img2 = Image.new("RGB", (200, 200), color=(255, 0, 0))

        img1_path = tmp_path / "img1.png"
        img2_path = tmp_path / "img2.png"
        img1.save(img1_path)
        img2.save(img2_path)

        # Should either resize or raise error
        try:
            ssim_score = calculate_ssim(img1_path, img2_path)
            assert 0.0 <= ssim_score <= 1.0
        except ValueError:
            pass  # Expected if no automatic resizing

    def test_score_range(self, tmp_path):
        """SSIM score should always be between 0 and 1."""
        from backend.model_converter.src.metrics.ssim import calculate_ssim

        img1 = Image.new("RGB", (100, 100), color=(100, 150, 200))
        img2 = Image.new("RGB", (100, 100), color=(110, 140, 210))

        img1_path = tmp_path / "img1.png"
        img2_path = tmp_path / "img2.png"
        img1.save(img1_path)
        img2.save(img2_path)

        ssim_score = calculate_ssim(img1_path, img2_path)

        assert 0.0 <= ssim_score <= 1.0
