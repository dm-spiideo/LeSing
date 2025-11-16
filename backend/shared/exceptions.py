"""
Custom exception hierarchy for 3D Model Pipeline.

Provides clear error types for different failure modes per FR-048 (clear error messages
distinguishing between user-fixable and system issues).

Feature: 002-3d-model-pipeline
"""


class PipelineError(Exception):
    """Base exception for all pipeline errors."""

    pass


# =============================================================================
# Input Validation Errors (User-Fixable)
# =============================================================================


class ValidationError(PipelineError):
    """Raised when input validation fails (user can fix by providing better input)."""

    def __init__(self, message: str, field: str | None = None):
        self.field = field
        super().__init__(message)


class FileFormatError(ValidationError):
    """Raised when file format is invalid or corrupted."""

    pass


class ImageValidationError(FileFormatError):
    """Raised when input image fails validation (FR-043)."""

    pass


class SVGValidationError(FileFormatError):
    """Raised when SVG structure is invalid (FR-044, FR-045)."""

    pass


class MeshValidationError(ValidationError):
    """Raised when mesh validation fails (watertight, manifold, build volume)."""

    pass


# =============================================================================
# Processing Errors (System Issues)
# =============================================================================


class ProcessingError(PipelineError):
    """Base class for processing failures (system-level issues)."""

    pass


class VectorizationError(ProcessingError):
    """Raised when image vectorization fails."""

    pass


class ConversionError(ProcessingError):
    """Raised when SVG→3D conversion fails."""

    pass


class RepairError(ProcessingError):
    """Raised when mesh repair fails (FR-020, FR-021)."""

    def __init__(self, message: str, original_error: Exception | None = None):
        self.original_error = original_error
        super().__init__(message)


class SlicingError(ProcessingError):
    """Raised when G-code generation fails."""

    pass


# =============================================================================
# Resource Errors
# =============================================================================


class TimeoutError(PipelineError):
    """Raised when operation exceeds timeout (FR-046)."""

    def __init__(self, operation: str, timeout_seconds: int):
        self.operation = operation
        self.timeout_seconds = timeout_seconds
        super().__init__(f"{operation} exceeded timeout of {timeout_seconds} seconds")


class FileSizeLimitError(ValidationError):
    """Raised when file exceeds size limits."""

    def __init__(self, file_type: str, size_bytes: int, limit_bytes: int):
        self.file_type = file_type
        self.size_bytes = size_bytes
        self.limit_bytes = limit_bytes
        super().__init__(
            f"{file_type} file size ({size_bytes:,} bytes) exceeds limit ({limit_bytes:,} bytes)"
        )


class ComplexityLimitError(ValidationError):
    """Raised when complexity exceeds limits (path count, face count)."""

    def __init__(self, metric: str, value: int, limit: int):
        self.metric = metric
        self.value = value
        self.limit = limit
        super().__init__(f"{metric} ({value:,}) exceeds limit ({limit:,})")


# =============================================================================
# Configuration Errors
# =============================================================================


class ConfigurationError(PipelineError):
    """Raised when configuration is missing or invalid."""

    pass


class ProfileNotFoundError(ConfigurationError):
    """Raised when printer or material profile is not found."""

    def __init__(self, profile_type: str, profile_name: str, available_profiles: list[str]):
        self.profile_type = profile_type
        self.profile_name = profile_name
        self.available_profiles = available_profiles
        super().__init__(
            f"{profile_type} profile '{profile_name}' not found. "
            f"Available profiles: {', '.join(available_profiles)}"
        )


# =============================================================================
# Utility Functions
# =============================================================================


def is_user_fixable_error(error: Exception) -> bool:
    """
    Determine if error is user-fixable or system issue (FR-048).

    User-fixable: ValidationError, FileFormatError, etc.
    System issue: ProcessingError, TimeoutError, etc.
    """
    return isinstance(error, (ValidationError, ConfigurationError))


def format_error_message(error: Exception) -> str:
    """
    Format error message with context for user (FR-048).

    Provides actionable guidance when possible.
    """
    if isinstance(error, ImageValidationError):
        return f"Invalid input image: {error}. Ensure image is PNG/JPEG, RGB, ≥512×512, and ≤20MB."

    if isinstance(error, SVGValidationError):
        return f"Invalid SVG file: {error}. Ensure SVG is well-formed XML with viewBox and geometry."

    if isinstance(error, MeshValidationError):
        return f"Mesh validation failed: {error}. Try regenerating with different parameters."

    if isinstance(error, RepairError):
        return f"Mesh repair failed: {error}. Model may have unfixable topology issues."

    if isinstance(error, TimeoutError):
        return f"Operation timed out: {error}. Try simplifying input or contact support."

    if isinstance(error, ProfileNotFoundError):
        return f"Configuration error: {error}"

    if isinstance(error, FileSizeLimitError):
        return f"File too large: {error}"

    if isinstance(error, ComplexityLimitError):
        return f"Complexity limit exceeded: {error}. Try simplifying the design."

    # Generic error formatting
    return f"{type(error).__name__}: {error}"
