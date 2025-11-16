"""
Unit tests for overall quality score calculation (T047).

Tests weighted quality score requiring ≥0.85 threshold (FR-032, FR-033).

Feature: 002-3d-model-pipeline
User Story: US2 - Automated Quality Validation
"""

from pathlib import Path
from unittest.mock import Mock, patch

import pytest

# Add backend to path for imports
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent.parent.parent))

from backend.shared.models import QualityMetrics


# This will fail until we implement metrics
@pytest.mark.skip(reason="Implementation not yet created - TDD red phase")
class TestOverallQualityScore:
    """Unit tests for overall quality score calculation."""

    def test_perfect_scores_overall_1_0(self):
        """All perfect scores should yield overall score of 1.0."""
        from backend.model_converter.src.metrics import calculate_overall_quality

        metrics = QualityMetrics.from_raw_metrics(
            ssim=1.0,
            edge_iou=1.0,
            color_corr=1.0,
            coverage=1.0,
            color_quant_err=0.0,  # 0 error is perfect
            lpips=0.0,  # 0 is perfect for LPIPS
        )

        assert metrics.overall_score == pytest.approx(1.0, abs=0.01)
        assert metrics.passed is True

    def test_weighted_combination_correct(self):
        """
        Weighted score per FR-032:
        - SSIM: 25%
        - LPIPS: 20% (inverted)
        - Edge IoU: 20%
        - Color: 15%
        - Coverage: 10%
        - Quantization: 10% (inverted)
        """
        from backend.model_converter.src.metrics import calculate_overall_quality

        # Test specific weights
        metrics = QualityMetrics.from_raw_metrics(
            ssim=0.9,  # 25% * 0.9 = 0.225
            edge_iou=0.8,  # 20% * 0.8 = 0.16
            color_corr=0.95,  # 15% * 0.95 = 0.1425
            coverage=1.0,  # 10% * 1.0 = 0.1
            color_quant_err=0.1,  # 10% * (1-0.1) = 0.09
            lpips=0.2,  # 20% * (1-0.2) = 0.16
        )

        expected = 0.225 + 0.16 + 0.16 + 0.1425 + 0.1 + 0.09
        assert metrics.overall_score == pytest.approx(expected, abs=0.01)

    def test_threshold_pass_at_0_85(self):
        """Overall score ≥0.85 should pass (FR-033)."""
        metrics = QualityMetrics.from_raw_metrics(
            ssim=0.85,
            edge_iou=0.85,
            color_corr=0.90,
            coverage=0.95,
            color_quant_err=0.05,
            lpips=None,  # Optional
        )

        assert metrics.overall_score >= 0.85
        assert metrics.passed is True

    def test_threshold_fail_below_0_85(self):
        """Overall score <0.85 should fail."""
        metrics = QualityMetrics.from_raw_metrics(
            ssim=0.70,  # Below threshold
            edge_iou=0.70,
            color_corr=0.80,
            coverage=0.90,
            color_quant_err=0.15,
            lpips=None,
        )

        assert metrics.overall_score < 0.85
        assert metrics.passed is False

    def test_individual_thresholds_checked(self):
        """Individual metric thresholds should be checked correctly."""
        metrics = QualityMetrics.from_raw_metrics(
            ssim=0.90,  # ≥0.85 ✓
            edge_iou=0.80,  # ≥0.75 ✓
            color_corr=0.95,  # ≥0.90 ✓
            coverage=1.0,
            color_quant_err=0.0,
            lpips=0.1,
        )

        assert metrics.ssim_passed is True  # ≥0.85
        assert metrics.edge_iou_passed is True  # ≥0.75
        assert metrics.color_passed is True  # ≥0.90

    def test_individual_threshold_failures(self):
        """Individual metrics below threshold should be flagged."""
        metrics = QualityMetrics.from_raw_metrics(
            ssim=0.80,  # <0.85 ✗
            edge_iou=0.70,  # <0.75 ✗
            color_corr=0.85,  # <0.90 ✗
            coverage=1.0,
            color_quant_err=0.0,
            lpips=0.1,
        )

        assert metrics.ssim_passed is False
        assert metrics.edge_iou_passed is False
        assert metrics.color_passed is False

    def test_lpips_optional_handling(self):
        """LPIPS is optional, should default gracefully."""
        # Without LPIPS
        metrics_no_lpips = QualityMetrics.from_raw_metrics(
            ssim=0.9,
            edge_iou=0.85,
            color_corr=0.92,
            coverage=1.0,
            color_quant_err=0.05,
            lpips=None,  # Not provided
        )

        # With LPIPS
        metrics_with_lpips = QualityMetrics.from_raw_metrics(
            ssim=0.9,
            edge_iou=0.85,
            color_corr=0.92,
            coverage=1.0,
            color_quant_err=0.05,
            lpips=0.15,
        )

        # Both should have valid overall scores
        assert 0.0 <= metrics_no_lpips.overall_score <= 1.0
        assert 0.0 <= metrics_with_lpips.overall_score <= 1.0

    def test_coverage_ratio_impact(self):
        """Coverage ratio should affect overall score (10% weight)."""
        # High coverage
        metrics_high_coverage = QualityMetrics.from_raw_metrics(
            ssim=0.85,
            edge_iou=0.85,
            color_corr=0.90,
            coverage=1.0,  # Full coverage
            color_quant_err=0.05,
        )

        # Low coverage
        metrics_low_coverage = QualityMetrics.from_raw_metrics(
            ssim=0.85,
            edge_iou=0.85,
            color_corr=0.90,
            coverage=0.5,  # Half coverage
            color_quant_err=0.05,
        )

        # High coverage should have better overall score
        assert metrics_high_coverage.overall_score > metrics_low_coverage.overall_score

    def test_quantization_error_impact(self):
        """Quantization error should affect overall score (10% weight, inverted)."""
        # Low error (good)
        metrics_low_error = QualityMetrics.from_raw_metrics(
            ssim=0.85,
            edge_iou=0.85,
            color_corr=0.90,
            coverage=1.0,
            color_quant_err=0.0,  # No error
        )

        # High error (bad)
        metrics_high_error = QualityMetrics.from_raw_metrics(
            ssim=0.85,
            edge_iou=0.85,
            color_corr=0.90,
            coverage=1.0,
            color_quant_err=0.3,  # High error
        )

        # Low error should have better overall score
        assert metrics_low_error.overall_score > metrics_high_error.overall_score
