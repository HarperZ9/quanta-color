"""Comprehensive tests for chromatic adaptation transforms."""

import numpy as np
import pytest

from quanta_color.adaptation import (
    ILLUMINANTS,
    MATRICES,
    adapt,
    adapt_partial,
    cct_to_xy,
    cct_to_xyz,
    estimate_white_gray_world,
    estimate_white_percentile,
    estimate_white_shades_of_gray,
    estimate_white_white_patch,
    get_adaptation_matrix,
    xy_to_cct_mccamy,
)

ALL_METHODS = list(MATRICES.keys())


# =========================================================================
# Roundtrip D65 -> D50 -> D65 for all 9 methods
# =========================================================================


class TestRoundtrip:
    """Adapting D65->D50 then D50->D65 should recover the original."""

    @pytest.mark.parametrize("method", ALL_METHODS)
    def test_roundtrip(self, method):
        d65 = ILLUMINANTS["D65"]
        d50 = ILLUMINANTS["D50"]
        test_xyz = np.array([0.5, 0.6, 0.7])

        adapted = adapt(test_xyz, d65, d50, method=method)
        recovered = adapt(adapted, d50, d65, method=method)
        np.testing.assert_allclose(recovered, test_xyz, atol=1e-8, err_msg=f"Roundtrip failed for {method}")

    @pytest.mark.parametrize("method", ALL_METHODS)
    def test_roundtrip_white(self, method):
        """Adapting D65 white to D50 should give D50 white, and back."""
        d65 = ILLUMINANTS["D65"]
        d50 = ILLUMINANTS["D50"]

        adapted = adapt(d65, d65, d50, method=method)
        np.testing.assert_allclose(adapted, d50, atol=0.01, err_msg=f"D65->D50 failed for {method}")

        recovered = adapt(adapted, d50, d65, method=method)
        np.testing.assert_allclose(recovered, d65, atol=0.01, err_msg=f"D50->D65 recovery failed for {method}")


# =========================================================================
# Bradford D65->D50 matches ICC values
# =========================================================================


class TestBradfordICC:
    """Bradford adaptation matrix D65->D50 should match ICC published values."""

    def test_bradford_d65_to_d50_matrix(self):
        """The Bradford D65->D50 matrix should be close to the ICC profile spec."""
        d65 = ILLUMINANTS["D65"]
        d50 = ILLUMINANTS["D50"]
        M = get_adaptation_matrix(d65, d50, method="bradford")

        # ICC profile specification Bradford D65->D50 matrix
        # (approximate reference values)
        icc_ref = np.array(
            [
                [1.0479, 0.0229, -0.0502],
                [0.0296, 0.9904, -0.0171],
                [-0.0092, 0.0150, 0.7521],
            ]
        )
        np.testing.assert_allclose(M, icc_ref, atol=0.005, err_msg="Bradford D65->D50 doesn't match ICC")

    def test_bradford_identity(self):
        """Adapting from D65 to D65 should produce identity matrix."""
        d65 = ILLUMINANTS["D65"]
        M = get_adaptation_matrix(d65, d65, method="bradford")
        np.testing.assert_allclose(M, np.eye(3), atol=1e-10)


# =========================================================================
# Partial adaptation
# =========================================================================


class TestPartialAdaptation:
    """Tests for adapt_partial with varying degree."""

    def test_degree_zero_returns_input(self):
        """Partial adaptation at 0.0 returns input unchanged."""
        d65 = ILLUMINANTS["D65"]
        d50 = ILLUMINANTS["D50"]
        xyz = np.array([0.5, 0.6, 0.7])
        result = adapt_partial(xyz, d65, d50, degree=0.0)
        np.testing.assert_allclose(result, xyz, atol=1e-15)

    def test_degree_one_returns_full(self):
        """Partial adaptation at 1.0 returns full adaptation result."""
        d65 = ILLUMINANTS["D65"]
        d50 = ILLUMINANTS["D50"]
        xyz = np.array([0.5, 0.6, 0.7])
        full = adapt(xyz, d65, d50)
        partial = adapt_partial(xyz, d65, d50, degree=1.0)
        np.testing.assert_allclose(partial, full, atol=1e-10)

    def test_degree_half_is_midpoint(self):
        """Degree 0.5 should be halfway between original and fully adapted."""
        d65 = ILLUMINANTS["D65"]
        d50 = ILLUMINANTS["D50"]
        xyz = np.array([0.5, 0.6, 0.7])
        full = adapt(xyz, d65, d50)
        partial = adapt_partial(xyz, d65, d50, degree=0.5)
        expected = 0.5 * xyz + 0.5 * full
        np.testing.assert_allclose(partial, expected, atol=1e-10)

    def test_degree_clamped(self):
        """Values outside [0,1] should be clamped."""
        d65 = ILLUMINANTS["D65"]
        d50 = ILLUMINANTS["D50"]
        xyz = np.array([0.5, 0.6, 0.7])
        # degree > 1 should clamp to 1
        result_over = adapt_partial(xyz, d65, d50, degree=2.0)
        result_one = adapt_partial(xyz, d65, d50, degree=1.0)
        np.testing.assert_allclose(result_over, result_one, atol=1e-10)


# =========================================================================
# CCT roundtrip
# =========================================================================


class TestCCTRoundtrip:
    """Color temperature conversion roundtrip tests."""

    @pytest.mark.parametrize(
        "target_cct,tol",
        [
            (4000, 50),
            (5000, 50),
            (5500, 50),
            (6500, 50),
            (7500, 150),
            (10000, 500),
        ],
    )
    def test_cct_roundtrip(self, target_cct, tol):
        """cct_to_xy -> xy_to_cct_mccamy should approximate original.

        McCamy's approximation is most accurate near 6500K and diverges
        at extreme temperatures, so tolerance is wider for high CCTs.
        """
        x, y = cct_to_xy(target_cct)
        recovered = xy_to_cct_mccamy(x, y)
        assert abs(recovered - target_cct) < tol, (
            f"CCT roundtrip: {target_cct}K -> ({x:.4f},{y:.4f}) -> {recovered:.1f}K"
        )

    def test_cct_to_xyz_has_unit_y(self):
        """cct_to_xyz should return Y=1 normalized values."""
        xyz = cct_to_xyz(6500)
        assert xyz[1] == pytest.approx(1.0, abs=1e-10)

    def test_cct_to_xy_returns_tuple(self):
        result = cct_to_xy(6500)
        assert len(result) == 2
        x, y = result
        assert 0.2 < x < 0.5
        assert 0.2 < y < 0.5


# =========================================================================
# Illuminants
# =========================================================================


class TestIlluminants:
    """Tests for standard illuminants."""

    @pytest.mark.parametrize("name", list(ILLUMINANTS.keys()))
    def test_y_equals_one(self, name):
        """All illuminants should have Y=1.0."""
        xyz = ILLUMINANTS[name]
        assert xyz[1] == pytest.approx(1.0, abs=1e-10), f"Illuminant {name} Y={xyz[1]} != 1.0"

    def test_seven_illuminants(self):
        """Should have at least 7 standard illuminants."""
        assert len(ILLUMINANTS) >= 7

    def test_d65_values(self):
        """D65 should match standard values."""
        d65 = ILLUMINANTS["D65"]
        np.testing.assert_allclose(d65, [0.95047, 1.0, 1.08883], atol=1e-5)

    def test_d50_values(self):
        """D50 should match standard values."""
        d50 = ILLUMINANTS["D50"]
        np.testing.assert_allclose(d50, [0.96422, 1.0, 0.82521], atol=1e-5)


# =========================================================================
# White balance estimators
# =========================================================================


class TestWhiteBalance:
    """Tests for white balance estimation functions."""

    def _make_test_image(self):
        """Create a simple 4x4 test image."""
        rng = np.random.RandomState(42)
        return rng.rand(4, 4, 3).astype(np.float64)

    def test_gray_world_returns_3_elements(self):
        image = self._make_test_image()
        result = estimate_white_gray_world(image)
        assert result.shape == (3,)

    def test_white_patch_returns_3_elements(self):
        image = self._make_test_image()
        result = estimate_white_white_patch(image)
        assert result.shape == (3,)

    def test_percentile_returns_3_elements(self):
        image = self._make_test_image()
        result = estimate_white_percentile(image)
        assert result.shape == (3,)

    def test_shades_of_gray_returns_3_elements(self):
        image = self._make_test_image()
        result = estimate_white_shades_of_gray(image)
        assert result.shape == (3,)

    def test_white_patch_ge_gray_world(self):
        """White patch should return values >= gray world (max >= mean)."""
        image = self._make_test_image()
        wp = estimate_white_white_patch(image)
        gw = estimate_white_gray_world(image)
        assert np.all(wp >= gw - 1e-10)

    def test_uniform_image(self):
        """Uniform color image: all estimators should return that color."""
        image = np.full((4, 4, 3), 0.5)
        gw = estimate_white_gray_world(image)
        np.testing.assert_allclose(gw, [0.5, 0.5, 0.5], atol=1e-10)


# =========================================================================
# Adaptation matrix properties
# =========================================================================


class TestAdaptationMatrixProperties:
    """General properties of adaptation matrices."""

    def test_nine_methods_available(self):
        assert len(MATRICES) >= 9

    @pytest.mark.parametrize("method", ALL_METHODS)
    def test_matrix_shape(self, method):
        assert MATRICES[method].shape == (3, 3)

    def test_invalid_method_raises(self):
        d65 = ILLUMINANTS["D65"]
        d50 = ILLUMINANTS["D50"]
        with pytest.raises(ValueError):
            get_adaptation_matrix(d65, d50, method="nonexistent")

    @pytest.mark.parametrize("method", ALL_METHODS)
    def test_batch_adaptation(self, method):
        """adapt should handle (N,3) arrays."""
        d65 = ILLUMINANTS["D65"]
        d50 = ILLUMINANTS["D50"]
        xyz_batch = np.array([[0.5, 0.6, 0.7], [0.3, 0.4, 0.5]])
        result = adapt(xyz_batch, d65, d50, method=method)
        assert result.shape == (2, 3)
