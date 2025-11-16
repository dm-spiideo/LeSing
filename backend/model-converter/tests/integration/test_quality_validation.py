"""
Integration test for quality validation workflow (T048).

Tests complete quality validation with metric calculation, reporting, and pass/fail decisions.

Feature: 002-3d-model-pipeline
User Story: US2 - Automated Quality Validation
"""

from pathlib import Path

import pytest
from PIL import Image, ImageDraw

# Add backend to path for imports
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent.parent))


# This will fail until we implement the full quality validation
@pytest.mark.skip(reason="Implementation not yet created - TDD red phase")
@pytest.mark.integration
class TestQualityValidationWorkflow:
    """Integration tests for quality validation workflow."""

    def test_high_quality_vectorization_passes(self, tmp_path):
        """
        High quality vectorization should pass all quality checks.

        Acceptance scenario: Quality metrics ≥ thresholds result in pass.
        """
        from backend.model_converter.src.vectorizer import vectorize_image
        from backend.model_converter.src.metrics import validate_quality

        # Create high-quality test image
        img_path = tmp_path / "input.png"
        img = Image.new("RGB", (1024, 1024), color=(255, 255, 255))
        draw = ImageDraw.Draw(img)
        draw.rectangle([200, 200, 800, 800], fill=(0, 0, 0))
        img.save(img_path)

        # Vectorize
        svg_path = tmp_path / "output.svg"
        vector_file = vectorize_image(img_path, svg_path)

        # Validate quality
        quality_report = validate_quality(img_path, svg_path)

        # Should pass quality checks
        assert quality_report.vectorization_passed is True
        assert quality_report.vectorization_metrics.overall_score >= 0.85
        assert quality_report.vectorization_metrics.ssim_score >= 0.85
        assert quality_report.vectorization_metrics.edge_iou >= 0.75
        assert quality_report.vectorization_metrics.color_correlation >= 0.90

    def test_low_quality_vectorization_fails(self, tmp_path):
        """
        Low quality vectorization should fail quality checks.
        """
        from backend.model_converter.src.vectorizer import vectorize_image
        from backend.model_converter.src.metrics import validate_quality

        # Create image that might vectorize poorly
        # (complex gradient or very small details)
        img_path = tmp_path / "complex.png"
        img = Image.new("RGB", (512, 512))
        pixels = img.load()
        for i in range(512):
            for j in range(512):
                # Create noise pattern
                pixels[i, j] = ((i * j) % 256, (i + j) % 256, (i - j) % 256)
        img.save(img_path)

        # Vectorize
        svg_path = tmp_path / "output.svg"
        vector_file = vectorize_image(img_path, svg_path)

        # Validate quality
        quality_report = validate_quality(img_path, svg_path)

        # May fail due to complexity
        if quality_report.vectorization_metrics.overall_score < 0.85:
            assert quality_report.vectorization_passed is False
            assert len(quality_report.vectorization_warnings) > 0

    def test_quality_report_generation(self, tmp_path):
        """
        Quality validation should generate comprehensive report (FR-031).
        """
        from backend.model_converter.src.vectorizer import vectorize_image
        from backend.model_converter.src.metrics import validate_quality

        img_path = tmp_path / "test.png"
        img = Image.new("RGB", (1024, 1024), color=(200, 200, 200))
        draw = ImageDraw.Draw(img)
        draw.ellipse([300, 300, 700, 700], fill=(50, 50, 50))
        img.save(img_path)

        svg_path = tmp_path / "output.svg"
        vectorize_image(img_path, svg_path)

        quality_report = validate_quality(img_path, svg_path)

        # Report should contain all metrics
        assert quality_report.vectorization_metrics is not None
        assert hasattr(quality_report.vectorization_metrics, 'ssim_score')
        assert hasattr(quality_report.vectorization_metrics, 'edge_iou')
        assert hasattr(quality_report.vectorization_metrics, 'color_correlation')
        assert hasattr(quality_report.vectorization_metrics, 'overall_score')
        assert hasattr(quality_report.vectorization_metrics, 'passed')

        # Report should have pass/fail status
        assert isinstance(quality_report.vectorization_passed, bool)

    def test_individual_metric_failures_reported(self, tmp_path):
        """
        Individual metric failures should be captured in warnings.

        Acceptance scenario: System reports which metrics failed.
        """
        from backend.model_converter.src.vectorizer import vectorize_image
        from backend.model_converter.src.metrics import validate_quality

        img_path = tmp_path / "test.png"
        img = Image.new("RGB", (1024, 1024), color=(128, 128, 128))
        img.save(img_path)

        svg_path = tmp_path / "output.svg"
        vectorize_image(img_path, svg_path)

        quality_report = validate_quality(img_path, svg_path)

        # If any individual metric fails, should be in warnings
        if not quality_report.vectorization_metrics.ssim_passed:
            warnings_str = " ".join(quality_report.vectorization_warnings)
            assert "SSIM" in warnings_str or "ssim" in warnings_str.lower()

        if not quality_report.vectorization_metrics.edge_iou_passed:
            warnings_str = " ".join(quality_report.vectorization_warnings)
            assert "edge" in warnings_str.lower() or "IoU" in warnings_str

        if not quality_report.vectorization_metrics.color_passed:
            warnings_str = " ".join(quality_report.vectorization_warnings)
            assert "color" in warnings_str.lower()

    def test_marginal_quality_triggers_warning(self, tmp_path):
        """
        Quality scores between 0.75-0.85 should trigger warnings but may pass.
        """
        from backend.model_converter.src.vectorizer import vectorize_image
        from backend.model_converter.src.metrics import validate_quality

        img_path = tmp_path / "test.png"
        img = Image.new("RGB", (1024, 1024), color=(150, 150, 150))
        draw = ImageDraw.Draw(img)
        # Create somewhat complex shape
        for i in range(10):
            draw.rectangle([i*100, i*100, i*100+50, i*100+50], fill=(50+i*20, 50+i*20, 50+i*20))
        img.save(img_path)

        svg_path = tmp_path / "output.svg"
        vectorize_image(img_path, svg_path)

        quality_report = validate_quality(img_path, svg_path)

        # Marginal quality should generate warnings
        if 0.75 <= quality_report.vectorization_metrics.overall_score < 0.85:
            assert len(quality_report.vectorization_warnings) > 0
            assert quality_report.total_warnings > 0

    def test_quality_validation_performance(self, tmp_path):
        """
        Quality validation should complete quickly (<10s per FR-040).
        """
        import time
        from backend.model_converter.src.vectorizer import vectorize_image
        from backend.model_converter.src.metrics import validate_quality

        img_path = tmp_path / "test.png"
        img = Image.new("RGB", (1024, 1024), color=(100, 100, 100))
        img.save(img_path)

        svg_path = tmp_path / "output.svg"
        vectorize_image(img_path, svg_path)

        start_time = time.time()
        quality_report = validate_quality(img_path, svg_path)
        validation_time = time.time() - start_time

        # Should complete quickly
        assert validation_time < 10.0  # 10 seconds max
        assert quality_report is not None

    def test_end_to_end_with_quality_validation(self, tmp_path):
        """
        Complete pipeline with integrated quality validation.
        """
        from backend.model_converter.src.vectorizer import vectorize_image
        from backend.model_converter.src.converter import convert_svg_to_3d
        from backend.model_converter.src.metrics import validate_quality

        # Create test image
        img_path = tmp_path / "name_sign.png"
        img = Image.new("RGB", (1024, 1024), color=(255, 255, 255))
        draw = ImageDraw.Draw(img)
        draw.text((300, 400), "TEST", fill=(0, 0, 0))
        img.save(img_path)

        # Vectorize
        svg_path = tmp_path / "vector.svg"
        vectorize_image(img_path, svg_path)

        # Validate vectorization quality
        quality_report = validate_quality(img_path, svg_path)

        # Only proceed to 3D if quality passes
        if quality_report.vectorization_passed:
            mesh_path = tmp_path / "model.3mf"
            mesh_file = convert_svg_to_3d(svg_path, mesh_path, extrusion_depth_mm=5.0)
            assert mesh_file.is_printable
        else:
            # Should have clear errors explaining why quality failed
            assert len(quality_report.vectorization_errors) > 0 or len(quality_report.vectorization_warnings) > 0
