"""Integration tests for styled image generation.

Tests the end-to-end flow with different styles.
"""

from pathlib import Path

import httpx
import pytest
import respx
from respx import MockRouter

from src.generator import AIImageGenerator


class TestStyledGeneration:
    """Integration tests for styled generation."""

    @pytest.fixture
    def generator(self, test_settings, temp_output_dir: Path):  # type: ignore[no-untyped-def]
        """Provide an AIImageGenerator instance."""
        test_settings.storage_path = temp_output_dir
        return AIImageGenerator(settings=test_settings)

    @respx.mock
    def test_generate_with_modern_style(
        self, generator: AIImageGenerator, respx_mock: MockRouter
    ) -> None:
        """Test generation with modern style."""
        from PIL import Image
        import io

        mock_api_response = {
            "created": 1699000000,
            "data": [
                {
                    "url": "https://example.com/modern-image.png",
                    "revised_prompt": "A modern, minimalist name sign displaying 'SARAH' in clean typography",
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
        respx_mock.get("https://example.com/modern-image.png").mock(
            return_value=httpx.Response(200, content=img_bytes.getvalue())
        )

        result = generator.generate_image("SARAH", style="modern")

        assert result.status == "success"
        assert result.metadata is not None
        assert result.metadata.original_prompt == "SARAH"
        # Optimized prompt should contain modern-related keywords
        assert "modern" in result.metadata.optimized_prompt.lower() or \
               "minimalist" in result.metadata.optimized_prompt.lower()

    @respx.mock
    def test_generate_with_classic_style(
        self, generator: AIImageGenerator, respx_mock: MockRouter
    ) -> None:
        """Test generation with classic style."""
        from PIL import Image
        import io

        mock_api_response = {
            "created": 1699000000,
            "data": [
                {
                    "url": "https://example.com/classic-image.png",
                    "revised_prompt": "A classic, elegant name sign displaying 'SARAH' in traditional typography",
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
        respx_mock.get("https://example.com/classic-image.png").mock(
            return_value=httpx.Response(200, content=img_bytes.getvalue())
        )

        result = generator.generate_image("SARAH", style="classic")

        assert result.status == "success"
        assert result.metadata is not None
        # Optimized prompt should contain classic-related keywords
        assert "classic" in result.metadata.optimized_prompt.lower() or \
               "elegant" in result.metadata.optimized_prompt.lower()

    @respx.mock
    def test_generate_with_playful_style(
        self, generator: AIImageGenerator, respx_mock: MockRouter
    ) -> None:
        """Test generation with playful style."""
        from PIL import Image
        import io

        mock_api_response = {
            "created": 1699000000,
            "data": [
                {
                    "url": "https://example.com/playful-image.png",
                    "revised_prompt": "A playful, fun name sign displaying 'SARAH' in colorful typography",
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
        respx_mock.get("https://example.com/playful-image.png").mock(
            return_value=httpx.Response(200, content=img_bytes.getvalue())
        )

        result = generator.generate_image("SARAH", style="playful")

        assert result.status == "success"
        assert result.metadata is not None
        # Optimized prompt should contain playful-related keywords
        assert "playful" in result.metadata.optimized_prompt.lower() or \
               "fun" in result.metadata.optimized_prompt.lower()

    @respx.mock
    def test_generate_without_style(
        self, generator: AIImageGenerator, respx_mock: MockRouter
    ) -> None:
        """Test generation without style (None)."""
        from PIL import Image
        import io

        mock_api_response = {
            "created": 1699000000,
            "data": [
                {
                    "url": "https://example.com/no-style-image.png",
                    "revised_prompt": "A name sign displaying 'SARAH'",
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
        respx_mock.get("https://example.com/no-style-image.png").mock(
            return_value=httpx.Response(200, content=img_bytes.getvalue())
        )

        result = generator.generate_image("SARAH")

        assert result.status == "success"
        assert result.metadata is not None
        # When no style, original and optimized should be the same or similar
        assert result.metadata.original_prompt == "SARAH"
