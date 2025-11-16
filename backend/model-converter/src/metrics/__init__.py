"""
Quality metrics calculation and validation.

Implements automated quality validation (FR-031 to FR-033) with:
- SSIM (Structural Similarity) e0.85 (FR-002)
- Edge IoU e0.75 (FR-003)
- Color Correlation e0.90 (FR-006)
- Weighted overall score e0.85 (FR-032)

Feature: 002-3d-model-pipeline
User Story: US2 - Automated Quality Validation
"""

from pathlib import Path
from typing import Optional

from backend.shared.logging_config import get_logger
from backend.shared.models import QualityMetrics, VectorFile

from .ssim import calculate_ssim, check_ssim_threshold, SSIM_THRESHOLD
from .edge_iou import calculate_edge_iou, check_edge_threshold, EDGE_IOU_THRESHOLD
from .color_fidelity import (
    calculate_color_correlation,
    check_color_threshold,
    COLOR_CORRELATION_THRESHOLD,
)

logger = get_logger(__name__)


# =============================================================================
# Public API
# =============================================================================

__all__ = [
    # Main validation functions
    "calculate_overall_quality",
    "validate_quality",
    # Individual metrics
    "calculate_ssim",
    "calculate_edge_iou",
    "calculate_color_correlation",
    # Threshold checks
    "check_ssim_threshold",
    "check_edge_threshold",
    "check_color_threshold",
    # Constants
    "SSIM_THRESHOLD",
    "EDGE_IOU_THRESHOLD",
    "COLOR_CORRELATION_THRESHOLD",
    "OVERALL_QUALITY_THRESHOLD",
]


# =============================================================================
# Constants
# =============================================================================

OVERALL_QUALITY_THRESHOLD = 0.85  # FR-032

# Weighted quality score formula (FR-032)
# Note: This is a simplified version focusing on the 3 key metrics
# Full formula includes LPIPS, coverage, quantization which we'll add later
WEIGHT_SSIM = 0.40  # Structural similarity (increased weight in simplified version)
WEIGHT_EDGE_IOU = 0.35  # Edge preservation (increased weight)
WEIGHT_COLOR = 0.25  # Color fidelity


# =============================================================================
# Overall Quality Calculation
# =============================================================================


def calculate_overall_quality(
    original_path: Path,
    vectorized_path: Path,
    rasterized_path: Optional[Path] = None,
) -> QualityMetrics:
    """
    Calculate complete quality metrics for vectorization (FR-032).

    Computes all individual metrics and weighted overall score:
    - SSIM (structural similarity)
    - Edge IoU (edge preservation)
    - Color correlation (color fidelity)
    - Overall weighted score

    Args:
        original_path: Path to original raster image
        vectorized_path: Path to vectorized SVG file
        rasterized_path: Optional path to pre-rasterized SVG (for comparison)
                        If not provided, will rasterize SVG automatically

    Returns:
        QualityMetrics with all scores and pass/fail status

    Raises:
        FileNotFoundError: If input files don't exist
        ProcessingError: If metric calculation fails
    """
    from backend.shared.logging_config import PerformanceLogger

    with PerformanceLogger("quality_metrics_calculation", logger) as perf:
        # Rasterize SVG if needed
        if rasterized_path is None:
            rasterized_path = _rasterize_svg(vectorized_path)
            cleanup_rasterized = True
        else:
            cleanup_rasterized = False

        try:
            # Calculate individual metrics
            logger.info(
                "calculating_quality_metrics",
                original=str(original_path.name),
                vectorized=str(vectorized_path.name),
            )

            ssim_score = calculate_ssim(original_path, rasterized_path)
            edge_iou = calculate_edge_iou(original_path, rasterized_path)
            color_correlation = calculate_color_correlation(original_path, rasterized_path)

            # Calculate weighted overall score (FR-032)
            overall_score = (
                WEIGHT_SSIM * ssim_score
                + WEIGHT_EDGE_IOU * edge_iou
                + WEIGHT_COLOR * color_correlation
            )

            # Check individual thresholds
            ssim_passed = check_ssim_threshold(ssim_score)
            edge_iou_passed = check_edge_threshold(edge_iou)
            color_passed = check_color_threshold(color_correlation)

            # Overall pass: all individual metrics pass AND overall score e threshold
            passed = ssim_passed and edge_iou_passed and color_passed and overall_score >= OVERALL_QUALITY_THRESHOLD

            metrics = QualityMetrics(
                ssim_score=ssim_score,
                lpips_score=0.0,  # TODO: Implement LPIPS in future iteration
                edge_iou=edge_iou,
                color_correlation=color_correlation,
                coverage_pct=100.0,  # TODO: Calculate actual coverage
                quantization_error=0.0,  # TODO: Calculate quantization error
                overall_score=overall_score,
                passed=passed,
                ssim_passed=ssim_passed,
                lpips_passed=True,  # TODO: Implement LPIPS check
                edge_iou_passed=edge_iou_passed,
                color_passed=color_passed,
                coverage_passed=True,  # TODO: Implement coverage check
            )

            logger.info(
                "quality_metrics_calculated",
                ssim=round(ssim_score, 3),
                edge_iou=round(edge_iou, 3),
                color=round(color_correlation, 3),
                overall=round(overall_score, 3),
                passed=passed,
            )

            perf.log_metric("overall_score", overall_score)
            perf.log_metric("passed", 1 if passed else 0)

            return metrics

        finally:
            # Cleanup temporary rasterized file
            if cleanup_rasterized and rasterized_path.exists():
                try:
                    rasterized_path.unlink()
                except Exception as e:
                    logger.warning(
                        "cleanup_failed",
                        file=str(rasterized_path),
                        error=str(e),
                    )


def validate_quality(
    original_path: Path,
    vectorized_path: Path,
    rasterized_path: Optional[Path] = None,
    job_id: Optional[str] = None,
) -> "ValidationReport":
    """
    Validate vectorization quality and generate report (FR-031, FR-033).

    Higher-level function that wraps calculate_overall_quality() and
    provides detailed validation report with warnings and errors.

    Args:
        original_path: Path to original raster image
        vectorized_path: Path to vectorized SVG file
        rasterized_path: Optional path to pre-rasterized SVG
        job_id: Optional job ID for tracking (auto-generated if not provided)

    Returns:
        ValidationReport with vectorization quality assessment
    """
    from backend.shared.models import ValidationReport
    import uuid

    # Generate job ID if not provided
    if job_id is None:
        job_id = f"quality_{uuid.uuid4().hex[:12]}"

    # Create report
    report = ValidationReport(
        job_id=job_id,
        original_image_path=original_path,
        overall_passed=False,  # Will be updated
    )

    try:
        metrics = calculate_overall_quality(original_path, vectorized_path, rasterized_path)

        # Set metrics
        report.vectorization_metrics = metrics
        report.vectorization_passed = metrics.passed

        # Generate warnings for failed individual metrics
        if not metrics.ssim_passed:
            report.add_warning(
                "vectorization",
                f"SSIM score {metrics.ssim_score:.3f} below threshold {SSIM_THRESHOLD} (FR-002)"
            )

        if not metrics.edge_iou_passed:
            report.add_warning(
                "vectorization",
                f"Edge IoU {metrics.edge_iou:.3f} below threshold {EDGE_IOU_THRESHOLD} (FR-003)"
            )

        if not metrics.color_passed:
            report.add_warning(
                "vectorization",
                f"Color correlation {metrics.color_correlation:.3f} below threshold {COLOR_CORRELATION_THRESHOLD} (FR-006)"
            )

        # Generate warning if overall score is marginal (between 0.75 and threshold)
        if 0.75 <= metrics.overall_score < OVERALL_QUALITY_THRESHOLD:
            report.add_warning(
                "vectorization",
                f"Overall quality score {metrics.overall_score:.3f} is marginal (threshold {OVERALL_QUALITY_THRESHOLD})"
            )

        # Generate error if overall quality fails
        if not metrics.passed:
            report.add_error(
                "vectorization",
                f"Quality validation failed: overall score {metrics.overall_score:.3f} < {OVERALL_QUALITY_THRESHOLD}"
            )

        # Update overall status
        report.overall_passed = metrics.passed

        logger.info(
            "quality_validation_complete",
            job_id=job_id,
            passed=metrics.passed,
            warnings_count=report.total_warnings,
            errors_count=report.total_errors,
        )

        return report

    except Exception as e:
        logger.error(
            "quality_validation_failed",
            job_id=job_id,
            error=str(e),
            error_type=type(e).__name__,
        )
        report.add_error("vectorization", f"Quality validation error: {str(e)}")
        report.overall_passed = False

        return report


# =============================================================================
# Helper Functions
# =============================================================================


def _rasterize_svg(svg_path: Path, dpi: int = 300) -> Path:
    """
    Rasterize SVG to PNG for quality comparison.

    Args:
        svg_path: Path to SVG file
        dpi: Dots per inch for rasterization (default 300)

    Returns:
        Path to temporary PNG file

    Raises:
        ProcessingError: If rasterization fails
    """
    try:
        # Try to use cairosvg (best quality)
        import cairosvg
        import tempfile

        # Create temporary PNG file
        temp_png = Path(tempfile.mktemp(suffix=".png", prefix="rasterized_"))

        cairosvg.svg2png(
            url=str(svg_path),
            write_to=str(temp_png),
            dpi=dpi,
        )

        logger.debug(
            "svg_rasterized",
            svg=str(svg_path.name),
            png=str(temp_png.name),
            dpi=dpi,
        )

        return temp_png

    except ImportError:
        # Fallback: Use PIL with svglib
        try:
            from svglib.svglib import svg2rlg
            from reportlab.graphics import renderPM
            import tempfile

            temp_png = Path(tempfile.mktemp(suffix=".png", prefix="rasterized_"))

            drawing = svg2rlg(str(svg_path))
            renderPM.drawToFile(drawing, str(temp_png), fmt="PNG", dpi=dpi)

            logger.debug(
                "svg_rasterized_fallback",
                svg=str(svg_path.name),
                png=str(temp_png.name),
                method="svglib",
            )

            return temp_png

        except ImportError:
            # Last resort: Use Pillow if available (lower quality)
            try:
                from PIL import Image
                import tempfile

                temp_png = Path(tempfile.mktemp(suffix=".png", prefix="rasterized_"))

                # This is very basic and may not handle complex SVGs well
                img = Image.open(svg_path)
                img.save(temp_png, "PNG", dpi=(dpi, dpi))

                logger.warning(
                    "svg_rasterized_basic",
                    svg=str(svg_path.name),
                    png=str(temp_png.name),
                    message="Using basic PIL rasterization - install cairosvg for better quality",
                )

                return temp_png

            except Exception as e:
                from backend.shared.exceptions import ProcessingError

                raise ProcessingError(
                    f"Failed to rasterize SVG: {str(e)}. "
                    "Install cairosvg or svglib for SVG rasterization support."
                )
