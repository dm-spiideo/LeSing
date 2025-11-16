"""AI Image Generation Component.

This package provides AI-powered text-to-image generation for name signs
using OpenAI's DALL-E 3 API.

Public API:
    - AIImageGenerator: Main class for generating images
    - ImageRequest: Request model
    - ImageResult: Result model
    - QualityValidation: Validation result model

Exceptions:
    - AIGenerationError: Base exception
    - ValidationError: Input validation errors
    - APIError: API communication errors
    - QualityError: Quality validation errors
    - StorageError: File storage errors
"""

# Import main public API components
# Note: generator.py will be created in Phase 3 (User Story 1)
# For now, we expose the models and exceptions

from .exceptions import (
    AIGenerationError,
    APIError,
    AuthenticationError,
    QualityError,
    RateLimitError,
    ServiceError,
    StorageError,
    ValidationError,
)
from .models import (
    GenerationMetadata,
    ImageRequest,
    ImageResult,
    QualityValidation,
)

__all__ = [
    # Main API (will be added when generator.py is created)
    # "AIImageGenerator",
    # Models
    "ImageRequest",
    "ImageResult",
    "QualityValidation",
    "GenerationMetadata",
    # Exceptions
    "AIGenerationError",
    "ValidationError",
    "APIError",
    "AuthenticationError",
    "RateLimitError",
    "ServiceError",
    "QualityError",
    "StorageError",
]

__version__ = "0.1.0"
