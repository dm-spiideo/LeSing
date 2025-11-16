#!/usr/bin/env python3
"""Styled image generation example.

This example demonstrates how to generate images with different design styles.
"""

from pathlib import Path

from src.generator import AIImageGenerator


def main():
    """Generate name sign images with different styles."""
    # Initialize the generator
    generator = AIImageGenerator()

    # The name to generate
    name = "SARAH"

    # Generate images with each supported style
    styles = ["modern", "classic", "playful"]

    print(f"Generating images for '{name}' with different styles...\n")

    for style in styles:
        print(f"Generating {style} style...")
        result = generator.generate_image(name, style=style)

        if result.status == "success":
            print(f"  ✓ Success! Saved to: {result.image_path}")

            # Show the optimized prompt used
            if result.metadata:
                print(f"  Original prompt: {result.metadata.original_prompt}")
                print(f"  Optimized prompt: {result.metadata.optimized_prompt}")
        else:
            print(f"  ✗ Failed: {result.error}")

        print()

    # You can also generate without a style (uses basic prompt)
    print("Generating without style...")
    result = generator.generate_image(name)

    if result.status == "success":
        print(f"  ✓ Success! Saved to: {result.image_path}")
    else:
        print(f"  ✗ Failed: {result.error}")


if __name__ == "__main__":
    main()
