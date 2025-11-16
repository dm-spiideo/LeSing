"""Integration tests for basic image generation.

Tests the end-to-end flow with mocked OpenAI API using respx.
"""

from pathlib import Path

import httpx
import pytest
import respx
from respx import MockRouter

from src.generator import AIImageGenerator


class TestBasicGeneration:
    """Integration tests for basic generation flow."""

    @pytest.fixture
    def generator(self, test_settings, temp_output_dir: Path):  # type: ignore[no-untyped-def]
        """Provide an AIImageGenerator instance."""
        test_settings.storage_path = temp_output_dir
        return AIImageGenerator(settings=test_settings)

    @respx.mock
    def test_generate_image_end_to_end(
        self, generator: AIImageGenerator, respx_mock: MockRouter
    ) -> None:
        """Test complete generation flow from prompt to saved image."""
        # Mock OpenAI API response
        mock_api_response = {
            "created": 1699000000,
            "data": [
                {
                    "url": "https://example.com/generated-image.png",
                    "revised_prompt": "A modern name sign displaying 'SARAH' in clean typography",
                }
            ],
        }

        # Mock image download (return a small valid PNG)
        from PIL import Image
        import io

        test_image = Image.new("RGB", (1024, 1024), color="white")
        img_bytes = io.BytesIO()
        test_image.save(img_bytes, format="PNG")
        img_bytes.seek(0)

        respx_mock.post("https://api.openai.com/v1/images/generations").mock(
            return_value=httpx.Response(200, json=mock_api_response)
        )
        respx_mock.get("https://example.com/generated-image.png").mock(
            return_value=httpx.Response(200, content=img_bytes.getvalue())
        )

        # Generate image
        result = generator.generate_image("SARAH")

        # Verify result
        assert result.status == "success"
        assert result.image_path is not None
        assert result.image_path.exists()
        assert result.metadata is not None
        assert result.metadata.original_prompt == "SARAH"
        assert result.metadata.quality_validation is not None
        assert result.metadata.quality_validation.validation_passed is True

    @respx.mock
    def test_generate_image_with_custom_size(
        self, generator: AIImageGenerator, respx_mock: MockRouter
    ) -> None:
        """Test generation with custom image size."""
        from PIL import Image
        import io

        mock_api_response = {
            "created": 1699000000,
            "data": [
                {
                    "url": "https://example.com/image.png",
                    "revised_prompt": "A name sign",
                }
            ],
        }

        test_image = Image.new("RGB", (1792, 1024), color="white")
        img_bytes = io.BytesIO()
        test_image.save(img_bytes, format="PNG")
        img_bytes.seek(0)

        respx_mock.post("https://api.openai.com/v1/images/generations").mock(
            return_value=httpx.Response(200, json=mock_api_response)
        )
        respx_mock.get("https://example.com/image.png").mock(
            return_value=httpx.Response(200, content=img_bytes.getvalue())
        )

        result = generator.generate_image("SARAH", size="1792x1024")

        assert result.status == "success"
        assert result.metadata.image_size == "1792x1024"  # type: ignore[union-attr]

    @respx.mock
    def test_generate_image_api_failure(
        self, generator: AIImageGenerator, respx_mock: MockRouter
    ) -> None:
        """Test generation handles API failures gracefully."""
        respx_mock.post("https://api.openai.com/v1/images/generations").mock(
            return_value=httpx.Response(
                503, json={"error": {"message": "Service unavailable"}}
            )
        )

        result = generator.generate_image("SARAH")

        assert result.status == "failed"
        assert result.error is not None
        assert "service" in result.error.lower() or "503" in result.error

    @respx.mock
    def test_generate_image_invalid_prompt(
        self, generator: AIImageGenerator, respx_mock: MockRouter
    ) -> None:
        """Test generation with invalid prompt fails gracefully."""
        # Too long prompt
        too_long_prompt = "A" * 51

        result = generator.generate_image(too_long_prompt)

        assert result.status == "failed"
        assert result.error is not None
        assert "validation" in result.error.lower() or "50" in result.error

    @respx.mock
    def test_generate_image_saves_metadata(
        self, generator: AIImageGenerator, respx_mock: MockRouter, temp_output_dir: Path
    ) -> None:
        """Test that metadata JSON file is saved alongside image."""
        from PIL import Image
        import io
        import json

        mock_api_response = {
            "created": 1699000000,
            "data": [
                {
                    "url": "https://example.com/image.png",
                    "revised_prompt": "A name sign",
                }
            ],
        }

        test_image = Image.new("RGB", (1024, 1024), color="white")
        img_bytes = io.BytesIO()
        test_image.save(img_bytes, format="PNG")
        img_bytes.seek(0)

        respx_mock.post("https://api.openai.com/v1/images/generations").mock(
            return_value=httpx.Response(200, json=mock_api_response)
        )
        respx_mock.get("https://example.com/image.png").mock(
            return_value=httpx.Response(200, content=img_bytes.getvalue())
        )

        result = generator.generate_image("SARAH")

        # Check metadata file exists
        assert result.image_path is not None
        metadata_path = result.image_path.with_suffix(".json")
        assert metadata_path.exists()

        # Verify metadata content
        with open(metadata_path) as f:
            metadata = json.load(f)
        assert "original_prompt" in metadata
        assert metadata["original_prompt"] == "SARAH"
