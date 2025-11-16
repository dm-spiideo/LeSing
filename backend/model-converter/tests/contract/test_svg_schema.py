"""
Contract tests for SVG output schema (T021).

Validates SVG output requirements per contracts/formats.md:
- Well-formed XML with valid root element
- viewBox or dimensions defined
- Contains at least one shape/path
- File size ≤ 5MB
- Path count ≤ 1000
- Color count ≤ 8

Feature: 002-3d-model-pipeline
User Story: US1 - Basic Image-to-3D Conversion
"""

from pathlib import Path

import pytest

# Add backend to path for imports
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent.parent))

from backend.shared.file_io import load_svg, write_svg
from backend.shared.exceptions import SVGValidationError, FileSizeLimitError


class TestSVGOutputContract:
    """Contract tests for SVG output validation."""

    def test_valid_svg_with_viewbox(self, tmp_path):
        """Valid SVG with viewBox should pass validation."""
        svg_path = tmp_path / "valid.svg"
        svg_content = """<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100">
  <rect x="10" y="10" width="80" height="80" fill="black"/>
</svg>"""
        write_svg(svg_content, svg_path)

        root = load_svg(svg_path)
        assert root.tag.endswith("svg")

    def test_valid_svg_with_dimensions(self, tmp_path):
        """Valid SVG with width/height instead of viewBox should pass."""
        svg_path = tmp_path / "dimensions.svg"
        svg_content = """<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" width="100" height="100">
  <circle cx="50" cy="50" r="40" fill="red"/>
</svg>"""
        write_svg(svg_content, svg_path)

        root = load_svg(svg_path)
        assert "width" in root.attrib
        assert "height" in root.attrib

    def test_svg_with_path_element(self, tmp_path):
        """SVG with path element should be valid."""
        svg_path = tmp_path / "path.svg"
        svg_content = """<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100">
  <path d="M 10 10 L 90 90" stroke="black"/>
</svg>"""
        write_svg(svg_content, svg_path)

        root = load_svg(svg_path)
        assert root is not None

    def test_malformed_xml_rejected(self, tmp_path):
        """Malformed XML should be rejected."""
        svg_path = tmp_path / "malformed.svg"
        svg_content = """<?xml version="1.0"?>
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100">
  <rect x="10" y="10" width="80" height="80">
  <!-- Missing closing tag -->
</svg>"""
        write_svg(svg_content, svg_path)

        with pytest.raises(SVGValidationError, match="Malformed SVG XML"):
            load_svg(svg_path)

    def test_non_svg_root_rejected(self, tmp_path):
        """XML with non-SVG root should be rejected."""
        svg_path = tmp_path / "not_svg.svg"
        svg_content = """<?xml version="1.0"?>
<html>
  <body>Not an SVG</body>
</html>"""
        write_svg(svg_content, svg_path)

        with pytest.raises(SVGValidationError, match="Invalid root element"):
            load_svg(svg_path)

    def test_missing_viewbox_and_dimensions_rejected(self, tmp_path):
        """SVG without viewBox or dimensions should be rejected."""
        svg_path = tmp_path / "no_viewbox.svg"
        svg_content = """<?xml version="1.0"?>
<svg xmlns="http://www.w3.org/2000/svg">
  <rect x="10" y="10" width="80" height="80"/>
</svg>"""
        write_svg(svg_content, svg_path)

        with pytest.raises(SVGValidationError, match="missing viewBox"):
            load_svg(svg_path)

    def test_empty_svg_rejected(self, tmp_path):
        """SVG with no geometry should be rejected."""
        svg_path = tmp_path / "empty.svg"
        svg_content = """<?xml version="1.0"?>
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100">
  <!-- No shapes -->
</svg>"""
        write_svg(svg_content, svg_path)

        with pytest.raises(SVGValidationError, match="no geometry"):
            load_svg(svg_path)

    def test_file_not_found(self, tmp_path):
        """Non-existent SVG files should raise error."""
        svg_path = tmp_path / "nonexistent.svg"

        with pytest.raises(SVGValidationError, match="not found"):
            load_svg(svg_path)

    def test_empty_file_rejected(self, tmp_path):
        """Empty SVG files should be rejected."""
        svg_path = tmp_path / "empty.svg"
        svg_path.touch()

        with pytest.raises(SVGValidationError, match="empty"):
            load_svg(svg_path)

    def test_multiple_shapes_valid(self, tmp_path):
        """SVG with multiple shapes should be valid."""
        svg_path = tmp_path / "multiple.svg"
        svg_content = """<?xml version="1.0"?>
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100">
  <rect x="10" y="10" width="30" height="30" fill="red"/>
  <circle cx="70" cy="70" r="20" fill="blue"/>
  <path d="M 10 90 L 90 10" stroke="green"/>
</svg>"""
        write_svg(svg_content, svg_path)

        root = load_svg(svg_path)
        assert root is not None

    def test_svg_with_groups(self, tmp_path):
        """SVG with grouped elements should be valid."""
        svg_path = tmp_path / "groups.svg"
        svg_content = """<?xml version="1.0"?>
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100">
  <g id="shapes">
    <rect x="10" y="10" width="80" height="80" fill="black"/>
  </g>
</svg>"""
        write_svg(svg_content, svg_path)

        root = load_svg(svg_path)
        assert root is not None

    # Note: Testing 5MB file size limit and path count ≤ 1000 requires larger fixtures
    # These are better tested in integration tests with actual vectorization output
