"""
Color Harmony Generation

Generate harmonious color palettes from a base color using
classical color theory relationships on the hue wheel.

Schemes:
    complementary       - Opposite hue (180 degrees)
    split_complementary - Two colors flanking the complement
    triadic             - Three equally spaced (120 degrees)
    tetradic            - Four equally spaced (90 degrees)
    analogous           - Adjacent hues (30 degrees apart)
    monochromatic       - Same hue, varied lightness/chroma
"""

import numpy as np


def _rgb_to_oklch(rgb: np.ndarray) -> np.ndarray:
    """Quick sRGB -> Oklch for harmony calculations."""
    from quanta_color.spaces import oklab_to_oklch, srgb_to_oklab

    return oklab_to_oklch(srgb_to_oklab(rgb))


def _oklch_to_rgb(oklch: np.ndarray) -> np.ndarray:
    """Quick Oklch -> sRGB for harmony calculations."""
    from quanta_color.spaces import oklab_to_srgb, oklch_to_oklab

    return oklab_to_srgb(oklch_to_oklab(oklch))


def complementary(base_rgb: np.ndarray) -> list[np.ndarray]:
    """Generate complementary color (opposite on hue wheel)."""
    lch = _rgb_to_oklch(np.asarray(base_rgb))
    comp = lch.copy()
    comp[2] = (comp[2] + 180) % 360
    return [base_rgb, np.clip(_oklch_to_rgb(comp), 0, 1)]


def split_complementary(base_rgb: np.ndarray, angle: float = 30.0) -> list[np.ndarray]:
    """Two colors flanking the complement."""
    lch = _rgb_to_oklch(np.asarray(base_rgb))
    c1, c2 = lch.copy(), lch.copy()
    c1[2] = (lch[2] + 180 - angle) % 360
    c2[2] = (lch[2] + 180 + angle) % 360
    return [base_rgb, np.clip(_oklch_to_rgb(c1), 0, 1), np.clip(_oklch_to_rgb(c2), 0, 1)]


def triadic(base_rgb: np.ndarray) -> list[np.ndarray]:
    """Three equally spaced colors (120 degrees apart)."""
    lch = _rgb_to_oklch(np.asarray(base_rgb))
    results = [base_rgb]
    for offset in [120, 240]:
        c = lch.copy()
        c[2] = (c[2] + offset) % 360
        results.append(np.clip(_oklch_to_rgb(c), 0, 1))
    return results


def tetradic(base_rgb: np.ndarray) -> list[np.ndarray]:
    """Four equally spaced colors (90 degrees apart)."""
    lch = _rgb_to_oklch(np.asarray(base_rgb))
    results = [base_rgb]
    for offset in [90, 180, 270]:
        c = lch.copy()
        c[2] = (c[2] + offset) % 360
        results.append(np.clip(_oklch_to_rgb(c), 0, 1))
    return results


def analogous(base_rgb: np.ndarray, angle: float = 30.0, count: int = 5) -> list[np.ndarray]:
    """Adjacent hues, evenly spread around the base."""
    lch = _rgb_to_oklch(np.asarray(base_rgb))
    results = []
    start = -(count // 2) * angle
    for i in range(count):
        c = lch.copy()
        c[2] = (c[2] + start + i * angle) % 360
        results.append(np.clip(_oklch_to_rgb(c), 0, 1))
    return results


def monochromatic(base_rgb: np.ndarray, count: int = 5) -> list[np.ndarray]:
    """Same hue, varied lightness."""
    lch = _rgb_to_oklch(np.asarray(base_rgb))
    results = []
    for i in range(count):
        c = lch.copy()
        c[0] = 0.15 + (0.85 - 0.15) * i / (count - 1)  # L from 0.15 to 0.85
        c[1] = lch[1] * (0.5 + 0.5 * i / (count - 1))  # Vary chroma slightly
        results.append(np.clip(_oklch_to_rgb(c), 0, 1))
    return results


SCHEMES = {
    "complementary": complementary,
    "split_complementary": split_complementary,
    "triadic": triadic,
    "tetradic": tetradic,
    "analogous": analogous,
    "monochromatic": monochromatic,
}


def generate(base_rgb: np.ndarray, scheme: str = "complementary", **kwargs) -> list[np.ndarray]:
    """Generate a color harmony palette."""
    fn = SCHEMES.get(scheme.lower())
    if fn is None:
        raise ValueError(f"Unknown scheme: {scheme}. Available: {list(SCHEMES.keys())}")
    return fn(base_rgb, **kwargs)
