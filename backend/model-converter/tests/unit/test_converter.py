"""
Unit tests for SVG→3D converter module (T024).

Tests Build123d extrusion with:
- Configurable depth 2-10mm (FR-008)
- 3MF export with metadata (FR-009)
- Depth accuracy validation ±5% (FR-010)

Feature: 002-3d-model-pipeline
User Story: US1 - Basic Image-to-3D Conversion
"""

from pathlib import Path
from unittest.mock import Mock, patch

import pytest

# Add backend to path for imports
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent.parent))

from backend.shared.exceptions import ConversionError


# This will fail until we implement converter.py
@pytest.mark.skip(reason="Implementation not yet created - TDD red phase")
class TestConverter:
    """Unit tests for SVG→3D conversion."""

    def test_convert_svg_to_3d(self, tmp_path):
        """Convert SVG to 3D mesh with default depth."""
        from backend.model_converter.src.converter import convert_svg_to_3d

        # Create simple SVG
        svg_path = tmp_path / "test.svg"
        svg_content = """<?xml version="1.0"?>
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100">
  <rect x="10" y="10" width="80" height="80" fill="black"/>
</svg>"""
        svg_path.write_text(svg_content)

        output_path = tmp_path / "output.3mf"
        result = convert_svg_to_3d(svg_path, output_path, extrusion_depth_mm=5.0)

        assert output_path.exists()
        assert result.file_path == output_path
        assert result.extrusion_depth_mm == 5.0

    def test_minimum_extrusion_depth(self, tmp_path):
        """Minimum extrusion depth of 2mm should work."""
        from backend.model_converter.src.converter import convert_svg_to_3d

        svg_path = tmp_path / "test.svg"
        svg_content = """<?xml version="1.0"?>
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100">
  <circle cx="50" cy="50" r="40" fill="red"/>
</svg>"""
        svg_path.write_text(svg_content)

        output_path = tmp_path / "output.3mf"
        result = convert_svg_to_3d(svg_path, output_path, extrusion_depth_mm=2.0)

        assert result.extrusion_depth_mm == 2.0
        assert 1.9 <= result.actual_depth_mm <= 2.1  # ±5% tolerance

    def test_maximum_extrusion_depth(self, tmp_path):
        """Maximum extrusion depth of 10mm should work."""
        from backend.model_converter.src.converter import convert_svg_to_3d

        svg_path = tmp_path / "test.svg"
        svg_content = """<?xml version="1.0"?>
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100">
  <path d="M 10 10 L 90 90" stroke="black" stroke-width="5"/>
</svg>"""
        svg_path.write_text(svg_content)

        output_path = tmp_path / "output.3mf"
        result = convert_svg_to_3d(svg_path, output_path, extrusion_depth_mm=10.0)

        assert result.extrusion_depth_mm == 10.0
        assert 9.5 <= result.actual_depth_mm <= 10.5  # ±5% tolerance

    def test_depth_accuracy_within_tolerance(self, tmp_path):
        """Depth accuracy should be within ±5% tolerance."""
        from backend.model_converter.src.converter import convert_svg_to_3d

        svg_path = tmp_path / "test.svg"
        svg_content = """<?xml version="1.0"?>
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100">
  <rect x="25" y="25" width="50" height="50" fill="blue"/>
</svg>"""
        svg_path.write_text(svg_content)

        output_path = tmp_path / "output.3mf"
        result = convert_svg_to_3d(svg_path, output_path, extrusion_depth_mm=5.0)

        # Depth accuracy should be ≥ 95%
        assert result.depth_accuracy_pct >= 95.0

    def test_3mf_metadata_export(self, tmp_path):
        """3MF should include metadata about source SVG."""
        from backend.model_converter.src.converter import convert_svg_to_3d

        svg_path = tmp_path / "source.svg"
        svg_content = """<?xml version="1.0"?>
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100">
  <circle cx="50" cy="50" r="30" fill="green"/>
</svg>"""
        svg_path.write_text(svg_content)

        output_path = tmp_path / "output.3mf"
        result = convert_svg_to_3d(svg_path, output_path, extrusion_depth_mm=5.0)

        # Metadata should reference source
        assert result.extrusion_depth_mm == 5.0
        assert result.file_size_bytes > 0

    def test_empty_svg_raises_error(self, tmp_path):
        """Empty SVG should raise ConversionError."""
        from backend.model_converter.src.converter import convert_svg_to_3d

        svg_path = tmp_path / "empty.svg"
        svg_content = """<?xml version="1.0"?>
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100">
  <!-- No shapes -->
</svg>"""
        svg_path.write_text(svg_content)

        output_path = tmp_path / "output.3mf"

        with pytest.raises(ConversionError):
            convert_svg_to_3d(svg_path, output_path)

    def test_malformed_svg_raises_error(self, tmp_path):
        """Malformed SVG should raise error."""
        from backend.model_converter.src.converter import convert_svg_to_3d

        svg_path = tmp_path / "malformed.svg"
        svg_path.write_text("Not valid SVG")

        output_path = tmp_path / "output.3mf"

        with pytest.raises(Exception):  # SVGValidationError or ConversionError
            convert_svg_to_3d(svg_path, output_path)

    def test_complex_svg_with_multiple_paths(self, tmp_path):
        """Complex SVG with multiple paths should convert successfully."""
        from backend.model_converter.src.converter import convert_svg_to_3d

        svg_path = tmp_path / "complex.svg"
        svg_content = """<?xml version="1.0"?>
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100">
  <rect x="10" y="10" width="30" height="30" fill="red"/>
  <circle cx="70" cy="70" r="20" fill="blue"/>
  <path d="M 10 90 L 90 10" stroke="green" stroke-width="2"/>
</svg>"""
        svg_path.write_text(svg_content)

        output_path = tmp_path / "output.3mf"
        result = convert_svg_to_3d(svg_path, output_path, extrusion_depth_mm=5.0)

        assert result.properties.face_count > 0
        assert result.properties.volume_mm3 > 0

    def test_svg_with_groups(self, tmp_path):
        """SVG with grouped elements should convert."""
        from backend.model_converter.src.converter import convert_svg_to_3d

        svg_path = tmp_path / "groups.svg"
        svg_content = """<?xml version="1.0"?>
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100">
  <g id="shapes">
    <rect x="20" y="20" width="60" height="60" fill="purple"/>
  </g>
</svg>"""
        svg_path.write_text(svg_content)

        output_path = tmp_path / "output.3mf"
        result = convert_svg_to_3d(svg_path, output_path, extrusion_depth_mm=5.0)

        assert result.properties.volume_mm3 > 0
