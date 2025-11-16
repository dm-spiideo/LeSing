"""
SSIM (Structural Similarity Index) metric calculation.

Measures structural similarity between original and vectorized images requiring ≥0.85 (FR-002).

Feature: 002-3d-model-pipeline
User Story: US2 - Automated Quality Validation
"""

from pathlib import Path

import numpy as np
from PIL import Image

from backend.shared.logging_config import get_logger

logger = get_logger(__name__)


# =============================================================================
# Constants
# =============================================================================

SSIM_THRESHOLD = 0.85  # FR-002
DEFAULT_WINDOW_SIZE = 7
DEFAULT_K1 = 0.01
DEFAULT_K2 = 0.03


# =============================================================================
# SSIM Calculation
# =============================================================================


def calculate_ssim(
    image1_path: Path,
    image2_path: Path,
    window_size: int = DEFAULT_WINDOW_SIZE,
) -> float:
    """
    Calculate Structural Similarity Index between two images.

    Args:
        image1_path: Path to first image (original)
        image2_path: Path to second image (vectorized/rasterized)
        window_size: Size of sliding window for local comparison

    Returns:
        SSIM score between 0.0 and 1.0 (1.0 = identical)
    """
    try:
        # Try to use scikit-image if available
        from skimage.metrics import structural_similarity

        # Load images
        img1 = Image.open(image1_path).convert("RGB")
        img2 = Image.open(image2_path).convert("RGB")

        # Resize if needed
        if img1.size != img2.size:
            logger.warning(
                "image_size_mismatch",
                img1_size=img1.size,
                img2_size=img2.size,
                message="Resizing to match dimensions",
            )
            img2 = img2.resize(img1.size, Image.Resampling.LANCZOS)

        # Convert to numpy arrays
        arr1 = np.array(img1)
        arr2 = np.array(img2)

        # Calculate SSIM (multichannel for RGB)
        ssim_score = structural_similarity(
            arr1,
            arr2,
            win_size=window_size,
            channel_axis=2,  # RGB channels
            data_range=255,
        )

        logger.info(
            "ssim_calculated",
            score=round(ssim_score, 3),
            image1=str(image1_path.name),
            image2=str(image2_path.name),
        )

        return float(ssim_score)

    except ImportError:
        # Fallback: Use simplified SSIM implementation
        logger.warning(
            "skimage_not_available",
            message="Using fallback SSIM calculation",
        )
        return _calculate_ssim_fallback(image1_path, image2_path)


def _calculate_ssim_fallback(image1_path: Path, image2_path: Path) -> float:
    """
    Simplified SSIM calculation (fallback when scikit-image unavailable).

    This is a basic implementation using mean squared error approximation.
    """
    # Load images
    img1 = Image.open(image1_path).convert("L")  # Convert to grayscale
    img2 = Image.open(image2_path).convert("L")

    # Resize if needed
    if img1.size != img2.size:
        img2 = img2.resize(img1.size, Image.Resampling.LANCZOS)

    # Convert to numpy
    arr1 = np.array(img1, dtype=np.float64)
    arr2 = np.array(img2, dtype=np.float64)

    # Calculate means
    mean1 = np.mean(arr1)
    mean2 = np.mean(arr2)

    # Calculate variances
    var1 = np.var(arr1)
    var2 = np.var(arr2)

    # Calculate covariance
    covar = np.mean((arr1 - mean1) * (arr2 - mean2))

    # SSIM formula (simplified)
    c1 = (DEFAULT_K1 * 255) ** 2
    c2 = (DEFAULT_K2 * 255) ** 2

    numerator = (2 * mean1 * mean2 + c1) * (2 * covar + c2)
    denominator = (mean1**2 + mean2**2 + c1) * (var1 + var2 + c2)

    if denominator == 0:
        return 1.0 if numerator == 0 else 0.0

    ssim_score = numerator / denominator

    return float(np.clip(ssim_score, 0.0, 1.0))


def check_ssim_threshold(ssim_score: float, threshold: float = SSIM_THRESHOLD) -> bool:
    """
    Check if SSIM score meets threshold requirement (FR-002).

    Args:
        ssim_score: SSIM value to check
        threshold: Minimum acceptable score (default 0.85)

    Returns:
        True if score >= threshold
    """
    return ssim_score >= threshold


def calculate_coverage_ratio(image_path: Path, background_color: tuple = (255, 255, 255)) -> float:
    """
    Calculate coverage ratio (non-background pixel ratio).

    Args:
        image_path: Path to image
        background_color: RGB tuple of background color to exclude

    Returns:
        Ratio of non-background pixels (0.0 to 1.0)
    """
    img = Image.open(image_path).convert("RGB")
    arr = np.array(img)

    # Count non-background pixels
    background_mask = np.all(arr == background_color, axis=2)
    non_background_pixels = np.sum(~background_mask)
    total_pixels = arr.shape[0] * arr.shape[1]

    coverage = non_background_pixels / total_pixels if total_pixels > 0 else 0.0

    logger.debug(
        "coverage_calculated",
        coverage=round(coverage, 3),
        non_background=non_background_pixels,
        total=total_pixels,
    )

    return float(coverage)
