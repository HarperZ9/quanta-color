"""
Color Naming

Maps any color to the nearest named CSS color, basic color category,
or a human-readable description like "dark muted red".

Functions:
    nearest_css_name    - Find closest CSS named color (distance in Oklab)
    nearest_basic_name  - Classify into one of 11 basic color names
    color_description   - "dark muted red" style natural language description
    all_css_colors      - Full CSS named colors dictionary
"""

import numpy as np
from typing import Tuple

# =============================================================================
# CSS Named Colors — all 148 (name -> (R, G, B) in 0-255)
# =============================================================================

CSS_COLORS: dict[str, tuple[int, int, int]] = {
    "aliceblue": (240, 248, 255),
    "antiquewhite": (250, 235, 215),
    "aqua": (0, 255, 255),
    "aquamarine": (127, 255, 212),
    "azure": (240, 255, 255),
    "beige": (245, 245, 220),
    "bisque": (255, 228, 196),
    "black": (0, 0, 0),
    "blanchedalmond": (255, 235, 205),
    "blue": (0, 0, 255),
    "blueviolet": (138, 43, 226),
    "brown": (165, 42, 42),
    "burlywood": (222, 184, 135),
    "cadetblue": (95, 158, 160),
    "chartreuse": (127, 255, 0),
    "chocolate": (210, 105, 30),
    "coral": (255, 127, 80),
    "cornflowerblue": (100, 149, 237),
    "cornsilk": (255, 248, 220),
    "crimson": (220, 20, 60),
    "cyan": (0, 255, 255),
    "darkblue": (0, 0, 139),
    "darkcyan": (0, 139, 139),
    "darkgoldenrod": (184, 134, 11),
    "darkgray": (169, 169, 169),
    "darkgreen": (0, 100, 0),
    "darkgrey": (169, 169, 169),
    "darkkhaki": (189, 183, 107),
    "darkmagenta": (139, 0, 139),
    "darkolivegreen": (85, 107, 47),
    "darkorange": (255, 140, 0),
    "darkorchid": (153, 50, 204),
    "darkred": (139, 0, 0),
    "darksalmon": (233, 150, 122),
    "darkseagreen": (143, 188, 143),
    "darkslateblue": (72, 61, 139),
    "darkslategray": (47, 79, 79),
    "darkslategrey": (47, 79, 79),
    "darkturquoise": (0, 206, 209),
    "darkviolet": (148, 0, 211),
    "deeppink": (255, 20, 147),
    "deepskyblue": (0, 191, 255),
    "dimgray": (105, 105, 105),
    "dimgrey": (105, 105, 105),
    "dodgerblue": (30, 144, 255),
    "firebrick": (178, 34, 34),
    "floralwhite": (255, 250, 240),
    "forestgreen": (34, 139, 34),
    "fuchsia": (255, 0, 255),
    "gainsboro": (220, 220, 220),
    "ghostwhite": (248, 248, 255),
    "gold": (255, 215, 0),
    "goldenrod": (218, 165, 32),
    "gray": (128, 128, 128),
    "green": (0, 128, 0),
    "grey": (128, 128, 128),
    "greenyellow": (173, 255, 47),
    "honeydew": (240, 255, 240),
    "hotpink": (255, 105, 180),
    "indianred": (205, 92, 92),
    "indigo": (75, 0, 130),
    "ivory": (255, 255, 240),
    "khaki": (240, 230, 140),
    "lavender": (230, 230, 250),
    "lavenderblush": (255, 240, 245),
    "lawngreen": (124, 252, 0),
    "lemonchiffon": (255, 250, 205),
    "lightblue": (173, 216, 230),
    "lightcoral": (240, 128, 128),
    "lightcyan": (224, 255, 255),
    "lightgoldenrodyellow": (250, 250, 210),
    "lightgray": (211, 211, 211),
    "lightgreen": (144, 238, 144),
    "lightgrey": (211, 211, 211),
    "lightpink": (255, 182, 193),
    "lightsalmon": (255, 160, 122),
    "lightseagreen": (32, 178, 170),
    "lightskyblue": (135, 206, 250),
    "lightslategray": (119, 136, 153),
    "lightslategrey": (119, 136, 153),
    "lightsteelblue": (176, 196, 222),
    "lightyellow": (255, 255, 224),
    "lime": (0, 255, 0),
    "limegreen": (50, 205, 50),
    "linen": (250, 240, 230),
    "magenta": (255, 0, 255),
    "maroon": (128, 0, 0),
    "mediumaquamarine": (102, 205, 170),
    "mediumblue": (0, 0, 205),
    "mediumorchid": (186, 85, 211),
    "mediumpurple": (147, 112, 219),
    "mediumseagreen": (60, 179, 113),
    "mediumslateblue": (123, 104, 238),
    "mediumspringgreen": (0, 250, 154),
    "mediumturquoise": (72, 209, 204),
    "mediumvioletred": (199, 21, 133),
    "midnightblue": (25, 25, 112),
    "mintcream": (245, 255, 250),
    "mistyrose": (255, 228, 225),
    "moccasin": (255, 228, 181),
    "navajowhite": (255, 222, 173),
    "navy": (0, 0, 128),
    "oldlace": (253, 245, 230),
    "olive": (128, 128, 0),
    "olivedrab": (107, 142, 35),
    "orange": (255, 165, 0),
    "orangered": (255, 69, 0),
    "orchid": (218, 112, 214),
    "palegoldenrod": (238, 232, 170),
    "palegreen": (152, 251, 152),
    "paleturquoise": (175, 238, 238),
    "palevioletred": (219, 112, 147),
    "papayawhip": (255, 239, 213),
    "peachpuff": (255, 218, 185),
    "peru": (205, 133, 63),
    "pink": (255, 192, 203),
    "plum": (221, 160, 221),
    "powderblue": (176, 224, 230),
    "purple": (128, 0, 128),
    "rebeccapurple": (102, 51, 153),
    "red": (255, 0, 0),
    "rosybrown": (188, 143, 143),
    "royalblue": (65, 105, 225),
    "saddlebrown": (139, 69, 19),
    "salmon": (250, 128, 114),
    "sandybrown": (244, 164, 96),
    "seagreen": (46, 139, 87),
    "seashell": (255, 245, 238),
    "sienna": (160, 82, 45),
    "silver": (192, 192, 192),
    "skyblue": (135, 206, 235),
    "slateblue": (106, 90, 205),
    "slategray": (112, 128, 144),
    "slategrey": (112, 128, 144),
    "snow": (255, 250, 250),
    "springgreen": (0, 255, 127),
    "steelblue": (70, 130, 180),
    "tan": (210, 180, 140),
    "teal": (0, 128, 128),
    "thistle": (216, 191, 216),
    "tomato": (255, 99, 71),
    "turquoise": (64, 224, 208),
    "violet": (238, 130, 238),
    "wheat": (245, 222, 179),
    "white": (255, 255, 255),
    "whitesmoke": (245, 245, 245),
    "yellow": (255, 255, 0),
    "yellowgreen": (154, 205, 50),
}

# Basic color categories with representative sRGB hue ranges in Oklch
_BASIC_COLORS: dict[str, tuple[int, int, int]] = {
    "red": (255, 0, 0),
    "orange": (255, 165, 0),
    "yellow": (255, 255, 0),
    "green": (0, 128, 0),
    "blue": (0, 0, 255),
    "purple": (128, 0, 128),
    "pink": (255, 192, 203),
    "brown": (139, 69, 19),
    "white": (255, 255, 255),
    "gray": (128, 128, 128),
    "black": (0, 0, 0),
}


def _rgb_to_oklab(rgb_255: tuple[int, int, int]) -> np.ndarray:
    """Convert 0-255 RGB to Oklab. Internal helper."""
    from quanta_color.spaces import srgb_to_oklab
    srgb = np.array(rgb_255, dtype=np.float64) / 255.0
    return srgb_to_oklab(srgb)


def _oklab_distance(a: np.ndarray, b: np.ndarray) -> float:
    """Euclidean distance in Oklab space."""
    d = a - b
    return float(np.sqrt(np.sum(d * d)))


def nearest_css_name(rgb: np.ndarray) -> tuple[str, float]:
    """
    Find the nearest CSS named color to the given sRGB value.

    Args:
        rgb: sRGB color in 0-1 range, shape (3,)

    Returns:
        (name, distance) where distance is Euclidean in Oklab space.
    """
    from quanta_color.spaces import srgb_to_oklab
    rgb = np.asarray(rgb, dtype=np.float64)
    target_oklab = srgb_to_oklab(rgb)

    best_name = ""
    best_dist = float("inf")

    for name, rgb_255 in CSS_COLORS.items():
        css_oklab = _rgb_to_oklab(rgb_255)
        dist = _oklab_distance(target_oklab, css_oklab)
        if dist < best_dist:
            best_dist = dist
            best_name = name

    return best_name, best_dist


def nearest_basic_name(rgb: np.ndarray) -> str:
    """
    Classify a color into one of 11 basic color names:
    red, orange, yellow, green, blue, purple, pink, brown,
    white, gray, black.

    Args:
        rgb: sRGB color in 0-1 range, shape (3,)

    Returns:
        Basic color name string.
    """
    from quanta_color.spaces import srgb_to_oklab
    rgb = np.asarray(rgb, dtype=np.float64)
    target_oklab = srgb_to_oklab(rgb)

    best_name = ""
    best_dist = float("inf")

    for name, rgb_255 in _BASIC_COLORS.items():
        basic_oklab = _rgb_to_oklab(rgb_255)
        dist = _oklab_distance(target_oklab, basic_oklab)
        if dist < best_dist:
            best_dist = dist
            best_name = name

    return best_name


def color_description(rgb: np.ndarray) -> str:
    """
    Generate a human-readable color description like "dark muted red"
    using lightness, saturation (chroma), and hue analysis in Oklch space.

    Args:
        rgb: sRGB color in 0-1 range, shape (3,)

    Returns:
        Description string, e.g., "dark muted red", "light vivid blue".
    """
    from quanta_color.spaces import srgb_to_oklab, oklab_to_oklch
    rgb = np.asarray(rgb, dtype=np.float64)
    oklab = srgb_to_oklab(rgb)
    oklch = oklab_to_oklch(oklab)
    L, C, h = float(oklch[0]), float(oklch[1]), float(oklch[2])

    # Achromatic check — Oklab can produce small non-zero chroma
    # for perfectly neutral colors due to matrix precision
    if C < 0.035:
        if L < 0.15:
            return "black"
        elif L < 0.35:
            return "very dark gray"
        elif L < 0.65:
            return "gray"
        elif L < 0.85:
            return "light gray"
        else:
            return "white"

    # Lightness descriptor
    if L < 0.25:
        lightness = "very dark"
    elif L < 0.40:
        lightness = "dark"
    elif L < 0.60:
        lightness = ""
    elif L < 0.75:
        lightness = "light"
    else:
        lightness = "very light"

    # Saturation descriptor (chroma in Oklch)
    if C < 0.04:
        saturation = "muted"
    elif C < 0.10:
        saturation = ""
    elif C < 0.18:
        saturation = "vivid"
    else:
        saturation = "intense"

    # Hue name from angle (Oklch hue wheel)
    if h < 20 or h >= 350:
        hue_name = "red"
    elif h < 45:
        hue_name = "orange"
    elif h < 80:
        hue_name = "yellow"
    elif h < 105:
        hue_name = "yellow-green"
    elif h < 150:
        hue_name = "green"
    elif h < 180:
        hue_name = "teal"
    elif h < 220:
        hue_name = "cyan"
    elif h < 260:
        hue_name = "blue"
    elif h < 300:
        hue_name = "purple"
    elif h < 330:
        hue_name = "magenta"
    else:
        hue_name = "pink"

    parts = [p for p in [lightness, saturation, hue_name] if p]
    return " ".join(parts)


def all_css_colors() -> dict[str, tuple[int, int, int]]:
    """
    Return the full CSS named colors dictionary.

    Returns:
        dict mapping color name -> (R, G, B) in 0-255 range.
    """
    return dict(CSS_COLORS)
