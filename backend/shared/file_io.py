"""
File I/O utilities for 3D Model Pipeline.

Provides safe file handling for images, SVG, 3MF, and G-code files with validation.

Feature: 002-3d-model-pipeline
"""

import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Any

from PIL import Image

from backend.shared.exceptions import (
    FileSizeLimitError,
    FileFormatError,
    ImageValidationError,
    SVGValidationError,
)


# =============================================================================
# Constants
# =============================================================================

MAX_IMAGE_SIZE_BYTES = 20 * 1024 * 1024  # 20MB
MAX_SVG_SIZE_BYTES = 5 * 1024 * 1024  # 5MB
MAX_3MF_SIZE_BYTES = 10 * 1024 * 1024  # 10MB

SUPPORTED_IMAGE_FORMATS = {".png", ".jpg", ".jpeg"}
MIN_IMAGE_RESOLUTION = 512


# =============================================================================
# Image Loading
# =============================================================================


def load_image(image_path: Path) -> Image.Image:
    """
    Load and validate image file (FR-043).

    Args:
        image_path: Path to PNG/JPEG image

    Returns:
        PIL Image object

    Raises:
        ImageValidationError: If image is invalid or corrupted
        FileSizeLimitError: If image exceeds size limit
    """
    # Check file exists
    if not image_path.exists():
        raise ImageValidationError(f"Image file not found: {image_path}")

    # Check file size
    file_size = image_path.stat().st_size
    if file_size > MAX_IMAGE_SIZE_BYTES:
        raise FileSizeLimitError("Image", file_size, MAX_IMAGE_SIZE_BYTES)

    if file_size == 0:
        raise ImageValidationError(f"Image file is empty: {image_path}")

    # Check file extension
    if image_path.suffix.lower() not in SUPPORTED_IMAGE_FORMATS:
        raise ImageValidationError(
            f"Unsupported image format: {image_path.suffix}. "
            f"Supported formats: {', '.join(SUPPORTED_IMAGE_FORMATS)}"
        )

    # Load image
    try:
        img = Image.open(image_path)
        img.load()  # Force loading to catch corrupted files
    except Exception as e:
        raise ImageValidationError(f"Failed to load image: {e}") from e

    # Validate image mode (RGB required)
    if img.mode not in ("RGB", "RGBA"):
        try:
            img = img.convert("RGB")
        except Exception as e:
            raise ImageValidationError(f"Failed to convert image to RGB: {e}") from e

    # Validate resolution
    width, height = img.size
    if width < MIN_IMAGE_RESOLUTION or height < MIN_IMAGE_RESOLUTION:
        raise ImageValidationError(
            f"Image resolution ({width}×{height}) below minimum "
            f"({MIN_IMAGE_RESOLUTION}×{MIN_IMAGE_RESOLUTION})"
        )

    return img


def save_image(image: Image.Image, output_path: Path, format: str = "PNG") -> None:
    """
    Save image to file.

    Args:
        image: PIL Image object
        output_path: Destination path
        format: Image format (PNG or JPEG)
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    image.save(output_path, format=format)


# =============================================================================
# SVG Loading & Validation
# =============================================================================


def load_svg(svg_path: Path) -> ET.Element:
    """
    Load and validate SVG file structure (FR-004, FR-044, FR-045).

    Args:
        svg_path: Path to SVG file

    Returns:
        XML Element tree root

    Raises:
        SVGValidationError: If SVG is malformed or invalid
        FileSizeLimitError: If SVG exceeds size limit
    """
    # Check file exists
    if not svg_path.exists():
        raise SVGValidationError(f"SVG file not found: {svg_path}")

    # Check file size
    file_size = svg_path.stat().st_size
    if file_size > MAX_SVG_SIZE_BYTES:
        raise FileSizeLimitError("SVG", file_size, MAX_SVG_SIZE_BYTES)

    if file_size == 0:
        raise SVGValidationError(f"SVG file is empty: {svg_path}")

    # Parse XML
    try:
        tree = ET.parse(svg_path)
        root = tree.getroot()
    except ET.ParseError as e:
        raise SVGValidationError(f"Malformed SVG XML: {e}") from e
    except Exception as e:
        raise SVGValidationError(f"Failed to parse SVG: {e}") from e

    # Validate root element is SVG
    if not root.tag.endswith("svg"):
        raise SVGValidationError(f"Invalid root element: {root.tag}. Expected 'svg'.")

    # Check for viewBox or dimensions
    has_viewbox = "viewBox" in root.attrib
    has_dimensions = "width" in root.attrib and "height" in root.attrib
    if not (has_viewbox or has_dimensions):
        raise SVGValidationError("SVG missing viewBox or width/height attributes")

    # Check for geometry (at least one shape/path)
    # Common SVG shape tags
    shape_tags = {
        "{http://www.w3.org/2000/svg}path",
        "{http://www.w3.org/2000/svg}rect",
        "{http://www.w3.org/2000/svg}circle",
        "{http://www.w3.org/2000/svg}ellipse",
        "{http://www.w3.org/2000/svg}line",
        "{http://www.w3.org/2000/svg}polyline",
        "{http://www.w3.org/2000/svg}polygon",
        "path",
        "rect",
        "circle",
        "ellipse",
        "line",
        "polyline",
        "polygon",
    }

    has_geometry = False
    for element in root.iter():
        if element.tag in shape_tags:
            has_geometry = True
            break

    if not has_geometry:
        raise SVGValidationError("SVG contains no geometry (no shapes or paths)")

    return root


def read_svg_text(svg_path: Path) -> str:
    """
    Read SVG file as raw text.

    Args:
        svg_path: Path to SVG file

    Returns:
        SVG content as string
    """
    if not svg_path.exists():
        raise FileNotFoundError(f"SVG file not found: {svg_path}")

    return svg_path.read_text(encoding="utf-8")


def write_svg(svg_content: str, output_path: Path) -> None:
    """
    Write SVG content to file.

    Args:
        svg_content: SVG XML as string
        output_path: Destination path
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(svg_content, encoding="utf-8")


# =============================================================================
# 3MF Loading
# =============================================================================


def validate_3mf_exists(mesh_path: Path) -> None:
    """
    Validate 3MF file exists and is not empty.

    Args:
        mesh_path: Path to 3MF file

    Raises:
        FileFormatError: If file is missing or invalid
        FileSizeLimitError: If file exceeds size limit
    """
    if not mesh_path.exists():
        raise FileFormatError(f"3MF file not found: {mesh_path}")

    file_size = mesh_path.stat().st_size
    if file_size > MAX_3MF_SIZE_BYTES:
        raise FileSizeLimitError("3MF", file_size, MAX_3MF_SIZE_BYTES)

    if file_size == 0:
        raise FileFormatError(f"3MF file is empty: {mesh_path}")


# =============================================================================
# G-code Loading & Validation
# =============================================================================


def read_gcode(gcode_path: Path) -> str:
    """
    Read G-code file as text.

    Args:
        gcode_path: Path to G-code file

    Returns:
        G-code content as string

    Raises:
        FileFormatError: If file is missing or invalid
    """
    if not gcode_path.exists():
        raise FileFormatError(f"G-code file not found: {gcode_path}")

    file_size = gcode_path.stat().st_size
    if file_size == 0:
        raise FileFormatError(f"G-code file is empty: {gcode_path}")

    return gcode_path.read_text(encoding="utf-8")


def validate_gcode(gcode_content: str) -> tuple[bool, bool]:
    """
    Validate G-code structure (FR-030).

    Args:
        gcode_content: G-code as string

    Returns:
        Tuple of (is_valid, has_temperature_commands)
    """
    if not gcode_content or len(gcode_content.strip()) == 0:
        return False, False

    # Check for temperature commands (M104 = nozzle, M140 = bed)
    has_temp_commands = "M104" in gcode_content or "M140" in gcode_content

    return True, has_temp_commands


def write_gcode(gcode_content: str, output_path: Path) -> None:
    """
    Write G-code content to file.

    Args:
        gcode_content: G-code as string
        output_path: Destination path
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(gcode_content, encoding="utf-8")


# =============================================================================
# Path Safety
# =============================================================================


def ensure_directory(directory: Path) -> None:
    """
    Ensure directory exists, create if needed.

    Args:
        directory: Directory path
    """
    directory.mkdir(parents=True, exist_ok=True)


def sanitize_filename(filename: str) -> str:
    """
    Sanitize filename to prevent directory traversal.

    Args:
        filename: Raw filename

    Returns:
        Safe filename
    """
    # Remove path separators and dangerous characters
    safe = filename.replace("/", "_").replace("\\", "_").replace("..", "_")
    # Limit length
    if len(safe) > 255:
        safe = safe[:255]
    return safe
