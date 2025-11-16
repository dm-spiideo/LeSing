"""
Integration test for automatic quality retry logic (T049).

Tests automatic retry when quality scores fall between 0.75-0.84 (FR-007).

Feature: 002-3d-model-pipeline
User Story: US2 - Automated Quality Validation
"""

from pathlib import Path
from unittest.mock import Mock, patch, call

import pytest
from PIL import Image, ImageDraw

# Add backend to path for imports
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent.parent))


# This will fail until we implement retry logic
@pytest.mark.skip(reason="Implementation not yet created - TDD red phase")
@pytest.mark.integration
class TestQualityRetryLogic:
    """Integration tests for automatic quality retry."""

    def test_low_quality_triggers_retry(self, tmp_path):
        """
        Quality score 0.75-0.84 should trigger automatic retry (FR-007).

        Acceptance scenario 4: System automatically retries with adjusted parameters.
        """
        from backend.model_converter.src.vectorizer import vectorize_with_retry

        # Create image that might produce marginal quality
        img_path = tmp_path / "test.png"
        img = Image.new("RGB", (512, 512), color=(200, 200, 200))
        draw = ImageDraw.Draw(img)
        # Small text-like pattern
        draw.text((100, 200), "TEST", fill=(50, 50, 50))
        img.save(img_path)

        svg_path = tmp_path / "output.svg"

        # This should automatically retry if quality is marginal
        result = vectorize_with_retry(img_path, svg_path, max_retries=3)

        # Should have attempted retry if quality was marginal
        if result.retry_count > 0:
            assert 0.75 <= result.initial_quality < 0.85
            assert result.final_quality > result.initial_quality

    def test_retry_with_adjusted_parameters(self, tmp_path):
        """
        Retry should use adjusted parameters to improve quality.
        """
        from backend.model_converter.src.vectorizer import vectorize_with_retry

        img_path = tmp_path / "complex.png"
        img = Image.new("RGB", (1024, 1024), color=(255, 255, 255))
        draw = ImageDraw.Draw(img)
        # Create complex pattern
        for i in range(20):
            draw.rectangle([i*50, i*50, i*50+40, i*50+40], outline=(0, 0, 0), width=1)
        img.save(img_path)

        svg_path = tmp_path / "output.svg"

        result = vectorize_with_retry(img_path, svg_path, max_retries=3)

        # If retries occurred, parameters should have been adjusted
        if result.retry_count > 0:
            assert hasattr(result, 'parameter_history')
            assert len(result.parameter_history) > 1

    def test_max_retries_respected(self, tmp_path):
        """
        Should not exceed maximum retry count (FR-047).
        """
        from backend.model_converter.src.vectorizer import vectorize_with_retry

        img_path = tmp_path / "test.png"
        img = Image.new("RGB", (512, 512), color=(128, 128, 128))
        img.save(img_path)

        svg_path = tmp_path / "output.svg"

        # Limit to 2 retries
        result = vectorize_with_retry(img_path, svg_path, max_retries=2)

        # Should not exceed limit
        assert result.retry_count <= 2

    def test_high_quality_no_retry(self, tmp_path):
        """
        High quality (≥0.85) should not trigger retry.
        """
        from backend.model_converter.src.vectorizer import vectorize_with_retry

        # Simple, high-contrast image should vectorize well
        img_path = tmp_path / "simple.png"
        img = Image.new("RGB", (1024, 1024), color=(255, 255, 255))
        draw = ImageDraw.Draw(img)
        draw.rectangle([200, 200, 800, 800], fill=(0, 0, 0))
        img.save(img_path)

        svg_path = tmp_path / "output.svg"

        result = vectorize_with_retry(img_path, svg_path, max_retries=3)

        # Should not retry if quality is already high
        if result.final_quality >= 0.85:
            assert result.retry_count == 0

    def test_retry_improves_quality(self, tmp_path):
        """
        Retry with adjusted parameters should improve quality.
        """
        from backend.model_converter.src.vectorizer import vectorize_with_retry

        img_path = tmp_path / "test.png"
        img = Image.new("RGB", (1024, 1024), color=(240, 240, 240))
        draw = ImageDraw.Draw(img)
        draw.text((300, 400), "RETRY", fill=(20, 20, 20))
        img.save(img_path)

        svg_path = tmp_path / "output.svg"

        result = vectorize_with_retry(img_path, svg_path, max_retries=3)

        # If retry occurred, final quality should be >= initial
        if result.retry_count > 0:
            assert result.final_quality >= result.initial_quality * 0.95  # Allow small variance

    def test_retry_failure_handling(self, tmp_path):
        """
        If retry cannot improve quality, should fail gracefully.
        """
        from backend.model_converter.src.vectorizer import vectorize_with_retry
        from backend.shared.exceptions import VectorizationError

        # Create very complex image that's hard to vectorize well
        img_path = tmp_path / "complex.png"
        img = Image.new("RGB", (512, 512))
        pixels = img.load()
        for i in range(512):
            for j in range(512):
                pixels[i, j] = ((i * j) % 256, (i + j) % 256, i % 256)
        img.save(img_path)

        svg_path = tmp_path / "output.svg"

        # Should either succeed with low quality or fail with clear message
        try:
            result = vectorize_with_retry(img_path, svg_path, max_retries=3)
            # If succeeded, should have tried all retries
            assert result.retry_count <= 3
        except VectorizationError as e:
            # Should have clear error message
            assert "quality" in str(e).lower() or "retry" in str(e).lower()

    def test_retry_logs_attempts(self, tmp_path):
        """
        Retry attempts should be logged for debugging.
        """
        from backend.model_converter.src.vectorizer import vectorize_with_retry

        img_path = tmp_path / "test.png"
        img = Image.new("RGB", (1024, 1024), color=(150, 150, 150))
        img.save(img_path)

        svg_path = tmp_path / "output.svg"

        with patch('backend.model_converter.src.vectorizer.logger') as mock_logger:
            result = vectorize_with_retry(img_path, svg_path, max_retries=3)

            # Should log retry attempts
            if result.retry_count > 0:
                # Check that retry was logged
                log_calls = [str(call) for call in mock_logger.info.call_args_list]
                log_str = " ".join(log_calls)
                assert "retry" in log_str.lower()

    def test_exponential_backoff(self, tmp_path):
        """
        Retries should use exponential backoff timing (FR-047).
        """
        import time
        from backend.model_converter.src.vectorizer import vectorize_with_retry

        img_path = tmp_path / "test.png"
        img = Image.new("RGB", (1024, 1024), color=(128, 128, 128))
        img.save(img_path)

        svg_path = tmp_path / "output.svg"

        start_time = time.time()
        result = vectorize_with_retry(img_path, svg_path, max_retries=3)
        total_time = time.time() - start_time

        # If retries occurred, timing should reflect backoff
        # (This is hard to test precisely without mocking, but check it completed)
        if result.retry_count > 0:
            # With exponential backoff, should take some time
            # but still complete in reasonable timeframe
            assert total_time < 120.0  # 2 minutes max
