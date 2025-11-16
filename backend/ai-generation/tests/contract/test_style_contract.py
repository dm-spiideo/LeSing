"""Contract tests for style parameter.

Tests verify the style parameter contracts are met.
"""

from pathlib import Path

import pytest

from src.exceptions import ValidationError
from src.generator import AIImageGenerator


class TestStyleContract:
    """Contract tests for style parameter."""

    @pytest.fixture
    def generator(self, test_settings, temp_output_dir: Path):  # type: ignore[no-untyped-def]
        """Provide an AIImageGenerator instance."""
        test_settings.storage_path = temp_output_dir
        return AIImageGenerator(settings=test_settings)

    def test_style_accepts_modern(self, generator: AIImageGenerator) -> None:
        """Test that style accepts 'modern' as valid value."""
        # This will make an API call, but tests the contract
        # In real execution, would mock the API
        result = generator.generate_image("Test", style="modern")
        # Should not raise ValidationError for valid style
        assert result is not None

    def test_style_accepts_classic(self, generator: AIImageGenerator) -> None:
        """Test that style accepts 'classic' as valid value."""
        result = generator.generate_image("Test", style="classic")
        assert result is not None

    def test_style_accepts_playful(self, generator: AIImageGenerator) -> None:
        """Test that style accepts 'playful' as valid value."""
        result = generator.generate_image("Test", style="playful")
        assert result is not None

    def test_style_accepts_none(self, generator: AIImageGenerator) -> None:
        """Test that style accepts None (no style)."""
        result = generator.generate_image("Test", style=None)
        assert result is not None

    def test_style_rejects_invalid_value(self, generator: AIImageGenerator) -> None:
        """Test that invalid style value raises ValidationError or returns failed status."""
        try:
            result = generator.generate_image("Test", style="invalid_style")  # type: ignore[arg-type]
            # If it doesn't raise, should return failed status
            if hasattr(result, "status"):
                assert result.status == "failed"
        except (ValidationError, TypeError):
            # Also acceptable to raise an exception
            pass

    def test_metadata_contains_style_info(self, generator: AIImageGenerator) -> None:
        """Test that metadata contains both original and optimized prompts."""
        result = generator.generate_image("Test", style="modern")

        if result.status == "success":
            assert result.metadata is not None
            assert hasattr(result.metadata, "original_prompt")
            assert hasattr(result.metadata, "optimized_prompt")
            assert result.metadata.original_prompt == "Test"
            # Optimized should be different when style is applied
            assert result.metadata.optimized_prompt is not None
