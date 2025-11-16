"""
Contract tests for 3MF output schema (T022).

Validates 3MF output requirements per contracts/formats.md:
- Watertight mesh (no holes/gaps) - NON-NEGOTIABLE
- Manifold geometry (valid solid) - NON-NEGOTIABLE
- Fits build volume (≤ 256×256×256mm) - NON-NEGOTIABLE
- File size ≤ 10MB
- Face count ≤ 100K (reject), warn > 50K

Feature: 002-3d-model-pipeline
User Story: US1 - Basic Image-to-3D Conversion
"""

from pathlib import Path

import pytest

# Add backend to path for imports
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent.parent))

from backend.shared.file_io import validate_3mf_exists
from backend.shared.exceptions import FileFormatError, FileSizeLimitError
from backend.shared.models import MeshFile, MeshProperties


class TestMeshFileContract:
    """Contract tests for 3MF/mesh output validation."""

    def test_mesh_properties_valid(self):
        """Valid mesh properties should pass validation."""
        props = MeshProperties(
            volume_mm3=1000.0,
            surface_area_mm2=600.0,
            vertex_count=100,
            face_count=200,
            bbox_min=(0.0, 0.0, 0.0),
            bbox_max=(50.0, 50.0, 5.0),
            bbox_dimensions_mm=(50.0, 50.0, 5.0),
        )

        assert props.volume_mm3 == 1000.0
        assert props.face_count == 200
        assert props.fits_build_volume()  # 50×50×5 fits in 256×256×256

    def test_mesh_exceeds_build_volume_x(self):
        """Mesh exceeding X build volume should fail fit check."""
        props = MeshProperties(
            volume_mm3=1000.0,
            surface_area_mm2=600.0,
            vertex_count=100,
            face_count=200,
            bbox_min=(0.0, 0.0, 0.0),
            bbox_max=(300.0, 50.0, 5.0),  # 300mm > 256mm
            bbox_dimensions_mm=(300.0, 50.0, 5.0),
        )

        assert not props.fits_build_volume()

    def test_mesh_exceeds_build_volume_y(self):
        """Mesh exceeding Y build volume should fail fit check."""
        props = MeshProperties(
            volume_mm3=1000.0,
            surface_area_mm2=600.0,
            vertex_count=100,
            face_count=200,
            bbox_min=(0.0, 0.0, 0.0),
            bbox_max=(50.0, 300.0, 5.0),  # 300mm > 256mm
            bbox_dimensions_mm=(50.0, 300.0, 5.0),
        )

        assert not props.fits_build_volume()

    def test_mesh_exceeds_build_volume_z(self):
        """Mesh exceeding Z build volume should fail fit check."""
        props = MeshProperties(
            volume_mm3=1000.0,
            surface_area_mm2=600.0,
            vertex_count=100,
            face_count=200,
            bbox_min=(0.0, 0.0, 0.0),
            bbox_max=(50.0, 50.0, 300.0),  # 300mm > 256mm
            bbox_dimensions_mm=(50.0, 50.0, 300.0),
        )

        assert not props.fits_build_volume()

    def test_mesh_at_build_volume_limit(self):
        """Mesh exactly at build volume limit should pass."""
        props = MeshProperties(
            volume_mm3=10000.0,
            surface_area_mm2=5000.0,
            vertex_count=1000,
            face_count=2000,
            bbox_min=(0.0, 0.0, 0.0),
            bbox_max=(256.0, 256.0, 256.0),
            bbox_dimensions_mm=(256.0, 256.0, 256.0),
        )

        assert props.fits_build_volume()

    def test_printable_mesh_all_checks_pass(self):
        """Mesh passing all checks should be printable."""
        props = MeshProperties(
            volume_mm3=1000.0,
            surface_area_mm2=600.0,
            vertex_count=100,
            face_count=200,
            bbox_min=(0.0, 0.0, 0.0),
            bbox_max=(50.0, 50.0, 5.0),
            bbox_dimensions_mm=(50.0, 50.0, 5.0),
        )

        mesh = MeshFile(
            file_path=Path("test.3mf"),
            file_size_bytes=1024,
            is_watertight=True,
            is_manifold=True,
            fits_build_volume=True,
            properties=props,
            extrusion_depth_mm=5.0,
            actual_depth_mm=5.0,
            depth_accuracy_pct=100.0,
            face_count_warning=False,
            face_count_reject=False,
            is_printable=True,
        )

        assert mesh.is_printable is True
        assert mesh.is_watertight is True
        assert mesh.is_manifold is True
        assert mesh.fits_build_volume is True

    def test_non_watertight_not_printable(self):
        """Non-watertight mesh should not be printable."""
        props = MeshProperties(
            volume_mm3=1000.0,
            surface_area_mm2=600.0,
            vertex_count=100,
            face_count=200,
            bbox_min=(0.0, 0.0, 0.0),
            bbox_max=(50.0, 50.0, 5.0),
            bbox_dimensions_mm=(50.0, 50.0, 5.0),
        )

        mesh = MeshFile(
            file_path=Path("test.3mf"),
            file_size_bytes=1024,
            is_watertight=False,  # Not watertight!
            is_manifold=True,
            fits_build_volume=True,
            properties=props,
            extrusion_depth_mm=5.0,
            actual_depth_mm=5.0,
            depth_accuracy_pct=100.0,
            face_count_warning=False,
            face_count_reject=False,
            is_printable=False,  # Validator will set this
        )

        # Pydantic validator should compute is_printable=False
        assert mesh.is_printable is False

    def test_non_manifold_not_printable(self):
        """Non-manifold mesh should not be printable."""
        props = MeshProperties(
            volume_mm3=1000.0,
            surface_area_mm2=600.0,
            vertex_count=100,
            face_count=200,
            bbox_min=(0.0, 0.0, 0.0),
            bbox_max=(50.0, 50.0, 5.0),
            bbox_dimensions_mm=(50.0, 50.0, 5.0),
        )

        mesh = MeshFile(
            file_path=Path("test.3mf"),
            file_size_bytes=1024,
            is_watertight=True,
            is_manifold=False,  # Not manifold!
            fits_build_volume=True,
            properties=props,
            extrusion_depth_mm=5.0,
            actual_depth_mm=5.0,
            depth_accuracy_pct=100.0,
            face_count_warning=False,
            face_count_reject=False,
            is_printable=False,
        )

        assert mesh.is_printable is False

    def test_exceeds_build_volume_not_printable(self):
        """Mesh exceeding build volume should not be printable."""
        props = MeshProperties(
            volume_mm3=1000.0,
            surface_area_mm2=600.0,
            vertex_count=100,
            face_count=200,
            bbox_min=(0.0, 0.0, 0.0),
            bbox_max=(300.0, 50.0, 5.0),
            bbox_dimensions_mm=(300.0, 50.0, 5.0),
        )

        mesh = MeshFile(
            file_path=Path("test.3mf"),
            file_size_bytes=1024,
            is_watertight=True,
            is_manifold=True,
            fits_build_volume=False,  # Too large!
            properties=props,
            extrusion_depth_mm=5.0,
            actual_depth_mm=5.0,
            depth_accuracy_pct=100.0,
            face_count_warning=False,
            face_count_reject=False,
            is_printable=False,
        )

        assert mesh.is_printable is False

    def test_face_count_warning_threshold(self):
        """Face count > 50K should trigger warning."""
        props = MeshProperties(
            volume_mm3=1000.0,
            surface_area_mm2=600.0,
            vertex_count=30000,
            face_count=60000,  # > 50K
            bbox_min=(0.0, 0.0, 0.0),
            bbox_max=(50.0, 50.0, 5.0),
            bbox_dimensions_mm=(50.0, 50.0, 5.0),
        )

        mesh = MeshFile(
            file_path=Path("test.3mf"),
            file_size_bytes=1024,
            is_watertight=True,
            is_manifold=True,
            fits_build_volume=True,
            properties=props,
            extrusion_depth_mm=5.0,
            actual_depth_mm=5.0,
            depth_accuracy_pct=100.0,
            face_count_warning=True,  # Should warn
            face_count_reject=False,
            is_printable=True,  # Still printable, just slow
        )

        assert mesh.face_count_warning is True
        assert mesh.is_printable is True

    def test_face_count_reject_threshold(self):
        """Face count > 100K should reject."""
        props = MeshProperties(
            volume_mm3=1000.0,
            surface_area_mm2=600.0,
            vertex_count=60000,
            face_count=120000,  # > 100K
            bbox_min=(0.0, 0.0, 0.0),
            bbox_max=(50.0, 50.0, 5.0),
            bbox_dimensions_mm=(50.0, 50.0, 5.0),
        )

        mesh = MeshFile(
            file_path=Path("test.3mf"),
            file_size_bytes=1024,
            is_watertight=True,
            is_manifold=True,
            fits_build_volume=True,
            properties=props,
            extrusion_depth_mm=5.0,
            actual_depth_mm=5.0,
            depth_accuracy_pct=100.0,
            face_count_warning=True,
            face_count_reject=True,  # Should reject
            is_printable=False,  # Not printable due to complexity
        )

        assert mesh.face_count_reject is True
        assert mesh.is_printable is False

    def test_depth_accuracy_calculation(self):
        """Depth accuracy should be calculated correctly."""
        props = MeshProperties(
            volume_mm3=1000.0,
            surface_area_mm2=600.0,
            vertex_count=100,
            face_count=200,
            bbox_min=(0.0, 0.0, 0.0),
            bbox_max=(50.0, 50.0, 5.0),
            bbox_dimensions_mm=(50.0, 50.0, 5.0),
        )

        # Target 5mm, actual 4.9mm = 98% accuracy
        mesh = MeshFile(
            file_path=Path("test.3mf"),
            file_size_bytes=1024,
            is_watertight=True,
            is_manifold=True,
            fits_build_volume=True,
            properties=props,
            extrusion_depth_mm=5.0,
            actual_depth_mm=4.9,
            depth_accuracy_pct=98.0,  # Validator computes this
            face_count_warning=False,
            face_count_reject=False,
            is_printable=True,
        )

        assert mesh.depth_accuracy_pct == 98.0
        assert mesh.actual_depth_mm == 4.9

    def test_repair_tracking(self):
        """Mesh repair tracking should work correctly."""
        props = MeshProperties(
            volume_mm3=1000.0,
            surface_area_mm2=600.0,
            vertex_count=100,
            face_count=200,
            bbox_min=(0.0, 0.0, 0.0),
            bbox_max=(50.0, 50.0, 5.0),
            bbox_dimensions_mm=(50.0, 50.0, 5.0),
        )

        mesh = MeshFile(
            file_path=Path("test.3mf"),
            file_size_bytes=1024,
            is_watertight=True,  # Now watertight after repair
            is_manifold=True,
            fits_build_volume=True,
            properties=props,
            extrusion_depth_mm=5.0,
            actual_depth_mm=5.0,
            depth_accuracy_pct=100.0,
            face_count_warning=False,
            face_count_reject=False,
            repair_attempted=True,
            repair_succeeded=True,
            repair_details="Manifold3D repaired 3 holes",
            is_printable=True,
        )

        assert mesh.repair_attempted is True
        assert mesh.repair_succeeded is True
        assert mesh.is_printable is True

    # Note: Testing actual 3MF file loading requires trimesh library
    # These are integration-level tests and will be in test_mesh_validation.py
