# Changelog

## v1.0.0 (2026-03-22)

### Features
- **15 color spaces**: sRGB, Display P3, Adobe RGB, Rec.2020, ACES AP0/AP1, CIE XYZ, CIE Lab, Oklab, Oklch, JzAzBz, ICtCp, HSV, HSL, LMS
- **12 tone mapping operators**: Reinhard, ACES filmic, Hable/Uncharted 2, AGX, Khronos PBR Neutral, HLG OETF/EOTF, PQ (ST.2084), and more
- **CIECAM02 and CAM16** color appearance models
- **Spectral rendering** with observer functions
- **Gamut mapping** with perceptual chroma compression
- **Color difference metrics**: CIEDE2000, CIE94, CMC
- **Color harmony generation**: complementary, triadic, analogous, split-complementary
- **3D LUT I/O**: .cube, .3dl import/export with tone mapping baking
- **ICC profile generation**: v4 profiles with D50/D65 adaptation
- **PyQt6 GUI**: color inspector, palette studio, LUT workshop, image analyzer
- **CLI**: 8 commands (info, convert, difference, harmony, spectrum, icc, gui)

### Tests
- 457 tests passing
