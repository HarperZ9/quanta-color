# Quanta Color — Usage Guide

Quanta Color is a Python color-science library with a command-line interface
(`quanta-color`) and an optional PyQt6 GUI. This guide covers installation, the
CLI commands, the Python API, and worked examples with their actual output.

All command and API examples below were run against the package in this
repository. Output blocks reflect real runs unless explicitly marked
*illustrative*.

## Install

```bash
# Core library + CLI (numpy only)
pip install .

# Everything, including the GUI (numpy + scipy + Pillow + PyQt6)
pip install ".[all]"

# Just the GUI extras
pip install ".[gui]"
```

This installs the `quanta-color` console script (entry point
`quanta_color.cli:main`). Requires Python 3.10+.

Without installing, you can run the CLI directly from a checkout:

```bash
python -m quanta_color.cli <command> ...
```

## CLI

```text
quanta-color [--version] <command> [options]
```

| Command | Description |
|---------|-------------|
| `quanta-color` | Launch the GUI (default when no command is given) |
| `quanta-color gui` | Launch the GUI workbench |
| `quanta-color info <color>` | Show a color across all spaces plus metadata |
| `quanta-color convert <color> --to <space>` | Convert between color spaces |
| `quanta-color difference <c1> <c2> [--metric <m>]` | Color difference (Delta E) |
| `quanta-color harmony <color> [--scheme <s>]` | Generate a harmony palette |
| `quanta-color adapt <xyz> [--from <ill>] [--to <ill>] [--method <m>]` | Chromatic adaptation |
| `quanta-color spectrum [--temp <K>] [--output <csv>]` | Blackbody spectral data |
| `quanta-color icc [--gamma <g>] [--name <n>] [--output <icc>]` | Create an ICC v4 profile |

Color arguments accept hex (`ff6030` or `#ff6030`), comma-separated floats
(`0.8,0.2,0.1`), or 0-255 triples (`200,50,25`). For `adapt`, the color
argument is comma-separated XYZ values.

Option vocabularies (from the source):

- `convert --to` / `--from`: `srgb`, `xyz`, `lab`, `oklab`, `jzazbz`, `hsv`, `p3`, `bt2020`, `acescg`
- `difference --metric`: `cie76`, `cie94`, `ciede2000`, `cmc`, `hyab`, `all` (default `ciede2000`)
- `harmony --scheme`: `complementary`, `split_complementary`, `triadic`, `tetradic`, `analogous`, `monochromatic` (default `triadic`)
- `adapt --from` / `--to` (illuminants): `D50`, `D55`, `D65`, `D75`, `A`, `F2`, `F11`
- `adapt --method`: `bradford` (default) and the other methods exposed by `quanta_color.adaptation`

## Worked examples (CLI)

### 1. Inspect a color

```bash
quanta-color info ff6030
```

```text
Color: #ff6030

  sRGB:      (1.0000, 0.3765, 0.1882)
  sRGB 8-bit: (255, 96, 48)
  XYZ:       (0.4596, 0.2985, 0.0614)
  xyY:       (0.5609, 0.3642, 0.2985)
  Lab (D65): (61.52, 58.31, 56.98)
  Oklab:     (0.6128, 0.8175, 0.0611)
  Oklch:     (0.6128, 0.8198, 4.3)
  HSV:       (13.9, 0.812, 1.000)
  Luminance: 0.2984
  Dominant wavelength: 775 nm
  Contrast vs white: 3.01:1
  Contrast vs black: 6.97:1
```

### 2. Convert sRGB to Oklab

```bash
quanta-color convert ff6030 --to oklab
```

```text
srgb (1.0000, 0.3765, 0.1882)  #ff6030
  -> oklab (0.6128, 0.8175, 0.0611)
```

### 3. Compare two colors across all Delta E metrics

```bash
quanta-color difference ff0000 00ff00 --metric all
```

```text
Color 1: (1.0000, 0.0000, 0.0000)  #ff0000
Color 2: (0.0000, 1.0000, 0.0000)  #00ff00

  CIE76         170.1404
  CIE94         74.8681
  CIEDE2000     87.6784
  CMC(2:1)      104.2193
  HyAB          201.1010
```

### 4. Generate a triadic palette

```bash
quanta-color harmony ff6030 --scheme triadic
```

```text
Base: (1.0000, 0.3765, 0.1882)  #ff6030
Scheme: triadic

  1. #ff6030  (1.000, 0.376, 0.188)
  2. #588a00  (0.349, 0.543, 0.000)
  3. #fe51ff  (0.999, 0.320, 1.000)
```

### 5. Chromatic adaptation (D65 -> D50)

```bash
quanta-color adapt 0.95047,1.0,1.08883 --from D65 --to D50 --method bradford
```

```text
XYZ (D65): (0.9505, 1.0000, 1.0888)
XYZ (D50):  (0.9642, 1.0000, 0.8252)
Method: bradford
```

## Python API

```python
import numpy as np
from quanta_color.spaces import srgb_to_oklab, oklab_to_srgb
from quanta_color.tonemap import aces_filmic, pq_eotf
from quanta_color.difference import delta_e_2000
from quanta_color.adaptation import adapt, ILLUMINANTS
from quanta_color.appearance import ciecam02_forward, ViewingConditions

# Color-space conversion
oklab = srgb_to_oklab(np.array([0.8, 0.2, 0.1]))
# -> [0.4606 0.8338 0.0251]

# Tone mapping (HDR scene-linear -> display)
hdr = np.array([0.0, 0.18, 1.0, 4.0, 10.0])
sdr = aces_filmic(hdr)
# -> [0.     0.2669 0.8038 0.9734 1.    ]

# Color difference in CIELAB
lab1 = np.array([50.0, 25.0, -10.0])
lab2 = np.array([60.0, 20.0, -5.0])
de = delta_e_2000(lab1, lab2)
# -> 10.1779

# Chromatic adaptation (XYZ from D65 to D50)
d65 = ILLUMINANTS["D65"]
d50 = ILLUMINANTS["D50"]
xyz = np.array([0.4596, 0.2985, 0.0614])
adapted = adapt(xyz, d65, d50, method="cat16")

# CIECAM02 appearance correlates
vc = ViewingConditions(white_point=d65)
appearance = ciecam02_forward(xyz, vc)
print(f"J={appearance.J:.1f}, C={appearance.C:.1f}, h={appearance.h:.0f}")
# -> J=15.4, C=29.0, h=38
```

`ILLUMINANTS` exposes the keys `D50`, `D55`, `D65`, `D75`, `A`, `F2`, `F11`.
`ViewingConditions` is a dataclass with fields `white_point` (required),
`L_A=64.0`, `Y_b=20.0`, and `surround="average"`. `ciecam02_forward` returns a
`CIECAM02Color` with correlates `J`, `C`, `h`, `Q`, `M`, `s`, `H`.

### Generate an ICC display profile

```python
from quanta_color.icc import create_display_profile

profile = create_display_profile(gamma=2.2, name="My Display")
profile.save("display.icc")
print(profile.size)  # bytes written
```

`create_display_profile` defaults to sRGB/Rec.709 primaries and the D65 white
point; override `red_xy`, `green_xy`, `blue_xy`, and `white_xy` for other gamuts.

## GUI

```bash
quanta-color gui
```

The GUI requires the `gui` (or `all`) extra so that PyQt6 is available. It
provides a Dashboard, Color Inspector, Palette Studio, LUT Workshop, and an
Image Analyzer (see `quanta_color/gui/pages/`).

## See also

- `README.md` — project overview and feature list.
- `examples/` — a runnable best-effort demo of the CLI and Python API.
