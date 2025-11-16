"""Unit tests for PromptValidator.

Tests cover:
- Valid prompts (various lengths and characters)
- Empty prompts
- Too long prompts (>50 characters)
- Non-Latin characters
"""

import pytest

from src.exceptions import ValidationError
from src.validation.validator import PromptValidator


class TestPromptValidator:
    """Test suite for PromptValidator class."""

    @pytest.fixture
    def validator(self) -> PromptValidator:
        """Provide a PromptValidator instance."""
        return PromptValidator()

    def test_validate_prompt_simple_word(self, validator: PromptValidator) -> None:
        """Test validation of simple single-word prompt."""
        result = validator.validate_prompt("SARAH")
        assert result == "SARAH"

    def test_validate_prompt_multiple_words(self, validator: PromptValidator) -> None:
        """Test validation of multi-word prompt."""
        result = validator.validate_prompt("Welcome Home")
        assert result == "Welcome Home"

    def test_validate_prompt_with_punctuation(self, validator: PromptValidator) -> None:
        """Test validation of prompt with allowed punctuation."""
        result = validator.validate_prompt("The Smith's House")
        assert result == "The Smith's House"

        result = validator.validate_prompt("Hello, World!")
        assert result == "Hello, World!"

    def test_validate_prompt_with_numbers(self, validator: PromptValidator) -> None:
        """Test validation of prompt with numbers."""
        result = validator.validate_prompt("House 123")
        assert result == "House 123"

    def test_validate_prompt_max_length(self, validator: PromptValidator) -> None:
        """Test validation of prompt at maximum allowed length (50 chars)."""
        max_length_prompt = "A" * 50
        result = validator.validate_prompt(max_length_prompt)
        assert result == max_length_prompt

    def test_validate_prompt_empty_raises_error(self, validator: PromptValidator) -> None:
        """Test that empty prompt raises ValidationError."""
        with pytest.raises(ValidationError) as exc_info:
            validator.validate_prompt("")

        assert "empty" in str(exc_info.value).lower()

    def test_validate_prompt_whitespace_only_raises_error(self, validator: PromptValidator) -> None:
        """Test that whitespace-only prompt raises ValidationError."""
        with pytest.raises(ValidationError) as exc_info:
            validator.validate_prompt("   ")

        assert "empty" in str(exc_info.value).lower()

    def test_validate_prompt_too_long_raises_error(self, validator: PromptValidator) -> None:
        """Test that prompt exceeding 50 characters raises ValidationError."""
        too_long_prompt = "A" * 51
        with pytest.raises(ValidationError) as exc_info:
            validator.validate_prompt(too_long_prompt)

        assert "50" in str(exc_info.value) or "long" in str(exc_info.value).lower()

    def test_validate_prompt_non_latin_characters_raises_error(self, validator: PromptValidator) -> None:
        """Test that non-Latin characters raise ValidationError."""
        # Cyrillic characters
        with pytest.raises(ValidationError) as exc_info:
            validator.validate_prompt("Привет")

        assert "latin" in str(exc_info.value).lower() or "character" in str(exc_info.value).lower()

        # Chinese characters
        with pytest.raises(ValidationError):
            validator.validate_prompt("你好")

        # Emoji
        with pytest.raises(ValidationError):
            validator.validate_prompt("Hello 👋")

    def test_validate_prompt_strips_whitespace(self, validator: PromptValidator) -> None:
        """Test that validator strips leading/trailing whitespace."""
        result = validator.validate_prompt("  SARAH  ")
        assert result == "SARAH"

    def test_validate_prompt_preserves_internal_spaces(self, validator: PromptValidator) -> None:
        """Test that validator preserves internal spaces."""
        result = validator.validate_prompt("Welcome  Home")
        assert "  " in result  # Double space preserved
