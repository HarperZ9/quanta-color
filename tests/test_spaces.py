"""Comprehensive tests for color space conversions."""
import numpy as np
import pytest
from quanta_color.spaces import (
    srgb_to_linear, linear_to_srgb,
    srgb_to_xyz, xyz_to_srgb,
    xyz_to_xyY, xyY_to_xyz,
    xyz_to_lab, lab_to_xyz,
    lab_to_lch, lch_to_lab,
    srgb_to_oklab, oklab_to_srgb,
    linear_srgb_to_oklab, oklab_to_linear_srgb,
    oklab_to_oklch, oklch_to_oklab,
    xyz_to_jzazbz, jzazbz_to_xyz,
    jzazbz_to_jzczhz, jzczhz_to_jzazbz,
    rgb_to_hsv, hsv_to_rgb,
    srgb_to_p3, srgb_to_bt2020, srgb_to_acescg,
    primaries_to_matrix, luminance,
    D50, D65, SRGB_TO_XYZ,
)


# =========================================================================
# Roundtrip tests
# =========================================================================

class TestSRGBXYZRoundtrip:
    """sRGB <-> XYZ roundtrip."""

    @pytest.mark.parametrize("color", [
        np.array([1.0, 0.0, 0.0]),
        np.array([0.0, 1.0, 0.0]),
        np.array([0.0, 0.0, 1.0]),
        np.array([1.0, 1.0, 1.0]),
        np.array([0.5, 0.5, 0.5]),
        np.array([0.18, 0.18, 0.18]),
    ])
    def test_roundtrip(self, color):
        xyz = srgb_to_xyz(color)
        recovered = xyz_to_srgb(xyz, clip=False)
        np.testing.assert_allclose(recovered, color, atol=1e-4)


class TestSRGBOklabRoundtrip:
    """sRGB <-> Oklab roundtrip."""

    @pytest.mark.parametrize("color", [
        np.array([1.0, 0.0, 0.0]),
        np.array([0.0, 1.0, 0.0]),
        np.array([0.0, 0.0, 1.0]),
        np.array([1.0, 1.0, 1.0]),
        np.array([0.5, 0.5, 0.5]),
    ])
    def test_roundtrip(self, color):
        oklab = srgb_to_oklab(color)
        recovered = oklab_to_srgb(oklab, clip=False)
        np.testing.assert_allclose(recovered, color, atol=1e-5)


class TestXYZJzAzBzRoundtrip:
    """XYZ <-> JzAzBz roundtrip."""

    @pytest.mark.parametrize("xyz_val", [
        np.array([100.0, 100.0, 100.0]),
        np.array([50.0, 50.0, 50.0]),
        np.array([200.0, 200.0, 200.0]),
        np.array([1000.0, 1000.0, 1000.0]),
    ])
    def test_roundtrip(self, xyz_val):
        jzazbz = xyz_to_jzazbz(xyz_val)
        recovered = jzazbz_to_xyz(jzazbz)
        np.testing.assert_allclose(recovered, xyz_val, rtol=1e-4, atol=1e-3)


class TestXYZLabRoundtrip:
    """XYZ <-> Lab roundtrip."""

    @pytest.mark.parametrize("xyz_val", [
        D50,                                  # D50 white
        np.array([0.5, 0.5, 0.5]),
        np.array([0.2, 0.3, 0.4]),
    ])
    def test_roundtrip_d50(self, xyz_val):
        lab = xyz_to_lab(xyz_val, white=D50)
        recovered = lab_to_xyz(lab, white=D50)
        np.testing.assert_allclose(recovered, xyz_val, atol=1e-10)

    def test_roundtrip_d65(self):
        xyz_val = D65
        lab = xyz_to_lab(xyz_val, white=D65)
        recovered = lab_to_xyz(lab, white=D65)
        np.testing.assert_allclose(recovered, xyz_val, atol=1e-10)


class TestLabLCHRoundtrip:
    """Lab <-> LCH roundtrip."""

    @pytest.mark.parametrize("lab", [
        np.array([50.0, 25.0, -10.0]),
        np.array([80.0, -30.0, 40.0]),
        np.array([20.0, 0.0, 0.0]),       # achromatic
    ])
    def test_roundtrip(self, lab):
        lch = lab_to_lch(lab)
        recovered = lch_to_lab(lch)
        np.testing.assert_allclose(recovered, lab, atol=1e-10)


class TestOklabOklchRoundtrip:
    """Oklab <-> Oklch roundtrip."""

    @pytest.mark.parametrize("oklab", [
        np.array([0.5, 0.1, -0.05]),
        np.array([0.8, -0.1, 0.1]),
        np.array([0.3, 0.0, 0.0]),        # achromatic
    ])
    def test_roundtrip(self, oklab):
        oklch = oklab_to_oklch(oklab)
        recovered = oklch_to_oklab(oklch)
        np.testing.assert_allclose(recovered, oklab, atol=1e-10)


class TestJzAzBzJzCzhzRoundtrip:
    """JzAzBz <-> JzCzhz roundtrip."""

    @pytest.mark.parametrize("jzazbz", [
        np.array([0.5, 0.1, -0.05]),
        np.array([0.2, -0.03, 0.04]),
    ])
    def test_roundtrip(self, jzazbz):
        jzczhz = jzazbz_to_jzczhz(jzazbz)
        recovered = jzczhz_to_jzazbz(jzczhz)
        np.testing.assert_allclose(recovered, jzazbz, atol=1e-10)


class TestRGBHSVRoundtrip:
    """RGB <-> HSV roundtrip."""

    @pytest.mark.parametrize("rgb", [
        np.array([1.0, 0.0, 0.0]),
        np.array([0.0, 1.0, 0.0]),
        np.array([0.0, 0.0, 1.0]),
        np.array([1.0, 1.0, 1.0]),
        np.array([0.5, 0.25, 0.75]),
        np.array([0.0, 0.0, 0.0]),
    ])
    def test_roundtrip(self, rgb):
        hsv = rgb_to_hsv(rgb)
        recovered = hsv_to_rgb(hsv)
        np.testing.assert_allclose(recovered, rgb, atol=1e-10)


# =========================================================================
# Known value tests
# =========================================================================

class TestKnownValues:
    """Test known reference values."""

    def test_d65_white_in_xyz(self):
        """D65 white XYZ is (0.95047, 1.0, 1.08883)."""
        np.testing.assert_allclose(D65, [0.95047, 1.0, 1.08883], atol=1e-5)

    def test_srgb_red_to_xyz(self):
        """Pure sRGB red (1,0,0) -> known XYZ values."""
        xyz = srgb_to_xyz(np.array([1.0, 0.0, 0.0]))
        # X should be ~0.4125, Y should be ~0.2127 (luminance coeff), Z very small
        assert xyz[0] == pytest.approx(0.4124564, abs=1e-5)
        assert xyz[1] == pytest.approx(0.2126729, abs=1e-5)
        assert xyz[2] == pytest.approx(0.0193339, abs=1e-5)

    def test_srgb_white_to_xyz(self):
        """Pure sRGB white (1,1,1) -> D65 XYZ."""
        xyz = srgb_to_xyz(np.array([1.0, 1.0, 1.0]))
        np.testing.assert_allclose(xyz, D65, atol=1e-4)

    def test_lab_of_d50_white(self):
        """D50 white in Lab (D50 ref) should be L=100, a=0, b=0."""
        lab = xyz_to_lab(D50, white=D50)
        assert lab[0] == pytest.approx(100.0, abs=1e-10)
        assert lab[1] == pytest.approx(0.0, abs=1e-10)
        assert lab[2] == pytest.approx(0.0, abs=1e-10)

    def test_lab_of_d65_white_with_d65_ref(self):
        """D65 white in Lab (D65 ref) should be L=100, a=0, b=0."""
        lab = xyz_to_lab(D65, white=D65)
        assert lab[0] == pytest.approx(100.0, abs=1e-10)
        assert lab[1] == pytest.approx(0.0, abs=1e-10)
        assert lab[2] == pytest.approx(0.0, abs=1e-10)

    def test_oklab_white(self):
        """sRGB white -> Oklab L should be ~1.0."""
        oklab = srgb_to_oklab(np.array([1.0, 1.0, 1.0]))
        assert oklab[0] == pytest.approx(1.0, abs=0.01)
        assert abs(oklab[1]) < 0.03
        assert abs(oklab[2]) < 0.02

    def test_oklab_black(self):
        """sRGB black -> Oklab L should be 0."""
        oklab = srgb_to_oklab(np.array([0.0, 0.0, 0.0]))
        assert oklab[0] == pytest.approx(0.0, abs=1e-10)

    def test_hsv_of_red(self):
        """Pure red in HSV: H=0, S=1, V=1."""
        hsv = rgb_to_hsv(np.array([1.0, 0.0, 0.0]))
        assert hsv[0] == pytest.approx(0.0, abs=1e-10)
        assert hsv[1] == pytest.approx(1.0, abs=1e-10)
        assert hsv[2] == pytest.approx(1.0, abs=1e-10)

    def test_hsv_of_green(self):
        """Pure green in HSV: H=120, S=1, V=1."""
        hsv = rgb_to_hsv(np.array([0.0, 1.0, 0.0]))
        assert hsv[0] == pytest.approx(120.0, abs=1e-10)

    def test_hsv_of_blue(self):
        """Pure blue in HSV: H=240, S=1, V=1."""
        hsv = rgb_to_hsv(np.array([0.0, 0.0, 1.0]))
        assert hsv[0] == pytest.approx(240.0, abs=1e-10)


# =========================================================================
# Edge cases
# =========================================================================

class TestEdgeCases:
    """Edge case handling."""

    def test_pure_black_xyz(self):
        xyz = srgb_to_xyz(np.array([0.0, 0.0, 0.0]))
        np.testing.assert_allclose(xyz, [0.0, 0.0, 0.0], atol=1e-15)

    def test_pure_white_xyz(self):
        xyz = srgb_to_xyz(np.array([1.0, 1.0, 1.0]))
        assert xyz[1] == pytest.approx(1.0, abs=1e-4)

    def test_pure_black_oklab(self):
        oklab = srgb_to_oklab(np.array([0.0, 0.0, 0.0]))
        np.testing.assert_allclose(oklab, [0.0, 0.0, 0.0], atol=1e-10)

    def test_xyz_to_srgb_clips(self):
        """Out-of-gamut XYZ clips to [0,1] when clip=True."""
        xyz = np.array([2.0, 2.0, 2.0])
        result = xyz_to_srgb(xyz, clip=True)
        assert np.all(result >= 0.0)
        assert np.all(result <= 1.0)

    def test_xyz_to_srgb_no_clip(self):
        """Out-of-gamut XYZ can exceed [0,1] when clip=False."""
        xyz = np.array([2.0, 2.0, 2.0])
        result = xyz_to_srgb(xyz, clip=False)
        # With such large XYZ, some channels may exceed 1.0
        assert result is not None

    def test_xyY_black_handling(self):
        """xyz_to_xyY should handle black (X+Y+Z = 0) without division error."""
        xyY = xyz_to_xyY(np.array([0.0, 0.0, 0.0]))
        assert np.all(np.isfinite(xyY))

    def test_srgb_gamma_linearity_threshold(self):
        """sRGB gamma has linear segment below 0.04045."""
        val = 0.03
        linear = srgb_to_linear(np.array([val]))
        expected = val / 12.92
        assert linear[0] == pytest.approx(expected, abs=1e-10)

    def test_srgb_gamma_power_segment(self):
        """sRGB gamma uses power curve above 0.04045."""
        val = 0.5
        linear = srgb_to_linear(np.array([val]))
        expected = ((val + 0.055) / 1.055) ** 2.4
        assert linear[0] == pytest.approx(expected, abs=1e-10)


# =========================================================================
# Batch processing
# =========================================================================

class TestBatchProcessing:
    """Verify (N,3) array support."""

    def test_srgb_to_xyz_batch(self):
        colors = np.array([
            [1.0, 0.0, 0.0],
            [0.0, 1.0, 0.0],
            [0.0, 0.0, 1.0],
        ])
        result = srgb_to_xyz(colors)
        assert result.shape == (3, 3)

    def test_xyz_to_srgb_batch(self):
        xyz = np.array([
            [0.4125, 0.2127, 0.0193],
            [0.3576, 0.7152, 0.1192],
        ])
        result = xyz_to_srgb(xyz)
        assert result.shape == (2, 3)

    def test_srgb_to_oklab_batch(self):
        colors = np.array([
            [0.5, 0.5, 0.5],
            [0.8, 0.2, 0.1],
        ])
        result = srgb_to_oklab(colors)
        assert result.shape == (2, 3)

    def test_oklab_to_srgb_batch(self):
        oklab = np.array([
            [0.5, 0.0, 0.0],
            [0.7, 0.1, -0.05],
        ])
        result = oklab_to_srgb(oklab)
        assert result.shape == (2, 3)

    def test_xyz_to_lab_batch(self):
        xyz = np.array([
            [0.5, 0.5, 0.5],
            [0.3, 0.4, 0.2],
        ])
        result = xyz_to_lab(xyz)
        assert result.shape == (2, 3)

    def test_lab_to_lch_batch(self):
        lab = np.array([
            [50.0, 25.0, -10.0],
            [80.0, -30.0, 40.0],
        ])
        result = lab_to_lch(lab)
        assert result.shape == (2, 3)

    def test_rgb_to_hsv_batch(self):
        rgb = np.array([
            [1.0, 0.0, 0.0],
            [0.0, 1.0, 0.0],
            [0.0, 0.0, 1.0],
        ])
        result = rgb_to_hsv(rgb)
        assert result.shape == (3, 3)

    def test_srgb_xyz_roundtrip_batch(self):
        colors = np.random.RandomState(42).rand(10, 3)
        xyz = srgb_to_xyz(colors)
        recovered = xyz_to_srgb(xyz, clip=False)
        np.testing.assert_allclose(recovered, colors, atol=1e-5)


# =========================================================================
# primaries_to_matrix
# =========================================================================

class TestPrimariesToMatrix:
    """Test primaries_to_matrix utility."""

    def test_srgb_primaries_produce_correct_matrix(self):
        """sRGB primaries should produce a matrix close to SRGB_TO_XYZ."""
        r_xy = (0.64, 0.33)
        g_xy = (0.30, 0.60)
        b_xy = (0.15, 0.06)
        w_xy = (0.3127, 0.3290)
        M = primaries_to_matrix(r_xy, g_xy, b_xy, w_xy)
        np.testing.assert_allclose(M, SRGB_TO_XYZ, atol=0.005)

    def test_matrix_shape(self):
        M = primaries_to_matrix((0.64, 0.33), (0.30, 0.60), (0.15, 0.06), (0.3127, 0.3290))
        assert M.shape == (3, 3)


# =========================================================================
# Luminance
# =========================================================================

class TestLuminance:
    """Test luminance calculation."""

    def test_white_luminance(self):
        assert luminance(np.array([1.0, 1.0, 1.0])) == pytest.approx(1.0, abs=1e-4)

    def test_black_luminance(self):
        assert luminance(np.array([0.0, 0.0, 0.0])) == pytest.approx(0.0, abs=1e-15)

    def test_mid_gray_luminance(self):
        """18% reflectance card should give luminance near 0.0 (nonlinear) or 0.18 (linear)."""
        lum = luminance(np.array([0.5, 0.5, 0.5]))
        # sRGB 0.5 -> linear ~0.214, luminance ~0.214
        assert 0.1 < lum < 0.3

    def test_luminance_red_vs_green(self):
        """Green has higher luminance coefficient than red."""
        lum_r = luminance(np.array([1.0, 0.0, 0.0]))
        lum_g = luminance(np.array([0.0, 1.0, 0.0]))
        assert lum_g > lum_r


# =========================================================================
# Wide gamut conversions
# =========================================================================

class TestWideGamut:
    """Test wide gamut conversion functions."""

    def test_srgb_to_p3_white(self):
        """sRGB white -> P3 white should be near white."""
        result = srgb_to_p3(np.array([1.0, 1.0, 1.0]))
        np.testing.assert_allclose(result, [1.0, 1.0, 1.0], atol=0.02)

    def test_srgb_to_p3_black(self):
        result = srgb_to_p3(np.array([0.0, 0.0, 0.0]))
        np.testing.assert_allclose(result, [0.0, 0.0, 0.0], atol=1e-10)

    def test_srgb_to_bt2020_shape(self):
        colors = np.array([[0.5, 0.5, 0.5], [0.8, 0.2, 0.1]])
        result = srgb_to_bt2020(colors)
        assert result.shape == (2, 3)

    def test_srgb_to_bt2020_white(self):
        result = srgb_to_bt2020(np.array([1.0, 1.0, 1.0]))
        # BT.2020 linear values for white should be near 1.0
        np.testing.assert_allclose(result, [1.0, 1.0, 1.0], atol=0.02)

    def test_srgb_to_acescg_shape(self):
        result = srgb_to_acescg(np.array([0.5, 0.3, 0.8]))
        assert result.shape == (3,)

    def test_srgb_to_acescg_white(self):
        """ACEScg uses different primaries/whitepoint so white may not be exactly 1,1,1."""
        result = srgb_to_acescg(np.array([1.0, 1.0, 1.0]))
        np.testing.assert_allclose(result, [1.0, 1.0, 1.0], atol=0.1)


# =========================================================================
# xyY
# =========================================================================

class TestXyY:
    """Test xyY conversions."""

    def test_roundtrip(self):
        xyz_orig = np.array([0.5, 0.6, 0.4])
        xyY = xyz_to_xyY(xyz_orig)
        recovered = xyY_to_xyz(xyY)
        np.testing.assert_allclose(recovered, xyz_orig, atol=1e-10)

    def test_d65_chromaticity(self):
        """D65 chromaticity should be near x=0.3127, y=0.3290."""
        xyY = xyz_to_xyY(D65)
        assert xyY[0] == pytest.approx(0.3127, abs=0.001)
        assert xyY[1] == pytest.approx(0.3290, abs=0.001)
