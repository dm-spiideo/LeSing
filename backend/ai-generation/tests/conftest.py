"""Shared test fixtures for AI Image Generation component.

This module provides common pytest fixtures used across all test types.
"""

from pathlib import Path
from typing import Any
from uuid import uuid4

import pytest

from config.settings import Settings


@pytest.fixture
def test_settings() -> Settings:
    """Provide test settings with safe defaults.

    Returns:
        Settings instance configured for testing
    """
    return Settings(
        openai_api_key="sk-test-dummy-key-for-testing",
        image_size="1024x1024",
        image_quality="standard",
        storage_path=Path("/tmp/ai-generation-test-output"),
        log_level="DEBUG",
        max_retries=3,
    )


@pytest.fixture
def mock_api_response() -> dict[str, Any]:
    """Provide a mock OpenAI API response.

    Returns:
        Dictionary mimicking OpenAI DALL-E 3 API response
    """
    return {
        "created": 1699000000,
        "data": [
            {
                "url": "https://example.com/generated-image.png",
                "revised_prompt": (
                    "A modern, minimalist name sign displaying 'SARAH' in clean, "
                    "elegant typography suitable for 3D printing"
                ),
            }
        ],
    }


@pytest.fixture
def sample_image_path(tmp_path: Path) -> Path:
    """Provide a sample image file for testing.

    Args:
        tmp_path: pytest's temporary directory fixture

    Returns:
        Path to a test image file
    """
    from PIL import Image

    # Create a simple test image
    image = Image.new("RGB", (1024, 1024), color="white")
    image_path = tmp_path / f"test_image_{uuid4().hex[:8]}.png"
    image.save(image_path, "PNG")

    return image_path


@pytest.fixture
def temp_output_dir(tmp_path: Path) -> Path:
    """Provide a temporary output directory for tests.

    Args:
        tmp_path: pytest's temporary directory fixture

    Returns:
        Path to temporary output directory
    """
    output_dir = tmp_path / "output"
    output_dir.mkdir(exist_ok=True)
    return output_dir
