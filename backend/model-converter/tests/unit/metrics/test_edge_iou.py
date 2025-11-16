"""
Unit tests for Edge IoU (Intersection over Union) metric (T045).

Tests edge preservation requiring ≥0.75 threshold (FR-003).

Feature: 002-3d-model-pipeline
User Story: US2 - Automated Quality Validation
"""

from pathlib import Path
from unittest.mock import Mock, patch

import pytest
import numpy as np
from PIL import Image, ImageDraw

# Add backend to path for imports
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent.parent.parent))


# This will fail until we implement metrics
@pytest.mark.skip(reason="Implementation not yet created - TDD red phase")
class TestEdgeIoUMetric:
    """Unit tests for Edge IoU metric calculation."""

    def test_identical_edges_perfect_score(self, tmp_path):
        """Identical edge maps should have IoU = 1.0."""
        from backend.model_converter.src.metrics.edge_iou import calculate_edge_iou

        # Create images with same edges
        img1 = Image.new("RGB", (100, 100), color=(255, 255, 255))
        draw1 = ImageDraw.Draw(img1)
        draw1.rectangle([25, 25, 75, 75], outline=(0, 0, 0), width=2)

        img2 = Image.new("RGB", (100, 100), color=(255, 255, 255))
        draw2 = ImageDraw.Draw(img2)
        draw2.rectangle([25, 25, 75, 75], outline=(0, 0, 0), width=2)

        img1_path = tmp_path / "img1.png"
        img2_path = tmp_path / "img2.png"
        img1.save(img1_path)
        img2.save(img2_path)

        iou_score = calculate_edge_iou(img1_path, img2_path)

        assert iou_score == pytest.approx(1.0, abs=0.1)

    def test_no_overlap_zero_score(self, tmp_path):
        """Completely different edge maps should have low IoU."""
        from backend.model_converter.src.metrics.edge_iou import calculate_edge_iou

        # Image 1: Left edge
        img1 = Image.new("RGB", (100, 100), color=(255, 255, 255))
        draw1 = ImageDraw.Draw(img1)
        draw1.rectangle([10, 25, 30, 75], outline=(0, 0, 0), width=2)

        # Image 2: Right edge
        img2 = Image.new("RGB", (100, 100), color=(255, 255, 255))
        draw2 = ImageDraw.Draw(img2)
        draw2.rectangle([70, 25, 90, 75], outline=(0, 0, 0), width=2)

        img1_path = tmp_path / "img1.png"
        img2_path = tmp_path / "img2.png"
        img1.save(img1_path)
        img2.save(img2_path)

        iou_score = calculate_edge_iou(img1_path, img2_path)

        assert iou_score < 0.3  # Low overlap

    def test_partial_overlap(self, tmp_path):
        """Partially overlapping edges should have moderate IoU."""
        from backend.model_converter.src.metrics.edge_iou import calculate_edge_iou

        # Slightly shifted rectangles
        img1 = Image.new("RGB", (100, 100), color=(255, 255, 255))
        draw1 = ImageDraw.Draw(img1)
        draw1.rectangle([25, 25, 75, 75], outline=(0, 0, 0), width=2)

        img2 = Image.new("RGB", (100, 100), color=(255, 255, 255))
        draw2 = ImageDraw.Draw(img2)
        draw2.rectangle([30, 30, 80, 80], outline=(0, 0, 0), width=2)

        img1_path = tmp_path / "img1.png"
        img2_path = tmp_path / "img2.png"
        img1.save(img1_path)
        img2.save(img2_path)

        iou_score = calculate_edge_iou(img1_path, img2_path)

        assert 0.4 < iou_score < 0.9  # Moderate overlap

    def test_threshold_check_passes(self, tmp_path):
        """Edge IoU ≥0.75 should pass threshold (FR-003)."""
        from backend.model_converter.src.metrics.edge_iou import calculate_edge_iou, check_edge_threshold

        img1 = Image.new("RGB", (100, 100), color=(255, 255, 255))
        draw1 = ImageDraw.Draw(img1)
        draw1.rectangle([25, 25, 75, 75], outline=(0, 0, 0), width=2)

        img2 = Image.new("RGB", (100, 100), color=(255, 255, 255))
        draw2 = ImageDraw.Draw(img2)
        draw2.rectangle([25, 25, 75, 75], outline=(0, 0, 0), width=2)

        img1_path = tmp_path / "img1.png"
        img2_path = tmp_path / "img2.png"
        img1.save(img1_path)
        img2.save(img2_path)

        iou_score = calculate_edge_iou(img1_path, img2_path)
        passes = check_edge_threshold(iou_score, threshold=0.75)

        assert iou_score >= 0.75
        assert passes is True

    def test_canny_edge_detection(self, tmp_path):
        """Should use Canny edge detection from OpenCV."""
        from backend.model_converter.src.metrics.edge_iou import calculate_edge_iou

        # Create image with clear edges
        img1 = Image.new("RGB", (100, 100), color=(255, 255, 255))
        draw1 = ImageDraw.Draw(img1)
        draw1.ellipse([25, 25, 75, 75], outline=(0, 0, 0), width=3)

        img2 = Image.new("RGB", (100, 100), color=(255, 255, 255))
        draw2 = ImageDraw.Draw(img2)
        draw2.ellipse([25, 25, 75, 75], outline=(0, 0, 0), width=3)

        img1_path = tmp_path / "img1.png"
        img2_path = tmp_path / "img2.png"
        img1.save(img1_path)
        img2.save(img2_path)

        iou_score = calculate_edge_iou(img1_path, img2_path)

        # Should detect edges and calculate IoU
        assert 0.0 <= iou_score <= 1.0

    def test_no_edges_handling(self, tmp_path):
        """Images with no edges should be handled gracefully."""
        from backend.model_converter.src.metrics.edge_iou import calculate_edge_iou

        # Solid color images (no edges)
        img1 = Image.new("RGB", (100, 100), color=(128, 128, 128))
        img2 = Image.new("RGB", (100, 100), color=(128, 128, 128))

        img1_path = tmp_path / "img1.png"
        img2_path = tmp_path / "img2.png"
        img1.save(img1_path)
        img2.save(img2_path)

        iou_score = calculate_edge_iou(img1_path, img2_path)

        # Should return 0 or 1 depending on implementation
        assert 0.0 <= iou_score <= 1.0

    def test_complex_shapes(self, tmp_path):
        """Complex shapes should have accurate edge matching."""
        from backend.model_converter.src.metrics.edge_iou import calculate_edge_iou

        img1 = Image.new("RGB", (100, 100), color=(255, 255, 255))
        draw1 = ImageDraw.Draw(img1)
        draw1.polygon([(50, 10), (90, 90), (10, 90)], outline=(0, 0, 0), width=2)

        img2 = Image.new("RGB", (100, 100), color=(255, 255, 255))
        draw2 = ImageDraw.Draw(img2)
        draw2.polygon([(50, 10), (90, 90), (10, 90)], outline=(0, 0, 0), width=2)

        img1_path = tmp_path / "img1.png"
        img2_path = tmp_path / "img2.png"
        img1.save(img1_path)
        img2.save(img2_path)

        iou_score = calculate_edge_iou(img1_path, img2_path)

        assert iou_score > 0.8  # High similarity for same shape

    def test_score_range(self, tmp_path):
        """IoU score should always be between 0 and 1."""
        from backend.model_converter.src.metrics.edge_iou import calculate_edge_iou

        img1 = Image.new("RGB", (100, 100), color=(255, 255, 255))
        draw1 = ImageDraw.Draw(img1)
        draw1.rectangle([20, 20, 80, 80], outline=(0, 0, 0), width=2)

        img2 = Image.new("RGB", (100, 100), color=(255, 255, 255))
        draw2 = ImageDraw.Draw(img2)
        draw2.rectangle([25, 25, 75, 75], outline=(0, 0, 0), width=2)

        img1_path = tmp_path / "img1.png"
        img2_path = tmp_path / "img2.png"
        img1.save(img1_path)
        img2.save(img2_path)

        iou_score = calculate_edge_iou(img1_path, img2_path)

        assert 0.0 <= iou_score <= 1.0
