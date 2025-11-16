"""Prompt validation for AI image generation.

This module provides validation logic for user prompts before they are
sent to the OpenAI API.
"""

import re

from ..exceptions import ValidationError


class PromptValidator:
    """Validator for user prompts.

    Ensures prompts meet requirements:
    - Length between 1-50 characters
    - Non-empty after stripping whitespace
    - Only Latin characters, numbers, spaces, and basic punctuation
    """

    MIN_LENGTH = 1
    MAX_LENGTH = 50

    # Regex pattern for allowed characters (Latin, numbers, spaces, basic punctuation)
    ALLOWED_PATTERN = re.compile(r'^[a-zA-Z0-9\s\-\'",!.]+$')

    def validate_prompt(self, prompt: str) -> str:
        """Validate a user prompt.

        Args:
            prompt: User's text to convert to image

        Returns:
            Validated and cleaned prompt (stripped of whitespace)

        Raises:
            ValidationError: If prompt is invalid
        """
        # Strip leading/trailing whitespace
        cleaned_prompt = prompt.strip()

        # Check if empty
        if not cleaned_prompt:
            raise ValidationError(
                "Prompt cannot be empty or whitespace only",
                details={"prompt": prompt},
            )

        # Check length
        if len(cleaned_prompt) > self.MAX_LENGTH:
            raise ValidationError(
                f"Prompt must be 50 characters or less (got {len(cleaned_prompt)})",
                details={"prompt": cleaned_prompt, "length": len(cleaned_prompt)},
            )

        # Check for only allowed characters
        if not self.ALLOWED_PATTERN.match(cleaned_prompt):
            raise ValidationError(
                "Prompt must contain only Latin characters, numbers, spaces, and basic punctuation",
                details={"prompt": cleaned_prompt},
            )

        return cleaned_prompt
