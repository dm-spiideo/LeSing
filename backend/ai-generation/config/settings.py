"""Configuration management for AI Image Generation component.

This module uses pydantic-settings to load and validate configuration
from environment variables with the AI_GEN_ prefix.
"""

from pathlib import Path
from typing import Literal

from pydantic import Field, SecretStr, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables.

    All settings use the AI_GEN_ prefix in environment variables.
    Example: AI_GEN_OPENAI_API_KEY for the openai_api_key field.

    Attributes:
        openai_api_key: OpenAI API key for DALL-E 3 access
        image_size: Default image dimensions (WxH)
        image_quality: Default quality level
        storage_path: Directory path for generated images
        log_level: Logging level
        max_retries: Maximum retry attempts for failed operations
    """

    model_config = SettingsConfigDict(
        env_prefix="AI_GEN_",
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",  # Ignore extra environment variables
    )

    # OpenAI API Configuration
    openai_api_key: SecretStr = Field(
        ...,  # Required field
        description="OpenAI API key for DALL-E 3 access",
    )

    # Image Generation Settings
    image_size: Literal["1024x1024", "1792x1024", "1024x1792"] = Field(
        default="1024x1024",
        description="Default image dimensions (width x height)",
    )

    image_quality: Literal["standard", "hd"] = Field(
        default="standard",
        description="Default image quality level",
    )

    # Storage Configuration
    storage_path: Path = Field(
        default=Path("./output/generated"),
        description="Directory path for generated images (relative to component root)",
    )

    # Logging Configuration
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = Field(
        default="INFO",
        description="Logging level",
    )

    # Retry Configuration
    max_retries: int = Field(
        default=3,
        ge=0,  # Greater than or equal to 0
        le=10,  # Less than or equal to 10
        description="Maximum retry attempts for failed operations",
    )

    @field_validator("storage_path", mode="before")
    @classmethod
    def validate_storage_path(cls, v: str | Path) -> Path:
        """Ensure storage_path is a Path object.

        Args:
            v: Input value (string or Path)

        Returns:
            Path object

        Raises:
            ValueError: If path is empty or invalid
        """
        if isinstance(v, str):
            if not v.strip():
                raise ValueError("storage_path cannot be empty")
            return Path(v)
        return v

    def get_api_key(self) -> str:
        """Get the OpenAI API key as a plain string.

        Returns:
            The API key string (decrypted from SecretStr)
        """
        # Cast to str since Pydantic SecretStr.get_secret_value() returns str
        return str(self.openai_api_key.get_secret_value())

    def ensure_storage_path_exists(self) -> Path:
        """Create storage path if it doesn't exist.

        Returns:
            Absolute path to storage directory

        Raises:
            StorageError: If directory creation fails
        """
        from src.exceptions import StorageError

        try:
            absolute_path = self.storage_path.resolve()
            absolute_path.mkdir(parents=True, exist_ok=True)
            return absolute_path
        except (OSError, PermissionError) as e:
            raise StorageError(
                f"Failed to create storage directory: {self.storage_path}",
                details={"path": str(self.storage_path), "error": str(e)},
            ) from e
