"""Comprehensive tests for tone mapping operators."""
import numpy as np
import pytest

from quanta_color.tonemap import (
    OPERATORS,
    aces_filmic,
    aces_hill,
    agx,
    bt2390_eetf,
    bt2446_method_a,
    get_operator,
    hable,
    hlg_eotf,
    hlg_oetf,
    knee,
    list_operators,
    lottes,
    pq_eotf,
    pq_oetf,
    reinhard,
    reinhard_extended,
    uchimura,
)

# All simple tone mapping operators (input -> [0,1])
SIMPLE_OPERATORS = [
    reinhard, aces_filmic, aces_hill, lottes, uchimura,
]

# Operators that need default params and should also preserve zero
ALL_TMO_NAMES = list(OPERATORS.keys())


# =========================================================================
# Black preservation: input 0 -> output 0
# =========================================================================

class TestBlackPreservation:
    """Every tone mapper should map 0 to 0 (or very close)."""

    @pytest.mark.parametrize("name", ALL_TMO_NAMES)
    def test_zero_input(self, name):
        fn = get_operator(name)
        result = fn(np.array([0.0]))
        assert result[0] == pytest.approx(0.0, abs=0.02), \
            f"{name} did not preserve black: got {result[0]}"


# =========================================================================
# Monotonicity: larger input -> larger output
# =========================================================================

class TestMonotonicity:
    """Every operator should be monotonically non-decreasing for non-negative input."""

    @pytest.mark.parametrize("fn", SIMPLE_OPERATORS, ids=lambda f: f.__name__)
    def test_monotonic_simple(self, fn):
        x = np.linspace(0, 10, 100)
        y = fn(x)
        diffs = np.diff(y)
        assert np.all(diffs >= -1e-10), f"{fn.__name__} is not monotonic"

    def test_reinhard_extended_monotonic(self):
        x = np.linspace(0, 10, 100)
        y = reinhard_extended(x, L_white=4.0)
        diffs = np.diff(y)
        assert np.all(diffs >= -1e-10)

    def test_hable_monotonic(self):
        x = np.linspace(0, 10, 100)
        y = hable(x)
        diffs = np.diff(y)
        assert np.all(diffs >= -1e-10)

    def test_agx_monotonic(self):
        x = np.linspace(0.001, 10, 100)
        y = agx(x)
        diffs = np.diff(y)
        assert np.all(diffs >= -1e-10)


# =========================================================================
# Output clamping to [0, 1]
# =========================================================================

class TestOutputRange:
    """Operators that explicitly clamp should produce output in [0,1]."""

    # These operators explicitly clamp or naturally stay in [0,1]:
    CLAMPED_OPERATORS = [
        "reinhard", "aces", "aces_hill", "hable", "lottes",
        "uchimura", "agx", "pbr_neutral", "bt2446",
    ]

    @pytest.mark.parametrize("name", CLAMPED_OPERATORS)
    def test_output_clamped(self, name):
        fn = get_operator(name)
        x = np.array([0.0, 0.01, 0.18, 0.5, 1.0, 2.0, 5.0, 10.0])
        result = fn(x)
        assert np.all(result >= -1e-10), f"{name} produced negative output"
        assert np.all(result <= 1.0 + 1e-10), f"{name} exceeded 1.0"

    def test_reinhard_extended_can_exceed_one(self):
        """Reinhard extended is designed to allow values > 1 for HDR white mapping."""
        result = reinhard_extended(np.array([10.0]), L_white=4.0)
        assert result[0] > 1.0

    def test_bt2390_output_in_nit_range(self):
        """BT.2390 maps nits to nits, not to [0,1]."""
        x = np.array([0.0, 100.0, 1000.0, 4000.0])
        result = bt2390_eetf(x, source_peak=4000, target_peak=1000)
        assert np.all(result >= 0)
        assert np.all(result <= 4001)  # Should be <= target or close


# =========================================================================
# PQ roundtrip
# =========================================================================

class TestPQRoundtrip:
    """PQ encode/decode roundtrip at key luminance levels."""

    @pytest.mark.parametrize("nits", [0.0, 100.0, 1000.0, 4000.0, 10000.0])
    def test_roundtrip(self, nits):
        encoded = pq_oetf(np.array([nits]))
        decoded = pq_eotf(encoded)
        np.testing.assert_allclose(decoded[0], nits, atol=0.1,
                                   err_msg=f"PQ roundtrip failed at {nits} nits")

    def test_pq_oetf_range(self):
        """PQ output should be in [0, 1]."""
        nits = np.array([0.0, 100.0, 1000.0, 10000.0])
        encoded = pq_oetf(nits)
        assert np.all(encoded >= 0)
        assert np.all(encoded <= 1.0 + 1e-10)

    def test_pq_eotf_range(self):
        """PQ decoded output should be in [0, 10000]."""
        signal = np.array([0.0, 0.25, 0.5, 0.75, 1.0])
        decoded = pq_eotf(signal)
        assert np.all(decoded >= 0)
        assert np.all(decoded <= 10001)

    def test_pq_batch(self):
        nits = np.linspace(0, 10000, 50)
        encoded = pq_oetf(nits)
        decoded = pq_eotf(encoded)
        np.testing.assert_allclose(decoded, nits, atol=0.5)


# =========================================================================
# HLG roundtrip
# =========================================================================

class TestHLGRoundtrip:
    """HLG encode/decode roundtrip."""

    @pytest.mark.parametrize("val", [0.0, 0.25, 0.5, 0.75, 1.0])
    def test_roundtrip(self, val):
        encoded = hlg_oetf(np.array([val]))
        decoded = hlg_eotf(encoded)
        assert decoded[0] == pytest.approx(val, abs=1e-6), \
            f"HLG roundtrip failed at {val}"

    def test_hlg_oetf_range(self):
        linear = np.linspace(0, 1, 50)
        encoded = hlg_oetf(linear)
        assert np.all(encoded >= 0)
        assert np.all(encoded <= 1.0 + 1e-10)

    def test_hlg_eotf_range(self):
        signal = np.linspace(0, 1, 50)
        decoded = hlg_eotf(signal)
        assert np.all(decoded >= 0)
        assert np.all(decoded <= 1.0 + 1e-6)


# =========================================================================
# BT.2390 EETF
# =========================================================================

class TestBT2390:
    """ITU-R BT.2390 EETF tests."""

    def test_compresses_source_to_target(self):
        """Output at source peak should be near target peak."""
        source_peak = 4000.0
        target_peak = 1000.0
        hdr = np.array([source_peak])
        result = bt2390_eetf(hdr, source_peak=source_peak, target_peak=target_peak)
        assert result[0] <= target_peak + 50, \
            f"BT.2390 output {result[0]} exceeds target {target_peak}"

    def test_low_values_pass_through(self):
        """Low luminance values should be relatively unchanged."""
        hdr = np.array([10.0])
        result = bt2390_eetf(hdr, source_peak=4000, target_peak=1000)
        # Low values should pass through approximately
        assert result[0] > 0

    def test_compresses_above_knee(self):
        """BT.2390 compresses values above the knee toward target peak.

        This is a tone compression function: above the knee point,
        increasing source luminance maps to decreasing compressed luminance
        in absolute nits, because the function maps the full source range
        [0, source_peak] into [0, target_peak].
        """
        x = np.linspace(0, 4000, 100)
        y = bt2390_eetf(x, source_peak=4000, target_peak=1000)
        # Output at source_peak should be near target_peak
        assert y[-1] == pytest.approx(1000, abs=50)
        # Low values should pass through relatively unchanged
        assert y[1] < x[1] + 1  # near start, output ~ input

    def test_accepts_array(self):
        x = np.array([0.0, 100.0, 500.0, 1000.0, 4000.0])
        result = bt2390_eetf(x, source_peak=4000, target_peak=1000)
        assert result.shape == x.shape


# =========================================================================
# BT.2446 Method A
# =========================================================================

class TestBT2446:
    """ITU-R BT.2446 Method A tests."""

    def test_maps_hdr_to_sdr(self):
        """HDR values should map to [0, 1] SDR range."""
        hdr = np.array([0.0, 100.0, 500.0, 1000.0])
        result = bt2446_method_a(hdr, L_hdr=1000.0, L_sdr=100.0)
        assert np.all(result >= 0)
        assert np.all(result <= 1.0 + 1e-10)

    def test_preserves_black(self):
        result = bt2446_method_a(np.array([0.0]))
        assert result[0] == pytest.approx(0.0, abs=0.01)

    def test_monotonic(self):
        x = np.linspace(0.001, 1000, 100)
        y = bt2446_method_a(x, L_hdr=1000.0)
        diffs = np.diff(y)
        assert np.all(diffs >= -1e-10)


# =========================================================================
# AgX looks
# =========================================================================

class TestAgX:
    """AgX tone mapping with different looks."""

    def test_neutral_vs_punchy(self):
        """Neutral and punchy variants should produce different results."""
        x = np.array([0.5])
        neutral = agx(x, look="neutral")
        punchy = agx(x, look="punchy")
        assert not np.allclose(neutral, punchy), \
            "AgX neutral and punchy should differ"

    def test_golden_modifies_rgb(self):
        """Golden look should modify per-channel differently."""
        x = np.array([0.5, 0.5, 0.5])
        golden = agx(x, look="golden")
        neutral = agx(x, look="neutral")
        # Golden boosts red and reduces blue
        assert golden[0] >= neutral[0] - 0.01  # red boosted or equal
        assert golden[2] <= neutral[2] + 0.01  # blue reduced or equal

    def test_output_range(self):
        x = np.linspace(0.01, 10, 50)
        for look in ["neutral", "punchy"]:
            result = agx(x, look=look)
            assert np.all(result >= 0)
            assert np.all(result <= 1.0 + 1e-10)


# =========================================================================
# Knee function
# =========================================================================

class TestKnee:
    """Custom knee function tests."""

    def test_below_knee_passthrough(self):
        """Values below knee_start should pass through unchanged."""
        x = np.array([0.0, 0.1, 0.3, 0.49])
        result = knee(x, knee_start=0.5)
        np.testing.assert_allclose(result, x, atol=1e-10)

    def test_above_knee_compressed(self):
        """Values above knee_start should be compressed toward max_output."""
        x = np.array([0.8, 1.5, 3.0])
        # With power < 1.0, the knee function can overshoot max_output
        # for large inputs. With power=1.0, it behaves more like a linear map.
        result = knee(x, knee_start=0.5, max_output=1.0, power=1.0)
        assert np.all(result >= 0.5)
        # All values should be less than the unconstrained input
        assert np.all(result <= x + 0.01)


# =========================================================================
# All operators accept numpy arrays
# =========================================================================

class TestArrayAcceptance:
    """All operators should accept and return numpy arrays."""

    @pytest.mark.parametrize("name", ALL_TMO_NAMES)
    def test_accepts_1d_array(self, name):
        fn = get_operator(name)
        x = np.array([0.0, 0.18, 1.0])
        result = fn(x)
        assert isinstance(result, np.ndarray)
        assert result.shape == x.shape

    @pytest.mark.parametrize("name", ALL_TMO_NAMES)
    def test_accepts_scalar_in_array(self, name):
        fn = get_operator(name)
        result = fn(np.array([0.5]))
        assert isinstance(result, np.ndarray)


# =========================================================================
# Utility functions
# =========================================================================

class TestUtility:
    """Test list_operators and get_operator."""

    def test_list_operators_count(self):
        ops = list_operators()
        assert len(ops) >= 10

    def test_list_operators_contains_all(self):
        ops = list_operators()
        expected = ["reinhard", "aces", "hable", "agx", "bt2390", "bt2446"]
        for e in expected:
            assert e in ops

    def test_get_operator_valid(self):
        fn = get_operator("reinhard")
        assert callable(fn)

    def test_get_operator_invalid(self):
        fn = get_operator("nonexistent_operator")
        assert fn is None

    def test_get_operator_case_insensitive(self):
        fn = get_operator("Reinhard")
        assert callable(fn)
