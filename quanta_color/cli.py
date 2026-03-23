"""
Quanta Color CLI

Command-line interface for color science operations.

Usage:
    quanta-color convert ff8030 --to oklab
    quanta-color difference ff0000 00ff00 --metric ciede2000
    quanta-color harmony ff6600 --scheme triadic
    quanta-color adapt 0.95,1.0,1.09 --from D65 --to D50
    quanta-color info ff8030
    quanta-color spectrum --temp 6500
    quanta-color icc --gamma 2.2 --name "My Display" --output display.icc
"""

import argparse
import sys
import numpy as np

__version__ = "1.0.0"


def _parse_color(s: str) -> np.ndarray:
    """Parse color from hex, rgb(), or comma-separated values."""
    s = s.strip()

    # Hex: ff8030 or #ff8030
    if s.startswith("#"):
        s = s[1:]
    if len(s) == 6 and all(c in "0123456789abcdefABCDEF" for c in s):
        r = int(s[0:2], 16) / 255.0
        g = int(s[2:4], 16) / 255.0
        b = int(s[4:6], 16) / 255.0
        return np.array([r, g, b])

    # Comma-separated: 0.8,0.2,0.1 or 200,50,25
    if "," in s:
        parts = [float(x.strip()) for x in s.split(",")]
        if len(parts) == 3:
            arr = np.array(parts)
            if np.all(arr > 1.0):
                arr /= 255.0  # Assume 0-255 range
            return arr

    raise ValueError(f"Cannot parse color: {s}")


def _format_color(arr: np.ndarray, space: str = "srgb") -> str:
    """Format a color array for display."""
    if space in ("srgb", "p3", "bt2020", "adobe", "acescg"):
        r, g, b = arr
        ri, gi, bi = int(r * 255), int(g * 255), int(b * 255)
        return f"({r:.4f}, {g:.4f}, {b:.4f})  #{ri:02x}{gi:02x}{bi:02x}"
    return f"({', '.join(f'{v:.4f}' for v in arr)})"


def cmd_convert(args):
    """Convert a color between spaces."""
    from quanta_color import spaces

    color = _parse_color(args.color)
    src = args.source.lower()
    dst = args.to.lower()

    # Convert source to XYZ first
    if src == "srgb":
        xyz = spaces.srgb_to_xyz(color)
    elif src == "xyz":
        xyz = color
    elif src == "lab":
        xyz = spaces.lab_to_xyz(color)
    elif src == "oklab":
        xyz = spaces.srgb_to_xyz(spaces.oklab_to_srgb(color))
    else:
        xyz = spaces.srgb_to_xyz(color)  # Default: treat as sRGB

    # Convert XYZ to destination
    converters = {
        "srgb": lambda x: spaces.xyz_to_srgb(x),
        "xyz": lambda x: x,
        "lab": lambda x: spaces.xyz_to_lab(x),
        "oklab": lambda x: spaces.srgb_to_oklab(spaces.xyz_to_srgb(x)),
        "jzazbz": lambda x: spaces.xyz_to_jzazbz(x),
        "hsv": lambda x: spaces.rgb_to_hsv(spaces.xyz_to_srgb(x)),
        "p3": lambda x: spaces.srgb_to_p3(spaces.xyz_to_srgb(x)),
        "bt2020": lambda x: spaces.srgb_to_bt2020(spaces.xyz_to_srgb(x)),
        "acescg": lambda x: spaces.srgb_to_acescg(spaces.xyz_to_srgb(x)),
    }

    if dst not in converters:
        print(f"Unknown space: {dst}. Available: {', '.join(converters.keys())}")
        return 1

    result = converters[dst](xyz)
    print(f"{src} {_format_color(color, src)}")
    print(f"  -> {dst} {_format_color(result, dst)}")
    return 0


def cmd_difference(args):
    """Compute color difference."""
    from quanta_color import spaces, difference

    c1 = _parse_color(args.color1)
    c2 = _parse_color(args.color2)

    lab1 = spaces.xyz_to_lab(spaces.srgb_to_xyz(c1))
    lab2 = spaces.xyz_to_lab(spaces.srgb_to_xyz(c2))

    if args.metric == "all":
        results = difference.compare_all(lab1, lab2)
        print(f"Color 1: {_format_color(c1)}")
        print(f"Color 2: {_format_color(c2)}")
        print()
        for name, value in results.items():
            print(f"  {name:12s}  {value:.4f}")
    else:
        metrics = {
            "cie76": difference.delta_e_76,
            "cie94": difference.delta_e_94,
            "ciede2000": difference.delta_e_2000,
            "cmc": difference.delta_e_cmc,
            "hyab": difference.delta_e_hyab,
        }
        fn = metrics.get(args.metric.lower())
        if not fn:
            print(f"Unknown metric: {args.metric}. Available: {', '.join(metrics.keys())}, all")
            return 1
        de = fn(lab1, lab2)
        print(f"Delta E ({args.metric}): {float(de):.4f}")
    return 0


def cmd_harmony(args):
    """Generate color harmony palette."""
    from quanta_color.harmony import generate, SCHEMES

    color = _parse_color(args.color)
    palette = generate(color, args.scheme)

    print(f"Base: {_format_color(color)}")
    print(f"Scheme: {args.scheme}")
    print()
    for i, c in enumerate(palette):
        ri, gi, bi = int(c[0]*255), int(c[1]*255), int(c[2]*255)
        print(f"  {i+1}. #{ri:02x}{gi:02x}{bi:02x}  ({c[0]:.3f}, {c[1]:.3f}, {c[2]:.3f})")
    return 0


def cmd_adapt(args):
    """Chromatic adaptation."""
    from quanta_color.adaptation import adapt, ILLUMINANTS, MATRICES

    color = np.array([float(x) for x in args.color.split(",")])

    src_wp = ILLUMINANTS.get(args.source.upper())
    dst_wp = ILLUMINANTS.get(args.dest.upper())
    if src_wp is None:
        print(f"Unknown illuminant: {args.source}. Available: {', '.join(ILLUMINANTS.keys())}")
        return 1
    if dst_wp is None:
        print(f"Unknown illuminant: {args.dest}. Available: {', '.join(ILLUMINANTS.keys())}")
        return 1

    result = adapt(color, src_wp, dst_wp, args.method)
    print(f"XYZ ({args.source}): ({', '.join(f'{v:.4f}' for v in color)})")
    print(f"XYZ ({args.dest}):  ({', '.join(f'{v:.4f}' for v in result)})")
    print(f"Method: {args.method}")
    return 0


def cmd_info(args):
    """Show comprehensive color info."""
    from quanta_color import spaces, difference, adaptation

    color = _parse_color(args.color)
    xyz = spaces.srgb_to_xyz(color)
    lab = spaces.xyz_to_lab(xyz, spaces.D65)
    oklab = spaces.srgb_to_oklab(color)
    oklch = spaces.oklab_to_oklch(oklab)
    hsv = spaces.rgb_to_hsv(color)
    lum = spaces.luminance(color)
    xyY = spaces.xyz_to_xyY(xyz)

    ri, gi, bi = int(color[0]*255), int(color[1]*255), int(color[2]*255)

    print(f"Color: #{ri:02x}{gi:02x}{bi:02x}")
    print()
    print(f"  sRGB:      ({color[0]:.4f}, {color[1]:.4f}, {color[2]:.4f})")
    print(f"  sRGB 8-bit: ({ri}, {gi}, {bi})")
    print(f"  XYZ:       ({xyz[0]:.4f}, {xyz[1]:.4f}, {xyz[2]:.4f})")
    print(f"  xyY:       ({xyY[0]:.4f}, {xyY[1]:.4f}, {xyY[2]:.4f})")
    print(f"  Lab (D65): ({lab[0]:.2f}, {lab[1]:.2f}, {lab[2]:.2f})")
    print(f"  Oklab:     ({oklab[0]:.4f}, {oklab[1]:.4f}, {oklab[2]:.4f})")
    print(f"  Oklch:     ({oklch[0]:.4f}, {oklch[1]:.4f}, {oklch[2]:.1f})")
    print(f"  HSV:       ({hsv[0]:.1f}, {hsv[1]:.3f}, {hsv[2]:.3f})")
    print(f"  Luminance: {lum:.4f}")

    # Dominant wavelength
    from quanta_color.spectral import dominant_wavelength
    dom = dominant_wavelength(xyY[0], xyY[1])
    print(f"  Dominant wavelength: {dom:.0f} nm")

    # WCAG contrast vs white and black
    from quanta_color.difference import contrast_ratio
    cr_white = contrast_ratio(lum, 1.0)
    cr_black = contrast_ratio(lum, 0.0)
    print(f"  Contrast vs white: {cr_white:.2f}:1")
    print(f"  Contrast vs black: {cr_black:.2f}:1")

    return 0


def cmd_spectrum(args):
    """Generate spectral data."""
    from quanta_color.spectral import planck_radiation, CMF_WAVELENGTHS, blackbody_chromaticity

    T = args.temp
    wavelengths = CMF_WAVELENGTHS
    spd = planck_radiation(wavelengths, T)

    x, y = blackbody_chromaticity(T)
    print(f"Blackbody at {T}K:")
    print(f"  Chromaticity: ({x:.4f}, {y:.4f})")
    print(f"  Peak wavelength: {2897771.25 / T:.0f} nm (Wien's law)")
    print()

    if args.output:
        with open(args.output, "w") as f:
            f.write("wavelength_nm,spectral_radiance\n")
            for w, s in zip(wavelengths, spd):
                f.write(f"{w:.0f},{s:.6e}\n")
        print(f"  Saved to {args.output}")
    else:
        print(f"  {'Wavelength':>12s}  {'Radiance':>14s}")
        for w, s in zip(wavelengths[::4], spd[::4]):  # Every 20nm
            print(f"  {w:>10.0f} nm  {s:>14.4e}")

    return 0


def cmd_icc(args):
    """Create an ICC profile."""
    from quanta_color.icc import create_display_profile

    profile = create_display_profile(
        gamma=args.gamma,
        name=args.name,
    )
    profile.save(args.output)
    print(f"ICC profile created: {args.output} ({profile.size} bytes)")
    print(f"  Gamma: {args.gamma}")
    print(f"  Name: {args.name}")
    return 0


def main():
    parser = argparse.ArgumentParser(
        prog="quanta-color",
        description="Quanta Color — Professional Color Science CLI",
    )
    parser.add_argument("--version", action="version", version=f"Quanta Color v{__version__}")

    sub = parser.add_subparsers(dest="command", help="Available commands")

    # convert
    p = sub.add_parser("convert", help="Convert color between spaces")
    p.add_argument("color", help="Color (hex, rgb, or comma-separated)")
    p.add_argument("--from", dest="source", default="srgb", help="Source space (default: srgb)")
    p.add_argument("--to", required=True, help="Target space (srgb, xyz, lab, oklab, jzazbz, hsv, p3, bt2020, acescg)")

    # difference
    p = sub.add_parser("difference", help="Compute color difference")
    p.add_argument("color1", help="First color")
    p.add_argument("color2", help="Second color")
    p.add_argument("--metric", default="ciede2000", help="Metric (cie76, cie94, ciede2000, cmc, hyab, all)")

    # harmony
    p = sub.add_parser("harmony", help="Generate color harmony palette")
    p.add_argument("color", help="Base color")
    p.add_argument("--scheme", default="triadic", help="Scheme (complementary, split_complementary, triadic, tetradic, analogous, monochromatic)")

    # adapt
    p = sub.add_parser("adapt", help="Chromatic adaptation")
    p.add_argument("color", help="XYZ values (comma-separated)")
    p.add_argument("--from", dest="source", default="D65", help="Source illuminant")
    p.add_argument("--to", dest="dest", default="D50", help="Target illuminant")
    p.add_argument("--method", default="bradford", help="Adaptation method")

    # info
    p = sub.add_parser("info", help="Show comprehensive color info")
    p.add_argument("color", help="Color (hex or rgb)")

    # spectrum
    p = sub.add_parser("spectrum", help="Generate spectral data")
    p.add_argument("--temp", type=float, default=6500, help="Temperature in Kelvin")
    p.add_argument("--output", "-o", help="Output CSV file")

    # icc
    p = sub.add_parser("icc", help="Create ICC profile")
    p.add_argument("--gamma", type=float, default=2.2, help="Display gamma")
    p.add_argument("--name", default="Quanta Color Display Profile", help="Profile name")
    p.add_argument("--output", "-o", default="display.icc", help="Output file")

    # gui
    sub.add_parser("gui", help="Launch interactive GUI workbench")

    args = parser.parse_args()

    if not args.command:
        # Default: launch GUI
        try:
            from quanta_color.gui import launch
            return launch()
        except ImportError:
            parser.print_help()
            return 0

    if args.command == "gui":
        from quanta_color.gui import launch
        return launch()

    commands = {
        "convert": cmd_convert,
        "difference": cmd_difference,
        "harmony": cmd_harmony,
        "adapt": cmd_adapt,
        "info": cmd_info,
        "spectrum": cmd_spectrum,
        "icc": cmd_icc,
    }

    return commands[args.command](args)


if __name__ == "__main__":
    sys.exit(main() or 0)
