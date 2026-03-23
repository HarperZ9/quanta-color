"""
Chromatic Adaptation Transforms

Professional chromatic adaptation for converting colors between
illuminants. Supports 9 cone response models.

Methods:
    xyz_scaling    - Simple XYZ scaling (identity matrix)
    von_kries      - Hunt-Pointer-Estevez cone response
    bradford       - Bradford (most widely used, ICC standard)
    sharp          - Sharp adaptation (enhanced Bradford)
    cmccat2000     - CMC Colour Appearance Transform 2000
    cat02          - CIE CAM02 (CIECAM02 standard)
    cat16          - CAM16 (recommended for modern work)
    fairchild      - Fairchild adaptation
    bianco         - Bianco-Schettini PC algorithm
"""

import numpy as np
from typing import Tuple, Optional

# =============================================================================
# Standard Illuminants (CIE 1931 xy + XYZ normalized to Y=1)
# =============================================================================

ILLUMINANTS = {
    "D50":  np.array([0.96422, 1.0, 0.82521]),
    "D55":  np.array([0.95682, 1.0, 0.92149]),
    "D65":  np.array([0.95047, 1.0, 1.08883]),
    "D75":  np.array([0.94972, 1.0, 1.22638]),
    "A":    np.array([1.09850, 1.0, 0.35585]),
    "F2":   np.array([0.99186, 1.0, 0.67393]),
    "F11":  np.array([1.00962, 1.0, 0.64350]),
}

# =============================================================================
# Cone Response Matrices
# =============================================================================

MATRICES = {
    "xyz_scaling": np.eye(3),

    "von_kries": np.array([
        [ 0.38971, 0.68898, -0.07868],
        [-0.22981, 1.18340,  0.04641],
        [ 0.00000, 0.00000,  1.00000],
    ]),

    "bradford": np.array([
        [ 0.8951,  0.2664, -0.1614],
        [-0.7502,  1.7135,  0.0367],
        [ 0.0389, -0.0685,  1.0296],
    ]),

    "sharp": np.array([
        [ 1.2694, -0.0988, -0.1706],
        [-0.8364,  1.8006,  0.0357],
        [ 0.0297, -0.0315,  1.0018],
    ]),

    "cmccat2000": np.array([
        [ 0.7982,  0.3389, -0.1371],
        [-0.5918,  1.5512,  0.0406],
        [ 0.0008,  0.0239,  0.9753],
    ]),

    "cat02": np.array([
        [ 0.7328,  0.4296, -0.1624],
        [-0.7036,  1.6975,  0.0061],
        [ 0.0030,  0.0136,  0.9834],
    ]),

    "cat16": np.array([
        [ 0.401288,  0.650173, -0.051461],
        [-0.250268,  1.204414,  0.045854],
        [-0.002079,  0.048952,  0.953127],
    ]),

    "fairchild": np.array([
        [ 0.8562,  0.3372, -0.1934],
        [-0.8360,  1.8327,  0.0033],
        [ 0.0357, -0.0469,  1.0112],
    ]),

    "bianco": np.array([
        [ 0.8752,  0.2787, -0.1539],
        [-0.8904,  1.8709,  0.0195],
        [-0.0061,  0.0162,  0.9899],
    ]),
}


def get_adaptation_matrix(
    source_white: np.ndarray,
    dest_white: np.ndarray,
    method: str = "bradford",
) -> np.ndarray:
    """
    Compute a 3x3 chromatic adaptation matrix.

    Args:
        source_white: Source illuminant XYZ (Y=1 normalized)
        dest_white: Destination illuminant XYZ (Y=1 normalized)
        method: Adaptation method name (see MATRICES)

    Returns:
        3x3 adaptation matrix. Usage: adapted_xyz = M @ xyz
    """
    M = MATRICES.get(method.lower())
    if M is None:
        raise ValueError(f"Unknown adaptation method: {method}. "
                         f"Available: {list(MATRICES.keys())}")

    source_cone = M @ source_white
    dest_cone = M @ dest_white
    scale = np.diag(dest_cone / source_cone)
    M_inv = np.linalg.inv(M)

    return M_inv @ scale @ M


def adapt(
    xyz: np.ndarray,
    source_white: np.ndarray,
    dest_white: np.ndarray,
    method: str = "bradford",
) -> np.ndarray:
    """
    Adapt XYZ values from one illuminant to another.

    Args:
        xyz: XYZ values as (3,) or (N, 3) array
        source_white: Source illuminant XYZ
        dest_white: Destination illuminant XYZ
        method: Adaptation method

    Returns:
        Adapted XYZ values
    """
    M = get_adaptation_matrix(source_white, dest_white, method)
    if xyz.ndim == 1:
        return M @ xyz
    return (M @ xyz.T).T


def adapt_partial(
    xyz: np.ndarray,
    source_white: np.ndarray,
    dest_white: np.ndarray,
    degree: float = 1.0,
    method: str = "bradford",
) -> np.ndarray:
    """
    Partial chromatic adaptation (0 = no adaptation, 1 = full).

    Useful for simulating incomplete adaptation (e.g., mixed lighting).
    """
    degree = max(0.0, min(1.0, degree))
    if degree == 0.0:
        return xyz.copy()
    if degree == 1.0:
        return adapt(xyz, source_white, dest_white, method)

    full_adapt = adapt(xyz, source_white, dest_white, method)
    return xyz * (1.0 - degree) + full_adapt * degree


# =============================================================================
# White Balance Estimation
# =============================================================================

def estimate_white_gray_world(image: np.ndarray) -> np.ndarray:
    """Gray World white balance: assumes average scene is neutral gray."""
    return np.mean(image.reshape(-1, 3), axis=0)


def estimate_white_white_patch(image: np.ndarray) -> np.ndarray:
    """White Patch: assumes brightest pixel is white."""
    return np.max(image.reshape(-1, 3), axis=0)


def estimate_white_percentile(image: np.ndarray, pct: float = 95.0) -> np.ndarray:
    """Modified White Patch: uses percentile instead of max (more robust)."""
    flat = image.reshape(-1, 3)
    return np.percentile(flat, pct, axis=0)


def estimate_white_shades_of_gray(image: np.ndarray, p: float = 6.0) -> np.ndarray:
    """Shades of Gray: Minkowski norm-based (p=1: gray world, p=inf: white patch)."""
    flat = image.reshape(-1, 3).astype(np.float64)
    return np.power(np.mean(np.power(flat, p), axis=0), 1.0 / p)


# =============================================================================
# Color Temperature
# =============================================================================

def xy_to_cct_mccamy(x: float, y: float) -> float:
    """McCamy's CCT approximation from CIE xy chromaticity."""
    n = (x - 0.3320) / (0.1858 - y)
    return 449.0 * n**3 + 3525.0 * n**2 + 6823.3 * n + 5520.33


def cct_to_xy(cct: float) -> Tuple[float, float]:
    """Convert CCT to CIE xy chromaticity (Hernandez-Andres approximation)."""
    T = cct
    if T < 4000:
        x = (-0.2661239e9 / T**3 - 0.2343589e6 / T**2 +
             0.8776956e3 / T + 0.179910)
    elif T <= 7000:
        x = (-3.0258469e9 / T**3 + 2.1070379e6 / T**2 +
             0.2226347e3 / T + 0.240390)
    else:
        x = (-3.0258469e9 / T**3 + 2.1070379e6 / T**2 +
             0.2226347e3 / T + 0.240390)

    y = -3.0 * x**2 + 2.87 * x - 0.275
    return (x, y)


def cct_to_xyz(cct: float) -> np.ndarray:
    """Convert CCT to XYZ (Y=1 normalized)."""
    x, y = cct_to_xy(cct)
    return np.array([x / y, 1.0, (1.0 - x - y) / y])
