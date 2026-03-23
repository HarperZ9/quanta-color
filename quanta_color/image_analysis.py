"""
Image-Level Color Analysis

Tools for analyzing the color content of images: histograms,
gamut coverage, dominant color extraction, WCAG accessibility
checks, and color vision deficiency confusability analysis.

Functions:
    histogram           - Per-channel histogram in any color space
    gamut_coverage      - Fraction of pixels within a target gamut
    out_of_gamut_mask   - Boolean mask of out-of-gamut pixels
    dominant_colors     - K-means dominant color extraction in Oklab
    wcag_check          - WCAG 2.x contrast ratio and pass/fail
    cvd_problem_pairs   - Find palette pairs confusable under CVD
"""

import numpy as np
from typing import Optional


# =============================================================================
# Histogram
# =============================================================================

def histogram(
    image: np.ndarray,
    space: str = "srgb",
    bins: int = 256,
) -> dict:
    """
    Compute per-channel histogram of an image.

    Args:
        image: (H, W, 3) float64 image in 0-1 sRGB.
        space: Color space for histogram. One of "srgb", "oklab", "lab", "hsv".
        bins: Number of bins per channel (default 256).

    Returns:
        dict with keys:
            channels: list of 3 np.ndarray histograms (one per channel)
            space: the color space used
            bins: number of bins
    """
    image = np.asarray(image, dtype=np.float64)
    pixels = image.reshape(-1, 3)

    if space == "srgb":
        data = pixels
        range_min, range_max = 0.0, 1.0
    elif space == "oklab":
        from quanta_color.spaces import srgb_to_oklab
        data = srgb_to_oklab(pixels)
        range_min, range_max = -0.5, 1.5
    elif space == "lab":
        from quanta_color.spaces import srgb_to_xyz, xyz_to_lab
        xyz = srgb_to_xyz(pixels)
        data = xyz_to_lab(xyz)
        range_min, range_max = -128.0, 128.0
    elif space == "hsv":
        from quanta_color.spaces import rgb_to_hsv
        data = rgb_to_hsv(pixels)
        range_min, range_max = 0.0, 360.0
    else:
        raise ValueError(f"Unknown space: {space}. Use: srgb, oklab, lab, hsv")

    channels = []
    for ch in range(3):
        if space == "lab" and ch == 0:
            hist, _ = np.histogram(data[:, ch], bins=bins, range=(0, 100))
        elif space == "hsv" and ch == 0:
            hist, _ = np.histogram(data[:, ch], bins=bins, range=(0, 360))
        elif space == "hsv" and ch > 0:
            hist, _ = np.histogram(data[:, ch], bins=bins, range=(0, 1))
        elif space == "srgb":
            hist, _ = np.histogram(data[:, ch], bins=bins, range=(0, 1))
        else:
            ch_data = data[:, ch]
            ch_min = float(np.min(ch_data))
            ch_max = float(np.max(ch_data))
            if ch_min == ch_max:
                ch_max = ch_min + 1.0
            hist, _ = np.histogram(ch_data, bins=bins, range=(ch_min, ch_max))
        channels.append(hist)

    return {
        "channels": channels,
        "space": space,
        "bins": bins,
    }


# =============================================================================
# Gamut analysis
# =============================================================================

def gamut_coverage(
    image: np.ndarray,
    target: str = "srgb",
) -> float:
    """
    Compute the fraction of pixels that are within a target gamut.

    The image is assumed to be in sRGB. For the "srgb" target, this
    checks if linear values are in [0, 1]. For "display_p3", the image
    is converted to Display P3 linear and checked similarly.

    Args:
        image: (H, W, 3) float64 image in 0-1 sRGB.
        target: Target gamut, one of "srgb", "display_p3", "bt2020".

    Returns:
        Fraction in [0, 1] of pixels that are in-gamut.
    """
    image = np.asarray(image, dtype=np.float64)
    pixels = image.reshape(-1, 3)
    tolerance = 0.001

    if target == "srgb":
        from quanta_color.spaces import srgb_to_linear
        linear = srgb_to_linear(pixels)
        in_gamut = np.all(linear >= -tolerance, axis=-1) & np.all(linear <= 1.0 + tolerance, axis=-1)

    elif target == "display_p3":
        from quanta_color.spaces import srgb_to_linear, SRGB_TO_XYZ, XYZ_TO_P3
        linear = srgb_to_linear(pixels)
        xyz = (SRGB_TO_XYZ @ linear.T).T
        p3_linear = (XYZ_TO_P3 @ xyz.T).T
        in_gamut = np.all(p3_linear >= -tolerance, axis=-1) & np.all(p3_linear <= 1.0 + tolerance, axis=-1)

    elif target == "bt2020":
        from quanta_color.spaces import srgb_to_linear, SRGB_TO_XYZ, XYZ_TO_BT2020
        linear = srgb_to_linear(pixels)
        xyz = (SRGB_TO_XYZ @ linear.T).T
        bt2020_linear = (XYZ_TO_BT2020 @ xyz.T).T
        in_gamut = np.all(bt2020_linear >= -tolerance, axis=-1) & np.all(bt2020_linear <= 1.0 + tolerance, axis=-1)

    else:
        raise ValueError(f"Unknown target gamut: {target}. Use: srgb, display_p3, bt2020")

    return float(np.mean(in_gamut))


def out_of_gamut_mask(
    image: np.ndarray,
    target: str = "srgb",
) -> np.ndarray:
    """
    Create a boolean mask of out-of-gamut pixels.

    Args:
        image: (H, W, 3) float64 image in 0-1 sRGB.
        target: Target gamut, one of "srgb", "display_p3", "bt2020".

    Returns:
        Boolean (H, W) array. True where pixel is OUT of gamut.
    """
    image = np.asarray(image, dtype=np.float64)
    h, w = image.shape[:2]
    pixels = image.reshape(-1, 3)
    tolerance = 0.001

    if target == "srgb":
        from quanta_color.spaces import srgb_to_linear
        linear = srgb_to_linear(pixels)
        in_gamut = np.all(linear >= -tolerance, axis=-1) & np.all(linear <= 1.0 + tolerance, axis=-1)

    elif target == "display_p3":
        from quanta_color.spaces import srgb_to_linear, SRGB_TO_XYZ, XYZ_TO_P3
        linear = srgb_to_linear(pixels)
        xyz = (SRGB_TO_XYZ @ linear.T).T
        p3_linear = (XYZ_TO_P3 @ xyz.T).T
        in_gamut = np.all(p3_linear >= -tolerance, axis=-1) & np.all(p3_linear <= 1.0 + tolerance, axis=-1)

    elif target == "bt2020":
        from quanta_color.spaces import srgb_to_linear, SRGB_TO_XYZ, XYZ_TO_BT2020
        linear = srgb_to_linear(pixels)
        xyz = (SRGB_TO_XYZ @ linear.T).T
        bt2020_linear = (XYZ_TO_BT2020 @ xyz.T).T
        in_gamut = np.all(bt2020_linear >= -tolerance, axis=-1) & np.all(bt2020_linear <= 1.0 + tolerance, axis=-1)

    else:
        raise ValueError(f"Unknown target gamut: {target}. Use: srgb, display_p3, bt2020")

    return ~in_gamut.reshape(h, w)


# =============================================================================
# Dominant colors
# =============================================================================

def dominant_colors(
    image: np.ndarray,
    n: int = 5,
) -> list[np.ndarray]:
    """
    Extract dominant colors from an image using k-means in Oklab space.

    If scipy is available, uses scipy.cluster.vq. Otherwise falls back
    to a simple iterative k-means implementation.

    Args:
        image: (H, W, 3) float64 image in 0-1 sRGB.
        n: Number of dominant colors to extract (default 5).

    Returns:
        List of n sRGB (3,) arrays representing dominant colors.
    """
    from quanta_color.spaces import srgb_to_oklab, oklab_to_srgb

    image = np.asarray(image, dtype=np.float64)
    pixels = image.reshape(-1, 3)

    # Subsample if image is very large
    max_samples = 10000
    if len(pixels) > max_samples:
        rng = np.random.RandomState(42)
        indices = rng.choice(len(pixels), max_samples, replace=False)
        pixels = pixels[indices]

    # Convert to Oklab
    oklab_pixels = srgb_to_oklab(pixels)

    try:
        from scipy.cluster.vq import kmeans2
        centroids, labels = kmeans2(oklab_pixels, n, minit="points", seed=42)
    except ImportError:
        centroids = _simple_kmeans(oklab_pixels, n, max_iter=30)

    # Convert centroids back to sRGB
    results = []
    for i in range(len(centroids)):
        srgb = np.clip(oklab_to_srgb(centroids[i]), 0.0, 1.0)
        results.append(srgb)

    return results


def _simple_kmeans(
    data: np.ndarray,
    k: int,
    max_iter: int = 30,
) -> np.ndarray:
    """Simple k-means clustering fallback when scipy is not available."""
    rng = np.random.RandomState(42)
    n = len(data)

    # Initialize with random points from the data
    indices = rng.choice(n, min(k, n), replace=False)
    centroids = data[indices].copy()

    for _ in range(max_iter):
        # Assign each point to nearest centroid
        dists = np.linalg.norm(data[:, np.newaxis] - centroids[np.newaxis, :], axis=-1)
        labels = np.argmin(dists, axis=1)

        # Update centroids
        new_centroids = np.empty_like(centroids)
        for i in range(k):
            mask = labels == i
            if np.any(mask):
                new_centroids[i] = data[mask].mean(axis=0)
            else:
                new_centroids[i] = centroids[i]

        # Check convergence
        if np.allclose(centroids, new_centroids, atol=1e-6):
            break
        centroids = new_centroids

    return centroids


# =============================================================================
# WCAG accessibility
# =============================================================================

def wcag_check(fg_rgb: np.ndarray, bg_rgb: np.ndarray) -> dict:
    """
    Check WCAG 2.x contrast ratio between foreground and background colors.

    Args:
        fg_rgb: Foreground sRGB color (0-1), shape (3,).
        bg_rgb: Background sRGB color (0-1), shape (3,).

    Returns:
        dict with keys:
            ratio: float contrast ratio (1.0 to 21.0)
            AA_normal: bool (ratio >= 4.5)
            AA_large: bool (ratio >= 3.0)
            AAA_normal: bool (ratio >= 7.0)
            AAA_large: bool (ratio >= 4.5)
    """
    from quanta_color.spaces import luminance

    fg_lum = float(luminance(np.asarray(fg_rgb, dtype=np.float64)))
    bg_lum = float(luminance(np.asarray(bg_rgb, dtype=np.float64)))

    lighter = max(fg_lum, bg_lum)
    darker = min(fg_lum, bg_lum)
    ratio = (lighter + 0.05) / (darker + 0.05)

    return {
        "ratio": ratio,
        "AA_normal": ratio >= 4.5,
        "AA_large": ratio >= 3.0,
        "AAA_normal": ratio >= 7.0,
        "AAA_large": ratio >= 4.5,
    }


# =============================================================================
# CVD confusability
# =============================================================================

def cvd_problem_pairs(
    palette: list[np.ndarray],
    threshold: float = 3.0,
) -> list[dict]:
    """
    Find color pairs in a palette that become confusable under CVD.

    Tests protanopia, deuteranopia, and tritanopia simulations.
    Two colors are considered confusable if their Oklab distance
    after CVD simulation drops below the threshold.

    Args:
        palette: List of sRGB (3,) arrays in 0-1 range.
        threshold: Oklab distance below which colors are confusable
                   (default 3.0 in CIEDE2000-like scale; internally
                   converted to Oklab units as threshold * 0.01).

    Returns:
        List of dicts, each with:
            i: int index of first color
            j: int index of second color
            deficiency: str type of CVD
            original_distance: float Oklab distance before simulation
            simulated_distance: float Oklab distance after simulation
    """
    from quanta_color.blindness import simulate
    from quanta_color.spaces import srgb_to_oklab
    from quanta_color.difference import delta_e_oklab

    # Threshold is given in approximate delta-E scale; convert to Oklab
    oklab_threshold = threshold * 0.01

    problems = []
    deficiencies = ["protanopia", "deuteranopia", "tritanopia"]

    n = len(palette)
    for deficiency in deficiencies:
        # Simulate all palette colors under this deficiency
        sim_colors = []
        for color in palette:
            sim = simulate(np.asarray(color, dtype=np.float64), deficiency, severity=1.0)
            sim_colors.append(sim)

        # Check all pairs
        for i in range(n):
            for j in range(i + 1, n):
                oklab_i = srgb_to_oklab(palette[i])
                oklab_j = srgb_to_oklab(palette[j])
                original_dist = float(delta_e_oklab(oklab_i, oklab_j))

                sim_oklab_i = srgb_to_oklab(sim_colors[i])
                sim_oklab_j = srgb_to_oklab(sim_colors[j])
                sim_dist = float(delta_e_oklab(sim_oklab_i, sim_oklab_j))

                if sim_dist < oklab_threshold:
                    problems.append({
                        "i": i,
                        "j": j,
                        "deficiency": deficiency,
                        "original_distance": original_dist,
                        "simulated_distance": sim_dist,
                    })

    return problems
