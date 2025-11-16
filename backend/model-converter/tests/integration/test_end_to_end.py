"""
End-to-end integration test for full image→3D pipeline (T030).

Tests complete PNG/JPEG→SVG→3MF conversion with all validation stages.
This is acceptance scenario 1 from spec.md.

Feature: 002-3d-model-pipeline
User Story: US1 - Basic Image-to-3D Conversion
"""

from pathlib import Path

import pytest
from PIL import Image, ImageDraw

# Add backend to path for imports
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent.parent))


# This will fail until we implement the full pipeline
@pytest.mark.skip(reason="Implementation not yet created - TDD red phase")
@pytest.mark.integration
class TestEndToEndPipeline:
    """End-to-end integration tests for complete pipeline."""

    def test_complete_pipeline_simple_image(self, tmp_path):
        """
        Acceptance Scenario 1: Complete image→3D pipeline.

        Given an AI-generated name sign image (PNG/JPEG),
        When I submit it to the conversion pipeline,
        Then I receive a valid 3D model file (3MF format) that is:
        - Watertight (no holes)
        - Manifold (valid solid)
        - Fits within printer build volume (256×256×256mm)
        """
        from backend.model_converter.src.vectorizer import vectorize_image
        from backend.model_converter.src.converter import convert_svg_to_3d
        from backend.model_converter.src.validator import validate_mesh

        # Step 1: Create test image (simulating AI-generated name sign)
        img_path = tmp_path / "name_sign.png"
        img = Image.new("RGB", (1024, 1024), color=(255, 255, 255))
        draw = ImageDraw.Draw(img)
        # Draw simple "TEST" text as rectangles
        draw.rectangle([100, 400, 200, 600], fill=(0, 0, 0))
        draw.rectangle([250, 400, 350, 600], fill=(0, 0, 0))
        draw.rectangle([400, 400, 500, 600], fill=(0, 0, 0))
        draw.rectangle([550, 400, 650, 600], fill=(0, 0, 0))
        img.save(img_path)

        # Step 2: Vectorize image
        svg_path = tmp_path / "vectorized.svg"
        vector_file = vectorize_image(img_path, svg_path, max_colors=8)

        assert vector_file.is_valid, "SVG should be valid"
        assert vector_file.color_count <= 8, "Colors should be quantized to ≤8"
        assert vector_file.has_geometry, "SVG should have geometry"

        # Step 3: Convert SVG to 3D
        mesh_path = tmp_path / "model.3mf"
        mesh_file = convert_svg_to_3d(svg_path, mesh_path, extrusion_depth_mm=5.0)

        assert mesh_path.exists(), "3MF file should exist"
        assert mesh_file.file_size_bytes <= 10_485_760, "3MF should be ≤10MB"

        # Step 4: Validate mesh (acceptance criteria)
        validated = validate_mesh(mesh_path)

        assert validated.is_watertight, "Mesh must be watertight (FR-013)"
        assert validated.is_manifold, "Mesh must be manifold (FR-014)"
        assert validated.fits_build_volume, "Mesh must fit within 256×256×256mm (FR-015)"
        assert validated.is_printable, "Mesh must be printable"

        # Additional checks
        assert validated.properties.volume_mm3 > 0, "Mesh should have positive volume"
        assert validated.properties.face_count > 0, "Mesh should have faces"
        assert not validated.face_count_reject, "Face count should be acceptable"

    def test_pipeline_with_high_quality_image(self, tmp_path):
        """High quality input should produce high quality 3D model."""
        from backend.model_converter.src.vectorizer import vectorize_image
        from backend.model_converter.src.converter import convert_svg_to_3d

        img_path = tmp_path / "high_quality.png"
        img = Image.new("RGB", (2048, 2048), color=(255, 255, 255))
        draw = ImageDraw.Draw(img)
        draw.ellipse([500, 500, 1500, 1500], fill=(0, 0, 0))
        img.save(img_path)

        svg_path = tmp_path / "vector.svg"
        vector_file = vectorize_image(img_path, svg_path)

        mesh_path = tmp_path / "model.3mf"
        mesh_file = convert_svg_to_3d(svg_path, mesh_path, extrusion_depth_mm=5.0)

        assert mesh_file.is_printable
        assert mesh_file.depth_accuracy_pct >= 95.0

    def test_pipeline_performance_under_60_seconds(self, tmp_path):
        """
        Performance requirement (FR-041): Pipeline should complete under 60 seconds.
        """
        import time
        from backend.model_converter.src.vectorizer import vectorize_image
        from backend.model_converter.src.converter import convert_svg_to_3d
        from backend.model_converter.src.validator import validate_mesh

        img_path = tmp_path / "test.png"
        img = Image.new("RGB", (1024, 1024), color=(200, 200, 200))
        draw = ImageDraw.Draw(img)
        draw.rectangle([300, 300, 700, 700], fill=(50, 50, 50))
        img.save(img_path)

        start_time = time.time()

        # Full pipeline
        svg_path = tmp_path / "vector.svg"
        vectorize_image(img_path, svg_path)

        mesh_path = tmp_path / "model.3mf"
        convert_svg_to_3d(svg_path, mesh_path, extrusion_depth_mm=5.0)

        validate_mesh(mesh_path)

        total_time = time.time() - start_time

        # Should complete under 60 seconds (target <30s)
        assert total_time < 60.0, f"Pipeline took {total_time:.1f}s, should be <60s"
