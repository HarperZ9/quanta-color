"""
Color Space Conversions

Complete color space conversion library supporting all major
color spaces used in display calibration, HDR processing,
color grading, and image processing.

Spaces:
    sRGB        - IEC 61966-2-1 (web/desktop standard)
    Linear RGB  - Linear light (no gamma)
    XYZ         - CIE 1931 tristimulus
    xyY         - CIE chromaticity + luminance
    Lab         - CIELAB (perceptual, D50 or D65)
    LCH         - Cylindrical CIELAB
    Oklab       - Bjorn Ottosson (modern perceptual)
    Oklch       - Cylindrical Oklab
    JzAzBz      - Safdar et al. (HDR perceptual)
    JzCzhz      - Cylindrical JzAzBz
    ICtCp       - Dolby (HDR brightness-adaptive)
    CAM16       - CIE Color Appearance Model 2016
    Display P3  - Apple/DCI wide gamut
    Rec.2020    - UHDTV/HDR container
    Adobe RGB   - Photography wide gamut
    ACEScg      - ACES computer graphics working space
    HSV / HSL   - Hue-based models
"""

import numpy as np
from typing import Tuple, Optional

# =============================================================================
# Matrices (high-precision float64)
# =============================================================================

# sRGB <-> XYZ (D65)
SRGB_TO_XYZ = np.array([
    [0.4124564, 0.3575761, 0.1804375],
    [0.2126729, 0.7151522, 0.0721750],
    [0.0193339, 0.1191920, 0.9503041],
], dtype=np.float64)

XYZ_TO_SRGB = np.array([
    [ 3.2404542, -1.5371385, -0.4985314],
    [-0.9692660,  1.8760108,  0.0415560],
    [ 0.0556434, -0.2040259,  1.0572252],
], dtype=np.float64)

# Display P3 <-> XYZ (D65)
P3_TO_XYZ = np.array([
    [0.4865709, 0.2656677, 0.1982173],
    [0.2289746, 0.6917385, 0.0792869],
    [0.0000000, 0.0451134, 1.0439444],
], dtype=np.float64)

XYZ_TO_P3 = np.linalg.inv(P3_TO_XYZ)

# BT.2020 <-> XYZ (D65)
BT2020_TO_XYZ = np.array([
    [0.6369580, 0.1446169, 0.1688810],
    [0.2627002, 0.6779981, 0.0593017],
    [0.0000000, 0.0280727, 1.0609851],
], dtype=np.float64)

XYZ_TO_BT2020 = np.linalg.inv(BT2020_TO_XYZ)

# Adobe RGB <-> XYZ (D65)
ADOBE_TO_XYZ = np.array([
    [0.5767309, 0.1855540, 0.1881852],
    [0.2973769, 0.6273491, 0.0752741],
    [0.0270343, 0.0706872, 0.9911085],
], dtype=np.float64)

XYZ_TO_ADOBE = np.linalg.inv(ADOBE_TO_XYZ)

# ACEScg <-> XYZ (D65, AP1 primaries)
ACESCG_TO_XYZ = np.array([
    [0.6624542, 0.1340042, 0.1561877],
    [0.2722287, 0.6740818, 0.0536895],
    [-0.0055746, 0.0040607, 1.0103391],
], dtype=np.float64)

XYZ_TO_ACESCG = np.linalg.inv(ACESCG_TO_XYZ)

# Oklab matrices
_OKLAB_M1 = np.array([
    [0.8189330101, 0.3618667424, -0.1288597137],
    [0.0329845436, 0.9293118715,  0.0361456387],
    [0.0482003018, 0.2643662691,  0.6338517070],
], dtype=np.float64)

_OKLAB_M2 = np.array([
    [0.2104542553, 0.7936177850, -0.0040720468],
    [1.9779984951, -2.4285922050, 0.4505937099],
    [0.0259040371, 0.7827717662, -0.8086757660],
], dtype=np.float64)

_OKLAB_M1_INV = np.linalg.inv(_OKLAB_M1)
_OKLAB_M2_INV = np.linalg.inv(_OKLAB_M2)

# Standard illuminants
D50 = np.array([0.96422, 1.0, 0.82521])
D65 = np.array([0.95047, 1.0, 1.08883])

# =============================================================================
# sRGB gamma
# =============================================================================

def srgb_to_linear(srgb: np.ndarray) -> np.ndarray:
    """sRGB gamma decode (signal -> linear light)."""
    s = np.asarray(srgb, dtype=np.float64)
    return np.where(s <= 0.04045, s / 12.92,
                    np.power((s + 0.055) / 1.055, 2.4))


def linear_to_srgb(linear: np.ndarray) -> np.ndarray:
    """sRGB gamma encode (linear light -> signal)."""
    c = np.asarray(linear, dtype=np.float64)
    return np.where(c <= 0.0031308, c * 12.92,
                    1.055 * np.power(np.maximum(c, 0), 1.0 / 2.4) - 0.055)


# =============================================================================
# XYZ conversions
# =============================================================================

def srgb_to_xyz(srgb: np.ndarray) -> np.ndarray:
    """sRGB (0-1) -> XYZ (D65)."""
    linear = srgb_to_linear(srgb)
    if linear.ndim == 1:
        return SRGB_TO_XYZ @ linear
    return (SRGB_TO_XYZ @ linear.T).T


def xyz_to_srgb(xyz: np.ndarray, clip: bool = True) -> np.ndarray:
    """XYZ (D65) -> sRGB (0-1)."""
    if xyz.ndim == 1:
        linear = XYZ_TO_SRGB @ xyz
    else:
        linear = (XYZ_TO_SRGB @ xyz.T).T
    result = linear_to_srgb(linear)
    return np.clip(result, 0, 1) if clip else result


def xyz_to_xyY(xyz: np.ndarray) -> np.ndarray:
    """XYZ -> xyY chromaticity."""
    xyz = np.asarray(xyz, dtype=np.float64)
    s = np.sum(xyz, axis=-1, keepdims=True)
    s = np.where(s == 0, 1, s)
    x = xyz[..., 0:1] / s
    y = xyz[..., 1:2] / s
    Y = xyz[..., 1:2]
    return np.concatenate([x, y, Y], axis=-1)


def xyY_to_xyz(xyY: np.ndarray) -> np.ndarray:
    """xyY chromaticity -> XYZ."""
    xyY = np.asarray(xyY, dtype=np.float64)
    x, y, Y = xyY[..., 0], xyY[..., 1], xyY[..., 2]
    safe_y = np.where(y == 0, 1, y)
    X = (Y / safe_y) * x
    Z = (Y / safe_y) * (1 - x - y)
    return np.stack([X, Y, Z], axis=-1)


# =============================================================================
# CIELAB
# =============================================================================

def _lab_f(t: np.ndarray) -> np.ndarray:
    delta = 6.0 / 29.0
    return np.where(t > delta**3,
                    np.cbrt(t),
                    t / (3 * delta**2) + 4.0 / 29.0)


def _lab_f_inv(t: np.ndarray) -> np.ndarray:
    delta = 6.0 / 29.0
    return np.where(t > delta,
                    t**3,
                    3 * delta**2 * (t - 4.0 / 29.0))


def xyz_to_lab(xyz: np.ndarray, white: np.ndarray = D50) -> np.ndarray:
    """XYZ -> CIELAB (default illuminant D50 for ICC)."""
    xyz = np.asarray(xyz, dtype=np.float64)
    r = xyz / white
    f = _lab_f(r)
    L = 116.0 * f[..., 1] - 16.0
    a = 500.0 * (f[..., 0] - f[..., 1])
    b = 200.0 * (f[..., 1] - f[..., 2])
    return np.stack([L, a, b], axis=-1)


def lab_to_xyz(lab: np.ndarray, white: np.ndarray = D50) -> np.ndarray:
    """CIELAB -> XYZ."""
    lab = np.asarray(lab, dtype=np.float64)
    fy = (lab[..., 0] + 16.0) / 116.0
    fx = lab[..., 1] / 500.0 + fy
    fz = fy - lab[..., 2] / 200.0
    x = _lab_f_inv(fx) * white[0]
    y = _lab_f_inv(fy) * white[1]
    z = _lab_f_inv(fz) * white[2]
    return np.stack([x, y, z], axis=-1)


def lab_to_lch(lab: np.ndarray) -> np.ndarray:
    """CIELAB -> LCH (cylindrical)."""
    L = lab[..., 0]
    a, b = lab[..., 1], lab[..., 2]
    C = np.sqrt(a**2 + b**2)
    h = np.degrees(np.arctan2(b, a)) % 360
    return np.stack([L, C, h], axis=-1)


def lch_to_lab(lch: np.ndarray) -> np.ndarray:
    """LCH -> CIELAB."""
    L, C, h = lch[..., 0], lch[..., 1], lch[..., 2]
    a = C * np.cos(np.radians(h))
    b = C * np.sin(np.radians(h))
    return np.stack([L, a, b], axis=-1)


# =============================================================================
# Oklab / Oklch
# =============================================================================

def linear_srgb_to_oklab(rgb: np.ndarray) -> np.ndarray:
    """Linear sRGB -> Oklab."""
    rgb = np.asarray(rgb, dtype=np.float64)
    if rgb.ndim == 1:
        lms = _OKLAB_M1 @ rgb
    else:
        lms = (_OKLAB_M1 @ rgb.T).T
    lms_g = np.sign(lms) * np.power(np.abs(lms), 1.0 / 3.0)
    if lms_g.ndim == 1:
        return _OKLAB_M2 @ lms_g
    return (_OKLAB_M2 @ lms_g.T).T


def oklab_to_linear_srgb(oklab: np.ndarray) -> np.ndarray:
    """Oklab -> Linear sRGB."""
    oklab = np.asarray(oklab, dtype=np.float64)
    if oklab.ndim == 1:
        lms_g = _OKLAB_M2_INV @ oklab
    else:
        lms_g = (_OKLAB_M2_INV @ oklab.T).T
    lms = lms_g**3
    if lms.ndim == 1:
        return _OKLAB_M1_INV @ lms
    return (_OKLAB_M1_INV @ lms.T).T


def srgb_to_oklab(srgb: np.ndarray) -> np.ndarray:
    """sRGB (gamma) -> Oklab."""
    return linear_srgb_to_oklab(srgb_to_linear(srgb))


def oklab_to_srgb(oklab: np.ndarray, clip: bool = True) -> np.ndarray:
    """Oklab -> sRGB (gamma)."""
    result = linear_to_srgb(oklab_to_linear_srgb(oklab))
    return np.clip(result, 0, 1) if clip else result


def oklab_to_oklch(oklab: np.ndarray) -> np.ndarray:
    """Oklab -> Oklch (cylindrical)."""
    L = oklab[..., 0]
    a, b = oklab[..., 1], oklab[..., 2]
    C = np.sqrt(a**2 + b**2)
    h = np.degrees(np.arctan2(b, a)) % 360
    return np.stack([L, C, h], axis=-1)


def oklch_to_oklab(oklch: np.ndarray) -> np.ndarray:
    """Oklch -> Oklab."""
    L, C, h = oklch[..., 0], oklch[..., 1], oklch[..., 2]
    a = C * np.cos(np.radians(h))
    b = C * np.sin(np.radians(h))
    return np.stack([L, a, b], axis=-1)


# =============================================================================
# JzAzBz (HDR perceptual)
# =============================================================================

_JZ_B = 1.15
_JZ_G = 0.66
_JZ_C1 = 0.8359375
_JZ_C2 = 18.8515625
_JZ_C3 = 18.6875
_JZ_N = 0.15930175781
_JZ_P = 134.034375
_JZ_D = -0.56
_JZ_D0 = 1.6295499532821566e-11

_JZ_M1 = np.array([
    [ 0.41478972, 0.57999900, 0.01464800],
    [-0.20151000, 1.12064900, 0.05310080],
    [-0.01660080, 0.26480000, 0.66847990],
], dtype=np.float64)

_JZ_M2 = np.array([
    [ 0.5,        0.5,        0.0       ],
    [ 3.524000,  -4.066708,   0.542708  ],
    [ 0.199076,   1.096799,  -1.295875  ],
], dtype=np.float64)

_JZ_M1_INV = np.linalg.inv(_JZ_M1)
_JZ_M2_INV = np.linalg.inv(_JZ_M2)


def _pq_encode(x: np.ndarray) -> np.ndarray:
    xp = np.power(np.maximum(x / 10000.0, 0), _JZ_N)
    return np.power((_JZ_C1 + _JZ_C2 * xp) / (1.0 + _JZ_C3 * xp), _JZ_P)


def _pq_decode(x: np.ndarray) -> np.ndarray:
    xp = np.power(np.maximum(x, 0), 1.0 / _JZ_P)
    return 10000.0 * np.power(
        np.maximum(xp - _JZ_C1, 0) / (_JZ_C2 - _JZ_C3 * xp), 1.0 / _JZ_N
    )


def xyz_to_jzazbz(xyz: np.ndarray) -> np.ndarray:
    """Absolute XYZ (cd/m2) -> JzAzBz."""
    xyz = np.asarray(xyz, dtype=np.float64)
    xp = _JZ_B * xyz[..., 0] - (_JZ_B - 1) * xyz[..., 2]
    yp = _JZ_G * xyz[..., 1] - (_JZ_G - 1) * xyz[..., 0]
    mod = np.stack([xp, yp, xyz[..., 2]], axis=-1)

    if mod.ndim == 1:
        lms = _JZ_M1 @ mod
    else:
        lms = (_JZ_M1 @ mod.T).T

    lms_pq = _pq_encode(lms)

    if lms_pq.ndim == 1:
        izazbz = _JZ_M2 @ lms_pq
    else:
        izazbz = (_JZ_M2 @ lms_pq.T).T

    Jz = (1.0 + _JZ_D) * izazbz[..., 0] / (1.0 + _JZ_D * izazbz[..., 0]) - _JZ_D0
    return np.stack([Jz, izazbz[..., 1], izazbz[..., 2]], axis=-1)


def jzazbz_to_xyz(jzazbz: np.ndarray) -> np.ndarray:
    """JzAzBz -> Absolute XYZ (cd/m2)."""
    jzazbz = np.asarray(jzazbz, dtype=np.float64)
    Jz = jzazbz[..., 0] + _JZ_D0
    Iz = Jz / (1.0 + _JZ_D - _JZ_D * Jz)
    izazbz = np.stack([Iz, jzazbz[..., 1], jzazbz[..., 2]], axis=-1)

    if izazbz.ndim == 1:
        lms_pq = _JZ_M2_INV @ izazbz
    else:
        lms_pq = (_JZ_M2_INV @ izazbz.T).T

    lms = _pq_decode(lms_pq)

    if lms.ndim == 1:
        mod = _JZ_M1_INV @ lms
    else:
        mod = (_JZ_M1_INV @ lms.T).T

    xp, yp, z = mod[..., 0], mod[..., 1], mod[..., 2]
    x = (xp + (_JZ_B - 1) * z) / _JZ_B
    y = (yp + (_JZ_G - 1) * x) / _JZ_G
    return np.stack([x, y, z], axis=-1)


def jzazbz_to_jzczhz(jzazbz: np.ndarray) -> np.ndarray:
    """JzAzBz -> JzCzhz (cylindrical)."""
    Jz = jzazbz[..., 0]
    az, bz = jzazbz[..., 1], jzazbz[..., 2]
    Cz = np.sqrt(az**2 + bz**2)
    hz = np.degrees(np.arctan2(bz, az)) % 360
    return np.stack([Jz, Cz, hz], axis=-1)


def jzczhz_to_jzazbz(jzczhz: np.ndarray) -> np.ndarray:
    """JzCzhz -> JzAzBz."""
    Jz, Cz, hz = jzczhz[..., 0], jzczhz[..., 1], jzczhz[..., 2]
    az = Cz * np.cos(np.radians(hz))
    bz = Cz * np.sin(np.radians(hz))
    return np.stack([Jz, az, bz], axis=-1)


# =============================================================================
# ICtCp (Dolby HDR)
# =============================================================================

_ICTCP_M1 = np.array([
    [0.3592832590121217, 0.6976051147779502, -0.0358915932320290],
    [-0.1920808463704993, 1.1004767970374321, 0.0753748658519118],
    [0.0070797844607479, 0.0748396662186362, 0.8433265453898765],
], dtype=np.float64)

_ICTCP_M2 = np.array([
    [2048, 2048, 0],
    [6610, -13613, 7003],
    [17933, -17390, -543],
], dtype=np.float64) / 4096.0


def xyz_to_ictcp(xyz: np.ndarray) -> np.ndarray:
    """Absolute XYZ (cd/m2) -> ICtCp."""
    xyz = np.asarray(xyz, dtype=np.float64)
    if xyz.ndim == 1:
        lms = _ICTCP_M1 @ xyz
    else:
        lms = (_ICTCP_M1 @ xyz.T).T
    lms_pq = _pq_encode(lms)
    if lms_pq.ndim == 1:
        return _ICTCP_M2 @ lms_pq
    return (_ICTCP_M2 @ lms_pq.T).T


# =============================================================================
# HSV / HSL
# =============================================================================

def rgb_to_hsv(rgb: np.ndarray) -> np.ndarray:
    """sRGB (0-1) -> HSV."""
    rgb = np.asarray(rgb, dtype=np.float64)
    r, g, b = rgb[..., 0], rgb[..., 1], rgb[..., 2]
    cmax = np.maximum(np.maximum(r, g), b)
    cmin = np.minimum(np.minimum(r, g), b)
    delta = cmax - cmin

    h = np.where(delta == 0, 0,
        np.where(cmax == r, 60 * (((g - b) / delta) % 6),
        np.where(cmax == g, 60 * ((b - r) / delta + 2),
                             60 * ((r - g) / delta + 4))))
    s = np.where(cmax == 0, 0, delta / cmax)
    v = cmax
    return np.stack([h, s, v], axis=-1)


def hsv_to_rgb(hsv: np.ndarray) -> np.ndarray:
    """HSV -> sRGB (0-1)."""
    hsv = np.asarray(hsv, dtype=np.float64)
    h, s, v = hsv[..., 0], hsv[..., 1], hsv[..., 2]
    c = v * s
    x = c * (1 - np.abs((h / 60) % 2 - 1))
    m = v - c

    h_idx = (h / 60).astype(int) % 6
    r = np.where(h_idx == 0, c, np.where(h_idx == 1, x, np.where(h_idx == 4, x, np.where(h_idx == 5, c, 0)))) + m
    g = np.where(h_idx == 0, x, np.where(h_idx == 1, c, np.where(h_idx == 2, c, np.where(h_idx == 3, x, 0)))) + m
    b = np.where(h_idx == 2, x, np.where(h_idx == 3, c, np.where(h_idx == 4, c, np.where(h_idx == 5, x, 0)))) + m
    return np.stack([r, g, b], axis=-1)


# =============================================================================
# Wide gamut conversions
# =============================================================================

def srgb_to_p3(srgb: np.ndarray) -> np.ndarray:
    """sRGB -> Display P3 (both gamma-encoded)."""
    linear = srgb_to_linear(srgb)
    xyz = (SRGB_TO_XYZ @ linear.T).T if linear.ndim > 1 else SRGB_TO_XYZ @ linear
    p3_lin = (XYZ_TO_P3 @ xyz.T).T if xyz.ndim > 1 else XYZ_TO_P3 @ xyz
    return linear_to_srgb(np.clip(p3_lin, 0, 1))


def srgb_to_bt2020(srgb: np.ndarray) -> np.ndarray:
    """sRGB -> BT.2020 (linear)."""
    linear = srgb_to_linear(srgb)
    xyz = (SRGB_TO_XYZ @ linear.T).T if linear.ndim > 1 else SRGB_TO_XYZ @ linear
    return (XYZ_TO_BT2020 @ xyz.T).T if xyz.ndim > 1 else XYZ_TO_BT2020 @ xyz


def srgb_to_acescg(srgb: np.ndarray) -> np.ndarray:
    """sRGB -> ACEScg working space."""
    linear = srgb_to_linear(srgb)
    xyz = (SRGB_TO_XYZ @ linear.T).T if linear.ndim > 1 else SRGB_TO_XYZ @ linear
    return (XYZ_TO_ACESCG @ xyz.T).T if xyz.ndim > 1 else XYZ_TO_ACESCG @ xyz


# =============================================================================
# Utility
# =============================================================================

def primaries_to_matrix(
    r_xy: Tuple[float, float],
    g_xy: Tuple[float, float],
    b_xy: Tuple[float, float],
    w_xy: Tuple[float, float],
) -> np.ndarray:
    """Compute RGB-to-XYZ matrix from chromaticity coordinates."""
    def xy_to_XYZ(x, y):
        return np.array([x / y, 1.0, (1 - x - y) / y])

    R = xy_to_XYZ(*r_xy)
    G = xy_to_XYZ(*g_xy)
    B = xy_to_XYZ(*b_xy)
    W = xy_to_XYZ(*w_xy)
    M = np.column_stack([R, G, B])
    S = np.linalg.solve(M, W)
    return M * S[np.newaxis, :]


def luminance(rgb: np.ndarray) -> np.ndarray:
    """Relative luminance from sRGB (ITU-R BT.709 coefficients)."""
    linear = srgb_to_linear(np.asarray(rgb, dtype=np.float64))
    return 0.2126 * linear[..., 0] + 0.7152 * linear[..., 1] + 0.0722 * linear[..., 2]
