"""Comprehensive tests for color vision deficiency simulation."""
import numpy as np
import pytest

from quanta_color.blindness import (
    DEFICIENCY_TYPES,
    error_map,
    simulate,
)

# =========================================================================
# Severity 0 returns input unchanged
# =========================================================================

class TestSeverityZero:
    """Severity 0 should return input unchanged."""

    @pytest.mark.parametrize("deficiency", DEFICIENCY_TYPES)
    def test_severity_zero_identity(self, deficiency):
        srgb = np.array([0.8, 0.3, 0.5])
        result = simulate(srgb, deficiency=deficiency, severity=0.0)
        np.testing.assert_allclose(result, srgb, atol=1e-10,
                                   err_msg=f"{deficiency} at severity=0 changed input")


# =========================================================================
# Achromatopsia at severity 1 returns grayscale
# =========================================================================

class TestAchromatopsia:
    """Full achromatopsia should produce grayscale (R=G=B)."""

    def test_grayscale_output(self):
        srgb = np.array([0.9, 0.2, 0.5])
        result = simulate(srgb, deficiency="achromatopsia", severity=1.0)
        # All channels should be equal (grayscale)
        assert result[0] == pytest.approx(result[1], abs=1e-5)
        assert result[1] == pytest.approx(result[2], abs=1e-5)

    def test_grayscale_pure_red(self):
        srgb = np.array([1.0, 0.0, 0.0])
        result = simulate(srgb, deficiency="achromatopsia", severity=1.0)
        assert result[0] == pytest.approx(result[1], abs=1e-5)
        assert result[1] == pytest.approx(result[2], abs=1e-5)

    def test_grayscale_white(self):
        srgb = np.array([1.0, 1.0, 1.0])
        result = simulate(srgb, deficiency="achromatopsia", severity=1.0)
        np.testing.assert_allclose(result, [1.0, 1.0, 1.0], atol=0.02)

    def test_grayscale_black(self):
        srgb = np.array([0.0, 0.0, 0.0])
        result = simulate(srgb, deficiency="achromatopsia", severity=1.0)
        np.testing.assert_allclose(result, [0.0, 0.0, 0.0], atol=1e-10)


# =========================================================================
# All 4 deficiency types produce valid output (0-1 range)
# =========================================================================

class TestValidOutput:
    """All deficiency types should produce values in [0, 1]."""

    @pytest.mark.parametrize("deficiency", DEFICIENCY_TYPES)
    def test_output_range_single(self, deficiency):
        srgb = np.array([0.8, 0.3, 0.5])
        result = simulate(srgb, deficiency=deficiency, severity=1.0)
        assert np.all(result >= 0.0), \
            f"{deficiency} produced negative values: {result}"
        assert np.all(result <= 1.0), \
            f"{deficiency} produced values > 1: {result}"

    @pytest.mark.parametrize("deficiency", DEFICIENCY_TYPES)
    def test_output_range_primary_colors(self, deficiency):
        """Test with saturated primary colors."""
        primaries = [
            np.array([1.0, 0.0, 0.0]),
            np.array([0.0, 1.0, 0.0]),
            np.array([0.0, 0.0, 1.0]),
            np.array([1.0, 1.0, 0.0]),
            np.array([0.0, 1.0, 1.0]),
            np.array([1.0, 0.0, 1.0]),
        ]
        for color in primaries:
            result = simulate(color, deficiency=deficiency, severity=1.0)
            assert np.all(result >= 0.0) and np.all(result <= 1.0), \
                f"{deficiency} out of range for {color}: {result}"

    @pytest.mark.parametrize("deficiency", DEFICIENCY_TYPES)
    @pytest.mark.parametrize("severity", [0.0, 0.25, 0.5, 0.75, 1.0])
    def test_output_range_varied_severity(self, deficiency, severity):
        srgb = np.array([0.7, 0.4, 0.9])
        result = simulate(srgb, deficiency=deficiency, severity=severity)
        assert np.all(result >= 0.0) and np.all(result <= 1.0 + 1e-10)


# =========================================================================
# Batch processing
# =========================================================================

class TestBatchProcessing:
    """Test (N,3) array batch processing."""

    @pytest.mark.parametrize("deficiency", DEFICIENCY_TYPES)
    def test_batch_10x3(self, deficiency):
        rng = np.random.RandomState(42)
        srgb = rng.rand(10, 3)
        result = simulate(srgb, deficiency=deficiency, severity=1.0)
        assert result.shape == (10, 3), \
            f"{deficiency} batch shape: {result.shape}, expected (10, 3)"
        assert np.all(result >= 0.0)
        assert np.all(result <= 1.0 + 1e-10)

    def test_batch_image_shape(self):
        """Simulate a small 4x4 image."""
        rng = np.random.RandomState(42)
        image = rng.rand(4, 4, 3)
        result = simulate(image, deficiency="deuteranopia", severity=1.0)
        assert result.shape == (4, 4, 3)
        assert np.all(result >= 0.0) and np.all(result <= 1.0 + 1e-10)

    def test_batch_consistency(self):
        """Batch result should match individual results."""
        colors = np.array([
            [0.8, 0.3, 0.5],
            [0.2, 0.7, 0.1],
            [0.5, 0.5, 0.5],
        ])
        batch_result = simulate(colors, deficiency="protanopia", severity=1.0)
        for i in range(3):
            single = simulate(colors[i], deficiency="protanopia", severity=1.0)
            np.testing.assert_allclose(batch_result[i], single, atol=1e-10)


# =========================================================================
# Error map
# =========================================================================

class TestErrorMap:
    """Tests for error_map function."""

    @pytest.mark.parametrize("deficiency", DEFICIENCY_TYPES)
    def test_error_map_non_negative(self, deficiency):
        srgb = np.array([0.8, 0.3, 0.5])
        err = error_map(srgb, deficiency=deficiency)
        assert np.all(err >= 0.0), f"error_map negative for {deficiency}"

    def test_error_map_zero_for_gray(self):
        """Grayscale should have near-zero error for most deficiencies."""
        gray = np.array([0.5, 0.5, 0.5])
        err = error_map(gray, deficiency="achromatopsia")
        # Achromatopsia on gray should produce very small error
        assert np.all(err < 0.05)

    def test_error_map_shape(self):
        srgb = np.array([[0.8, 0.3, 0.5], [0.2, 0.7, 0.1]])
        err = error_map(srgb, deficiency="deuteranopia")
        assert err.shape == (2, 3)

    def test_error_map_saturated_has_error(self):
        """Saturated colors should have significant error for CVD."""
        red = np.array([1.0, 0.0, 0.0])
        err = error_map(red, deficiency="protanopia")
        # Protanopia should lose information about pure red
        assert np.max(err) > 0.01


# =========================================================================
# Edge cases
# =========================================================================

class TestEdgeCases:
    """Edge case handling."""

    def test_invalid_deficiency_raises(self):
        with pytest.raises(ValueError):
            simulate(np.array([0.5, 0.5, 0.5]), deficiency="invalid_type")

    def test_four_deficiency_types(self):
        assert len(DEFICIENCY_TYPES) == 4
        assert "protanopia" in DEFICIENCY_TYPES
        assert "deuteranopia" in DEFICIENCY_TYPES
        assert "tritanopia" in DEFICIENCY_TYPES
        assert "achromatopsia" in DEFICIENCY_TYPES

    def test_different_deficiencies_differ(self):
        """Different deficiency types should produce different results."""
        srgb = np.array([0.8, 0.3, 0.5])
        results = {}
        for d in ["protanopia", "deuteranopia", "tritanopia"]:
            results[d] = simulate(srgb, deficiency=d, severity=1.0)
        # At least two should differ
        assert not np.allclose(results["protanopia"], results["deuteranopia"], atol=1e-3) or \
               not np.allclose(results["protanopia"], results["tritanopia"], atol=1e-3)
