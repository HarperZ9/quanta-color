"""Tests for color naming module."""
import numpy as np
import pytest
from quanta_color.naming import (
    nearest_css_name,
    nearest_basic_name,
    color_description,
    all_css_colors,
    CSS_COLORS,
)


class TestNearestCSSName:
    """Test nearest_css_name function."""

    def test_exact_red(self):
        """Pure red should match CSS 'red' exactly."""
        name, dist = nearest_css_name(np.array([1.0, 0.0, 0.0]))
        assert name == "red"
        assert dist < 0.001

    def test_exact_blue(self):
        """Pure blue should match CSS 'blue'."""
        name, dist = nearest_css_name(np.array([0.0, 0.0, 1.0]))
        assert name == "blue"
        assert dist < 0.001

    def test_exact_white(self):
        """Pure white should match CSS 'white'."""
        name, dist = nearest_css_name(np.array([1.0, 1.0, 1.0]))
        assert name == "white"
        assert dist < 0.001

    def test_exact_black(self):
        """Pure black should match CSS 'black'."""
        name, dist = nearest_css_name(np.array([0.0, 0.0, 0.0]))
        assert name == "black"
        assert dist < 0.001

    def test_returns_tuple(self):
        """Should return (name, distance) tuple."""
        result = nearest_css_name(np.array([0.5, 0.3, 0.7]))
        assert isinstance(result, tuple)
        assert len(result) == 2
        assert isinstance(result[0], str)
        assert isinstance(result[1], float)

    def test_distance_non_negative(self):
        """Distance should always be non-negative."""
        _, dist = nearest_css_name(np.array([0.42, 0.87, 0.13]))
        assert dist >= 0.0

    def test_near_coral(self):
        """A color close to coral should match coral."""
        # coral is (255, 127, 80) = (1.0, 0.498, 0.314)
        name, dist = nearest_css_name(np.array([1.0, 0.498, 0.314]))
        assert name == "coral"
        assert dist < 0.01


class TestNearestBasicName:
    """Test nearest_basic_name function."""

    def test_red(self):
        assert nearest_basic_name(np.array([0.9, 0.1, 0.1])) == "red"

    def test_blue(self):
        assert nearest_basic_name(np.array([0.1, 0.1, 0.9])) == "blue"

    def test_green(self):
        name = nearest_basic_name(np.array([0.0, 0.5, 0.0]))
        assert name == "green"

    def test_white(self):
        assert nearest_basic_name(np.array([1.0, 1.0, 1.0])) == "white"

    def test_black(self):
        assert nearest_basic_name(np.array([0.0, 0.0, 0.0])) == "black"

    def test_returns_string(self):
        result = nearest_basic_name(np.array([0.5, 0.5, 0.5]))
        assert isinstance(result, str)


class TestColorDescription:
    """Test color_description function."""

    def test_black(self):
        desc = color_description(np.array([0.0, 0.0, 0.0]))
        assert "black" in desc

    def test_white(self):
        desc = color_description(np.array([1.0, 1.0, 1.0]))
        assert "white" in desc

    def test_gray(self):
        desc = color_description(np.array([0.5, 0.5, 0.5]))
        assert "gray" in desc

    def test_vivid_color_has_hue(self):
        """A saturated color should include a hue name."""
        desc = color_description(np.array([1.0, 0.0, 0.0]))
        # Should contain a hue word like red/orange
        assert len(desc) > 0
        # Should not be just "gray" or "black"
        assert "gray" not in desc
        assert "black" not in desc

    def test_returns_string(self):
        desc = color_description(np.array([0.3, 0.6, 0.9]))
        assert isinstance(desc, str)
        assert len(desc) > 0


class TestAllCSSColors:
    """Test all_css_colors function."""

    def test_returns_dict(self):
        result = all_css_colors()
        assert isinstance(result, dict)

    def test_count(self):
        """Should return all 148 CSS named colors."""
        result = all_css_colors()
        assert len(result) == 148

    def test_contains_standard_colors(self):
        result = all_css_colors()
        for name in ["red", "green", "blue", "white", "black", "rebeccapurple"]:
            assert name in result

    def test_values_are_rgb_tuples(self):
        result = all_css_colors()
        for name, rgb in result.items():
            assert len(rgb) == 3
            assert all(0 <= c <= 255 for c in rgb)

    def test_is_copy(self):
        """Returned dict should be a copy, not the internal constant."""
        result = all_css_colors()
        assert result is not CSS_COLORS
