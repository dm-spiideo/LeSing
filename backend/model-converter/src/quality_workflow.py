"""
Quality-aware vectorization workflow with automatic retry.

Implements FR-007: Automatic retry with exponential backoff and parameter tuning.

Feature: 002-3d-model-pipeline
User Story: US2 - Automated Quality Validation
"""

import time
from pathlib import Path
from typing import Optional, Tuple

from backend.shared.exceptions import ProcessingError, TimeoutError
from backend.shared.logging_config import get_logger, PerformanceLogger
from backend.shared.models import ValidationReport, VectorFile

from .vectorizer import vectorize_image
from .metrics import validate_quality

logger = get_logger(__name__)


# =============================================================================
# Constants
# =============================================================================

MAX_RETRIES = 3  # FR-007: Maximum retry attempts
INITIAL_BACKOFF_SECONDS = 2.0  # Starting backoff delay
BACKOFF_MULTIPLIER = 2.0  # Exponential backoff multiplier

# Parameter tuning strategies for retries
RETRY_STRATEGIES = [
    {"max_colors": 8, "description": "Standard 8-color quantization"},
    {"max_colors": 16, "description": "Higher color count (16) for complex images"},
    {"max_colors": 4, "description": "Lower color count (4) for simpler representation"},
    {"max_colors": 12, "description": "Medium color count (12) as final attempt"},
]


# =============================================================================
# Result Classes
# =============================================================================


class QualityWorkflowResult:
    """
    Result from quality-aware vectorization workflow.

    Tracks retry attempts, quality progression, and parameter history.
    """

    def __init__(
        self,
        vector_file: VectorFile,
        quality_report: ValidationReport,
        retry_count: int,
        initial_quality: float,
        final_quality: float,
        parameter_history: list[dict],
    ):
        self.vector_file = vector_file
        self.quality_report = quality_report
        self.retry_count = retry_count
        self.initial_quality = initial_quality
        self.final_quality = final_quality
        self.parameter_history = parameter_history


# =============================================================================
# Quality-Aware Vectorization Workflow
# =============================================================================


def vectorize_with_quality_check(
    image_path: Path,
    output_path: Path,
    max_colors: int = 8,
    timeout_seconds: int = 120,
    job_id: Optional[str] = None,
    enable_retry: bool = True,
) -> QualityWorkflowResult:
    """
    Vectorize image with automatic quality validation and retry (FR-007).

    Implements workflow:
    1. Vectorize image
    2. Validate quality metrics
    3. If quality fails and retries enabled, retry with adjusted parameters
    4. Return final result with validation report

    Args:
        image_path: Path to input raster image
        output_path: Path for output SVG file
        max_colors: Maximum colors for quantization (default 8)
        timeout_seconds: Timeout for vectorization (default 120s)
        job_id: Optional job ID for tracking
        enable_retry: Enable automatic retry on quality failure (default True)

    Returns:
        QualityWorkflowResult with retry statistics and quality metrics

    Raises:
        ProcessingError: If vectorization fails after all retries
        TimeoutError: If processing exceeds timeout
    """
    with PerformanceLogger("vectorize_with_quality_check", logger) as perf:
        attempt = 0
        last_error = None
        best_result = None
        best_score = -1.0
        initial_quality_score = None
        parameter_history = []

        while attempt <= MAX_RETRIES:
            try:
                # Determine parameters for this attempt
                if attempt == 0:
                    # First attempt: use provided parameters
                    current_colors = max_colors
                    strategy_desc = f"Initial attempt with {max_colors} colors"
                elif attempt <= len(RETRY_STRATEGIES):
                    # Subsequent attempts: try different strategies
                    strategy = RETRY_STRATEGIES[attempt - 1]
                    current_colors = strategy["max_colors"]
                    strategy_desc = strategy["description"]
                else:
                    # Exhausted strategies
                    break

                logger.info(
                    "vectorization_attempt",
                    attempt=attempt + 1,
                    max_retries=MAX_RETRIES + 1,
                    strategy=strategy_desc,
                    max_colors=current_colors,
                )

                # Vectorize
                vector_file = vectorize_image(
                    image_path,
                    output_path,
                    max_colors=current_colors,
                    timeout_seconds=timeout_seconds,
                )

                # Validate quality
                quality_report = validate_quality(
                    original_path=image_path,
                    vectorized_path=output_path,
                    job_id=job_id,
                )

                # Track best result
                if quality_report.vectorization_metrics:
                    current_score = quality_report.vectorization_metrics.overall_score

                    # Track initial quality on first attempt
                    if initial_quality_score is None:
                        initial_quality_score = current_score

                    # Track parameter history
                    parameter_history.append({
                        "attempt": attempt + 1,
                        "max_colors": current_colors,
                        "quality": current_score,
                        "passed": quality_report.vectorization_passed,
                    })

                    if current_score > best_score:
                        best_score = current_score
                        best_result = (vector_file, quality_report)

                # Check if quality passed
                if quality_report.vectorization_passed:
                    logger.info(
                        "vectorization_quality_passed",
                        attempt=attempt + 1,
                        overall_score=round(current_score, 3),
                    )
                    perf.log_metric("attempts", attempt + 1)
                    perf.log_metric("success", 1)

                    return QualityWorkflowResult(
                        vector_file=vector_file,
                        quality_report=quality_report,
                        retry_count=attempt,
                        initial_quality=initial_quality_score or current_score,
                        final_quality=current_score,
                        parameter_history=parameter_history,
                    )

                # Quality failed
                logger.warning(
                    "vectorization_quality_failed",
                    attempt=attempt + 1,
                    overall_score=round(current_score, 3),
                    warnings=len(quality_report.vectorization_warnings),
                    errors=len(quality_report.vectorization_errors),
                )

                # Check if retry is enabled
                if not enable_retry:
                    logger.info("retry_disabled")
                    perf.log_metric("attempts", attempt + 1)
                    perf.log_metric("success", 0)

                    return QualityWorkflowResult(
                        vector_file=vector_file,
                        quality_report=quality_report,
                        retry_count=0,
                        initial_quality=initial_quality_score or current_score,
                        final_quality=current_score,
                        parameter_history=parameter_history,
                    )

                # Exponential backoff before retry
                if attempt < MAX_RETRIES:
                    backoff_delay = INITIAL_BACKOFF_SECONDS * (BACKOFF_MULTIPLIER ** attempt)
                    logger.info(
                        "retry_backoff",
                        delay_seconds=round(backoff_delay, 2),
                        next_attempt=attempt + 2,
                    )
                    time.sleep(backoff_delay)

                attempt += 1

            except TimeoutError as e:
                logger.error(
                    "vectorization_timeout",
                    attempt=attempt + 1,
                    error=str(e),
                )
                last_error = e
                attempt += 1

                if attempt <= MAX_RETRIES and enable_retry:
                    backoff_delay = INITIAL_BACKOFF_SECONDS * (BACKOFF_MULTIPLIER ** (attempt - 1))
                    time.sleep(backoff_delay)
                else:
                    break

            except Exception as e:
                logger.error(
                    "vectorization_error",
                    attempt=attempt + 1,
                    error=str(e),
                    error_type=type(e).__name__,
                )
                last_error = e
                attempt += 1

                if attempt <= MAX_RETRIES and enable_retry:
                    backoff_delay = INITIAL_BACKOFF_SECONDS * (BACKOFF_MULTIPLIER ** (attempt - 1))
                    time.sleep(backoff_delay)
                else:
                    break

        # All retries exhausted
        if best_result is not None:
            # Return best result even if it didn't pass
            vector_file, quality_report = best_result
            logger.warning(
                "vectorization_completed_with_quality_issues",
                best_score=round(best_score, 3),
                total_attempts=attempt,
            )
            perf.log_metric("attempts", attempt)
            perf.log_metric("success", 0)

            return QualityWorkflowResult(
                vector_file=vector_file,
                quality_report=quality_report,
                retry_count=attempt,
                initial_quality=initial_quality_score or best_score,
                final_quality=best_score,
                parameter_history=parameter_history,
            )
        else:
            # Complete failure
            error_msg = f"Vectorization failed after {attempt} attempts"
            if last_error:
                error_msg += f": {str(last_error)}"

            logger.error(
                "vectorization_failed_all_attempts",
                attempts=attempt,
                last_error=str(last_error) if last_error else None,
            )
            perf.log_metric("attempts", attempt)
            perf.log_metric("success", 0)

            raise ProcessingError(error_msg)


def batch_vectorize_with_quality(
    image_paths: list[Path],
    output_dir: Path,
    max_colors: int = 8,
    timeout_seconds: int = 120,
    enable_retry: bool = True,
) -> list[QualityWorkflowResult]:
    """
    Batch vectorize multiple images with quality validation.

    Args:
        image_paths: List of input image paths
        output_dir: Directory for output SVG files
        max_colors: Maximum colors for quantization
        timeout_seconds: Timeout per image
        enable_retry: Enable automatic retry

    Returns:
        List of QualityWorkflowResult objects
    """
    results = []

    for i, image_path in enumerate(image_paths):
        logger.info(
            "batch_vectorization_progress",
            current=i + 1,
            total=len(image_paths),
            image=str(image_path.name),
        )

        try:
            output_path = output_dir / f"{image_path.stem}.svg"
            job_id = f"batch_{i:04d}"

            workflow_result = vectorize_with_quality_check(
                image_path=image_path,
                output_path=output_path,
                max_colors=max_colors,
                timeout_seconds=timeout_seconds,
                job_id=job_id,
                enable_retry=enable_retry,
            )

            results.append(workflow_result)

        except Exception as e:
            logger.error(
                "batch_vectorization_error",
                image=str(image_path.name),
                error=str(e),
            )
            # Continue with next image
            continue

    logger.info(
        "batch_vectorization_complete",
        total_images=len(image_paths),
        successful=len(results),
        failed=len(image_paths) - len(results),
    )

    return results
