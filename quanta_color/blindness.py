"""
Color Vision Deficiency Simulation

Simulates how colors appear to people with different types of
color vision deficiency (CVD) using the Brettel et al. (1997) method.

Types:
    protanopia    - Red-blind (~1% of males)
    deuteranopia  - Green-blind (~1% of males)
    tritanopia    - Blue-yellow blind (rare)
    achromatopsia - Complete color blindness (very rare)

Usage:
    from quanta_color.blindness import simulate
    simulated = simulate(srgb_image, "deuteranopia", severity=1.0)
"""

import numpy as np

# Brettel et al. (1997) simulation matrices
# Applied to linear sRGB values

PROTANOPIA_MATRIX = np.array(
    [
        [0.152286, 1.052583, -0.204868],
        [0.114503, 0.786281, 0.099216],
        [-0.003882, -0.048116, 1.051998],
    ],
    dtype=np.float64,
)

DEUTERANOPIA_MATRIX = np.array(
    [
        [0.367322, 0.860646, -0.227968],
        [0.280085, 0.672501, 0.047413],
        [-0.011820, 0.042940, 0.968881],
    ],
    dtype=np.float64,
)

TRITANOPIA_MATRIX = np.array(
    [
        [1.255528, -0.076749, -0.178779],
        [-0.078411, 0.930809, 0.147602],
        [0.004733, 0.691367, 0.303900],
    ],
    dtype=np.float64,
)


def _srgb_to_linear(s):
    return np.where(s <= 0.04045, s / 12.92, np.power((s + 0.055) / 1.055, 2.4))


def _linear_to_srgb(c):
    return np.where(c <= 0.0031308, c * 12.92, 1.055 * np.power(np.maximum(c, 0), 1.0 / 2.4) - 0.055)


def simulate(
    srgb: np.ndarray,
    deficiency: str = "deuteranopia",
    severity: float = 1.0,
) -> np.ndarray:
    """
    Simulate color vision deficiency.

    Args:
        srgb: sRGB image or color array (0-1 range)
        deficiency: "protanopia", "deuteranopia", "tritanopia", "achromatopsia"
        severity: 0.0 (normal vision) to 1.0 (full deficiency)

    Returns:
        Simulated sRGB values
    """
    srgb = np.asarray(srgb, dtype=np.float64)
    severity = max(0.0, min(1.0, severity))

    if severity == 0.0:
        return srgb.copy()

    # Convert to linear
    linear = _srgb_to_linear(srgb)

    deficiency = deficiency.lower()

    if deficiency == "achromatopsia":
        # Convert to luminance only
        lum = 0.2126 * linear[..., 0] + 0.7152 * linear[..., 1] + 0.0722 * linear[..., 2]
        sim = np.stack([lum, lum, lum], axis=-1)
    elif deficiency == "protanopia":
        sim = _apply_matrix(linear, PROTANOPIA_MATRIX)
    elif deficiency == "deuteranopia":
        sim = _apply_matrix(linear, DEUTERANOPIA_MATRIX)
    elif deficiency == "tritanopia":
        sim = _apply_matrix(linear, TRITANOPIA_MATRIX)
    else:
        raise ValueError(f"Unknown deficiency: {deficiency}. Use: protanopia, deuteranopia, tritanopia, achromatopsia")

    # Blend with original based on severity
    result = linear * (1 - severity) + sim * severity

    # Convert back to sRGB
    return np.clip(_linear_to_srgb(result), 0, 1)


def _apply_matrix(linear: np.ndarray, matrix: np.ndarray) -> np.ndarray:
    """Apply CVD simulation matrix to linear RGB."""
    if linear.ndim == 1:
        return matrix @ linear
    original_shape = linear.shape
    flat = linear.reshape(-1, 3)
    result = (matrix @ flat.T).T
    return result.reshape(original_shape)


def error_map(
    srgb: np.ndarray,
    deficiency: str = "deuteranopia",
) -> np.ndarray:
    """
    Compute the color error — what information is lost for a CVD viewer.

    Returns the difference between normal and simulated vision,
    useful for checking if your design is CVD-accessible.
    """
    sim = simulate(srgb, deficiency, severity=1.0)
    return np.abs(srgb - sim)


DEFICIENCY_TYPES = ["protanopia", "deuteranopia", "tritanopia", "achromatopsia"]
