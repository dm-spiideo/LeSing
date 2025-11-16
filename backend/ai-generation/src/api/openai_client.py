"""OpenAI API client for DALL-E 3 image generation.

This module provides a wrapper around the OpenAI API for generating images
with proper error handling and retry logic.
"""

from typing import Any

import httpx
from openai import AuthenticationError as OpenAIAuthError
from openai import OpenAI
from openai import RateLimitError as OpenAIRateLimitError
from tenacity import retry, stop_after_attempt, wait_exponential

from config.settings import Settings

from ..exceptions import AuthenticationError, RateLimitError, ServiceError


class OpenAIClient:
    """Client for OpenAI DALL-E 3 API.

    Handles:
    - Image generation from prompts
    - Error handling and mapping to custom exceptions
    - Retry logic with exponential backoff
    """

    def __init__(self, api_key: str, settings: Settings) -> None:
        """Initialize OpenAI client.

        Args:
            api_key: OpenAI API key
            settings: Application settings
        """
        self.client = OpenAI(api_key=api_key)
        self.settings = settings

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=2, min=2, max=16),
        retry_error_callback=lambda retry_state: None,
    )
    def generate_image_from_prompt(self, prompt: str, size: str, quality: str) -> dict[str, Any]:
        """Generate image from prompt using DALL-E 3.

        Args:
            prompt: Text to convert to image
            size: Image dimensions (e.g., "1024x1024")
            quality: Quality level ("standard" or "hd")

        Returns:
            Dictionary with 'url' and 'revised_prompt' keys

        Raises:
            AuthenticationError: Invalid API key
            RateLimitError: Rate limit exceeded
            ServiceError: OpenAI service error
        """
        try:
            response = self.client.images.generate(
                model="dall-e-3",
                prompt=prompt,
                size=size,  # type: ignore[arg-type]
                quality=quality,  # type: ignore[arg-type]
                n=1,
            )

            # Extract result
            image_data = response.data[0]
            return {
                "url": image_data.url,
                "revised_prompt": image_data.revised_prompt or prompt,
            }

        except OpenAIAuthError as e:
            raise AuthenticationError(
                "OpenAI authentication failed - check API key",
                details={"original_error": str(e)},
            ) from e

        except OpenAIRateLimitError as e:
            raise RateLimitError(
                "OpenAI rate limit exceeded - please wait and retry",
                details={"original_error": str(e)},
            ) from e

        except httpx.HTTPStatusError as e:
            # Handle HTTP status errors from underlying httpx library
            if e.response.status_code == 401:
                raise AuthenticationError(
                    "OpenAI authentication failed - check API key",
                    details={"status_code": e.response.status_code},
                ) from e
            elif e.response.status_code == 429:
                raise RateLimitError(
                    "OpenAI rate limit exceeded - please wait and retry",
                    details={"status_code": e.response.status_code},
                ) from e
            elif e.response.status_code >= 500:
                raise ServiceError(
                    f"OpenAI service error: HTTP {e.response.status_code}",
                    details={"status_code": e.response.status_code},
                ) from e
            else:
                raise ServiceError(
                    f"OpenAI service error: {str(e)}",
                    details={"original_error": str(e)},
                ) from e

        except Exception as e:
            # Catch-all for service errors
            raise ServiceError(
                f"OpenAI service error: {str(e)}",
                details={"original_error": str(e)},
            ) from e
