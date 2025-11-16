"""
Unit tests for mesh validator module (T025).

Tests mesh validation with:
- Watertight check (FR-013)
- Manifold check (FR-014)
- Build volume check (FR-015)
- Mesh properties calculation (FR-016)
- Face count warnings/rejection (FR-017, FR-018)

Feature: 002-3d-model-pipeline
User Story: US1 - Basic Image-to-3D Conversion
"""

from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

import pytest

# Add backend to path for imports
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent.parent))

from backend.shared.exceptions import MeshValidationError


# This will fail until we implement validator.py
@pytest.mark.skip(reason="Implementation not yet created - TDD red phase")
class TestMeshValidator:
    """Unit tests for mesh validation."""

    def test_validate_watertight_mesh(self, tmp_path):
        """Watertight mesh should pass validation."""
        from backend.model_converter.src.validator import validate_mesh

        # Mock 3MF file path (actual file handling tested in integration)
        mesh_path = tmp_path / "watertight.3mf"
        mesh_path.touch()

        result = validate_mesh(mesh_path)

        assert result.is_watertight is True
        assert result.is_printable is True

    def test_validate_manifold_mesh(self, tmp_path):
        """Manifold mesh should pass validation."""
        from backend.model_converter.src.validator import validate_mesh

        mesh_path = tmp_path / "manifold.3mf"
        mesh_path.touch()

        result = validate_mesh(mesh_path)

        assert result.is_manifold is True
        assert result.is_printable is True

    def test_non_watertight_mesh_fails(self, tmp_path):
        """Non-watertight mesh should fail validation."""
        from backend.model_converter.src.validator import validate_mesh

        mesh_path = tmp_path / "not_watertight.3mf"
        mesh_path.touch()

        # Mock trimesh to return non-watertight
        with patch("backend.model_converter.src.validator.trimesh") as mock_trimesh:
            mock_mesh = Mock()
            mock_mesh.is_watertight = False
            mock_mesh.is_volume = True
            mock_trimesh.load.return_value = mock_mesh

            result = validate_mesh(mesh_path)

            assert result.is_watertight is False
            assert result.is_printable is False

    def test_non_manifold_mesh_fails(self, tmp_path):
        """Non-manifold mesh should fail validation."""
        from backend.model_converter.src.validator import validate_mesh

        mesh_path = tmp_path / "not_manifold.3mf"
        mesh_path.touch()

        with patch("backend.model_converter.src.validator.trimesh") as mock_trimesh:
            mock_mesh = Mock()
            mock_mesh.is_watertight = True
            mock_mesh.is_volume = False  # Not manifold
            mock_trimesh.load.return_value = mock_mesh

            result = validate_mesh(mesh_path)

            assert result.is_manifold is False
            assert result.is_printable is False

    def test_mesh_within_build_volume(self, tmp_path):
        """Mesh within build volume should pass."""
        from backend.model_converter.src.validator import validate_mesh

        mesh_path = tmp_path / "fits.3mf"
        mesh_path.touch()

        with patch("backend.model_converter.src.validator.trimesh") as mock_trimesh:
            mock_mesh = Mock()
            mock_mesh.is_watertight = True
            mock_mesh.is_volume = True
            mock_mesh.bounds = [[0, 0, 0], [100, 100, 5]]  # 100×100×5mm
            mock_trimesh.load.return_value = mock_mesh

            result = validate_mesh(mesh_path)

            assert result.fits_build_volume is True
            assert result.is_printable is True

    def test_mesh_exceeds_build_volume(self, tmp_path):
        """Mesh exceeding build volume should fail."""
        from backend.model_converter.src.validator import validate_mesh

        mesh_path = tmp_path / "too_large.3mf"
        mesh_path.touch()

        with patch("backend.model_converter.src.validator.trimesh") as mock_trimesh:
            mock_mesh = Mock()
            mock_mesh.is_watertight = True
            mock_mesh.is_volume = True
            mock_mesh.bounds = [[0, 0, 0], [300, 100, 5]]  # 300mm > 256mm
            mock_trimesh.load.return_value = mock_mesh

            result = validate_mesh(mesh_path)

            assert result.fits_build_volume is False
            assert result.is_printable is False

    def test_mesh_properties_calculation(self, tmp_path):
        """Mesh properties should be calculated correctly."""
        from backend.model_converter.src.validator import validate_mesh

        mesh_path = tmp_path / "test.3mf"
        mesh_path.touch()

        with patch("backend.model_converter.src.validator.trimesh") as mock_trimesh:
            mock_mesh = Mock()
            mock_mesh.is_watertight = True
            mock_mesh.is_volume = True
            mock_mesh.bounds = [[0, 0, 0], [50, 50, 5]]
            mock_mesh.volume = 12500.0  # mm³
            mock_mesh.area = 5000.0  # mm²
            mock_mesh.vertices = [[0, 0, 0]] * 100
            mock_mesh.faces = [[0, 1, 2]] * 200
            mock_trimesh.load.return_value = mock_mesh

            result = validate_mesh(mesh_path)

            assert result.properties.volume_mm3 == 12500.0
            assert result.properties.surface_area_mm2 == 5000.0
            assert result.properties.vertex_count == 100
            assert result.properties.face_count == 200

    def test_face_count_warning_50k(self, tmp_path):
        """Face count > 50K should trigger warning."""
        from backend.model_converter.src.validator import validate_mesh

        mesh_path = tmp_path / "high_poly.3mf"
        mesh_path.touch()

        with patch("backend.model_converter.src.validator.trimesh") as mock_trimesh:
            mock_mesh = Mock()
            mock_mesh.is_watertight = True
            mock_mesh.is_volume = True
            mock_mesh.bounds = [[0, 0, 0], [50, 50, 5]]
            mock_mesh.volume = 12500.0
            mock_mesh.area = 5000.0
            mock_mesh.vertices = [[0, 0, 0]] * 30000
            mock_mesh.faces = [[0, 1, 2]] * 60000  # > 50K
            mock_trimesh.load.return_value = mock_mesh

            result = validate_mesh(mesh_path)

            assert result.face_count_warning is True
            assert result.is_printable is True  # Still printable, just slow

    def test_face_count_reject_100k(self, tmp_path):
        """Face count > 100K should reject mesh."""
        from backend.model_converter.src.validator import validate_mesh

        mesh_path = tmp_path / "very_high_poly.3mf"
        mesh_path.touch()

        with patch("backend.model_converter.src.validator.trimesh") as mock_trimesh:
            mock_mesh = Mock()
            mock_mesh.is_watertight = True
            mock_mesh.is_volume = True
            mock_mesh.bounds = [[0, 0, 0], [50, 50, 5]]
            mock_mesh.volume = 12500.0
            mock_mesh.area = 5000.0
            mock_mesh.vertices = [[0, 0, 0]] * 60000
            mock_mesh.faces = [[0, 1, 2]] * 120000  # > 100K
            mock_trimesh.load.return_value = mock_mesh

            result = validate_mesh(mesh_path)

            assert result.face_count_reject is True
            assert result.is_printable is False

    def test_bbox_dimensions_calculation(self, tmp_path):
        """Bounding box dimensions should be calculated correctly."""
        from backend.model_converter.src.validator import validate_mesh

        mesh_path = tmp_path / "test.3mf"
        mesh_path.touch()

        with patch("backend.model_converter.src.validator.trimesh") as mock_trimesh:
            mock_mesh = Mock()
            mock_mesh.is_watertight = True
            mock_mesh.is_volume = True
            mock_mesh.bounds = [[10, 20, 0], [110, 120, 5]]  # 100×100×5mm
            mock_mesh.volume = 50000.0
            mock_mesh.area = 20000.0
            mock_mesh.vertices = [[0, 0, 0]] * 100
            mock_mesh.faces = [[0, 1, 2]] * 200
            mock_trimesh.load.return_value = mock_mesh

            result = validate_mesh(mesh_path)

            dims = result.properties.bbox_dimensions_mm
            assert dims == (100.0, 100.0, 5.0)

    def test_zero_volume_mesh_rejected(self, tmp_path):
        """Mesh with zero volume should be rejected."""
        from backend.model_converter.src.validator import validate_mesh

        mesh_path = tmp_path / "zero_volume.3mf"
        mesh_path.touch()

        with patch("backend.model_converter.src.validator.trimesh") as mock_trimesh:
            mock_mesh = Mock()
            mock_mesh.is_watertight = False
            mock_mesh.is_volume = False
            mock_mesh.volume = 0.0
            mock_trimesh.load.return_value = mock_mesh

            with pytest.raises(MeshValidationError, match="zero volume|no volume"):
                validate_mesh(mesh_path)

    def test_file_not_found_raises_error(self, tmp_path):
        """Non-existent mesh file should raise error."""
        from backend.model_converter.src.validator import validate_mesh

        mesh_path = tmp_path / "nonexistent.3mf"

        with pytest.raises(Exception):  # FileFormatError
            validate_mesh(mesh_path)
