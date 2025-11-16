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
from .generator import AIImageGenerator
from .models import (
    GenerationMetadata,
    ImageRequest,
    ImageResult,
    QualityValidation,
)

__all__ = [
    # Main API
    "AIImageGenerator",
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
