#!/usr/bin/env python3
"""Image validation example.

This example demonstrates how to validate image quality for 3D printing suitability.
"""

from pathlib import Path

from src.generator import AIImageGenerator


def main():
    """Validate an existing image file."""
    # Initialize the generator
    generator = AIImageGenerator()

    # First, generate an image
    print("Generating a test image...")
    result = generator.generate_image("TEST")

    if result.status != "success" or not result.image_path:
        print(f"✗ Generation failed: {result.error}")
        return

    print(f"✓ Image generated: {result.image_path}\n")

    # Validate the generated image
    print("Validating image quality...")
    validation = generator.validate_image(result.image_path)

    # Display validation results
    print(f"\nValidation Results:")
    print(f"  Quality Score: {validation.quality_score:.2f}")
    print(f"  Resolution: {validation.width}x{validation.height}")
    print(f"  Format: {validation.image_format}")
    print(f"  File Size: {validation.file_size_bytes:,} bytes")
    print(f"  Resolution Met: {'✓' if validation.resolution_met else '✗'}")
    print(f"  Format Valid: {'✓' if validation.format_valid else '✗'}")
    print(f"  Overall: {'✓ PASSED' if validation.validation_passed else '✗ FAILED'}")

    # Interpret the quality score
    print(f"\nQuality Assessment:")
    if validation.quality_score >= 0.9:
        print("  Excellent - Highly suitable for 3D printing")
    elif validation.quality_score >= 0.7:
        print("  Good - Suitable for 3D printing")
    elif validation.quality_score >= 0.5:
        print("  Fair - May work for 3D printing")
    else:
        print("  Poor - Not recommended for 3D printing")

    # You can also validate any image file
    print("\n" + "=" * 50)
    print("To validate any image file, use:")
    print("  validation = generator.validate_image(Path('/path/to/image.png'))")


if __name__ == "__main__":
    main()
