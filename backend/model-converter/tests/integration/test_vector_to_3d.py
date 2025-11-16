"""
Integration test for vector→3D pipeline (T028).

Tests complete SVG→3MF conversion with validation.

Feature: 002-3d-model-pipeline
User Story: US1 - Basic Image-to-3D Conversion
"""

from pathlib import Path

import pytest

# Add backend to path for imports
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent.parent))

from backend.shared.file_io import write_svg


# This will fail until we implement the full pipeline
@pytest.mark.skip(reason="Implementation not yet created - TDD red phase")
@pytest.mark.integration
class TestVectorTo3DPipeline:
    """Integration tests for SVG→3D conversion pipeline."""

    def test_simple_svg_to_3d(self, tmp_path):
        """Simple SVG should convert to valid 3D mesh."""
        from backend.model_converter.src.converter import convert_svg_to_3d
        from backend.model_converter.src.validator import validate_mesh

        # Create SVG
        svg_path = tmp_path / "input.svg"
        svg_content = """<?xml version="1.0"?>
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100">
  <rect x="25" y="25" width="50" height="50" fill="black"/>
</svg>"""
        write_svg(svg_content, svg_path)

        # Convert to 3D
        mesh_path = tmp_path / "output.3mf"
        mesh_file = convert_svg_to_3d(svg_path, mesh_path, extrusion_depth_mm=5.0)

        # Validate mesh
        validated = validate_mesh(mesh_path)

        assert validated.is_watertight
        assert validated.is_manifold
        assert validated.is_printable
        assert validated.fits_build_volume

    def test_multiple_shapes_to_3d(self, tmp_path):
        """SVG with multiple shapes should merge into single mesh."""
        from backend.model_converter.src.converter import convert_svg_to_3d

        svg_path = tmp_path / "multi.svg"
        svg_content = """<?xml version="1.0"?>
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100">
  <rect x="10" y="10" width="30" height="30" fill="red"/>
  <circle cx="70" cy="70" r="20" fill="blue"/>
</svg>"""
        write_svg(svg_content, svg_path)

        mesh_path = tmp_path / "output.3mf"
        mesh_file = convert_svg_to_3d(svg_path, mesh_path, extrusion_depth_mm=5.0)

        assert mesh_file.properties.volume_mm3 > 0
        assert mesh_file.properties.face_count > 0

    def test_extrusion_depth_variations(self, tmp_path):
        """Different extrusion depths should produce different meshes."""
        from backend.model_converter.src.converter import convert_svg_to_3d

        svg_path = tmp_path / "test.svg"
        svg_content = """<?xml version="1.0"?>
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100">
  <rect x="40" y="40" width="20" height="20" fill="black"/>
</svg>"""
        write_svg(svg_content, svg_path)

        # Convert with 2mm depth
        mesh_2mm = tmp_path / "depth_2mm.3mf"
        result_2mm = convert_svg_to_3d(svg_path, mesh_2mm, extrusion_depth_mm=2.0)

        # Convert with 10mm depth
        mesh_10mm = tmp_path / "depth_10mm.3mf"
        result_10mm = convert_svg_to_3d(svg_path, mesh_10mm, extrusion_depth_mm=10.0)

        # Volume should scale with depth
        assert result_10mm.properties.volume_mm3 > result_2mm.properties.volume_mm3
        assert result_10mm.properties.bbox_dimensions_mm[2] > result_2mm.properties.bbox_dimensions_mm[2]

    def test_conversion_with_validation(self, tmp_path):
        """Conversion should include automatic validation."""
        from backend.model_converter.src.converter import convert_svg_to_3d
        from backend.model_converter.src.validator import validate_mesh

        svg_path = tmp_path / "test.svg"
        svg_content = """<?xml version="1.0"?>
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 50 50">
  <circle cx="25" cy="25" r="20" fill="green"/>
</svg>"""
        write_svg(svg_content, svg_path)

        mesh_path = tmp_path / "output.3mf"
        mesh_file = convert_svg_to_3d(svg_path, mesh_path, extrusion_depth_mm=5.0)

        # Validate separately
        validated = validate_mesh(mesh_path)

        # Both should agree on printability
        assert mesh_file.is_printable == validated.is_printable
        assert mesh_file.is_watertight == validated.is_watertight

    def test_complex_path_conversion(self, tmp_path):
        """Complex SVG paths should convert successfully."""
        from backend.model_converter.src.converter import convert_svg_to_3d

        svg_path = tmp_path / "complex.svg"
        svg_content = """<?xml version="1.0"?>
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100">
  <path d="M 10 10 L 50 10 L 50 50 L 10 50 Z" fill="purple"/>
  <path d="M 60 60 L 90 60 L 90 90 L 60 90 Z" fill="orange"/>
</svg>"""
        write_svg(svg_content, svg_path)

        mesh_path = tmp_path / "output.3mf"
        mesh_file = convert_svg_to_3d(svg_path, mesh_path, extrusion_depth_mm=5.0)

        assert mesh_file.properties.face_count > 0
        assert mesh_file.is_printable
