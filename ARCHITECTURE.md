# Architecture

Build Color is a single-package, dependency-light color-science library. The only
required runtime dependency is `numpy`; SciPy, Pillow, and PyQt6 are optional and gate
specific features. The public API is a flat set of focused modules under `build_color/`,
each owning one well-bounded area of color science, plus a thin CLI and an optional GUI.

## Layers

```
build_color/
  spaces.py         Color space conversions (sRGB, linear, XYZ, Lab/Luv, Oklab, JzAzBz, ICtCp, Display P3, Rec.2020, AdobeRGB, ACES)
  adaptation.py     Chromatic adaptation transforms (Bradford, CAT02, von Kries), illuminant handling (D50/D65)
  appearance.py     Color appearance models (CAM16 / CAM16-UCS)
  difference.py     Perceptual difference metrics (CIEDE2000, CIE76/94, CAM16-UCS dE)
  gamut.py          Gamut boundary + mapping (perceptual compression, clipping)
  tonemap.py        HDR tone mapping operators and transfer functions (PQ / ST.2084, HLG, sRGB, BT.1886)
  spectral.py       Spectral utilities (SPD sampling, color-matching functions, spectral-to-XYZ)
  icc.py            ICC profile generation / parsing helpers
  blindness.py      Color-vision-deficiency simulation
  harmony.py        Color harmony / palette relationships
  naming.py         Human-readable color naming
  image_analysis.py Image-level color statistics
  image_io.py       Image load/save (optional Pillow)
  lut_io.py         3D LUT read/write (.cube and related)
  cli.py            Command-line entry point (`build-color`)
  gui/              Optional PyQt6 workbench (thin adapter over the core; not required)
```

## Data flow

The library is functional and stateless at its core: values flow through pure
conversions. A typical path is

```
input color / image
  -> spaces (into a working space, e.g. linear or Oklab)
  -> adaptation (align white points)
  -> operation (tonemap / gamut map / difference / appearance)
  -> spaces (back to an output space)
  -> icc / lut_io / image_io (persist the result)
```

Each module takes and returns numpy arrays in documented shapes, so modules compose
without shared mutable state. The GUI and CLI are consumers of this core, never a
dependency of it.

## Design decisions

- **numpy-only core.** Everything needed for correct color math is expressed with
  numpy. SciPy is optional (used only where a heavier numeric routine genuinely helps),
  and imaging/GUI extras are isolated behind optional dependency groups so the core stays
  installable and importable anywhere.
- **Flat, single-purpose modules.** Each file answers one question ("how do I convert
  spaces?", "how different are these colors?"), which keeps the public surface legible
  and each unit independently testable. The test suite exercises the core directly.
- **Type-clean core, boundary-typed GUI.** The numeric core is fully type-checked
  (`mypy` clean). The PyQt6 GUI is a thin adapter over an untyped Qt binding and is
  checked at its public boundary rather than strict-typed internally.
- **Deterministic and offline.** Conversions are pure functions of their inputs. The
  library performs no network access and no code evaluation.

## Testing

The suite under `tests/` covers conversions with round-trip and reference-value checks,
metric correctness against published examples, and I/O round-trips for LUT and ICC paths.
Run `pytest` for the full suite; `ruff check .` and `mypy` gate style and types.
