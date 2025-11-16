"""Exception hierarchy for AI Image Generation component.

This module defines all custom exceptions used throughout the component,
organized in a clear hierarchy for proper error handling and reporting.
"""


class AIGenerationError(Exception):
    """Base exception for all AI generation errors.

    All custom exceptions in this component inherit from this base class,
    allowing for catch-all error handling when needed.

    Attributes:
        message: Human-readable error description
        details: Optional dict with additional error context
    """

    def __init__(self, message: str, details: dict[str, object] | None = None) -> None:
        """Initialize exception with message and optional details.

        Args:
            message: Human-readable error description
            details: Optional dictionary with additional context
        """
        self.message = message
        self.details = details or {}
        super().__init__(message)

    def __str__(self) -> str:
        """Return string representation of the exception."""
        if self.details:
            return f"{self.message} (details: {self.details})"
        return self.message


class ValidationError(AIGenerationError):
    """Raised when input validation fails.

    This exception is raised for invalid user inputs such as:
    - Empty or too-long prompts
    - Invalid style, size, or quality parameters
    - Non-Latin characters in prompts (POC limitation)

    This is a non-retryable error - the client must fix their input.
    """
    pass


class APIError(AIGenerationError):
    """Base class for all OpenAI API-related errors.

    This exception and its subclasses represent errors that occur during
    communication with the OpenAI API.
    """
    pass


class AuthenticationError(APIError):
    """Raised when API authentication fails.

    This typically indicates:
    - Missing API key
    - Invalid API key
    - Expired API key

    This is a non-retryable error - the API key must be corrected.
    """
    pass


class RateLimitError(APIError):
    """Raised when OpenAI API rate limit is exceeded.

    This error indicates the client has made too many requests too quickly.

    This is a retryable error - the request should be retried after
    a backoff period (typically 60 seconds for OpenAI).
    """
    pass


class ServiceError(APIError):
    """Raised when OpenAI service encounters an error.

    This represents server-side errors (5xx status codes) or other
    service availability issues.

    This is a retryable error - the request may succeed if retried
    after a short delay.
    """
    pass


class QualityError(AIGenerationError):
    """Raised when generated image fails quality validation.

    This exception indicates the image was generated but did not meet
    quality criteria such as:
    - Insufficient resolution (<1024x1024)
    - Invalid format (not PNG/JPEG)
    - File not readable
    - Low quality score

    This is a retryable error - regeneration with a modified prompt
    may produce better results.
    """
    pass


class StorageError(AIGenerationError):
    """Raised when file storage operations fail.

    This exception indicates errors with:
    - Creating output directories
    - Saving image files
    - Saving metadata JSON files
    - Disk space issues
    - Permission issues

    This is a non-retryable error - the storage configuration must be fixed.
    """
    pass
