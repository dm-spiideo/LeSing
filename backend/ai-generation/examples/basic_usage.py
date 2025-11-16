#!/usr/bin/env python3
"""Basic usage example for AI Image Generator.

This example demonstrates the simplest way to generate a name sign image.
"""

from pathlib import Path

from src.generator import AIImageGenerator


def main():
    """Generate a basic name sign image."""
    # Initialize the generator
    # It will automatically load settings from environment variables
    generator = AIImageGenerator()

    # Generate an image from a simple text prompt
    print("Generating image for 'SARAH'...")
    result = generator.generate_image("SARAH")

    # Check if generation was successful
    if result.status == "success":
        print(f"✓ Success! Image saved to: {result.image_path}")

        # Access metadata
        if result.metadata:
            print(f"  Model: {result.metadata.model}")
            print(f"  Generation time: {result.metadata.generation_time_ms}ms")
            print(f"  Image size: {result.metadata.image_size}")
            print(f"  Quality score: {result.metadata.quality_validation.quality_score}")
    else:
        print(f"✗ Generation failed: {result.error}")


if __name__ == "__main__":
    main()
