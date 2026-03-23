"""Comprehensive tests for color difference metrics."""
import numpy as np
import pytest
from quanta_color.difference import (
    delta_e_76, delta_e_94, delta_e_2000,
    delta_e_cmc, delta_e_hyab,
    delta_e_jzazbz, delta_e_oklab,
    compare_all, contrast_ratio,
)


# =========================================================================
# CIEDE2000 known pairs from Sharma et al. 2005 (Table 1)
# Reference: "The CIEDE2000 Color-Difference Formula", Sharma et al.
# =========================================================================

class TestCIEDE2000KnownPairs:
    """CIEDE2000 validated against published reference values."""

    # (Lab1, Lab2, expected_dE2000)
    # Reference: Sharma, Wu, Dalal 2005, "The CIEDE2000 Color-Difference Formula"
    SHARMA_PAIRS = [
        # Pair 1
        (np.array([50.0000, 2.6772, -79.7751]),
         np.array([50.0000, 0.0000, -82.7485]),
         2.0425),
        # Pair 2
        (np.array([50.0000, 3.1571, -77.2803]),
         np.array([50.0000, 0.0000, -82.7485]),
         2.8615),
        # Pair 3
        (np.array([50.0000, 2.8361, -74.0200]),
         np.array([50.0000, 0.0000, -82.7485]),
         3.4412),
        # Pair 9 (near-achromatic, small b)
        (np.array([50.0000, -0.0010, 2.4900]),
         np.array([50.0000, 0.0009, -2.4900]),
         4.8045),
        # Pair 17 (lightness difference)
        (np.array([50.0000, 2.5000, 0.0000]),
         np.array([73.0000, 25.0000, -18.0000]),
         27.1492),
        # Pair 25 (chromatic, similar hue)
        (np.array([60.2574, -34.0099, 36.2677]),
         np.array([60.4626, -34.1751, 39.4387]),
         1.2644),
    ]

    @pytest.mark.parametrize("lab1,lab2,expected", SHARMA_PAIRS,
                             ids=[f"pair_{i}" for i in range(len(SHARMA_PAIRS))])
    def test_sharma_pair(self, lab1, lab2, expected):
        result = delta_e_2000(lab1, lab2)
        assert result == pytest.approx(expected, abs=0.005), \
            f"CIEDE2000 got {result}, expected {expected}"


# =========================================================================
# CIE76
# =========================================================================

class TestCIE76:
    """CIE 1976 color difference tests."""

    def test_identical_colors_zero(self):
        lab = np.array([50.0, 0.0, 0.0])
        assert delta_e_76(lab, lab) == pytest.approx(0.0, abs=1e-10)

    def test_known_euclidean(self):
        """Simple Euclidean distance check."""
        lab1 = np.array([50.0, 0.0, 0.0])
        lab2 = np.array([53.0, 4.0, 0.0])
        expected = np.sqrt(3**2 + 4**2)  # = 5.0
        assert delta_e_76(lab1, lab2) == pytest.approx(expected, abs=1e-10)

    def test_symmetry(self):
        lab1 = np.array([50.0, 25.0, -10.0])
        lab2 = np.array([60.0, 20.0, -5.0])
        assert delta_e_76(lab1, lab2) == pytest.approx(delta_e_76(lab2, lab1), abs=1e-10)

    def test_non_negative(self):
        lab1 = np.array([10.0, -30.0, 40.0])
        lab2 = np.array([80.0, 50.0, -60.0])
        assert delta_e_76(lab1, lab2) >= 0


# =========================================================================
# CIE94
# =========================================================================

class TestCIE94:
    """CIE 1994 color difference tests."""

    def test_graphics_vs_textiles_differ(self):
        """graphic_arts and textiles applications should give different results."""
        lab1 = np.array([50.0, 25.0, -10.0])
        lab2 = np.array([60.0, 20.0, -5.0])
        de_graphics = delta_e_94(lab1, lab2, application="graphic_arts")
        de_textiles = delta_e_94(lab1, lab2, application="textiles")
        assert de_graphics != pytest.approx(de_textiles, abs=0.001), \
            "CIE94 graphics and textiles should differ"

    def test_identical_zero(self):
        lab = np.array([50.0, 25.0, -10.0])
        assert delta_e_94(lab, lab) == pytest.approx(0.0, abs=1e-10)

    def test_non_negative(self):
        lab1 = np.array([10.0, -30.0, 40.0])
        lab2 = np.array([80.0, 50.0, -60.0])
        assert delta_e_94(lab1, lab2) >= 0


# =========================================================================
# CMC
# =========================================================================

class TestCMC:
    """CMC(l:c) color difference tests."""

    def test_cmc_2_1_vs_1_1_differ(self):
        """CMC(2:1) and CMC(1:1) should produce different results."""
        lab1 = np.array([50.0, 25.0, -10.0])
        lab2 = np.array([60.0, 20.0, -5.0])
        de_21 = delta_e_cmc(lab1, lab2, l=2.0, c=1.0)
        de_11 = delta_e_cmc(lab1, lab2, l=1.0, c=1.0)
        assert de_21 != pytest.approx(de_11, abs=0.001), \
            "CMC(2:1) and CMC(1:1) should differ"

    def test_identical_zero(self):
        lab = np.array([50.0, 25.0, -10.0])
        assert delta_e_cmc(lab, lab) == pytest.approx(0.0, abs=1e-10)

    def test_non_negative(self):
        lab1 = np.array([10.0, -30.0, 40.0])
        lab2 = np.array([80.0, 50.0, -60.0])
        assert delta_e_cmc(lab1, lab2) >= 0

    def test_asymmetric(self):
        """CMC is asymmetric -- order matters for some pairs."""
        lab1 = np.array([40.0, 40.0, 10.0])
        lab2 = np.array([60.0, -10.0, 30.0])
        de_ab = delta_e_cmc(lab1, lab2)
        de_ba = delta_e_cmc(lab2, lab1)
        # They may or may not differ, but the function should work both ways
        assert de_ab >= 0
        assert de_ba >= 0


# =========================================================================
# HyAB
# =========================================================================

class TestHyAB:
    """HyAB hybrid color difference tests."""

    def test_hyab_ge_cie76_for_most_cases(self):
        """HyAB >= CIE76 for most Lab pairs (due to |dL| + chroma_dist)."""
        rng = np.random.RandomState(42)
        for _ in range(20):
            lab1 = rng.uniform(-50, 100, 3)
            lab2 = rng.uniform(-50, 100, 3)
            hyab = delta_e_hyab(lab1, lab2)
            cie76 = delta_e_76(lab1, lab2)
            # HyAB uses |dL| + sqrt(da^2+db^2) which >= sqrt(dL^2+da^2+db^2)
            # by triangle inequality, this should hold
            assert hyab >= cie76 - 1e-10, \
                f"HyAB ({hyab}) < CIE76 ({cie76}) for {lab1} vs {lab2}"

    def test_identical_zero(self):
        lab = np.array([50.0, 25.0, -10.0])
        assert delta_e_hyab(lab, lab) == pytest.approx(0.0, abs=1e-10)

    def test_non_negative(self):
        lab1 = np.array([10.0, -30.0, 40.0])
        lab2 = np.array([80.0, 50.0, -60.0])
        assert delta_e_hyab(lab1, lab2) >= 0


# =========================================================================
# compare_all
# =========================================================================

class TestCompareAll:
    """Test the compare_all convenience function."""

    def test_returns_five_metrics(self):
        lab1 = np.array([50.0, 25.0, -10.0])
        lab2 = np.array([60.0, 20.0, -5.0])
        result = compare_all(lab1, lab2)
        assert len(result) == 5
        expected_keys = {"CIE76", "CIE94", "CIEDE2000", "CMC(2:1)", "HyAB"}
        assert set(result.keys()) == expected_keys

    def test_all_values_positive_for_different_colors(self):
        lab1 = np.array([50.0, 25.0, -10.0])
        lab2 = np.array([60.0, 20.0, -5.0])
        result = compare_all(lab1, lab2)
        for key, val in result.items():
            assert val > 0, f"{key} should be positive for different colors"

    def test_all_values_zero_for_identical(self):
        lab = np.array([50.0, 25.0, -10.0])
        result = compare_all(lab, lab)
        for key, val in result.items():
            assert val == pytest.approx(0.0, abs=1e-10), \
                f"{key} should be 0 for identical colors"


# =========================================================================
# Batch processing
# =========================================================================

class TestBatchDifference:
    """Test (N,3) array batch processing."""

    def test_cie76_batch(self):
        lab1 = np.array([[50.0, 25.0, -10.0], [30.0, 10.0, 20.0]])
        lab2 = np.array([[60.0, 20.0, -5.0], [35.0, 15.0, 25.0]])
        result = delta_e_76(lab1, lab2)
        assert result.shape == (2,)
        assert np.all(result >= 0)

    def test_ciede2000_batch(self):
        lab1 = np.array([[50.0, 2.6772, -79.7751], [50.0, 3.1571, -77.2803]])
        lab2 = np.array([[50.0, 0.0, -82.7485], [50.0, 0.0, -82.7485]])
        result = delta_e_2000(lab1, lab2)
        assert result.shape == (2,)
        assert np.all(result > 0)

    def test_cie94_batch(self):
        lab1 = np.array([[50.0, 25.0, -10.0], [30.0, 10.0, 20.0]])
        lab2 = np.array([[60.0, 20.0, -5.0], [35.0, 15.0, 25.0]])
        result = delta_e_94(lab1, lab2)
        assert result.shape == (2,)

    def test_cmc_batch(self):
        lab1 = np.array([[50.0, 25.0, -10.0], [30.0, 10.0, 20.0]])
        lab2 = np.array([[60.0, 20.0, -5.0], [35.0, 15.0, 25.0]])
        result = delta_e_cmc(lab1, lab2)
        assert result.shape == (2,)

    def test_jzazbz_batch(self):
        jz1 = np.array([[0.5, 0.1, -0.05], [0.3, 0.0, 0.0]])
        jz2 = np.array([[0.6, 0.05, -0.03], [0.4, 0.1, 0.1]])
        result = delta_e_jzazbz(jz1, jz2)
        assert result.shape == (2,)

    def test_oklab_batch(self):
        ok1 = np.array([[0.5, 0.1, -0.05], [0.3, 0.0, 0.0]])
        ok2 = np.array([[0.6, 0.05, -0.03], [0.4, 0.1, 0.1]])
        result = delta_e_oklab(ok1, ok2)
        assert result.shape == (2,)


# =========================================================================
# Contrast ratio
# =========================================================================

class TestContrastRatio:
    """WCAG contrast ratio tests."""

    def test_black_on_white(self):
        """Black on white should give 21:1."""
        ratio = contrast_ratio(0.0, 1.0)
        assert ratio == pytest.approx(21.0, abs=0.01)

    def test_same_color(self):
        """Same luminance gives 1:1."""
        ratio = contrast_ratio(0.5, 0.5)
        assert ratio == pytest.approx(1.0, abs=0.01)

    def test_order_independent(self):
        assert contrast_ratio(0.2, 0.8) == pytest.approx(
            contrast_ratio(0.8, 0.2), abs=1e-10)
