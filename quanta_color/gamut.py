"""
Gamut Mapping

Algorithms for mapping out-of-gamut colors to a target gamut
while preserving perceptual quality.

Methods:
    clip            - Simple RGB clipping (fastest, worst quality)
    compress         - Soft compression near gamut boundary
    oklab_chroma    - Reduce chroma in Oklab (CSS Color Level 4)
    jzazbz_chroma   - Reduce chroma in JzAzBz (HDR-optimized)
    perceptual      - Binary search for max chroma at given hue/lightness
"""

import numpy as np


def clip(rgb: np.ndarray) -> np.ndarray:
    """Simple gamut clipping to [0, 1]."""
    return np.clip(np.asarray(rgb), 0.0, 1.0)


def compress(rgb: np.ndarray, threshold: float = 0.8, limit: float = 1.0, power: float = 1.2) -> np.ndarray:
    """
    Soft gamut compression. Values above threshold are smoothly
    compressed toward limit instead of hard-clipped.
    """
    rgb = np.asarray(rgb, dtype=np.float64)

    def _compress_channel(x):
        above = x > threshold
        excess = x - threshold
        max_excess = limit - threshold
        with np.errstate(divide="ignore", invalid="ignore"):
            compressed = threshold + max_excess * np.power(excess / (max_excess + 1e-10), 1.0 / power) * np.where(
                excess > 0, 1, 0
            )
        return np.where(above, np.minimum(compressed, limit), np.maximum(x, 0))

    result = np.empty_like(rgb)
    for i in range(3):
        result[..., i] = _compress_channel(rgb[..., i])
    return result


def oklab_chroma_reduce(srgb: np.ndarray, target_gamut: str = "srgb") -> np.ndarray:
    """
    Reduce chroma in Oklab space until color is in gamut.
    CSS Color Module Level 4 approach.
    """
    from quanta_color.spaces import (
        srgb_to_oklab,
    )

    srgb = np.asarray(srgb, dtype=np.float64)
    oklab = srgb_to_oklab(srgb)

    if srgb.ndim == 1:
        return _reduce_single(oklab)

    # Batch processing
    shape = srgb.shape
    flat = oklab.reshape(-1, 3)
    result = np.empty_like(flat)
    for i in range(len(flat)):
        result[i] = _reduce_single(flat[i])
    return result.reshape(shape)


def _reduce_single(oklab: np.ndarray) -> np.ndarray:
    """Reduce chroma for a single Oklab color."""
    from quanta_color.spaces import (
        linear_to_srgb,
        oklab_to_linear_srgb,
        oklab_to_oklch,
        oklch_to_oklab,
    )

    # Check if already in gamut
    linear = oklab_to_linear_srgb(oklab)
    if np.all(linear >= -0.001) and np.all(linear <= 1.001):
        return np.clip(linear_to_srgb(np.clip(linear, 0, 1)), 0, 1)

    # Convert to cylindrical
    lch = oklab_to_oklch(oklab)
    L, C, h = lch[0], lch[1], lch[2]

    # Binary search for max chroma
    lo, hi = 0.0, C
    for _ in range(20):
        mid = (lo + hi) / 2
        test_lch = np.array([L, mid, h])
        test_oklab = oklch_to_oklab(test_lch)
        test_linear = oklab_to_linear_srgb(test_oklab)
        if np.all(test_linear >= -0.001) and np.all(test_linear <= 1.001):
            lo = mid
        else:
            hi = mid

    final_lch = np.array([L, lo, h])
    final_oklab = oklch_to_oklab(final_lch)
    final_linear = np.clip(oklab_to_linear_srgb(final_oklab), 0, 1)
    return np.clip(linear_to_srgb(final_linear), 0, 1)


def is_in_gamut(rgb: np.ndarray, tolerance: float = 0.001) -> np.ndarray:
    """Check if RGB values are within the [0, 1] gamut."""
    rgb = np.asarray(rgb)
    return np.all(rgb >= -tolerance, axis=-1) & np.all(rgb <= 1 + tolerance, axis=-1)


def gamut_coverage(
    display_primaries: list,
    target_primaries: list,
) -> float:
    """
    Calculate 2D gamut coverage (area ratio) using the Shoelace formula.

    Args:
        display_primaries: [(rx,ry), (gx,gy), (bx,by)] of the display
        target_primaries: [(rx,ry), (gx,gy), (bx,by)] of the target

    Returns:
        Coverage as fraction (0-1+). >1 means display exceeds target.
    """

    def _triangle_area(pts):
        n = len(pts)
        area = 0.0
        for i in range(n):
            j = (i + 1) % n
            area += pts[i][0] * pts[j][1]
            area -= pts[j][0] * pts[i][1]
        return abs(area) / 2.0

    display_area = _triangle_area(display_primaries)
    target_area = _triangle_area(target_primaries)

    if target_area == 0:
        return 0.0
    return display_area / target_area
