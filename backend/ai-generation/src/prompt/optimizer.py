"""Prompt optimization for styled image generation.

This module enhances user prompts with style-specific keywords to guide
the AI image generation towards desired aesthetic characteristics.
"""

from typing import Literal


class PromptOptimizer:
    """Optimizer for enhancing prompts with style keywords.

    Applies style-specific keywords to user prompts to guide DALL-E 3
    towards generating images with the desired aesthetic characteristics.
    """

    # Style-specific keywords for prompt enhancement
    STYLE_KEYWORDS = {
        "modern": "modern, minimalist, clean lines, sleek, contemporary",
        "classic": "classic, elegant, traditional, timeless, sophisticated",
        "playful": "playful, fun, colorful, whimsical, vibrant, rounded",
    }

    def optimize(
        self,
        prompt: str,
        style: Literal["modern", "classic", "playful"] | None = None,
    ) -> str:
        """Optimize prompt by adding style-specific keywords.

        Args:
            prompt: Original user prompt
            style: Optional design style to apply

        Returns:
            Optimized prompt with style keywords (or original if no style)
        """
        if style is None:
            return prompt

        # Get style keywords
        style_keywords = self.STYLE_KEYWORDS.get(style, "")

        if not style_keywords:
            return prompt

        # Combine original prompt with style keywords
        # Format: "A [style_keywords] name sign displaying '[prompt]'"
        optimized = (
            f"A {style_keywords} name sign displaying '{prompt}' "
            f"suitable for 3D printing with clear, readable typography"
        )

        return optimized
