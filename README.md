# Quanta Color

Professional color science library for Python. Tone mapping, color spaces, gamut mapping, HDR, spectral rendering, and more.

## Quick Start

```bash
pip install ".[all]"
quanta-color
```

Launch the GUI, or use the CLI:

```bash
quanta-color info ff6030
quanta-color convert ff6030 --to oklab
quanta-color difference ff0000 00ff00 --metric all
quanta-color harmony ff6030 --scheme triadic
quanta-color spectrum --temp 6500
quanta-color icc --gamma 2.2 --output display.icc
```

## Features

### Color Spaces (15+)
sRGB, Linear RGB, XYZ, xyY, CIELAB, LCH, Oklab, Oklch, JzAzBz, JzCzhz, ICtCp, HSV, Display P3, BT.2020, Adobe RGB, ACEScg

### Tone Mapping (12 operators)
ACES (Narkowicz + Hill), AgX (neutral/punchy/golden), Reinhard (simple + extended), Hable/Uncharted 2, Lottes, Uchimura/Gran Turismo, PBR Neutral (Khronos glTF), BT.2390 EETF, BT.2446 Method A, custom knee function

### HDR Processing
PQ (ST.2084) encode/decode, HLG (BT.2100) encode/decode, BT.2390 EETF tone mapping, BT.2446 HDR-to-SDR

### Color Appearance Models
CIECAM02 forward/inverse (machine-epsilon roundtrip), CAM16, CAM16-UCS uniform color space, hue quadrature

### Color Difference (7 metrics)
CIE76, CIE94 (graphics/textiles), CIEDE2000, CMC(l:c), JzAzBz Delta E, Oklab Delta E, HyAB

### Chromatic Adaptation (9 methods)
Bradford, CAT16, CAT02, Sharp, Von Kries, CMCCAT2000, Fairchild, Bianco-Schettini, XYZ Scaling

### Additional
- **Spectral rendering** - Planck blackbody, CIE 1931 CMFs, daylight illuminants, SPD-to-XYZ integration
- **ICC profiles** - Generate ICC v4 display profiles from primaries + gamma
- **CVD simulation** - Protanopia, deuteranopia, tritanopia, achromatopsia (Brettel et al.)
- **Gamut mapping** - Clip, soft compression, Oklab chroma reduction
- **Color harmony** - Complementary, triadic, tetradic, analogous, split complementary, monochromatic

## GUI

Interactive workbench with 5 tools:

- **Color Inspector** - Pick a color, see it in every space with luminance, wavelength, contrast
- **Palette Generator** - Generate harmonious palettes, copy as CSS
- **Color Difference** - Compare two colors across all metrics with visual grades
- **Tone Mapping** - Preview all 12 operators with curve visualization
- **CVD Simulator** - See how colors appear to color-blind viewers

```bash
quanta-color gui
```

## CLI Commands

| Command | Description |
|---------|-------------|
| `quanta-color` | Launch GUI (default) |
| `quanta-color info <color>` | Show color in all spaces + metadata |
| `quanta-color convert <color> --to <space>` | Convert between color spaces |
| `quanta-color difference <c1> <c2>` | Compute color difference |
| `quanta-color harmony <color> --scheme <type>` | Generate palette |
| `quanta-color adapt <xyz> --from D65 --to D50` | Chromatic adaptation |
| `quanta-color spectrum --temp <K>` | Blackbody spectral data |
| `quanta-color icc --gamma 2.2` | Create ICC profile |
| `quanta-color gui` | Launch GUI workbench |

## Installation

```bash
pip install ".[all]"    # Everything (numpy + scipy + PyQt6)
pip install .           # Core only (numpy)
```

## Python API

```python
import numpy as np
from quanta_color.spaces import srgb_to_oklab, oklab_to_srgb
from quanta_color.tonemap import aces_filmic, pq_eotf
from quanta_color.difference import delta_e_2000
from quanta_color.adaptation import adapt, ILLUMINANTS
from quanta_color.appearance import ciecam02_forward, ViewingConditions

# Color space conversion
oklab = srgb_to_oklab(np.array([0.8, 0.2, 0.1]))

# Tone mapping
hdr = np.array([0.0, 0.18, 1.0, 4.0, 10.0])
sdr = aces_filmic(hdr)

# Color difference
lab1 = np.array([50.0, 25.0, -10.0])
lab2 = np.array([60.0, 20.0, -5.0])
de = delta_e_2000(lab1, lab2)

# Chromatic adaptation
d65 = ILLUMINANTS["D65"]
d50 = ILLUMINANTS["D50"]
adapted = adapt(xyz, d65, d50, method="cat16")

# CIECAM02
vc = ViewingConditions(white_point=d65)
appearance = ciecam02_forward(xyz, vc)
print(f"J={appearance.J:.1f}, C={appearance.C:.1f}, h={appearance.h:.0f}")
```

## Architecture

```
quanta_color/
  spaces.py       15+ color space conversions
  tonemap.py      12 tone mapping operators + PQ/HLG
  appearance.py   CIECAM02, CAM16, CAM16-UCS
  difference.py   7 color difference metrics
  adaptation.py   9 chromatic adaptation methods
  spectral.py     Planck, CIE CMFs, daylight
  icc.py          ICC v4 profile generation
  blindness.py    CVD simulation (4 types)
  gamut.py        Gamut mapping
  harmony.py      6 color harmony schemes
  cli.py          Command-line interface (8 commands)
  gui.py          PyQt6 interactive workbench
```

## License

Copyright (c) 2022-2026 Zain Dana Harper. All rights reserved. See [LICENSE](LICENSE).
