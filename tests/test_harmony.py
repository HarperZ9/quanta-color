"""Comprehensive tests for color harmony generation."""
import numpy as np
import pytest

from quanta_color.harmony import (
    SCHEMES,
    analogous,
    complementary,
    generate,
    monochromatic,
    split_complementary,
    tetradic,
    triadic,
)

BASE_RED = np.array([0.8, 0.2, 0.1])
BASE_BLUE = np.array([0.1, 0.3, 0.9])
BASE_GREEN = np.array([0.2, 0.8, 0.3])


# =========================================================================
# Count tests
# =========================================================================

class TestColorCounts:
    """Verify each scheme returns the correct number of colors."""

    def test_complementary_returns_2(self):
        result = complementary(BASE_RED)
        assert len(result) == 2

    def test_split_complementary_returns_3(self):
        result = split_complementary(BASE_RED)
        assert len(result) == 3

    def test_triadic_returns_3(self):
        result = triadic(BASE_RED)
        assert len(result) == 3

    def test_tetradic_returns_4(self):
        result = tetradic(BASE_RED)
        assert len(result) == 4

    def test_analogous_default_5(self):
        result = analogous(BASE_RED)
        assert len(result) == 5

    def test_analogous_custom_count(self):
        result = analogous(BASE_RED, count=7)
        assert len(result) == 7

    def test_analogous_count_3(self):
        result = analogous(BASE_RED, count=3)
        assert len(result) == 3

    def test_monochromatic_default_5(self):
        result = monochromatic(BASE_RED)
        assert len(result) == 5

    def test_monochromatic_custom_count(self):
        result = monochromatic(BASE_RED, count=8)
        assert len(result) == 8


# =========================================================================
# Valid sRGB range [0, 1]
# =========================================================================

class TestOutputRange:
    """All outputs should be in valid sRGB range [0, 1]."""

    @pytest.mark.parametrize("base", [BASE_RED, BASE_BLUE, BASE_GREEN])
    def test_complementary_range(self, base):
        for color in complementary(base):
            assert np.all(color >= 0.0) and np.all(color <= 1.0), \
                f"complementary out of range: {color}"

    @pytest.mark.parametrize("base", [BASE_RED, BASE_BLUE, BASE_GREEN])
    def test_split_complementary_range(self, base):
        for color in split_complementary(base):
            assert np.all(color >= 0.0) and np.all(color <= 1.0), \
                f"split_complementary out of range: {color}"

    @pytest.mark.parametrize("base", [BASE_RED, BASE_BLUE, BASE_GREEN])
    def test_triadic_range(self, base):
        for color in triadic(base):
            assert np.all(color >= 0.0) and np.all(color <= 1.0), \
                f"triadic out of range: {color}"

    @pytest.mark.parametrize("base", [BASE_RED, BASE_BLUE, BASE_GREEN])
    def test_tetradic_range(self, base):
        for color in tetradic(base):
            assert np.all(color >= 0.0) and np.all(color <= 1.0), \
                f"tetradic out of range: {color}"

    @pytest.mark.parametrize("base", [BASE_RED, BASE_BLUE, BASE_GREEN])
    def test_analogous_range(self, base):
        for color in analogous(base):
            assert np.all(color >= 0.0) and np.all(color <= 1.0), \
                f"analogous out of range: {color}"

    @pytest.mark.parametrize("base", [BASE_RED, BASE_BLUE, BASE_GREEN])
    def test_monochromatic_range(self, base):
        for color in monochromatic(base):
            assert np.all(color >= 0.0) and np.all(color <= 1.0), \
                f"monochromatic out of range: {color}"


# =========================================================================
# generate() with all scheme names
# =========================================================================

class TestGenerate:
    """Test the generate() dispatch function."""

    @pytest.mark.parametrize("scheme", list(SCHEMES.keys()))
    def test_generate_all_schemes(self, scheme):
        result = generate(BASE_RED, scheme=scheme)
        assert isinstance(result, list)
        assert len(result) >= 2

    def test_generate_invalid_scheme_raises(self):
        with pytest.raises(ValueError):
            generate(BASE_RED, scheme="nonexistent_scheme")

    def test_generate_complementary(self):
        result = generate(BASE_RED, scheme="complementary")
        assert len(result) == 2

    def test_generate_triadic(self):
        result = generate(BASE_RED, scheme="triadic")
        assert len(result) == 3

    def test_generate_tetradic(self):
        result = generate(BASE_RED, scheme="tetradic")
        assert len(result) == 4

    def test_generate_analogous_with_kwargs(self):
        result = generate(BASE_RED, scheme="analogous", count=7)
        assert len(result) == 7

    def test_generate_monochromatic_with_kwargs(self):
        result = generate(BASE_RED, scheme="monochromatic", count=4)
        assert len(result) == 4


# =========================================================================
# Scheme properties
# =========================================================================

class TestSchemeProperties:
    """Test expected properties of color harmony schemes."""

    def test_complementary_first_is_base(self):
        """First color in complementary should be the base color."""
        result = complementary(BASE_RED)
        np.testing.assert_allclose(result[0], BASE_RED, atol=1e-10)

    def test_triadic_first_is_base(self):
        result = triadic(BASE_RED)
        np.testing.assert_allclose(result[0], BASE_RED, atol=1e-10)

    def test_tetradic_first_is_base(self):
        result = tetradic(BASE_RED)
        np.testing.assert_allclose(result[0], BASE_RED, atol=1e-10)

    def test_complementary_colors_differ(self):
        """Complementary colors should be noticeably different."""
        result = complementary(BASE_RED)
        assert not np.allclose(result[0], result[1], atol=0.05), \
            "Complementary colors should differ"

    def test_triadic_colors_all_differ(self):
        """All three triadic colors should differ from each other."""
        result = triadic(BASE_RED)
        assert not np.allclose(result[0], result[1], atol=0.05)
        assert not np.allclose(result[1], result[2], atol=0.05)
        assert not np.allclose(result[0], result[2], atol=0.05)

    def test_monochromatic_varies_lightness(self):
        """Monochromatic should produce colors of varying lightness."""
        result = monochromatic(BASE_RED, count=5)
        from quanta_color.spaces import srgb_to_oklab
        lightnesses = [srgb_to_oklab(c)[0] for c in result]
        # Lightness values should span a range
        assert max(lightnesses) - min(lightnesses) > 0.2

    def test_all_output_shapes(self):
        """All returned colors should be (3,) arrays."""
        for scheme_name in SCHEMES:
            result = generate(BASE_RED, scheme=scheme_name)
            for i, color in enumerate(result):
                assert color.shape == (3,), \
                    f"{scheme_name} color {i} has shape {color.shape}"


# =========================================================================
# Schemes dict
# =========================================================================

class TestSchemesDict:
    """Test the SCHEMES dictionary."""

    def test_six_schemes(self):
        assert len(SCHEMES) == 6

    def test_all_callable(self):
        for name, fn in SCHEMES.items():
            assert callable(fn), f"Scheme {name} is not callable"

    def test_expected_names(self):
        expected = {
            "complementary", "split_complementary", "triadic",
            "tetradic", "analogous", "monochromatic",
        }
        assert set(SCHEMES.keys()) == expected
