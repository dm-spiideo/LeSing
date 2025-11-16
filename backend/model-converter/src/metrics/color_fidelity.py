"""
Color fidelity metric calculation using histogram correlation.

Measures color accuracy requiring ≥0.90 correlation (FR-006).

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

COLOR_CORRELATION_THRESHOLD = 0.90  # FR-006
HISTOGRAM_BINS = 256


# =============================================================================
# Color Fidelity Calculation
# =============================================================================


def calculate_color_correlation(
    image1_path: Path,
    image2_path: Path,
) -> float:
    """
    Calculate color histogram correlation between two images.

    Uses Pearson correlation coefficient on RGB histograms.

    Args:
        image1_path: Path to first image (original)
        image2_path: Path to second image (vectorized/rasterized)

    Returns:
        Correlation coefficient between -1.0 and 1.0 (1.0 = identical distribution)
    """
    # Load images as RGB
    img1 = Image.open(image1_path).convert("RGB")
    img2 = Image.open(image2_path).convert("RGB")

    # Resize if needed
    if img1.size != img2.size:
        logger.warning(
            "image_size_mismatch",
            img1_size=img1.size,
            img2_size=img2.size,
            message="Resizing for color comparison",
        )
        img2 = img2.resize(img1.size, Image.Resampling.LANCZOS)

    # Convert to numpy arrays
    arr1 = np.array(img1)
    arr2 = np.array(img2)

    # Calculate histograms for each channel
    correlations = []
    for channel in range(3):  # R, G, B
        hist1, _ = np.histogram(arr1[:, :, channel], bins=HISTOGRAM_BINS, range=(0, 256))
        hist2, _ = np.histogram(arr2[:, :, channel], bins=HISTOGRAM_BINS, range=(0, 256))

        # Normalize histograms
        hist1 = hist1.astype(np.float64) / np.sum(hist1)
        hist2 = hist2.astype(np.float64) / np.sum(hist2)

        # Calculate correlation
        correlation = np.corrcoef(hist1, hist2)[0, 1]

        # Handle NaN (occurs when histogram is constant)
        if np.isnan(correlation):
            correlation = 1.0 if np.array_equal(hist1, hist2) else 0.0

        correlations.append(correlation)

    # Average correlation across channels
    avg_correlation = float(np.mean(correlations))

    logger.info(
        "color_correlation_calculated",
        correlation=round(avg_correlation, 3),
        r_corr=round(correlations[0], 3),
        g_corr=round(correlations[1], 3),
        b_corr=round(correlations[2], 3),
        image1=str(image1_path.name),
        image2=str(image2_path.name),
    )

    return avg_correlation


def check_color_threshold(correlation: float, threshold: float = COLOR_CORRELATION_THRESHOLD) -> bool:
    """
    Check if color correlation meets threshold requirement (FR-006).

    Args:
        correlation: Correlation value to check
        threshold: Minimum acceptable correlation (default 0.90)

    Returns:
        True if correlation >= threshold
    """
    return correlation >= threshold


def calculate_quantization_error(
    original_path: Path,
    quantized_path: Path,
) -> float:
    """
    Calculate color quantization error.

    Measures how much color information was lost during quantization.

    Args:
        original_path: Path to original image (before quantization)
        quantized_path: Path to quantized image (after quantization)

    Returns:
        Quantization error between 0.0 and 1.0 (0.0 = no error)
    """
    # Load images
    img1 = Image.open(original_path).convert("RGB")
    img2 = Image.open(quantized_path).convert("RGB")

    # Resize if needed
    if img1.size != img2.size:
        img2 = img2.resize(img1.size, Image.Resampling.LANCZOS)

    # Convert to numpy arrays
    arr1 = np.array(img1, dtype=np.float64)
    arr2 = np.array(img2, dtype=np.float64)

    # Calculate mean squared error per pixel
    mse = np.mean((arr1 - arr2) ** 2)

    # Normalize to 0-1 range (max possible MSE is 255^2 = 65025)
    max_mse = 255.0 ** 2
    normalized_error = mse / max_mse

    logger.debug(
        "quantization_error_calculated",
        error=round(normalized_error, 3),
        mse=round(mse, 2),
    )

    return float(np.clip(normalized_error, 0.0, 1.0))


def extract_color_palette(image_path: Path, num_colors: int = 8) -> list[tuple]:
    """
    Extract dominant color palette from image.

    Args:
        image_path: Path to image
        num_colors: Number of colors to extract

    Returns:
        List of RGB tuples representing dominant colors
    """
    img = Image.open(image_path).convert("RGB")

    # Quantize to specified number of colors
    quantized = img.quantize(colors=num_colors)

    # Get palette
    palette = quantized.getpalette()

    # Extract RGB tuples
    colors = []
    for i in range(num_colors):
        r = palette[i * 3]
        g = palette[i * 3 + 1]
        b = palette[i * 3 + 2]
        colors.append((r, g, b))

    logger.debug(
        "palette_extracted",
        num_colors=len(colors),
        colors=[f"rgb({r},{g},{b})" for r, g, b in colors[:3]],  # Log first 3
    )

    return colors
