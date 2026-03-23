"""
Spectral Rendering

Physical spectral calculations for color science:
- Planck blackbody radiation
- CIE daylight illuminants
- Color matching functions (1931 2-degree observer)
- Spectral to XYZ integration
- Cauchy dispersion model
"""

import numpy as np
from typing import Tuple


# =============================================================================
# Physical Constants
# =============================================================================

C1 = 3.741771e-16   # First radiation constant (W*m^2)
C2 = 1.4387769e-2   # Second radiation constant (m*K)
SPEED_OF_LIGHT = 299792458.0  # m/s
PLANCK_H = 6.62607015e-34     # J*s
BOLTZMANN_K = 1.380649e-23    # J/K


# =============================================================================
# CIE 1931 2-degree Color Matching Functions (5nm intervals, 380-780nm)
# =============================================================================

# Wavelengths
CMF_WAVELENGTHS = np.arange(380, 785, 5, dtype=np.float64)

# x-bar
CMF_X = np.array([
    0.001368, 0.002236, 0.004243, 0.007650, 0.014310,
    0.023190, 0.043510, 0.077630, 0.134380, 0.214770,
    0.283900, 0.328500, 0.348280, 0.348060, 0.336200,
    0.318700, 0.290800, 0.251100, 0.195360, 0.142100,
    0.095640, 0.058010, 0.032010, 0.014700, 0.004900,
    0.002400, 0.009300, 0.029100, 0.063270, 0.109600,
    0.165500, 0.225750, 0.290400, 0.359700, 0.433450,
    0.512050, 0.594500, 0.678400, 0.762100, 0.842500,
    0.916300, 0.978600, 1.026300, 1.056700, 1.062200,
    1.045600, 1.002600, 0.938400, 0.854450, 0.751400,
    0.642400, 0.541900, 0.447900, 0.360800, 0.283500,
    0.218700, 0.164900, 0.121200, 0.087400, 0.063600,
    0.046770, 0.032900, 0.022700, 0.015840, 0.011359,
    0.008111, 0.005790, 0.004109, 0.002899, 0.002049,
    0.001440, 0.001000, 0.000690, 0.000476, 0.000332,
    0.000235, 0.000166, 0.000117, 0.000083, 0.000059,
    0.000042,
], dtype=np.float64)

# y-bar
CMF_Y = np.array([
    0.000039, 0.000064, 0.000120, 0.000217, 0.000396,
    0.000640, 0.001210, 0.002180, 0.004000, 0.007300,
    0.011600, 0.016840, 0.023000, 0.029800, 0.038000,
    0.048000, 0.060000, 0.073900, 0.090980, 0.112600,
    0.139020, 0.169300, 0.208020, 0.258600, 0.323000,
    0.407300, 0.503000, 0.608200, 0.710000, 0.793200,
    0.862000, 0.914850, 0.954000, 0.980300, 0.994950,
    1.000000, 0.995000, 0.978600, 0.952000, 0.915400,
    0.870000, 0.816300, 0.757000, 0.694900, 0.631000,
    0.566800, 0.503000, 0.441200, 0.381000, 0.321000,
    0.265000, 0.217000, 0.175000, 0.138200, 0.107000,
    0.081600, 0.061000, 0.044580, 0.032000, 0.023200,
    0.017000, 0.011920, 0.008210, 0.005723, 0.004102,
    0.002929, 0.002091, 0.001484, 0.001047, 0.000740,
    0.000520, 0.000361, 0.000249, 0.000172, 0.000120,
    0.000085, 0.000060, 0.000042, 0.000030, 0.000021,
    0.000015,
], dtype=np.float64)

# z-bar
CMF_Z = np.array([
    0.006450, 0.010550, 0.020050, 0.036210, 0.067850,
    0.110200, 0.207400, 0.371300, 0.645600, 1.039050,
    1.385600, 1.622960, 1.747060, 1.782600, 1.772110,
    1.744100, 1.669200, 1.528100, 1.287640, 1.041900,
    0.812950, 0.616200, 0.465180, 0.353300, 0.272000,
    0.212300, 0.158200, 0.111700, 0.078250, 0.057250,
    0.042160, 0.029840, 0.020300, 0.013400, 0.008750,
    0.005750, 0.003900, 0.002750, 0.002100, 0.001800,
    0.001650, 0.001400, 0.001100, 0.001000, 0.000800,
    0.000600, 0.000340, 0.000240, 0.000190, 0.000100,
    0.000050, 0.000030, 0.000020, 0.000010, 0.000000,
    0.000000, 0.000000, 0.000000, 0.000000, 0.000000,
    0.000000, 0.000000, 0.000000, 0.000000, 0.000000,
    0.000000, 0.000000, 0.000000, 0.000000, 0.000000,
    0.000000, 0.000000, 0.000000, 0.000000, 0.000000,
    0.000000, 0.000000, 0.000000, 0.000000, 0.000000,
    0.000000,
], dtype=np.float64)


# =============================================================================
# Planck Blackbody
# =============================================================================

def planck_radiation(wavelength_nm: np.ndarray, temperature_K: float) -> np.ndarray:
    """
    Spectral radiance of a blackbody at given temperature.

    Args:
        wavelength_nm: Wavelength(s) in nanometers
        temperature_K: Temperature in Kelvin

    Returns:
        Spectral radiance in W/(m^2 * sr * nm)
    """
    lam = np.asarray(wavelength_nm, dtype=np.float64) * 1e-9  # nm -> m
    T = float(temperature_K)
    return C1 / (lam**5 * (np.exp(C2 / (lam * T)) - 1.0)) * 1e-9


def blackbody_chromaticity(temperature_K: float) -> Tuple[float, float]:
    """Compute CIE xy chromaticity of a blackbody at given temperature."""
    spd = planck_radiation(CMF_WAVELENGTHS, temperature_K)
    xyz = spd_to_xyz(CMF_WAVELENGTHS, spd)
    s = np.sum(xyz)
    return (xyz[0] / s, xyz[1] / s)


# =============================================================================
# CIE Daylight
# =============================================================================

def daylight_chromaticity(cct: float) -> Tuple[float, float]:
    """CIE daylight chromaticity from correlated color temperature."""
    T = cct
    if T < 4000 or T > 25000:
        # Use Planckian locus outside daylight range
        return blackbody_chromaticity(T)

    if T <= 7000:
        x = (-4.6070e9 / T**3 + 2.9678e6 / T**2 +
             0.09911e3 / T + 0.244063)
    else:
        x = (-2.0064e9 / T**3 + 1.9018e6 / T**2 +
             0.24748e3 / T + 0.237040)

    y = -3.000 * x**2 + 2.870 * x - 0.275
    return (x, y)


# =============================================================================
# Spectral Integration
# =============================================================================

def spd_to_xyz(
    wavelengths: np.ndarray,
    spd: np.ndarray,
    cmf_x: np.ndarray = CMF_X,
    cmf_y: np.ndarray = CMF_Y,
    cmf_z: np.ndarray = CMF_Z,
    cmf_wavelengths: np.ndarray = CMF_WAVELENGTHS,
) -> np.ndarray:
    """
    Integrate a spectral power distribution to CIE XYZ.

    X = integral(S(lam) * x_bar(lam) d_lam)
    Y = integral(S(lam) * y_bar(lam) d_lam)
    Z = integral(S(lam) * z_bar(lam) d_lam)
    """
    wavelengths = np.asarray(wavelengths, dtype=np.float64)
    spd = np.asarray(spd, dtype=np.float64)

    # Interpolate CMFs to match SPD wavelengths if needed
    if not np.array_equal(wavelengths, cmf_wavelengths):
        cmf_x = np.interp(wavelengths, cmf_wavelengths, cmf_x)
        cmf_y = np.interp(wavelengths, cmf_wavelengths, cmf_y)
        cmf_z = np.interp(wavelengths, cmf_wavelengths, cmf_z)

    # Trapezoidal integration
    dlam = np.diff(wavelengths)
    X = np.sum((spd[:-1] * cmf_x[:-1] + spd[1:] * cmf_x[1:]) / 2 * dlam)
    Y = np.sum((spd[:-1] * cmf_y[:-1] + spd[1:] * cmf_y[1:]) / 2 * dlam)
    Z = np.sum((spd[:-1] * cmf_z[:-1] + spd[1:] * cmf_z[1:]) / 2 * dlam)

    # Normalize so Y=1 for equal-energy illuminant
    k = 1.0 / np.sum((cmf_y[:-1] + cmf_y[1:]) / 2 * dlam)
    return np.array([X * k, Y * k, Z * k])


def dominant_wavelength(x: float, y: float) -> float:
    """Find the dominant wavelength for a chromaticity coordinate."""
    # White point (D65)
    xw, yw = 0.3127, 0.3290
    dx, dy = x - xw, y - yw

    best_lam = 550.0
    best_dot = -1.0

    for i in range(len(CMF_WAVELENGTHS)):
        sx = CMF_X[i] / (CMF_X[i] + CMF_Y[i] + CMF_Z[i] + 1e-10)
        sy = CMF_Y[i] / (CMF_X[i] + CMF_Y[i] + CMF_Z[i] + 1e-10)
        lx, ly = sx - xw, sy - yw
        dot = dx * lx + dy * ly
        if dot > best_dot:
            best_dot = dot
            best_lam = CMF_WAVELENGTHS[i]

    return best_lam


# =============================================================================
# Dispersion
# =============================================================================

def cauchy_ior(wavelength_nm: float, n0: float = 1.5, B: float = 0.004,
               C: float = 0.0) -> float:
    """Cauchy dispersion model: n(lam) = n0 + B/lam^2 + C/lam^4."""
    lam_um = wavelength_nm / 1000.0  # nm -> um
    return n0 + B / lam_um**2 + C / lam_um**4
