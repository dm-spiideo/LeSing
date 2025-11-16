"""
Edge IoU (Intersection over Union) metric calculation.

Measures edge preservation accuracy requiring ≥0.75 (FR-003).

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

EDGE_IOU_THRESHOLD = 0.75  # FR-003
DEFAULT_CANNY_LOW = 50
DEFAULT_CANNY_HIGH = 150


# =============================================================================
# Edge IoU Calculation
# =============================================================================


def calculate_edge_iou(
    image1_path: Path,
    image2_path: Path,
    canny_low: int = DEFAULT_CANNY_LOW,
    canny_high: int = DEFAULT_CANNY_HIGH,
) -> float:
    """
    Calculate Intersection over Union for edge maps.

    Uses Canny edge detection to extract edges, then calculates IoU.

    Args:
        image1_path: Path to first image (original)
        image2_path: Path to second image (vectorized/rasterized)
        canny_low: Lower threshold for Canny edge detection
        canny_high: Upper threshold for Canny edge detection

    Returns:
        IoU score between 0.0 and 1.0 (1.0 = perfect overlap)
    """
    try:
        # Try to use OpenCV if available
        import cv2

        # Load images as grayscale
        img1 = cv2.imread(str(image1_path), cv2.IMREAD_GRAYSCALE)
        img2 = cv2.imread(str(image2_path), cv2.IMREAD_GRAYSCALE)

        if img1 is None or img2 is None:
            raise ValueError("Failed to load images")

        # Resize if needed
        if img1.shape != img2.shape:
            logger.warning(
                "image_shape_mismatch",
                shape1=img1.shape,
                shape2=img2.shape,
                message="Resizing to match dimensions",
            )
            img2 = cv2.resize(img2, (img1.shape[1], img1.shape[0]))

        # Detect edges using Canny
        edges1 = cv2.Canny(img1, canny_low, canny_high)
        edges2 = cv2.Canny(img2, canny_low, canny_high)

        # Calculate IoU
        iou = _calculate_iou(edges1, edges2)

        logger.info(
            "edge_iou_calculated",
            iou=round(iou, 3),
            image1=str(image1_path.name),
            image2=str(image2_path.name),
        )

        return float(iou)

    except ImportError:
        # Fallback: Use PIL-based edge detection
        logger.warning(
            "opencv_not_available",
            message="Using fallback edge detection",
        )
        return _calculate_edge_iou_fallback(image1_path, image2_path)


def _calculate_iou(edges1: np.ndarray, edges2: np.ndarray) -> float:
    """
    Calculate Intersection over Union for two binary edge maps.

    Args:
        edges1: First binary edge map
        edges2: Second binary edge map

    Returns:
        IoU score (0.0 to 1.0)
    """
    # Convert to binary (edge/no-edge)
    binary1 = (edges1 > 0).astype(np.uint8)
    binary2 = (edges2 > 0).astype(np.uint8)

    # Calculate intersection and union
    intersection = np.sum(binary1 & binary2)
    union = np.sum(binary1 | binary2)

    # Handle empty edge maps
    if union == 0:
        # Both images have no edges - consider them identical
        return 1.0 if intersection == 0 else 0.0

    iou = intersection / union
    return float(iou)


def _calculate_edge_iou_fallback(image1_path: Path, image2_path: Path) -> float:
    """
    Simplified edge IoU calculation (fallback without OpenCV).

    Uses basic gradient detection instead of Canny.
    """
    from PIL import ImageFilter

    # Load images
    img1 = Image.open(image1_path).convert("L")
    img2 = Image.open(image2_path).convert("L")

    # Resize if needed
    if img1.size != img2.size:
        img2 = img2.resize(img1.size, Image.Resampling.LANCZOS)

    # Apply edge detection filter (Find edges)
    edges1 = img1.filter(ImageFilter.FIND_EDGES)
    edges2 = img2.filter(ImageFilter.FIND_EDGES)

    # Convert to numpy arrays
    arr1 = np.array(edges1)
    arr2 = np.array(edges2)

    # Threshold to binary
    threshold = 30
    binary1 = (arr1 > threshold).astype(np.uint8)
    binary2 = (arr2 > threshold).astype(np.uint8)

    # Calculate IoU
    intersection = np.sum(binary1 & binary2)
    union = np.sum(binary1 | binary2)

    if union == 0:
        return 1.0

    iou = intersection / union
    return float(iou)


def check_edge_threshold(iou_score: float, threshold: float = EDGE_IOU_THRESHOLD) -> bool:
    """
    Check if Edge IoU meets threshold requirement (FR-003).

    Args:
        iou_score: IoU value to check
        threshold: Minimum acceptable score (default 0.75)

    Returns:
        True if score >= threshold
    """
    return iou_score >= threshold
