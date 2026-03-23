"""
Color Difference Metrics

Professional color difference calculations for display calibration,
quality control, and color matching.

Metrics:
    delta_e_76      - CIE 1976 (simple Euclidean in Lab)
    delta_e_94      - CIE 1994 (weighted, graphics/textiles)
    delta_e_2000    - CIEDE2000 (most perceptually accurate for SDR)
    delta_e_cmc     - CMC(l:c) (asymmetric, textile industry)
    delta_e_jzazbz  - JzAzBz Delta E (HDR-optimized)
    delta_e_oklab   - Oklab Delta E (modern perceptual)
    delta_e_hyab    - HyAB (hybrid absolute-relative)
    contrast_ratio  - WCAG contrast ratio
"""

import numpy as np
from typing import Tuple


def delta_e_76(lab1: np.ndarray, lab2: np.ndarray) -> np.ndarray:
    """CIE 1976 color difference (simple Euclidean in CIELAB)."""
    lab1, lab2 = np.asarray(lab1), np.asarray(lab2)
    d = lab1 - lab2
    return np.sqrt(np.sum(d * d, axis=-1))


def delta_e_94(lab1: np.ndarray, lab2: np.ndarray,
               application: str = "graphic_arts") -> np.ndarray:
    """
    CIE 1994 color difference.

    Args:
        application: "graphic_arts" (default) or "textiles"
    """
    lab1, lab2 = np.asarray(lab1, dtype=np.float64), np.asarray(lab2, dtype=np.float64)

    dL = lab1[..., 0] - lab2[..., 0]
    C1 = np.sqrt(lab1[..., 1]**2 + lab1[..., 2]**2)
    C2 = np.sqrt(lab2[..., 1]**2 + lab2[..., 2]**2)
    dC = C1 - C2
    da = lab1[..., 1] - lab2[..., 1]
    db = lab1[..., 2] - lab2[..., 2]
    dH_sq = np.maximum(da**2 + db**2 - dC**2, 0.0)

    if application == "textiles":
        kL, K1, K2 = 2.0, 0.048, 0.014
    else:  # graphic_arts
        kL, K1, K2 = 1.0, 0.045, 0.015

    SL = 1.0
    SC = 1.0 + K1 * C1
    SH = 1.0 + K2 * C1

    return np.sqrt((dL / (kL * SL))**2 + (dC / SC)**2 + dH_sq / SH**2)


def delta_e_2000(lab1: np.ndarray, lab2: np.ndarray,
                  kL: float = 1.0, kC: float = 1.0, kH: float = 1.0) -> np.ndarray:
    """
    CIEDE2000 color difference (the standard for display calibration).

    The most perceptually accurate color difference metric for SDR content.
    """
    lab1, lab2 = np.asarray(lab1, dtype=np.float64), np.asarray(lab2, dtype=np.float64)

    L1, a1, b1 = lab1[..., 0], lab1[..., 1], lab1[..., 2]
    L2, a2, b2 = lab2[..., 0], lab2[..., 1], lab2[..., 2]

    C1 = np.sqrt(a1**2 + b1**2)
    C2 = np.sqrt(a2**2 + b2**2)
    C_avg = (C1 + C2) / 2.0
    C_avg7 = C_avg**7
    G = 0.5 * (1.0 - np.sqrt(C_avg7 / (C_avg7 + 25.0**7)))
    a1p = a1 * (1.0 + G)
    a2p = a2 * (1.0 + G)
    C1p = np.sqrt(a1p**2 + b1**2)
    C2p = np.sqrt(a2p**2 + b2**2)
    h1p = np.degrees(np.arctan2(b1, a1p)) % 360
    h2p = np.degrees(np.arctan2(b2, a2p)) % 360

    dLp = L2 - L1
    dCp = C2p - C1p

    dhp = np.where(
        C1p * C2p == 0, 0.0,
        np.where(np.abs(h2p - h1p) <= 180, h2p - h1p,
                 np.where(h2p - h1p > 180, h2p - h1p - 360, h2p - h1p + 360))
    )
    dHp = 2.0 * np.sqrt(C1p * C2p) * np.sin(np.radians(dhp / 2.0))

    L_avg = (L1 + L2) / 2.0
    Cp_avg = (C1p + C2p) / 2.0
    hp_avg = np.where(
        C1p * C2p == 0, h1p + h2p,
        np.where(np.abs(h1p - h2p) <= 180, (h1p + h2p) / 2.0,
                 np.where(h1p + h2p < 360, (h1p + h2p + 360) / 2.0, (h1p + h2p - 360) / 2.0))
    )

    T = (1.0 - 0.17 * np.cos(np.radians(hp_avg - 30)) +
         0.24 * np.cos(np.radians(2 * hp_avg)) +
         0.32 * np.cos(np.radians(3 * hp_avg + 6)) -
         0.20 * np.cos(np.radians(4 * hp_avg - 63)))

    SL = 1.0 + 0.015 * (L_avg - 50)**2 / np.sqrt(20 + (L_avg - 50)**2)
    SC = 1.0 + 0.045 * Cp_avg
    SH = 1.0 + 0.015 * Cp_avg * T

    Cp_avg7 = Cp_avg**7
    RC = 2.0 * np.sqrt(Cp_avg7 / (Cp_avg7 + 25.0**7))
    d_theta = 30.0 * np.exp(-((hp_avg - 275) / 25.0)**2)
    RT = -np.sin(np.radians(2 * d_theta)) * RC

    return np.sqrt(
        (dLp / (kL * SL))**2 +
        (dCp / (kC * SC))**2 +
        (dHp / (kH * SH))**2 +
        RT * (dCp / (kC * SC)) * (dHp / (kH * SH))
    )


def delta_e_cmc(lab1: np.ndarray, lab2: np.ndarray,
                l: float = 2.0, c: float = 1.0) -> np.ndarray:
    """
    CMC(l:c) color difference (asymmetric — order matters).

    Default l=2, c=1 for acceptability. Use l=1, c=1 for perceptibility.
    Widely used in textile and print industries.
    """
    lab1, lab2 = np.asarray(lab1, dtype=np.float64), np.asarray(lab2, dtype=np.float64)

    L1, a1, b1 = lab1[..., 0], lab1[..., 1], lab1[..., 2]
    L2, a2, b2 = lab2[..., 0], lab2[..., 1], lab2[..., 2]

    C1 = np.sqrt(a1**2 + b1**2)
    C2 = np.sqrt(a2**2 + b2**2)
    dC = C1 - C2
    dL = L1 - L2
    da = a1 - a2
    db = b1 - b2
    dH_sq = np.maximum(da**2 + db**2 - dC**2, 0.0)

    SL = np.where(L1 < 16, 0.511, 0.040975 * L1 / (1.0 + 0.01765 * L1))
    SC = 0.0638 * C1 / (1.0 + 0.0131 * C1) + 0.638
    F = np.sqrt(C1**4 / (C1**4 + 1900.0))

    h1 = np.degrees(np.arctan2(b1, a1)) % 360
    T = np.where(
        (h1 >= 164) & (h1 <= 345),
        0.56 + np.abs(0.2 * np.cos(np.radians(h1 + 168))),
        0.36 + np.abs(0.4 * np.cos(np.radians(h1 + 35))),
    )
    SH = SC * (F * T + 1.0 - F)

    return np.sqrt((dL / (l * SL))**2 + (dC / (c * SC))**2 + dH_sq / SH**2)


def delta_e_jzazbz(jzazbz1: np.ndarray, jzazbz2: np.ndarray) -> np.ndarray:
    """JzAzBz color difference (optimized for HDR content)."""
    d = np.asarray(jzazbz1) - np.asarray(jzazbz2)
    return np.sqrt(np.sum(d * d, axis=-1))


def delta_e_oklab(oklab1: np.ndarray, oklab2: np.ndarray) -> np.ndarray:
    """Oklab color difference (modern perceptual uniformity)."""
    d = np.asarray(oklab1) - np.asarray(oklab2)
    return np.sqrt(np.sum(d * d, axis=-1))


def delta_e_hyab(lab1: np.ndarray, lab2: np.ndarray) -> np.ndarray:
    """HyAB hybrid color difference: |dL| + sqrt(da^2 + db^2)."""
    lab1, lab2 = np.asarray(lab1), np.asarray(lab2)
    dL = np.abs(lab1[..., 0] - lab2[..., 0])
    da = lab1[..., 1] - lab2[..., 1]
    db = lab1[..., 2] - lab2[..., 2]
    return dL + np.sqrt(da**2 + db**2)


def contrast_ratio(L1: float, L2: float) -> float:
    """WCAG contrast ratio between two relative luminances."""
    lighter = max(L1, L2)
    darker = min(L1, L2)
    return (lighter + 0.05) / (darker + 0.05)


def compare_all(lab1: np.ndarray, lab2: np.ndarray) -> dict:
    """Compute all Lab-based color difference metrics at once."""
    return {
        "CIE76": float(delta_e_76(lab1, lab2)),
        "CIE94": float(delta_e_94(lab1, lab2)),
        "CIEDE2000": float(delta_e_2000(lab1, lab2)),
        "CMC(2:1)": float(delta_e_cmc(lab1, lab2)),
        "HyAB": float(delta_e_hyab(lab1, lab2)),
    }
