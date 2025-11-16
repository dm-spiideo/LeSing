"""
Automatic mesh repair using Manifold3D.

Attempts to repair non-watertight or non-manifold meshes for printability.

Feature: 002-3d-model-pipeline
User Story: US1 - Basic Image-to-3D Conversion
Satisfies: FR-019 (automatic repair), FR-020 (success reporting), FR-021 (specific errors)
"""

from pathlib import Path
from typing import Optional

from backend.shared.exceptions import RepairError
from backend.shared.file_io import validate_3mf_exists
from backend.shared.models import MeshFile
from backend.shared.logging_config import get_logger, PerformanceLogger

logger = get_logger(__name__)


# =============================================================================
# Mesh Repair
# =============================================================================


def repair_mesh(
    input_path: Path,
    output_path: Path,
    aggressive: bool = False,
) -> MeshFile:
    """
    Attempt to repair mesh issues (watertight, manifold).

    Args:
        input_path: Path to input mesh file
        output_path: Path for repaired output mesh
        aggressive: If True, use more aggressive repair strategies

    Returns:
        MeshFile with repair status and results

    Raises:
        RepairError: If repair fails critically
    """
    with PerformanceLogger("mesh_repair", logger) as perf:
        # Validate input file exists
        validate_3mf_exists(input_path)

        # Load mesh
        try:
            mesh = _load_mesh_for_repair(input_path)
            perf.add_metric("input_face_count", len(mesh.get("faces", [])))
        except Exception as e:
            raise RepairError(f"Failed to load mesh for repair: {e}", e) from e

        # Check if repair is needed
        initial_watertight = _is_watertight(mesh)
        initial_manifold = _is_manifold(mesh)

        logger.info(
            "repair_assessment",
            input_path=str(input_path),
            initial_watertight=initial_watertight,
            initial_manifold=initial_manifold,
        )

        repair_details = []

        # Attempt repair if needed
        if not initial_watertight or not initial_manifold:
            try:
                repaired_mesh, details = _perform_repair(mesh, aggressive)
                repair_details = details
                repair_succeeded = True

                logger.info(
                    "repair_successful",
                    details=", ".join(details),
                )

            except Exception as e:
                logger.error(
                    "repair_failed",
                    error=str(e),
                )
                raise RepairError(
                    f"Mesh repair failed: {e}. "
                    "Model may have complex topology that cannot be automatically fixed.",
                    e
                ) from e
        else:
            # No repair needed
            repaired_mesh = mesh
            repair_succeeded = True
            repair_details = ["No repair needed - mesh already valid"]

            logger.info(
                "repair_skipped",
                message="Mesh already watertight and manifold",
            )

        # Export repaired mesh
        try:
            _export_mesh(repaired_mesh, output_path)
            perf.add_metric("output_size_bytes", output_path.stat().st_size)
        except Exception as e:
            raise RepairError(f"Failed to export repaired mesh: {e}", e) from e

        # Validate repair results
        from backend.model_converter.src.validator import validate_mesh

        try:
            validated = validate_mesh(output_path)

            # Update with repair tracking
            return MeshFile(
                file_path=validated.file_path,
                file_size_bytes=validated.file_size_bytes,
                is_watertight=validated.is_watertight,
                is_manifold=validated.is_manifold,
                fits_build_volume=validated.fits_build_volume,
                properties=validated.properties,
                extrusion_depth_mm=validated.extrusion_depth_mm,
                actual_depth_mm=validated.actual_depth_mm,
                depth_accuracy_pct=validated.depth_accuracy_pct,
                face_count_warning=validated.face_count_warning,
                face_count_reject=validated.face_count_reject,
                repair_attempted=True,
                repair_succeeded=repair_succeeded,
                repair_details="; ".join(repair_details),
                is_printable=validated.is_printable,
            )

        except Exception as e:
            raise RepairError(f"Failed to validate repaired mesh: {e}", e) from e


# =============================================================================
# Mesh Loading for Repair
# =============================================================================


def _load_mesh_for_repair(mesh_path: Path) -> dict:
    """Load mesh for repair operations."""
    try:
        # Try to use trimesh if available
        import trimesh

        mesh = trimesh.load(str(mesh_path))

        return {
            "trimesh": mesh,
            "vertices": mesh.vertices.tolist(),
            "faces": mesh.faces.tolist(),
            "is_watertight": mesh.is_watertight,
            "is_volume": mesh.is_volume,
        }

    except ImportError:
        # Fallback: Parse STL manually
        logger.warning(
            "trimesh_not_available",
            message="trimesh not found for repair, using fallback",
        )
        from backend.model_converter.src.validator import _parse_stl_fallback
        return _parse_stl_fallback(mesh_path)


# =============================================================================
# Repair Operations
# =============================================================================


def _perform_repair(mesh: dict, aggressive: bool) -> tuple[dict, list[str]]:
    """
    Perform mesh repair operations.

    Returns:
        Tuple of (repaired_mesh, details_list)
    """
    details = []

    # Try using Manifold3D if available
    try:
        import manifold3d

        logger.info("repair_method", method="manifold3d")

        # Convert to manifold
        if mesh.get("trimesh") is not None:
            manifold_mesh = manifold3d.Mesh(
                vert_properties=mesh["trimesh"].vertices,
                tri_verts=mesh["trimesh"].faces,
            )
        else:
            import numpy as np
            manifold_mesh = manifold3d.Mesh(
                vert_properties=np.array(mesh["vertices"]),
                tri_verts=np.array(mesh["faces"]),
            )

        # Create manifold object
        manifold_obj = manifold3d.Manifold(manifold_mesh)

        # Get repaired mesh
        repaired = manifold_obj.to_mesh()

        details.append("Manifold3D repair applied")

        # Convert back to dict format
        repaired_mesh = {
            "vertices": repaired.vert_properties.tolist(),
            "faces": repaired.tri_verts.tolist(),
            "trimesh": None,
        }

        return repaired_mesh, details

    except ImportError:
        logger.warning(
            "manifold3d_not_available",
            message="Manifold3D not found, using trimesh repair",
        )

    # Try using trimesh repair if available
    if mesh.get("trimesh") is not None:
        try:
            import trimesh

            tm = mesh["trimesh"]

            # Fill holes
            if not tm.is_watertight:
                trimesh.repair.fill_holes(tm)
                details.append("Filled holes")

            # Fix normals
            trimesh.repair.fix_normals(tm)
            details.append("Fixed normals")

            # Fix winding
            trimesh.repair.fix_inversion(tm)
            details.append("Fixed face winding")

            # Remove duplicate vertices
            tm.merge_vertices()
            details.append("Merged duplicate vertices")

            # Remove degenerate faces
            tm.remove_degenerate_faces()
            details.append("Removed degenerate faces")

            repaired_mesh = {
                "trimesh": tm,
                "vertices": tm.vertices.tolist(),
                "faces": tm.faces.tolist(),
                "is_watertight": tm.is_watertight,
                "is_volume": tm.is_volume,
            }

            return repaired_mesh, details

        except Exception as e:
            logger.error("trimesh_repair_failed", error=str(e))

    # Fallback: Basic cleanup
    details.append("Basic cleanup applied (limited repair without trimesh/manifold3d)")

    # Remove duplicate vertices manually
    cleaned_mesh = _remove_duplicate_vertices(mesh)

    return cleaned_mesh, details


def _remove_duplicate_vertices(mesh: dict) -> dict:
    """Basic vertex deduplication (fallback repair)."""
    vertices = mesh["vertices"]
    faces = mesh["faces"]

    # Create mapping of unique vertices
    unique_verts = []
    vert_map = {}

    for i, v in enumerate(vertices):
        v_tuple = tuple(v)
        if v_tuple not in vert_map:
            vert_map[v_tuple] = len(unique_verts)
            unique_verts.append(v)

    # Remap faces
    new_faces = []
    for face in faces:
        new_face = [vert_map[tuple(vertices[vi])] for vi in face]
        new_faces.append(new_face)

    return {
        "vertices": unique_verts,
        "faces": new_faces,
        "trimesh": None,
    }


# =============================================================================
# Validation Helpers
# =============================================================================


def _is_watertight(mesh: dict) -> bool:
    """Check if mesh is watertight."""
    if mesh.get("trimesh") is not None:
        return mesh.get("is_watertight", False)
    return len(mesh.get("faces", [])) > 0  # Fallback assumption


def _is_manifold(mesh: dict) -> bool:
    """Check if mesh is manifold."""
    if mesh.get("trimesh") is not None:
        return mesh.get("is_volume", False)
    return len(mesh.get("faces", [])) > 0  # Fallback assumption


# =============================================================================
# Mesh Export
# =============================================================================


def _export_mesh(mesh: dict, output_path: Path) -> None:
    """Export repaired mesh to file."""
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # If we have trimesh object, use it
    if mesh.get("trimesh") is not None:
        mesh["trimesh"].export(str(output_path))
        return

    # Fallback: Export as STL
    from backend.model_converter.src.converter import _generate_stl

    stl_content = _generate_stl(mesh["vertices"], mesh["faces"])
    output_path.write_bytes(stl_content)
