"""
Tone Mapping Operators

Professional HDR-to-SDR tone mapping for display calibration,
color grading, and image processing.

Operators:
    reinhard          - Simple Reinhard (1 param)
    reinhard_extended - Reinhard with white point
    aces_filmic       - Academy Color Encoding System (Narkowicz fit)
    aces_hill         - Stephen Hill's ACES fit (more accurate)
    hable             - Uncharted 2 / Hable curve
    lottes            - Timothy Lottes (contrast-preserving)
    uchimura          - Gran Turismo / Uchimura
    agx               - AgX (Troy Sobotka)
    pbr_neutral       - Khronos PBR Neutral (glTF standard)
    bt2390_eetf       - ITU-R BT.2390 EETF (broadcast standard)
    bt2446_method_a   - ITU-R BT.2446 Method A (scene-referred)
    knee              - Custom knee function (configurable)

All operators accept numpy arrays and work element-wise.
Input: linear HDR values (0 to unbounded)
Output: SDR values (0 to 1)
"""

import numpy as np


def reinhard(L: np.ndarray) -> np.ndarray:
    """Simple Reinhard tone mapping. L / (1 + L)."""
    L = np.asarray(L, dtype=np.float64)
    return L / (1.0 + L)


def reinhard_extended(L: np.ndarray, L_white: float = 4.0) -> np.ndarray:
    """Reinhard with white point. Brighter values can exceed 1.0 mapping."""
    L = np.asarray(L, dtype=np.float64)
    return L * (1.0 + L / (L_white * L_white)) / (1.0 + L)


def aces_filmic(x: np.ndarray) -> np.ndarray:
    """ACES filmic tone mapping (Narkowicz 2015 fit)."""
    x = np.asarray(x, dtype=np.float64)
    a, b, c, d, e = 2.51, 0.03, 2.43, 0.59, 0.14
    return np.clip((x * (a * x + b)) / (x * (c * x + d) + e), 0.0, 1.0)


def aces_hill(x: np.ndarray) -> np.ndarray:
    """Stephen Hill's improved ACES fit (2016)."""
    x = np.asarray(x, dtype=np.float64)
    # RRT + ODT fit
    a = x * (x + 0.0245786) - 0.000090537
    b = x * (0.983729 * x + 0.4329510) + 0.238081
    return np.clip(a / b, 0.0, 1.0)


def hable(x: np.ndarray, source_peak: float = 4.0) -> np.ndarray:
    """Uncharted 2 / Hable tone mapping curve."""
    x = np.asarray(x, dtype=np.float64)

    A, B, C, D, E, F = 0.15, 0.50, 0.10, 0.20, 0.02, 0.30

    def _curve(v):
        return ((v * (A * v + C * B) + D * E) / (v * (A * v + B) + D * F)) - E / F

    white = _curve(np.array([source_peak]))[0]
    return np.clip(_curve(x) / white, 0.0, 1.0)


def lottes(
    x: np.ndarray, a: float = 1.6, d: float = 0.977, hdr_max: float = 8.0, mid_in: float = 0.18, mid_out: float = 0.267
) -> np.ndarray:
    """Timothy Lottes tone mapping (contrast-preserving)."""
    x = np.asarray(x, dtype=np.float64)
    b = (-np.power(mid_in, a) + np.power(hdr_max, a) * mid_out) / (
        (np.power(hdr_max, a * d) - np.power(mid_in, a * d)) * mid_out
    )
    c = (np.power(hdr_max, a * d) * np.power(mid_in, a) - np.power(hdr_max, a) * np.power(mid_in, a * d) * mid_out) / (
        (np.power(hdr_max, a * d) - np.power(mid_in, a * d)) * mid_out
    )
    return np.clip(np.power(x, a) / (np.power(x, a * d) * b + c), 0.0, 1.0)


def uchimura(
    x: np.ndarray, P: float = 1.0, a: float = 1.0, m: float = 0.22, l: float = 0.4, c: float = 1.33, b: float = 0.0
) -> np.ndarray:
    """Gran Turismo / Uchimura tone mapping."""
    x = np.asarray(x, dtype=np.float64)
    l0 = ((P - m) * l) / a
    S0 = m + l0
    S1 = m + a * l0
    C2 = (a * P) / (P - S1)
    CP = -C2 / P

    1.0 - np.where(x < m, x / m, 1.0)
    w1 = np.where(x < m, 0.0, 1.0)

    T = m * np.power(x / m, c) + b
    S = P - (P - S1) * np.exp(CP * (x - S0))
    return np.clip(T * (1.0 - w1) + S * w1, 0.0, 1.0)


def agx(x: np.ndarray, look: str = "neutral") -> np.ndarray:
    """AgX tone mapping (Troy Sobotka). Looks: 'neutral', 'punchy', 'golden'."""
    x = np.asarray(x, dtype=np.float64)
    # AgX log encoding
    x = np.maximum(x, 1e-10)
    x = np.clip(np.log2(x) / 12.47393 + 0.5, 0.0, 1.0)

    # Hermite polynomial approximation of AgX curve
    x2 = x * x
    x4 = x2 * x2
    mapped = 15.5 * x4 * x2 - 40.14 * x4 * x + 31.96 * x4 - 6.868 * x2 * x + 0.4298 * x2 + 0.1191 * x - 0.00232
    mapped = np.clip(mapped, 0.0, 1.0)

    if look == "punchy":
        # Increase contrast in midtones
        mapped = np.power(mapped, 1.35) * 1.1
    elif look == "golden":
        # Warm tint
        if mapped.ndim >= 1 and mapped.shape[-1] == 3:
            mapped[..., 0] *= 1.05  # Boost red
            mapped[..., 2] *= 0.92  # Reduce blue

    return np.clip(mapped, 0.0, 1.0)


def pbr_neutral(x: np.ndarray) -> np.ndarray:
    """Khronos PBR Neutral tone mapping (glTF standard)."""
    x = np.asarray(x, dtype=np.float64)
    start_compression = 0.8 - 0.04
    desaturation = 0.15

    # Luminance
    if x.ndim >= 1 and x.shape[-1] == 3:
        lum = 0.2126 * x[..., 0] + 0.7152 * x[..., 1] + 0.0722 * x[..., 2]
    else:
        lum = x

    # Desaturation
    x_desat = np.where(
        lum[..., np.newaxis] > start_compression if x.ndim >= 2 else lum > start_compression,
        x * (1.0 - desaturation) + lum[..., np.newaxis] * desaturation if x.ndim >= 2 else x,
        x,
    )
    # Simple filmic compression
    return np.clip(x_desat / (1.0 + x_desat), 0.0, 1.0)


# =============================================================================
# HDR Broadcast Standards
# =============================================================================

# PQ constants (SMPTE ST.2084)
_PQ_M1 = 2610.0 / 16384.0
_PQ_M2 = 2523.0 / 4096.0 * 128.0
_PQ_C1 = 3424.0 / 4096.0
_PQ_C2 = 2413.0 / 4096.0 * 32.0
_PQ_C3 = 2392.0 / 4096.0 * 32.0
_PQ_PEAK = 10000.0


def pq_eotf(E: np.ndarray) -> np.ndarray:
    """PQ (ST.2084) EOTF: signal [0,1] -> linear nits [0,10000]."""
    E = np.clip(np.asarray(E, dtype=np.float64), 0, 1)
    Ep = np.power(E, 1.0 / _PQ_M2)
    num = np.maximum(Ep - _PQ_C1, 0.0)
    den = _PQ_C2 - _PQ_C3 * Ep
    return _PQ_PEAK * np.power(num / den, 1.0 / _PQ_M1)


def pq_oetf(Y: np.ndarray) -> np.ndarray:
    """PQ (ST.2084) OETF: linear nits [0,10000] -> signal [0,1]."""
    Y = np.clip(np.asarray(Y, dtype=np.float64), 0, _PQ_PEAK)
    Yn = Y / _PQ_PEAK
    Yp = np.power(Yn, _PQ_M1)
    num = _PQ_C1 + _PQ_C2 * Yp
    den = 1.0 + _PQ_C3 * Yp
    return np.power(num / den, _PQ_M2)


# HLG constants (BT.2100)
_HLG_A = 0.17883277
_HLG_B = 0.28466892
_HLG_C = 0.55991073


def hlg_oetf(E: np.ndarray) -> np.ndarray:
    """HLG OETF: linear [0,1] -> HLG signal [0,1]."""
    E = np.clip(np.asarray(E, dtype=np.float64), 0, 1)
    with np.errstate(divide="ignore", invalid="ignore"):
        return np.where(
            E <= 1.0 / 12.0,
            np.sqrt(3.0 * E),
            _HLG_A * np.log(12.0 * E - _HLG_B) + _HLG_C,
        )


def hlg_eotf(E: np.ndarray) -> np.ndarray:
    """HLG EOTF: HLG signal [0,1] -> linear [0,1]."""
    E = np.clip(np.asarray(E, dtype=np.float64), 0, 1)
    return np.where(
        E <= 0.5,
        E * E / 3.0,
        (np.exp((E - _HLG_C) / _HLG_A) + _HLG_B) / 12.0,
    )


def bt2390_eetf(
    L: np.ndarray, source_peak: float = 4000.0, target_peak: float = 1000.0, min_lum: float = 0.0
) -> np.ndarray:
    """
    ITU-R BT.2390 EETF (Electrical-Electrical Transfer Function).

    Maps HDR content from source peak luminance to display peak luminance
    using a hermite spline with knee point. The broadcast standard for
    HDR tone mapping.
    """
    L = np.asarray(L, dtype=np.float64)

    # Normalize to PQ domain
    e1 = pq_oetf(L)
    max_pq = pq_oetf(np.array([source_peak]))[0]
    min_pq = pq_oetf(np.array([min_lum]))[0]
    target_pq = pq_oetf(np.array([target_peak]))[0]

    # Normalize to [0, 1]
    e_norm = (e1 - min_pq) / (max_pq - min_pq + 1e-10)
    e_norm = np.clip(e_norm, 0, 1)

    # Knee point
    knee = 0.5 * target_pq / max_pq + 0.5

    # Hermite spline interpolation
    t = np.clip((e_norm - knee) / (1.0 - knee + 1e-10), 0, 1)
    # Smooth hermite
    p = t * t * (3.0 - 2.0 * t)

    e2 = np.where(
        e_norm < knee,
        e_norm,
        knee + (target_pq / max_pq - knee) * p,
    )

    # Denormalize from PQ
    e2_pq = e2 * (max_pq - min_pq) + min_pq
    return pq_eotf(e2_pq)


def bt2446_method_a(y_hdr: np.ndarray, L_hdr: float = 1000.0, L_sdr: float = 100.0) -> np.ndarray:
    """ITU-R BT.2446 Method A: scene-referred HDR-to-SDR conversion."""
    y_hdr = np.asarray(y_hdr, dtype=np.float64)
    y_norm = y_hdr / L_hdr
    rho = 1.0 + 32.0 * np.power(np.maximum(y_norm, 1e-10), 1.0 / 2.4)
    y_sdr = np.log(rho) / np.log(33.0) * L_sdr
    return np.clip(y_sdr / L_sdr, 0.0, 1.0)


def knee(L: np.ndarray, knee_start: float = 0.5, max_output: float = 1.0, power: float = 0.5) -> np.ndarray:
    """Custom knee function with configurable parameters."""
    L = np.asarray(L, dtype=np.float64)
    excess = L - knee_start
    compressed = knee_start + np.power(np.clip(excess / (max_output - knee_start + 1e-10), 0, None), power) * (
        max_output - knee_start
    )
    return np.where(knee_start >= L, L, compressed)


# =============================================================================
# Utility
# =============================================================================

OPERATORS = {
    "reinhard": reinhard,
    "reinhard_extended": reinhard_extended,
    "aces": aces_filmic,
    "aces_hill": aces_hill,
    "hable": hable,
    "lottes": lottes,
    "uchimura": uchimura,
    "agx": agx,
    "pbr_neutral": pbr_neutral,
    "bt2390": bt2390_eetf,
    "bt2446": bt2446_method_a,
    "knee": knee,
}


def list_operators():
    """List all available tone mapping operators."""
    return list(OPERATORS.keys())


def get_operator(name: str):
    """Get a tone mapping operator function by name."""
    return OPERATORS.get(name.lower())
