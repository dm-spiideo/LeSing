"""
Synthetic test image generator for automated testing.

Generates test images with known characteristics for quality validation and regression testing (FR-037).

Feature: 002-3d-model-pipeline
Usage:
    python generate_test_images.py
"""

from pathlib import Path
from typing import Tuple

from PIL import Image, ImageDraw, ImageFont

# Add backend to path for imports
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent.parent))

from backend.shared.models import TestFixture, FixtureComplexity


# =============================================================================
# Constants
# =============================================================================

OUTPUT_DIR = Path(__file__).parent / "synthetic"
BACKGROUND_COLOR = (255, 255, 255)  # White
TEXT_COLOR = (0, 0, 0)  # Black


# =============================================================================
# Image Generation
# =============================================================================


def generate_test_image(
    text: str,
    resolution: Tuple[int, int],
    line_thickness: int,
    output_path: Path,
) -> None:
    """
    Generate a synthetic test image with text.

    Args:
        text: Text to render
        resolution: (width, height) in pixels
        line_thickness: Stroke width for text
        output_path: Path to save image
    """
    width, height = resolution

    # Create image with white background
    img = Image.new("RGB", (width, height), BACKGROUND_COLOR)
    draw = ImageDraw.Draw(img)

    # Try to use a default font, fall back to default if not available
    try:
        # Try to load a TrueType font (works on most systems)
        font_size = min(width, height) // 4
        font = ImageFont.load_default()
    except Exception:
        font = ImageFont.load_default()

    # Calculate text position (center)
    # For default font, we need to estimate size
    text_width = len(text) * (font_size // 2)
    text_height = font_size
    x = (width - text_width) // 2
    y = (height - text_height) // 2

    # Draw text with outline for thickness effect
    for offset_x in range(-line_thickness, line_thickness + 1):
        for offset_y in range(-line_thickness, line_thickness + 1):
            draw.text((x + offset_x, y + offset_y), text, fill=TEXT_COLOR, font=font)

    # Save image
    output_path.parent.mkdir(parents=True, exist_ok=True)
    img.save(output_path, "PNG")
    print(f"Generated: {output_path} ({width}×{height}, line_thickness={line_thickness})")


def generate_from_fixture(fixture: TestFixture) -> Path:
    """
    Generate test image from TestFixture specification.

    Args:
        fixture: TestFixture specification

    Returns:
        Path to generated image
    """
    filename = f"{fixture.fixture_id}_{fixture.resolution_width}x{fixture.resolution_height}.png"
    output_path = OUTPUT_DIR / filename

    generate_test_image(
        text=fixture.text_content,
        resolution=(fixture.resolution_width, fixture.resolution_height),
        line_thickness=fixture.line_thickness_px,
        output_path=output_path,
    )

    return output_path


# =============================================================================
# Predefined Test Fixtures
# =============================================================================


def create_baseline_fixtures() -> list[TestFixture]:
    """
    Create baseline test fixtures for regression testing (FR-037, FR-038).

    Returns:
        List of TestFixture specifications
    """
    fixtures = []

    # 1. Simple text (baseline test case)
    fixtures.append(
        TestFixture(
            fixture_id="simple_text_TEST",
            text_content="TEST",
            resolution_width=1024,
            resolution_height=1024,
            color_count=2,
            complexity=FixtureComplexity.SIMPLE,
            line_thickness_px=5,
            path_count_estimate=40,
            is_low_resolution=False,
            is_high_resolution=False,
            is_extreme_aspect_ratio=False,
            has_thin_lines=False,
            is_high_complexity=False,
            expected_ssim_min=0.90,
            expected_edge_iou_min=0.85,
        )
    )

    # 2. Thin lines (edge case - FR-042)
    fixtures.append(
        TestFixture(
            fixture_id="thin_lines",
            text_content="THIN",
            resolution_width=1024,
            resolution_height=1024,
            color_count=2,
            complexity=FixtureComplexity.MODERATE,
            line_thickness_px=1,
            path_count_estimate=100,
            has_thin_lines=True,
            expected_ssim_min=0.75,
            expected_edge_iou_min=0.65,
        )
    )

    # 3. High resolution (edge case - FR-042)
    fixtures.append(
        TestFixture(
            fixture_id="high_res",
            text_content="HIRES",
            resolution_width=2048,
            resolution_height=2048,
            color_count=2,
            complexity=FixtureComplexity.MODERATE,
            line_thickness_px=8,
            path_count_estimate=200,
            is_high_resolution=True,
            expected_ssim_min=0.88,
            expected_edge_iou_min=0.80,
        )
    )

    # 4. Extreme aspect ratio (edge case - FR-042)
    fixtures.append(
        TestFixture(
            fixture_id="extreme_aspect",
            text_content="WIDE_SIGN",
            resolution_width=2560,
            resolution_height=256,
            color_count=2,
            complexity=FixtureComplexity.COMPLEX,
            line_thickness_px=4,
            path_count_estimate=300,
            is_extreme_aspect_ratio=True,
            expected_ssim_min=0.80,
            expected_edge_iou_min=0.70,
        )
    )

    # 5. Low resolution (edge case - FR-042)
    fixtures.append(
        TestFixture(
            fixture_id="low_res",
            text_content="LOW",
            resolution_width=512,
            resolution_height=512,
            color_count=2,
            complexity=FixtureComplexity.SIMPLE,
            line_thickness_px=3,
            path_count_estimate=50,
            is_low_resolution=True,
            expected_ssim_min=0.85,
            expected_edge_iou_min=0.75,
        )
    )

    return fixtures


# =============================================================================
# Main Generation
# =============================================================================


def main() -> None:
    """Generate all baseline test images."""
    print("Generating synthetic test images...")
    print(f"Output directory: {OUTPUT_DIR}\n")

    fixtures = create_baseline_fixtures()

    for fixture in fixtures:
        output_path = generate_from_fixture(fixture)
        # Update fixture with generated path
        fixture.model_copy(update={"generated_image_path": output_path})

    print(f"\n✓ Generated {len(fixtures)} test images")
    print(f"✓ Output: {OUTPUT_DIR}")


if __name__ == "__main__":
    main()
