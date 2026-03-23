"""Tests for LUT I/O module."""
import numpy as np
import pytest
import tempfile
from pathlib import Path
from quanta_color.lut_io import (
    LUT3D,
    LUT1D,
    read_cube,
    write_cube,
    read_clf,
    write_clf,
    identity_lut,
    apply_lut,
    lut_from_function,
)


class TestIdentityLUT:
    """Test identity LUT creation."""

    def test_default_size(self):
        lut = identity_lut()
        assert lut.size == 33
        assert lut.data.shape == (33, 33, 33, 3)

    def test_custom_size(self):
        lut = identity_lut(size=5)
        assert lut.size == 5
        assert lut.data.shape == (5, 5, 5, 3)

    def test_corners(self):
        """Identity LUT should map corners correctly."""
        lut = identity_lut(size=5)
        # Black corner: data[0,0,0] should be (0,0,0)
        np.testing.assert_allclose(lut.data[0, 0, 0], [0, 0, 0], atol=1e-10)
        # White corner: data[-1,-1,-1] should be (1,1,1)
        np.testing.assert_allclose(lut.data[-1, -1, -1], [1, 1, 1], atol=1e-10)

    def test_red_corner(self):
        """data[0, 0, -1] should be (1, 0, 0) = pure red."""
        lut = identity_lut(size=5)
        np.testing.assert_allclose(lut.data[0, 0, -1], [1, 0, 0], atol=1e-10)

    def test_has_title(self):
        lut = identity_lut()
        assert lut.title == "Identity"


class TestCubeRoundtrip:
    """Test .cube file read/write roundtrip."""

    def test_3d_roundtrip(self):
        """Write and read back a 3D LUT, data should match."""
        lut = identity_lut(size=5)
        lut.title = "Test 3D LUT"

        with tempfile.NamedTemporaryFile(suffix=".cube", delete=False) as f:
            path = Path(f.name)

        try:
            write_cube(lut, path)
            loaded = read_cube(path)
            assert isinstance(loaded, LUT3D)
            assert loaded.size == 5
            assert loaded.title == "Test 3D LUT"
            np.testing.assert_allclose(loaded.data, lut.data, atol=1e-8)
        finally:
            path.unlink(missing_ok=True)

    def test_1d_roundtrip(self):
        """Write and read back a 1D LUT."""
        data = np.column_stack([
            np.linspace(0, 1, 16),
            np.linspace(0, 1, 16),
            np.linspace(0, 1, 16),
        ])
        lut = LUT1D(data=data, size=16, title="Test 1D")

        with tempfile.NamedTemporaryFile(suffix=".cube", delete=False) as f:
            path = Path(f.name)

        try:
            write_cube(lut, path)
            loaded = read_cube(path)
            assert isinstance(loaded, LUT1D)
            assert loaded.size == 16
            assert loaded.title == "Test 1D"
            np.testing.assert_allclose(loaded.data, lut.data, atol=1e-8)
        finally:
            path.unlink(missing_ok=True)


class TestCLFRoundtrip:
    """Test CLF XML read/write roundtrip."""

    def test_clf_roundtrip(self):
        """Write and read back a CLF 3D LUT."""
        lut = identity_lut(size=5)
        lut.title = "CLF Test"

        with tempfile.NamedTemporaryFile(suffix=".clf", delete=False) as f:
            path = Path(f.name)

        try:
            write_clf(lut, path)
            loaded = read_clf(path)
            assert isinstance(loaded, LUT3D)
            assert loaded.size == 5
            np.testing.assert_allclose(loaded.data, lut.data, atol=1e-8)
        finally:
            path.unlink(missing_ok=True)


class TestApplyLUT:
    """Test LUT application with trilinear interpolation."""

    def test_identity_preserves_image(self):
        """Applying identity LUT should not change the image."""
        lut = identity_lut(size=17)
        image = np.random.RandomState(42).rand(4, 6, 3)
        result = apply_lut(image, lut)
        np.testing.assert_allclose(result, image, atol=0.02)

    def test_output_shape(self):
        """Output shape should match input."""
        lut = identity_lut(size=5)
        image = np.random.RandomState(42).rand(10, 15, 3)
        result = apply_lut(image, lut)
        assert result.shape == (10, 15, 3)

    def test_black_stays_black(self):
        """Black input through identity should stay black."""
        lut = identity_lut(size=5)
        image = np.zeros((2, 2, 3))
        result = apply_lut(image, lut)
        np.testing.assert_allclose(result, 0.0, atol=1e-10)

    def test_white_stays_white(self):
        """White input through identity should stay white."""
        lut = identity_lut(size=5)
        image = np.ones((2, 2, 3))
        result = apply_lut(image, lut)
        np.testing.assert_allclose(result, 1.0, atol=1e-10)


class TestLUTFromFunction:
    """Test baking a function into a LUT."""

    def test_identity_function(self):
        """Baking an identity function should produce an identity LUT."""
        lut = lut_from_function(lambda x: x, size=5)
        identity = identity_lut(size=5)
        np.testing.assert_allclose(lut.data, identity.data, atol=1e-10)

    def test_invert_function(self):
        """Baking a negative function should produce inverted values."""
        lut = lut_from_function(lambda x: 1.0 - x, size=5)
        # Black corner should map to white
        np.testing.assert_allclose(lut.data[0, 0, 0], [1, 1, 1], atol=1e-10)
        # White corner should map to black
        np.testing.assert_allclose(lut.data[-1, -1, -1], [0, 0, 0], atol=1e-10)

    def test_output_size(self):
        lut = lut_from_function(lambda x: x * 0.5, size=9)
        assert lut.size == 9
        assert lut.data.shape == (9, 9, 9, 3)


class TestLUT3DValidation:
    """Test LUT3D dataclass validation."""

    def test_valid_creation(self):
        data = np.zeros((3, 3, 3, 3))
        lut = LUT3D(data=data, size=3)
        assert lut.size == 3

    def test_invalid_shape_raises(self):
        """Mismatched data shape should raise ValueError."""
        data = np.zeros((4, 4, 4, 3))
        with pytest.raises(ValueError):
            LUT3D(data=data, size=3)


class TestLUT1DValidation:
    """Test LUT1D dataclass validation."""

    def test_valid_creation(self):
        data = np.zeros((10, 3))
        lut = LUT1D(data=data, size=10)
        assert lut.size == 10

    def test_invalid_shape_raises(self):
        data = np.zeros((10, 3))
        with pytest.raises(ValueError):
            LUT1D(data=data, size=5)
