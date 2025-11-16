"""Unit tests for PromptOptimizer.

Tests cover:
- optimize method with modern/classic/playful styles
- verify style keywords added
- original text preserved
- no style (None) returns original prompt
"""

import pytest

from src.prompt.optimizer import PromptOptimizer


class TestPromptOptimizer:
    """Test suite for PromptOptimizer class."""

    @pytest.fixture
    def optimizer(self) -> PromptOptimizer:
        """Provide a PromptOptimizer instance."""
        return PromptOptimizer()

    def test_optimize_modern_style(self, optimizer: PromptOptimizer) -> None:
        """Test that modern style adds appropriate keywords."""
        result = optimizer.optimize("SARAH", style="modern")

        # Should contain modern-related keywords
        result_lower = result.lower()
        assert "modern" in result_lower or "minimalist" in result_lower or "clean" in result_lower
        # Original text should be preserved
        assert "SARAH" in result

    def test_optimize_classic_style(self, optimizer: PromptOptimizer) -> None:
        """Test that classic style adds appropriate keywords."""
        result = optimizer.optimize("Welcome Home", style="classic")

        # Should contain classic-related keywords
        result_lower = result.lower()
        assert "classic" in result_lower or "elegant" in result_lower or "traditional" in result_lower
        # Original text should be preserved
        assert "Welcome Home" in result

    def test_optimize_playful_style(self, optimizer: PromptOptimizer) -> None:
        """Test that playful style adds appropriate keywords."""
        result = optimizer.optimize("Party Time", style="playful")

        # Should contain playful-related keywords
        result_lower = result.lower()
        assert "playful" in result_lower or "fun" in result_lower or "colorful" in result_lower
        # Original text should be preserved
        assert "Party Time" in result

    def test_optimize_no_style(self, optimizer: PromptOptimizer) -> None:
        """Test that None style returns original prompt unchanged."""
        original = "SARAH"
        result = optimizer.optimize(original, style=None)

        assert result == original

    def test_optimize_preserves_original_text(self, optimizer: PromptOptimizer) -> None:
        """Test that original text is always preserved in optimized prompt."""
        prompts = ["SARAH", "The Smiths", "Welcome Home"]
        styles = ["modern", "classic", "playful"]

        for prompt in prompts:
            for style in styles:
                result = optimizer.optimize(prompt, style=style)
                assert prompt in result, f"Original text '{prompt}' not found in optimized prompt"

    def test_optimize_modern_keywords(self, optimizer: PromptOptimizer) -> None:
        """Test specific modern style keywords."""
        result = optimizer.optimize("Test", style="modern")
        result_lower = result.lower()

        # At least one of these keywords should be present
        modern_keywords = ["modern", "minimalist", "clean", "sleek", "contemporary"]
        assert any(keyword in result_lower for keyword in modern_keywords)

    def test_optimize_classic_keywords(self, optimizer: PromptOptimizer) -> None:
        """Test specific classic style keywords."""
        result = optimizer.optimize("Test", style="classic")
        result_lower = result.lower()

        # At least one of these keywords should be present
        classic_keywords = ["classic", "elegant", "traditional", "timeless", "sophisticated"]
        assert any(keyword in result_lower for keyword in classic_keywords)

    def test_optimize_playful_keywords(self, optimizer: PromptOptimizer) -> None:
        """Test specific playful style keywords."""
        result = optimizer.optimize("Test", style="playful")
        result_lower = result.lower()

        # At least one of these keywords should be present
        playful_keywords = ["playful", "fun", "colorful", "whimsical", "vibrant"]
        assert any(keyword in result_lower for keyword in playful_keywords)

    def test_optimize_returns_string(self, optimizer: PromptOptimizer) -> None:
        """Test that optimize always returns a string."""
        result = optimizer.optimize("Test", style="modern")
        assert isinstance(result, str)
        assert len(result) > 0
