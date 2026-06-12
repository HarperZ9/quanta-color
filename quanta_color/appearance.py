"""
Color Appearance Models

CIE color appearance models for predicting how colors look under
real viewing conditions. Accounts for surround, adaptation, and
luminance level — essential for cross-media color reproduction.

Models:
    CIECAM02        - CIE 2002 standard (forward and inverse)
    CAM16-UCS       - Uniform color space derived from CAM16 (Li et al. 2017)
    Hue Quadrature  - Unique-hue composition (CIECAM02 / CAM16)

Functions:
    ciecam02_forward    - XYZ -> J, C, h, Q, M, s, H
    ciecam02_inverse    - J, C, h -> XYZ
    cam16_forward       - XYZ -> J, C, h, Q, M, s, H  (CAM16 variant)
    cam16_ucs           - XYZ -> (J', a', b') uniform coordinates
    delta_e_cam16       - Euclidean distance in CAM16-UCS
    hue_quadrature      - h -> H (unique-hue interpolation)
"""

from dataclasses import dataclass

import numpy as np

# =============================================================================
# Viewing Conditions
# =============================================================================


@dataclass
class ViewingConditions:
    """
    Describes the viewing environment for color appearance computation.

    Attributes:
        white_point: XYZ tristimulus of the reference white (Y=1 normalized).
        L_A: Adapting field luminance in cd/m^2. Typical values:
             64 (average surround), 16-32 (dim), 0.2 (dark).
        Y_b: Background luminance factor as a percentage of the reference
             white Y. Typically 20 for a mid-gray surround.
        surround: Viewing surround condition — one of
                  "average", "dim", or "dark".
    """

    white_point: np.ndarray
    L_A: float = 64.0
    Y_b: float = 20.0
    surround: str = "average"


# =============================================================================
# Surround Parameters
# =============================================================================

SURROUND = {
    "average": {"c": 0.69, "Nc": 1.0, "F": 1.0},
    "dim": {"c": 0.59, "Nc": 0.9, "F": 0.9},
    "dark": {"c": 0.525, "Nc": 0.8, "F": 0.8},
}


# =============================================================================
# CAT02 and CAM16 Chromatic Adaptation Matrices
# =============================================================================

M_CAT02 = np.array(
    [
        [0.7328, 0.4296, -0.1624],
        [-0.7036, 1.6975, 0.0061],
        [0.0030, 0.0136, 0.9834],
    ],
    dtype=np.float64,
)

M_CAT02_INV = np.linalg.inv(M_CAT02)

# Hunt-Pointer-Estevez matrix for post-adaptation cone space
M_HPE = np.array(
    [
        [0.38971, 0.68898, -0.07868],
        [-0.22981, 1.18340, 0.04641],
        [0.00000, 0.00000, 1.00000],
    ],
    dtype=np.float64,
)

M_HPE_INV = np.linalg.inv(M_HPE)

# CAM16 chromatic adaptation matrix
M_CAM16 = np.array(
    [
        [0.401288, 0.650173, -0.051461],
        [-0.250268, 1.204414, 0.045854],
        [-0.002079, 0.048952, 0.953127],
    ],
    dtype=np.float64,
)

M_CAM16_INV = np.linalg.inv(M_CAM16)


# =============================================================================
# Hue Quadrature Data (CIECAM02)
# =============================================================================

# Unique hue data: (h_i, e_i, H_i)
#   Red, Yellow, Green, Blue, Red (wrap)
_UNIQUE_HUES = {
    "h": np.array([20.14, 90.00, 164.25, 237.53, 380.14]),
    "e": np.array([0.8, 0.7, 1.0, 1.2, 0.8]),
    "H": np.array([0.0, 100.0, 200.0, 300.0, 400.0]),
}


def hue_quadrature(h: float) -> float:
    """
    Compute hue quadrature H from hue angle h (degrees).

    Uses CIECAM02 piecewise interpolation between the four unique
    hues: Red (0), Yellow (100), Green (200), Blue (300).

    Args:
        h: Hue angle in degrees [0, 360).

    Returns:
        Hue quadrature H in the range [0, 400).
    """
    h_p = h
    if h_p < _UNIQUE_HUES["h"][0]:
        h_p += 360.0

    hi = _UNIQUE_HUES["h"]
    ei = _UNIQUE_HUES["e"]
    Hi = _UNIQUE_HUES["H"]

    # Find the interval
    for i in range(4):
        if hi[i] <= h_p < hi[i + 1]:
            h_i = hi[i]
            e_i = ei[i]
            H_i = Hi[i]
            h_next = hi[i + 1]
            e_next = ei[i + 1]
            break
    else:
        # Should not reach here with valid input
        return 0.0

    num = (h_p - h_i) / e_i
    denom = (h_p - h_i) / e_i + (h_next - h_p) / e_next
    H = H_i + (100.0 * num) / denom

    return H


def _inv_hue_quadrature(H: float) -> float:
    """Inverse: compute hue angle h from hue quadrature H."""
    hi = _UNIQUE_HUES["h"]
    ei = _UNIQUE_HUES["e"]
    Hi = _UNIQUE_HUES["H"]

    # Find interval
    for i in range(4):
        if Hi[i] <= H < Hi[i + 1]:
            break
    else:
        i = 3

    h_i = hi[i]
    e_i = ei[i]
    H_i = Hi[i]
    h_next = hi[i + 1]
    e_next = ei[i + 1]

    (H - H_i) * (e_next * h_i - e_i * h_next)
    -100.0 * h_next * e_i
    100.0 * h_i * e_next

    # H = H_i + 100 * ((h' - h_i)/e_i) / ((h' - h_i)/e_i + (h_{i+1} - h')/e_{i+1})
    # Solve for h':
    # (H - H_i) * ((h' - h_i)/e_i + (h_{i+1} - h')/e_{i+1}) = 100 * (h' - h_i)/e_i
    # Let fraction = (H - H_i) / 100
    frac = (H - H_i) / 100.0

    # frac * ((h' - h_i)/e_i + (h_next - h')/e_next) = (h' - h_i)/e_i
    # frac * (h' - h_i)/e_i + frac * (h_next - h')/e_next = (h' - h_i)/e_i
    # frac*(h_next - h')/e_next = (1 - frac)*(h' - h_i)/e_i
    # frac*h_next/e_next - frac*h'/e_next = (1-frac)*h'/e_i - (1-frac)*h_i/e_i
    # h' * ((1-frac)/e_i + frac/e_next) = frac*h_next/e_next + (1-frac)*h_i/e_i
    numer = frac * h_next / e_next + (1.0 - frac) * h_i / e_i
    denom = (1.0 - frac) / e_i + frac / e_next

    h_p = numer / denom

    # Unwrap
    if h_p > 360.0:
        h_p -= 360.0

    return h_p


# =============================================================================
# Nonlinear Response Function
# =============================================================================


def _nonlinear_adaptation(x: np.ndarray, F_L: float) -> np.ndarray:
    """
    CIECAM02 / CAM16 nonlinear post-adaptation cone response.

    f(x) = sign(x) * 400 * (F_L * |x| / 100)^0.42
                / (27.13 + (F_L * |x| / 100)^0.42) + 0.1

    Args:
        x: Cone response values.
        F_L: Luminance adaptation factor.

    Returns:
        Compressed cone responses.
    """
    abs_x = np.abs(x)
    p = (F_L * abs_x / 100.0) ** 0.42
    return np.sign(x) * 400.0 * p / (27.13 + p) + 0.1


def _nonlinear_adaptation_inv(y: np.ndarray, F_L: float) -> np.ndarray:
    """
    Inverse of the nonlinear adaptation function.

    Given compressed value y, recover the linear cone response x.
    """
    y0 = y - 0.1
    abs_y0 = np.abs(y0)
    # Avoid division by zero
    denom = np.maximum(400.0 - abs_y0, 1e-12)
    p = 27.13 * abs_y0 / denom
    x = np.sign(y0) * (100.0 / F_L) * p ** (1.0 / 0.42)
    return x


# =============================================================================
# CIECAM02 Forward Model
# =============================================================================


def _compute_adaptation_params(vc: ViewingConditions) -> dict:
    """
    Precompute all adaptation parameters from viewing conditions.

    This is shared between forward and inverse transforms.
    """
    surround = SURROUND.get(vc.surround.lower())
    if surround is None:
        raise ValueError(f"Unknown surround: {vc.surround}. Options: {list(SURROUND.keys())}")

    c = surround["c"]
    Nc = surround["Nc"]
    F = surround["F"]

    # Degree of adaptation
    k = 1.0 / (5.0 * vc.L_A + 1.0)
    F_L = 0.2 * k**4 * 5.0 * vc.L_A + 0.1 * (1.0 - k**4) ** 2 * (5.0 * vc.L_A) ** (1.0 / 3.0)

    n = vc.Y_b / vc.white_point[1]
    Nbb = 0.725 * (1.0 / n) ** 0.2
    Ncb = Nbb
    z = 1.48 + np.sqrt(n)

    # Degree of adaptation D
    D = F * (1.0 - (1.0 / 3.6) * np.exp((-vc.L_A - 42.0) / 92.0))
    D = max(0.0, min(1.0, D))

    # Adapted white point cone responses
    RGB_w = M_CAT02 @ vc.white_point
    D_R = D * vc.white_point[1] / RGB_w[0] + 1.0 - D
    D_G = D * vc.white_point[1] / RGB_w[1] + 1.0 - D
    D_B = D * vc.white_point[1] / RGB_w[2] + 1.0 - D

    # Adapted cone responses of white (for A_w calculation)
    RGB_wc = np.array([D_R * RGB_w[0], D_G * RGB_w[1], D_B * RGB_w[2]])

    # Convert to HPE space
    RGB_w_hpe = M_HPE @ (M_CAT02_INV @ RGB_wc)

    # Nonlinear adaptation of white
    RGB_aw = _nonlinear_adaptation(RGB_w_hpe, F_L)

    # Achromatic response of white
    A_w = (2.0 * RGB_aw[0] + RGB_aw[1] + 0.05 * RGB_aw[2] - 0.305) * Nbb

    return {
        "c": c,
        "Nc": Nc,
        "F": F,
        "F_L": F_L,
        "n": n,
        "Nbb": Nbb,
        "Ncb": Ncb,
        "z": z,
        "D": D,
        "D_R": D_R,
        "D_G": D_G,
        "D_B": D_B,
        "RGB_w": RGB_w,
        "A_w": A_w,
    }


@dataclass
class CIECAM02Color:
    """
    Complete set of CIECAM02 appearance correlates for a color stimulus.

    Attributes:
        J: Lightness (0 = black, 100 = white).
        C: Chroma (0 = achromatic, unbounded above).
        h: Hue angle in degrees [0, 360).
        Q: Brightness (absolute, depends on luminance level).
        M: Colorfulness (absolute chroma scaled by luminance).
        s: Saturation (colorfulness relative to brightness).
        H: Hue quadrature (0-400 composition of unique hues).
    """

    J: float
    C: float
    h: float
    Q: float
    M: float
    s: float
    H: float


def ciecam02_forward(
    xyz: np.ndarray,
    vc: ViewingConditions,
) -> CIECAM02Color:
    """
    CIECAM02 forward model: XYZ -> appearance correlates.

    Computes lightness, chroma, hue angle, brightness, colorfulness,
    saturation, and hue quadrature for the given stimulus under the
    specified viewing conditions.

    Args:
        xyz: Tristimulus values as a shape (3,) array.
        vc: Viewing conditions (white point, surround, luminance).

    Returns:
        CIECAM02Color with all seven correlates.

    Example:
        >>> vc = ViewingConditions(
        ...     white_point=np.array([0.95047, 1.0, 1.08883]),
        ...     L_A=64.0, Y_b=20.0, surround="average"
        ... )
        >>> result = ciecam02_forward(np.array([0.20654, 0.12197, 0.05136]), vc)
        >>> round(result.J, 2)
        41.73
    """
    xyz = np.asarray(xyz, dtype=np.float64)
    params = _compute_adaptation_params(vc)

    c = params["c"]
    Nc = params["Nc"]
    F_L = params["F_L"]
    Nbb = params["Nbb"]
    Ncb = params["Ncb"]
    z = params["z"]
    n = params["n"]
    D_R = params["D_R"]
    D_G = params["D_G"]
    D_B = params["D_B"]
    A_w = params["A_w"]

    # Step 1: CAT02 forward — cone responses
    RGB = M_CAT02 @ xyz

    # Step 2: Degree-of-adaptation transform
    RGB_c = np.array([D_R * RGB[0], D_G * RGB[1], D_B * RGB[2]])

    # Step 3: HPE cone-like responses
    RGB_p = M_HPE @ (M_CAT02_INV @ RGB_c)

    # Step 4: Nonlinear post-adaptation compression
    RGB_a = _nonlinear_adaptation(RGB_p, F_L)

    # Step 5: Opponent color dimensions
    a = RGB_a[0] - 12.0 * RGB_a[1] / 11.0 + RGB_a[2] / 11.0
    b = (RGB_a[0] + RGB_a[1] - 2.0 * RGB_a[2]) / 9.0

    # Step 6: Hue angle
    h = np.degrees(np.arctan2(b, a)) % 360.0

    # Step 7: Eccentricity factor and hue quadrature
    H = hue_quadrature(h)

    np.radians(h)

    # Eccentricity
    h_p = h
    if h_p < _UNIQUE_HUES["h"][0]:
        h_p += 360.0
    # Find the interval for eccentricity
    hi = _UNIQUE_HUES["h"]
    ei = _UNIQUE_HUES["e"]
    for i in range(4):
        if hi[i] <= h_p < hi[i + 1]:
            e_t = ei[i] + (ei[i + 1] - ei[i]) * (h_p - hi[i]) / (hi[i + 1] - hi[i])
            break
    else:
        e_t = ei[0]

    # Step 8: Achromatic response
    A = (2.0 * RGB_a[0] + RGB_a[1] + 0.05 * RGB_a[2] - 0.305) * Nbb

    # Step 9: Lightness J
    J = 100.0 * (A / A_w) ** (c * z)

    # Step 10: Brightness Q
    Q = (4.0 / c) * (J / 100.0) ** 0.5 * (A_w + 4.0) * F_L**0.25

    # Step 11: Chroma preliminary — t
    t_num = (50000.0 / 13.0) * Nc * Ncb * e_t * np.sqrt(a**2 + b**2)
    t_den = RGB_a[0] + RGB_a[1] + 21.0 * RGB_a[2] / 20.0
    t = t_num / max(t_den, 1e-12)

    # Step 12: Chroma C
    C = t**0.9 * (J / 100.0) ** 0.5 * (1.64 - 0.29**n) ** 0.73

    # Step 13: Colorfulness M
    M = C * F_L**0.25

    # Step 14: Saturation s
    if Q > 1e-12:
        s = 100.0 * (M / Q) ** 0.5
    else:
        s = 0.0

    return CIECAM02Color(J=J, C=C, h=h, Q=Q, M=M, s=s, H=H)


# =============================================================================
# CIECAM02 Inverse Model
# =============================================================================


def ciecam02_inverse(
    J: float,
    C: float,
    h: float,
    vc: ViewingConditions,
) -> np.ndarray:
    """
    CIECAM02 inverse model: (J, C, h) -> XYZ.

    Reconstructs tristimulus values from lightness, chroma, and hue
    under the given viewing conditions.

    Args:
        J: Lightness (0-100).
        C: Chroma (>= 0).
        h: Hue angle in degrees [0, 360).
        vc: Viewing conditions.

    Returns:
        XYZ tristimulus values as a shape (3,) array.

    Example:
        >>> vc = ViewingConditions(
        ...     white_point=np.array([0.95047, 1.0, 1.08883]),
        ...     L_A=64.0, Y_b=20.0, surround="average"
        ... )
        >>> xyz_in = np.array([0.20654, 0.12197, 0.05136])
        >>> fwd = ciecam02_forward(xyz_in, vc)
        >>> xyz_out = ciecam02_inverse(fwd.J, fwd.C, fwd.h, vc)
        >>> np.allclose(xyz_in, xyz_out, atol=1e-10)
        True
    """
    params = _compute_adaptation_params(vc)

    c_param = params["c"]
    Nc = params["Nc"]
    F_L = params["F_L"]
    Nbb = params["Nbb"]
    Ncb = params["Ncb"]
    z = params["z"]
    n = params["n"]
    D_R = params["D_R"]
    D_G = params["D_G"]
    D_B = params["D_B"]
    A_w = params["A_w"]

    h_rad = np.radians(h)

    # Step 1: Recover A from J
    A = A_w * (J / 100.0) ** (1.0 / (c_param * z))

    # Step 2: Recover t from C, J
    p2 = (1.64 - 0.29**n) ** 0.73
    if J > 1e-12 and abs(p2) > 1e-12:
        t = (C / ((J / 100.0) ** 0.5 * p2)) ** (1.0 / 0.9)
    else:
        t = 0.0

    # Step 3: Eccentricity factor
    h_p = h
    if h_p < _UNIQUE_HUES["h"][0]:
        h_p += 360.0
    hi = _UNIQUE_HUES["h"]
    ei = _UNIQUE_HUES["e"]
    for i in range(4):
        if hi[i] <= h_p < hi[i + 1]:
            e_t = ei[i] + (ei[i + 1] - ei[i]) * (h_p - hi[i]) / (hi[i + 1] - hi[i])
            break
    else:
        e_t = ei[0]

    # Step 4: Recover a, b from t, hue, and the achromatic signal.
    #
    # From the forward model the adapted cone responses are related to
    # opponent signals a, b and the achromatic variable p2 by:
    #
    #   Ra = (460*p2 + 451*a + 288*b) / 1403
    #   Ga = (460*p2 - 891*a - 261*b) / 1403
    #   Ba = (460*p2 - 220*a - 6300*b) / 1403
    #
    # The constraint from the colorfulness variable t is:
    #   Ra + Ga + 21*Ba/20 = (50000/13)*Nc*Ncb*e_t * sqrt(a^2+b^2) / t
    #
    # Substituting the Ra, Ga, Ba expressions into the left side:
    #   Ra + Ga + 21*Ba/20
    #     = (1/1403) * [460*p2 + 451*a + 288*b
    #                 + 460*p2 - 891*a - 261*b
    #                 + (21/20)*(460*p2 - 220*a - 6300*b)]
    #     = (1/1403) * [p2*(920 + 483) + a*(451-891-231) + b*(288-261-6615)]
    #     = (1/1403) * [1403*p2 + a*(-671) + b*(-6588)]  ... but let's not
    #       simplify here — use the standard CIE 159:2004 route instead.
    #
    # The standard approach: given a = gamma*cos(h), b = gamma*sin(h),
    # substitute into the constraint and solve for gamma.  Then
    # a = gamma*cos(h), b = gamma*sin(h).
    #
    # From the forward definition of t:
    #   t = (50000/13)*Nc*Ncb*e_t*sqrt(a^2+b^2) / (Ra + Ga + 21*Ba/20)
    #
    # Let gamma = sqrt(a^2+b^2).  Then a = gamma*cos(h), b = gamma*sin(h).
    # Let S = Ra + Ga + 21*Ba/20 (the "colorfulness denominator").
    #
    # Expressing S in terms of p2 and gamma:
    #   S = (1/1403)*[460*p2*(2 + 21/20) + gamma*(cos(h)*(451-891-21*220/20)
    #                                             + sin(h)*(288-261-21*6300/20))]
    #
    #   460*(2 + 21/20) = 460 * 61/20 = 1403     (!)
    #   cos coeff: 451 - 891 - 231 = -671
    #   sin coeff: 288 - 261 - 6615 = -6588
    #
    # So S = p2 + gamma*(-671*cos(h) - 6588*sin(h)) / 1403
    #
    # And from t: gamma = t * S / ((50000/13)*Nc*Ncb*e_t)
    # Let K = (50000/13)*Nc*Ncb*e_t.  Then gamma = t*S/K.
    # Substituting S:
    #   gamma = (t/K) * [p2 + gamma*(-671*cos(h) - 6588*sin(h))/1403]
    #   gamma = t*p2/K + gamma*t*(-671*cos(h) - 6588*sin(h))/(K*1403)
    #   gamma * [1 - t*(-671*cos(h) - 6588*sin(h))/(K*1403)] = t*p2/K
    #   gamma = (t*p2/K) / [1 + t*(671*cos(h) + 6588*sin(h))/(K*1403)]
    #
    # This is algebraically exact and avoids the sin/cos branch issue.

    p2_val = A / Nbb + 0.305

    if t > 1e-12:
        cos_h = np.cos(h_rad)
        sin_h = np.sin(h_rad)

        K = (50000.0 / 13.0) * Nc * Ncb * e_t
        gamma_num = t * p2_val / K
        gamma_den = 1.0 + t * (671.0 * cos_h + 6588.0 * sin_h) / (K * 1403.0)

        if abs(gamma_den) > 1e-12:
            gamma = gamma_num / gamma_den
        else:
            gamma = 0.0

        a_val = gamma * cos_h
        b_val = gamma * sin_h
    else:
        a_val = 0.0
        b_val = 0.0

    # Step 5: Recover adapted cone responses from a, b, and achromatic signal

    Ra = (460.0 * p2_val + 451.0 * a_val + 288.0 * b_val) / 1403.0
    Ga = (460.0 * p2_val - 891.0 * a_val - 261.0 * b_val) / 1403.0
    Ba = (460.0 * p2_val - 220.0 * a_val - 6300.0 * b_val) / 1403.0

    # Step 6: Inverse nonlinear adaptation
    RGB_p = _nonlinear_adaptation_inv(np.array([Ra, Ga, Ba]), F_L)

    # Step 7: HPE inverse -> CAT02 adapted space
    RGB_c = M_CAT02 @ (M_HPE_INV @ RGB_p)

    # Step 8: Undo degree-of-adaptation
    RGB = np.array(
        [
            RGB_c[0] / D_R,
            RGB_c[1] / D_G,
            RGB_c[2] / D_B,
        ]
    )

    # Step 9: CAT02 inverse -> XYZ
    xyz = M_CAT02_INV @ RGB

    return xyz


# =============================================================================
# CAM16 Forward Model
# =============================================================================


@dataclass
class CAM16Color:
    """
    Complete set of CAM16 appearance correlates.

    Same attributes as CIECAM02Color but computed with the updated
    CAM16 chromatic adaptation transform.
    """

    J: float
    C: float
    h: float
    Q: float
    M: float
    s: float
    H: float


def _compute_cam16_params(vc: ViewingConditions) -> dict:
    """
    Precompute adaptation parameters for the CAM16 model.

    Uses the CAM16 (M_CAM16) matrix instead of CAT02,
    and the simplified CAM16 adaptation transform (no HPE step).
    """
    surround = SURROUND.get(vc.surround.lower())
    if surround is None:
        raise ValueError(f"Unknown surround: {vc.surround}. Options: {list(SURROUND.keys())}")

    c = surround["c"]
    Nc = surround["Nc"]
    F = surround["F"]

    k = 1.0 / (5.0 * vc.L_A + 1.0)
    F_L = 0.2 * k**4 * 5.0 * vc.L_A + 0.1 * (1.0 - k**4) ** 2 * (5.0 * vc.L_A) ** (1.0 / 3.0)

    n = vc.Y_b / vc.white_point[1]
    Nbb = 0.725 * (1.0 / n) ** 0.2
    Ncb = Nbb
    z = 1.48 + np.sqrt(n)

    D = F * (1.0 - (1.0 / 3.6) * np.exp((-vc.L_A - 42.0) / 92.0))
    D = max(0.0, min(1.0, D))

    # White point adaptation in CAM16 space
    RGB_w = M_CAM16 @ vc.white_point
    D_R = D * vc.white_point[1] / RGB_w[0] + 1.0 - D
    D_G = D * vc.white_point[1] / RGB_w[1] + 1.0 - D
    D_B = D * vc.white_point[1] / RGB_w[2] + 1.0 - D

    # In CAM16, adapted cone responses go directly to post-adaptation
    # (no separate HPE step)
    RGB_wc = np.array([D_R * RGB_w[0], D_G * RGB_w[1], D_B * RGB_w[2]])
    RGB_aw = _nonlinear_adaptation(RGB_wc, F_L)

    A_w = (2.0 * RGB_aw[0] + RGB_aw[1] + 0.05 * RGB_aw[2] - 0.305) * Nbb

    return {
        "c": c,
        "Nc": Nc,
        "F": F,
        "F_L": F_L,
        "n": n,
        "Nbb": Nbb,
        "Ncb": Ncb,
        "z": z,
        "D": D,
        "D_R": D_R,
        "D_G": D_G,
        "D_B": D_B,
        "RGB_w": RGB_w,
        "A_w": A_w,
    }


def cam16_forward(
    xyz: np.ndarray,
    vc: ViewingConditions,
) -> CAM16Color:
    """
    CAM16 forward model: XYZ -> appearance correlates.

    CAM16 (Li et al. 2017) improves on CIECAM02 by replacing the
    CAT02 + HPE two-step adaptation with a single M_CAM16 matrix,
    fixing well-known blue-purple issues.

    Args:
        xyz: Tristimulus values as a shape (3,) array.
        vc: Viewing conditions.

    Returns:
        CAM16Color with J, C, h, Q, M, s, H.
    """
    xyz = np.asarray(xyz, dtype=np.float64)
    params = _compute_cam16_params(vc)

    c = params["c"]
    Nc = params["Nc"]
    F_L = params["F_L"]
    Nbb = params["Nbb"]
    Ncb = params["Ncb"]
    z = params["z"]
    n = params["n"]
    D_R = params["D_R"]
    D_G = params["D_G"]
    D_B = params["D_B"]
    A_w = params["A_w"]

    # Step 1: CAM16 cone responses
    RGB = M_CAM16 @ xyz

    # Step 2: Adapted cone responses (single-step, no HPE needed)
    RGB_c = np.array([D_R * RGB[0], D_G * RGB[1], D_B * RGB[2]])

    # Step 3: Nonlinear post-adaptation compression
    RGB_a = _nonlinear_adaptation(RGB_c, F_L)

    # Step 4: Opponent dimensions
    a = RGB_a[0] - 12.0 * RGB_a[1] / 11.0 + RGB_a[2] / 11.0
    b = (RGB_a[0] + RGB_a[1] - 2.0 * RGB_a[2]) / 9.0

    # Step 5: Hue angle
    h = np.degrees(np.arctan2(b, a)) % 360.0

    # Step 6: Hue quadrature
    H = hue_quadrature(h)

    # Eccentricity
    h_p = h
    if h_p < _UNIQUE_HUES["h"][0]:
        h_p += 360.0
    hi = _UNIQUE_HUES["h"]
    ei = _UNIQUE_HUES["e"]
    for i in range(4):
        if hi[i] <= h_p < hi[i + 1]:
            e_t = ei[i] + (ei[i + 1] - ei[i]) * (h_p - hi[i]) / (hi[i + 1] - hi[i])
            break
    else:
        e_t = ei[0]

    # Step 7: Achromatic response
    A = (2.0 * RGB_a[0] + RGB_a[1] + 0.05 * RGB_a[2] - 0.305) * Nbb

    # Step 8: Lightness J
    J = 100.0 * (A / A_w) ** (c * z)

    # Step 9: Brightness Q
    Q = (4.0 / c) * (J / 100.0) ** 0.5 * (A_w + 4.0) * F_L**0.25

    # Step 10: Chroma
    t_num = (50000.0 / 13.0) * Nc * Ncb * e_t * np.sqrt(a**2 + b**2)
    t_den = RGB_a[0] + RGB_a[1] + 21.0 * RGB_a[2] / 20.0
    t = t_num / max(t_den, 1e-12)

    C = t**0.9 * (J / 100.0) ** 0.5 * (1.64 - 0.29**n) ** 0.73

    # Step 11: Colorfulness M
    M = C * F_L**0.25

    # Step 12: Saturation s
    if Q > 1e-12:
        s = 100.0 * (M / Q) ** 0.5
    else:
        s = 0.0

    return CAM16Color(J=J, C=C, h=h, Q=Q, M=M, s=s, H=H)


# =============================================================================
# CAM16-UCS (Uniform Color Space)
# =============================================================================


def cam16_ucs(
    xyz: np.ndarray,
    vc: ViewingConditions,
) -> np.ndarray:
    """
    child safety assessment XYZ to CAM16-UCS uniform coordinates (J', a', b').

    The CAM16-UCS projection (Li et al. 2017, LCD variant) compresses
    lightness and colorfulness for perceptual uniformity:

        J' = 1.7 * J / (1 + 0.007 * J)
        M' = ln(1 + 0.0228 * M) / 0.0228
        a' = M' * cos(h)
        b' = M' * sin(h)

    Args:
        xyz: Tristimulus values as a shape (3,) array.
        vc: Viewing conditions.

    Returns:
        Shape (3,) array of [J', a', b'].
    """
    cam = cam16_forward(xyz, vc)

    J_prime = 1.7 * cam.J / (1.0 + 0.007 * cam.J)
    M_prime = np.log(1.0 + 0.0228 * cam.M) / 0.0228

    h_rad = np.radians(cam.h)
    a_prime = M_prime * np.cos(h_rad)
    b_prime = M_prime * np.sin(h_rad)

    return np.array([J_prime, a_prime, b_prime])


def delta_e_cam16(
    ucs1: np.ndarray,
    ucs2: np.ndarray,
) -> float:
    """
    Color difference in CAM16-UCS (Euclidean distance).

    Args:
        ucs1: First color as (J', a', b').
        ucs2: Second color as (J', a', b').

    Returns:
        Scalar distance. Perceptual threshold ~1.0.

    Example:
        >>> vc = ViewingConditions(
        ...     white_point=np.array([0.95047, 1.0, 1.08883]),
        ...     L_A=64.0, Y_b=20.0, surround="average"
        ... )
        >>> ucs1 = cam16_ucs(np.array([0.20654, 0.12197, 0.05136]), vc)
        >>> ucs2 = cam16_ucs(np.array([0.20000, 0.12000, 0.05000]), vc)
        >>> de = delta_e_cam16(ucs1, ucs2)
    """
    ucs1 = np.asarray(ucs1, dtype=np.float64)
    ucs2 = np.asarray(ucs2, dtype=np.float64)
    d = ucs1 - ucs2
    return float(np.sqrt(np.sum(d * d)))


# =============================================================================
# Batch / convenience helpers
# =============================================================================


def ciecam02_forward_batch(
    xyz_array: np.ndarray,
    vc: ViewingConditions,
) -> np.ndarray:
    """
    CIECAM02 forward model for an array of colors.

    Args:
        xyz_array: Shape (N, 3) array of XYZ values.
        vc: Viewing conditions (shared for the batch).

    Returns:
        Shape (N, 7) array where columns are [J, C, h, Q, M, s, H].
    """
    xyz_array = np.asarray(xyz_array, dtype=np.float64)
    n = xyz_array.shape[0]
    result = np.empty((n, 7), dtype=np.float64)

    for i in range(n):
        cam = ciecam02_forward(xyz_array[i], vc)
        result[i] = [cam.J, cam.C, cam.h, cam.Q, cam.M, cam.s, cam.H]

    return result


def cam16_ucs_batch(
    xyz_array: np.ndarray,
    vc: ViewingConditions,
) -> np.ndarray:
    """
    CAM16-UCS mapping for an array of colors.

    Args:
        xyz_array: Shape (N, 3) array of XYZ values.
        vc: Viewing conditions.

    Returns:
        Shape (N, 3) array of [J', a', b'] rows.
    """
    xyz_array = np.asarray(xyz_array, dtype=np.float64)
    n = xyz_array.shape[0]
    result = np.empty((n, 3), dtype=np.float64)

    for i in range(n):
        result[i] = cam16_ucs(xyz_array[i], vc)

    return result


def delta_e_cam16_batch(
    ucs_array1: np.ndarray,
    ucs_array2: np.ndarray,
) -> np.ndarray:
    """
    Pairwise CAM16-UCS color difference for arrays of colors.

    Args:
        ucs_array1: Shape (N, 3) array of (J', a', b').
        ucs_array2: Shape (N, 3) array of (J', a', b').

    Returns:
        Shape (N,) array of distances.
    """
    d = np.asarray(ucs_array1) - np.asarray(ucs_array2)
    return np.sqrt(np.sum(d * d, axis=-1))
