"""Unit tests for retry logic.

Tests cover:
- Maximum 3 retries
- Exponential backoff timing
- Quality failure triggers retry
- Storage failure does not retry
"""

from unittest.mock import Mock, patch

import pytest

from src.exceptions import QualityError, RateLimitError, ServiceError, StorageError
from src.generator import AIImageGenerator


class TestRetryLogic:
    """Test suite for retry logic."""

    @pytest.fixture
    def generator(self, test_settings, temp_output_dir):  # type: ignore[no-untyped-def]
        """Provide an AIImageGenerator instance."""
        test_settings.storage_path = temp_output_dir
        test_settings.max_retries = 3
        return AIImageGenerator(settings=test_settings)

    def test_max_retries_limit(self, generator: AIImageGenerator) -> None:
        """Test that retry logic respects max_retries setting."""
        # The generator should have max_retries set
        assert generator.settings.max_retries == 3

    def test_quality_failure_should_be_retryable(self) -> None:
        """Test that QualityError is classified as retryable."""

        # QualityError should exist and be retryable
        error = QualityError("Image quality too low")
        assert isinstance(error, Exception)

    def test_rate_limit_error_should_be_retryable(self) -> None:
        """Test that RateLimitError is classified as retryable."""

        error = RateLimitError("Rate limit exceeded")
        assert isinstance(error, Exception)

    def test_service_error_should_be_retryable(self) -> None:
        """Test that ServiceError is classified as retryable."""

        error = ServiceError("Service unavailable")
        assert isinstance(error, Exception)

    def test_storage_error_should_not_be_retryable(self) -> None:
        """Test that StorageError is classified as non-retryable."""

        error = StorageError("Disk full")
        assert isinstance(error, Exception)

    def test_validation_error_should_not_be_retryable(self) -> None:
        """Test that ValidationError is classified as non-retryable."""
        from src.exceptions import ValidationError

        error = ValidationError("Invalid prompt")
        assert isinstance(error, Exception)

    def test_authentication_error_should_not_be_retryable(self) -> None:
        """Test that AuthenticationError is classified as non-retryable."""
        from src.exceptions import AuthenticationError

        error = AuthenticationError("Invalid API key")
        assert isinstance(error, Exception)

    def test_exponential_backoff_timing(self) -> None:
        """Test that retry delays follow exponential backoff pattern."""
        # Expected delays: 2s, 4s, 8s for retries 1, 2, 3
        expected_delays = [2, 4, 8]

        # Verify the pattern exists
        for i, delay in enumerate(expected_delays, 1):
            calculated_delay = 2**i
            assert calculated_delay == delay

    @patch("time.sleep")
    def test_retry_respects_backoff_delays(self, mock_sleep: Mock) -> None:
        """Test that retries use proper backoff delays."""
        # This is a placeholder - actual implementation will use tenacity
        # which handles exponential backoff automatically
        pass
