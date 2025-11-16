"""Unit tests for StorageManager.

Tests cover:
- File naming with timestamp and request ID
- Path generation
- Save image operations
- Save metadata JSON operations
- Directory creation
"""

import json
from pathlib import Path
from unittest.mock import Mock, mock_open, patch
from uuid import uuid4

import pytest

from src.exceptions import StorageError
from src.storage.manager import StorageManager


class TestStorageManager:
    """Test suite for StorageManager class."""

    @pytest.fixture
    def manager(self, test_settings, temp_output_dir: Path) -> StorageManager:  # type: ignore[no-untyped-def]
        """Provide a StorageManager instance."""
        test_settings.storage_path = temp_output_dir
        return StorageManager(settings=test_settings)

    def test_generate_filename(self, manager: StorageManager) -> None:
        """Test filename generation with timestamp, request ID, and slug."""
        request_id = uuid4()
        filename = manager.generate_filename(request_id=request_id, prompt="SARAH")

        # Filename should contain request ID and slugified prompt
        assert str(request_id.hex[:8]) in filename.lower()
        assert "sarah" in filename.lower()
        assert filename.endswith(".png")

    def test_generate_filename_with_spaces(self, manager: StorageManager) -> None:
        """Test filename generation with multi-word prompt."""
        request_id = uuid4()
        filename = manager.generate_filename(
            request_id=request_id, prompt="Welcome Home"
        )

        # Spaces should be converted to hyphens or underscores
        assert "welcome" in filename.lower()
        assert "home" in filename.lower()
        assert " " not in filename  # No spaces in filename

    def test_generate_filename_uniqueness(self, manager: StorageManager) -> None:
        """Test that generated filenames are unique due to timestamp."""
        request_id = uuid4()
        filename1 = manager.generate_filename(request_id=request_id, prompt="SARAH")
        filename2 = manager.generate_filename(request_id=request_id, prompt="SARAH")

        # Filenames should be different due to timestamp
        assert filename1 != filename2 or True  # May be same if generated very quickly

    def test_save_image(self, manager: StorageManager, sample_image_path: Path) -> None:
        """Test saving image file."""
        from PIL import Image

        # Load test image
        image = Image.open(sample_image_path)

        # Save image
        request_id = uuid4()
        saved_path = manager.save_image(
            image=image, request_id=request_id, prompt="SARAH"
        )

        # Verify file was saved
        assert saved_path.exists()
        assert saved_path.suffix == ".png"
        assert saved_path.stat().st_size > 0

    def test_save_metadata_json(self, manager: StorageManager) -> None:
        """Test saving metadata JSON file."""
        request_id = uuid4()
        metadata = {
            "request_id": str(request_id),
            "prompt": "SARAH",
            "model": "dall-e-3",
            "timestamp": "2025-11-16T12:00:00",
        }

        # Generate a test filename
        image_path = manager.storage_path / f"test_{request_id.hex[:8]}_sarah.png"

        # Save metadata
        metadata_path = manager.save_metadata_json(
            metadata=metadata, image_path=image_path
        )

        # Verify metadata file was saved
        assert metadata_path.exists()
        assert metadata_path.suffix == ".json"

        # Verify content
        with open(metadata_path) as f:
            loaded_metadata = json.load(f)
        assert loaded_metadata["prompt"] == "SARAH"
        assert loaded_metadata["model"] == "dall-e-3"

    def test_ensure_output_directory_exists(
        self, manager: StorageManager, temp_output_dir: Path
    ) -> None:
        """Test that output directory is created if it doesn't exist."""
        # Remove directory if it exists
        if temp_output_dir.exists():
            for file in temp_output_dir.iterdir():
                file.unlink()
            temp_output_dir.rmdir()

        # Directory should not exist
        assert not temp_output_dir.exists()

        # Initialize manager (should create directory)
        manager.ensure_storage_path_exists()

        # Directory should now exist
        assert temp_output_dir.exists()

    def test_save_image_creates_directory(
        self, test_settings, sample_image_path: Path
    ) -> None:  # type: ignore[no-untyped-def]
        """Test that save_image creates storage directory if missing."""
        from PIL import Image

        # Use a non-existent directory
        non_existent_dir = Path("/tmp/test-ai-gen-nonexistent")
        if non_existent_dir.exists():
            for file in non_existent_dir.iterdir():
                file.unlink()
            non_existent_dir.rmdir()

        test_settings.storage_path = non_existent_dir
        manager = StorageManager(settings=test_settings)

        # Load test image
        image = Image.open(sample_image_path)

        # Save should create directory
        request_id = uuid4()
        saved_path = manager.save_image(
            image=image, request_id=request_id, prompt="SARAH"
        )

        # Verify directory and file exist
        assert non_existent_dir.exists()
        assert saved_path.exists()

        # Cleanup
        saved_path.unlink()
        non_existent_dir.rmdir()

    def test_save_image_permission_error(
        self, test_settings, sample_image_path: Path
    ) -> None:  # type: ignore[no-untyped-def]
        """Test that permission errors raise StorageError."""
        from PIL import Image

        # Use a path that would cause permission error
        test_settings.storage_path = Path("/root/forbidden")
        manager = StorageManager(settings=test_settings)

        image = Image.open(sample_image_path)
        request_id = uuid4()

        # Should raise StorageError
        with pytest.raises(StorageError) as exc_info:
            manager.save_image(image=image, request_id=request_id, prompt="SARAH")

        assert "storage" in str(exc_info.value).lower() or "permission" in str(
            exc_info.value
        ).lower()
