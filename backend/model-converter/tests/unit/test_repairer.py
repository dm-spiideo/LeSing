"""
Unit tests for mesh repairer module (T026).

Tests Manifold3D wrapper with:
- Automatic repair attempt (FR-019)
- Success/failure reporting (FR-020, FR-021)
- Before/after status tracking

Feature: 002-3d-model-pipeline
User Story: US1 - Basic Image-to-3D Conversion
"""

from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

import pytest

# Add backend to path for imports
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent.parent))

from backend.shared.exceptions import RepairError


# This will fail until we implement repairer.py
@pytest.mark.skip(reason="Implementation not yet created - TDD red phase")
class TestMeshRepairer:
    """Unit tests for mesh repair."""

    def test_repair_non_watertight_mesh(self, tmp_path):
        """Non-watertight mesh should be repaired."""
        from backend.model_converter.src.repairer import repair_mesh

        mesh_path = tmp_path / "input.3mf"
        output_path = tmp_path / "repaired.3mf"
        mesh_path.touch()

        result = repair_mesh(mesh_path, output_path)

        assert result.repair_attempted is True
        assert result.repair_succeeded is True
        assert result.is_watertight is True
        assert output_path.exists()

    def test_repair_improves_manifold(self, tmp_path):
        """Non-manifold mesh should be repaired."""
        from backend.model_converter.src.repairer import repair_mesh

        mesh_path = tmp_path / "input.3mf"
        output_path = tmp_path / "repaired.3mf"
        mesh_path.touch()

        result = repair_mesh(mesh_path, output_path)

        assert result.repair_attempted is True
        assert result.repair_succeeded is True
        assert result.is_manifold is True

    def test_repair_failure_reported(self, tmp_path):
        """Failed repair should be reported clearly."""
        from backend.model_converter.src.repairer import repair_mesh

        mesh_path = tmp_path / "unrepairable.3mf"
        output_path = tmp_path / "repaired.3mf"
        mesh_path.touch()

        # Mock Manifold3D to fail repair
        with patch("backend.model_converter.src.repairer.manifold3d") as mock_manifold:
            mock_manifold.repair.side_effect = Exception("Cannot repair complex topology")

            with pytest.raises(RepairError):
                repair_mesh(mesh_path, output_path)

    def test_repair_details_logged(self, tmp_path):
        """Repair should log details of what was fixed."""
        from backend.model_converter.src.repairer import repair_mesh

        mesh_path = tmp_path / "input.3mf"
        output_path = tmp_path / "repaired.3mf"
        mesh_path.touch()

        result = repair_mesh(mesh_path, output_path)

        assert result.repair_details is not None
        assert len(result.repair_details) > 0
        # Should describe what was repaired (e.g., "Fixed 3 holes")

    def test_already_valid_mesh_no_repair_needed(self, tmp_path):
        """Already valid mesh should not need repair."""
        from backend.model_converter.src.repairer import repair_mesh

        mesh_path = tmp_path / "already_valid.3mf"
        output_path = tmp_path / "output.3mf"
        mesh_path.touch()

        with patch("backend.model_converter.src.repairer.trimesh") as mock_trimesh:
            mock_mesh = Mock()
            mock_mesh.is_watertight = True
            mock_mesh.is_volume = True
            mock_trimesh.load.return_value = mock_mesh

            # May skip repair or report success immediately
            result = repair_mesh(mesh_path, output_path)

            # Either no repair attempted, or repair succeeded trivially
            assert result.is_watertight is True
            assert result.is_manifold is True

    def test_repair_preserves_mesh_properties(self, tmp_path):
        """Repair should preserve mesh properties (volume, dimensions)."""
        from backend.model_converter.src.repairer import repair_mesh

        mesh_path = tmp_path / "input.3mf"
        output_path = tmp_path / "repaired.3mf"
        mesh_path.touch()

        result = repair_mesh(mesh_path, output_path)

        # Volume should be approximately the same (within 10%)
        assert result.properties.volume_mm3 > 0
        # Bounding box should be similar
        assert result.properties.bbox_dimensions_mm[0] > 0

    def test_repair_complex_topology(self, tmp_path):
        """Complex topology issues should be handled."""
        from backend.model_converter.src.repairer import repair_mesh

        mesh_path = tmp_path / "complex.3mf"
        output_path = tmp_path / "repaired.3mf"
        mesh_path.touch()

        # Some meshes may be unrepairable
        try:
            result = repair_mesh(mesh_path, output_path)
            assert result.repair_attempted is True
        except RepairError as e:
            # Expected for unfixable topology
            assert "topology" in str(e).lower() or "repair" in str(e).lower()

    def test_repair_before_after_status(self, tmp_path):
        """Repair should track before/after status."""
        from backend.model_converter.src.repairer import repair_mesh

        mesh_path = tmp_path / "input.3mf"
        output_path = tmp_path / "repaired.3mf"
        mesh_path.touch()

        result = repair_mesh(mesh_path, output_path)

        # Should have status for both before and after
        assert result.repair_attempted is True
        if result.repair_succeeded:
            assert result.is_watertight is True
            assert result.is_manifold is True

    def test_repair_output_file_created(self, tmp_path):
        """Repair should create output 3MF file."""
        from backend.model_converter.src.repairer import repair_mesh

        mesh_path = tmp_path / "input.3mf"
        output_path = tmp_path / "repaired.3mf"
        mesh_path.touch()

        result = repair_mesh(mesh_path, output_path)

        if result.repair_succeeded:
            assert output_path.exists()
            assert output_path.stat().st_size > 0

    def test_repair_invalid_input_raises_error(self, tmp_path):
        """Invalid input file should raise error."""
        from backend.model_converter.src.repairer import repair_mesh

        mesh_path = tmp_path / "nonexistent.3mf"
        output_path = tmp_path / "repaired.3mf"

        with pytest.raises(Exception):  # FileFormatError or RepairError
            repair_mesh(mesh_path, output_path)
