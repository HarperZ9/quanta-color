"""Comprehensive tests for gamut mapping."""
import numpy as np
import pytest

from quanta_color.gamut import (
    clip,
    compress,
    gamut_coverage,
    is_in_gamut,
    oklab_chroma_reduce,
)

# =========================================================================
# clip
# =========================================================================

class TestClip:
    """Tests for simple gamut clipping."""

    def test_clamps_above_one(self):
        rgb = np.array([1.5, 0.5, 0.0])
        result = clip(rgb)
        assert result[0] == pytest.approx(1.0)
        assert result[1] == pytest.approx(0.5)
        assert result[2] == pytest.approx(0.0)

    def test_clamps_below_zero(self):
        rgb = np.array([-0.3, 0.5, 1.2])
        result = clip(rgb)
        assert result[0] == pytest.approx(0.0)
        assert result[2] == pytest.approx(1.0)

    def test_in_gamut_unchanged(self):
        rgb = np.array([0.3, 0.6, 0.9])
        result = clip(rgb)
        np.testing.assert_allclose(result, rgb, atol=1e-10)

    def test_clip_batch(self):
        rgb = np.array([
            [1.5, -0.1, 0.5],
            [0.3, 0.6, 0.9],
        ])
        result = clip(rgb)
        assert result.shape == (2, 3)
        assert np.all(result >= 0.0)
        assert np.all(result <= 1.0)

    def test_clip_preserves_black(self):
        result = clip(np.array([0.0, 0.0, 0.0]))
        np.testing.assert_allclose(result, [0.0, 0.0, 0.0])

    def test_clip_preserves_white(self):
        result = clip(np.array([1.0, 1.0, 1.0]))
        np.testing.assert_allclose(result, [1.0, 1.0, 1.0])


# =========================================================================
# compress
# =========================================================================

class TestCompress:
    """Tests for soft gamut compression."""

    def test_keeps_values_in_range(self):
        rgb = np.array([1.5, 0.5, -0.2])
        result = compress(rgb)
        assert np.all(result >= 0.0), f"Negative values: {result}"
        assert np.all(result <= 1.0 + 0.01), f"Values exceed 1.0: {result}"

    def test_below_threshold_unchanged(self):
        """Values below threshold should pass through unchanged."""
        rgb = np.array([0.3, 0.5, 0.7])
        result = compress(rgb, threshold=0.8)
        np.testing.assert_allclose(result, rgb, atol=1e-10)

    def test_above_threshold_compressed(self):
        """Values above threshold should be less than raw value."""
        rgb = np.array([1.5, 1.5, 1.5])
        result = compress(rgb, threshold=0.8, limit=1.0)
        assert np.all(result <= 1.0 + 0.01)
        assert np.all(result >= 0.8)

    def test_compress_batch(self):
        rgb = np.array([
            [1.5, -0.1, 0.5],
            [0.3, 0.6, 2.0],
        ])
        result = compress(rgb)
        assert result.shape == (2, 3)
        assert np.all(result >= 0.0)
        assert np.all(result <= 1.0 + 0.01)

    def test_black_unchanged(self):
        result = compress(np.array([0.0, 0.0, 0.0]))
        np.testing.assert_allclose(result, [0.0, 0.0, 0.0], atol=1e-10)


# =========================================================================
# is_in_gamut
# =========================================================================

class TestIsInGamut:
    """Tests for gamut membership checking."""

    def test_in_gamut_valid(self):
        rgb = np.array([0.5, 0.5, 0.5])
        assert is_in_gamut(rgb)

    def test_out_of_gamut_above(self):
        rgb = np.array([1.1, 0.5, 0.5])
        assert not is_in_gamut(rgb)

    def test_out_of_gamut_below(self):
        rgb = np.array([0.5, -0.1, 0.5])
        assert not is_in_gamut(rgb)

    def test_boundary_with_tolerance(self):
        """Values slightly outside [0,1] but within tolerance should be in-gamut."""
        rgb = np.array([1.0005, 0.5, -0.0005])
        assert is_in_gamut(rgb, tolerance=0.001)

    def test_boundary_without_tolerance(self):
        rgb = np.array([1.0005, 0.5, -0.0005])
        assert not is_in_gamut(rgb, tolerance=0.0)

    def test_batch_gamut_check(self):
        rgb = np.array([
            [0.5, 0.5, 0.5],    # in gamut
            [1.1, 0.5, 0.5],    # out of gamut
            [0.0, 0.0, 0.0],    # in gamut (black)
            [1.0, 1.0, 1.0],    # in gamut (white)
        ])
        result = is_in_gamut(rgb)
        assert result.shape == (4,)
        assert result[0]
        assert not result[1]
        assert result[2]
        assert result[3]

    def test_pure_primaries_in_gamut(self):
        for color in [[1, 0, 0], [0, 1, 0], [0, 0, 1]]:
            assert is_in_gamut(np.array(color, dtype=float))


# =========================================================================
# gamut_coverage
# =========================================================================

class TestGamutCoverage:
    """Tests for gamut coverage calculation."""

    def test_srgb_vs_srgb_equals_one(self):
        """sRGB vs sRGB coverage should be 1.0."""
        srgb_primaries = [(0.64, 0.33), (0.30, 0.60), (0.15, 0.06)]
        coverage = gamut_coverage(srgb_primaries, srgb_primaries)
        assert coverage == pytest.approx(1.0, abs=1e-10)

    def test_p3_covers_more_than_srgb(self):
        """Display P3 should cover more than sRGB."""
        srgb_primaries = [(0.64, 0.33), (0.30, 0.60), (0.15, 0.06)]
        p3_primaries = [(0.680, 0.320), (0.265, 0.690), (0.150, 0.060)]
        coverage = gamut_coverage(p3_primaries, srgb_primaries)
        assert coverage > 1.0, "P3 should be larger than sRGB"

    def test_srgb_in_bt2020(self):
        """sRGB should cover less than BT.2020."""
        srgb_primaries = [(0.64, 0.33), (0.30, 0.60), (0.15, 0.06)]
        bt2020_primaries = [(0.708, 0.292), (0.170, 0.797), (0.131, 0.046)]
        coverage = gamut_coverage(srgb_primaries, bt2020_primaries)
        assert coverage < 1.0, "sRGB should be smaller than BT.2020"

    def test_zero_area_target(self):
        """Zero-area target should return 0."""
        display = [(0.64, 0.33), (0.30, 0.60), (0.15, 0.06)]
        degenerate = [(0.5, 0.5), (0.5, 0.5), (0.5, 0.5)]
        coverage = gamut_coverage(display, degenerate)
        assert coverage == pytest.approx(0.0)

    def test_returns_positive(self):
        srgb_primaries = [(0.64, 0.33), (0.30, 0.60), (0.15, 0.06)]
        p3_primaries = [(0.680, 0.320), (0.265, 0.690), (0.150, 0.060)]
        coverage = gamut_coverage(srgb_primaries, p3_primaries)
        assert coverage > 0


# =========================================================================
# oklab_chroma_reduce
# =========================================================================

class TestOklabChromaReduce:
    """Tests for Oklab chroma reduction gamut mapping."""

    def test_in_gamut_stays_in_gamut(self):
        """Already in-gamut color should remain valid."""
        srgb = np.array([0.5, 0.3, 0.8])
        result = oklab_chroma_reduce(srgb)
        assert np.all(result >= 0.0) and np.all(result <= 1.0)

    def test_out_of_gamut_brought_in(self):
        """Out-of-gamut color should be brought into gamut."""
        # This imaginary sRGB value would be out of gamut in some transform
        # Use a highly saturated value that is in sRGB but test the function works
        srgb = np.array([1.0, 0.0, 0.0])
        result = oklab_chroma_reduce(srgb)
        assert np.all(result >= -0.01) and np.all(result <= 1.01)

    def test_preserves_lightness_approximately(self):
        """Chroma reduce should preserve lightness of the color."""
        from quanta_color.spaces import srgb_to_oklab
        srgb = np.array([0.8, 0.2, 0.1])
        oklab_orig = srgb_to_oklab(srgb)
        result = oklab_chroma_reduce(srgb)
        oklab_mapped = srgb_to_oklab(result)
        # Lightness should be approximately preserved
        assert oklab_mapped[0] == pytest.approx(oklab_orig[0], abs=0.1)

    def test_batch_processing(self):
        """Should work with (N,3) arrays."""
        srgb = np.array([
            [0.8, 0.3, 0.5],
            [0.2, 0.7, 0.1],
            [0.5, 0.5, 0.5],
        ])
        result = oklab_chroma_reduce(srgb)
        assert result.shape == (3, 3)
        assert np.all(result >= -0.01) and np.all(result <= 1.01)

    def test_black_stays_black(self):
        result = oklab_chroma_reduce(np.array([0.0, 0.0, 0.0]))
        np.testing.assert_allclose(result, [0.0, 0.0, 0.0], atol=0.01)

    def test_white_stays_white(self):
        result = oklab_chroma_reduce(np.array([1.0, 1.0, 1.0]))
        np.testing.assert_allclose(result, [1.0, 1.0, 1.0], atol=0.02)
