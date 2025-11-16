"""File storage management for generated images and metadata.

This module handles saving generated images and their metadata to the local
filesystem.
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Any
from uuid import UUID

from PIL import Image

from ..exceptions import StorageError
from config.settings import Settings


class StorageManager:
    """Manager for saving generated images and metadata.

    Handles:
    - Filename generation with timestamps and request IDs
    - Image file storage
    - Metadata JSON storage
    - Directory creation
    """

    def __init__(self, settings: Settings) -> None:
        """Initialize storage manager.

        Args:
            settings: Application settings
        """
        self.settings = settings
        self.storage_path = settings.storage_path
        self.ensure_storage_path_exists()

    def ensure_storage_path_exists(self) -> None:
        """Create storage directory if it doesn't exist.

        Raises:
            StorageError: If directory creation fails
        """
        try:
            self.storage_path.mkdir(parents=True, exist_ok=True)
        except (OSError, PermissionError) as e:
            raise StorageError(
                f"Failed to create storage directory: {self.storage_path}",
                details={"path": str(self.storage_path), "error": str(e)},
            ) from e

    def generate_filename(self, request_id: UUID, prompt: str) -> str:
        """Generate unique filename for image.

        Format: YYYYMMDD_HHMMSS_<request_id_prefix>_<prompt_slug>.png

        Args:
            request_id: Unique request identifier
            prompt: User's prompt (will be slugified)

        Returns:
            Filename string
        """
        # Timestamp
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")

        # Request ID prefix (first 8 chars)
        request_id_prefix = str(request_id).replace("-", "")[:8]

        # Slugify prompt (lowercase, replace spaces with hyphens, remove special chars)
        slug = prompt.lower()
        slug = slug.replace(" ", "-")
        slug = "".join(c for c in slug if c.isalnum() or c == "-")
        slug = slug[:20]  # Limit length

        filename = f"{timestamp}_{request_id_prefix}_{slug}.png"
        return filename

    def save_image(self, image: Image.Image, request_id: UUID, prompt: str) -> Path:
        """Save generated image to storage.

        Args:
            image: PIL Image object
            request_id: Unique request identifier
            prompt: User's prompt

        Returns:
            Path to saved image file

        Raises:
            StorageError: If save operation fails
        """
        try:
            # Ensure directory exists
            self.ensure_storage_path_exists()

            # Generate filename
            filename = self.generate_filename(request_id, prompt)
            file_path = self.storage_path / filename

            # Save image
            image.save(file_path, "PNG")

            return file_path

        except (OSError, PermissionError) as e:
            raise StorageError(
                f"Failed to save image: {str(e)}",
                details={
                    "request_id": str(request_id),
                    "prompt": prompt,
                    "error": str(e),
                },
            ) from e

    def save_metadata_json(
        self, metadata: dict[str, Any], image_path: Path
    ) -> Path:
        """Save metadata JSON file alongside image.

        Args:
            metadata: Metadata dictionary to save
            image_path: Path to associated image file

        Returns:
            Path to saved metadata file

        Raises:
            StorageError: If save operation fails
        """
        try:
            # Use same filename with .json extension
            metadata_path = image_path.with_suffix(".json")

            # Save metadata
            with open(metadata_path, "w") as f:
                json.dump(metadata, f, indent=2, default=str)

            return metadata_path

        except (OSError, PermissionError) as e:
            raise StorageError(
                f"Failed to save metadata: {str(e)}",
                details={"image_path": str(image_path), "error": str(e)},
            ) from e
