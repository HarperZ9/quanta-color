# Quanta Color - Roadmap to Production

Current state: 9 modules, 1,937 lines, 17 tests.
Target state: Calibrate Pro level (~10K+ lines, 100+ tests, GUI, standalone exe, documentation).

---

## Phase 1: Core Library Hardening (Week 1)

The math exists but needs production-grade testing, edge case handling, and documentation.

### 1.1 Comprehensive Test Suite (target: 100+ tests)
- [ ] `test_spaces.py` - Roundtrip tests for every color space conversion (sRGB->XYZ->sRGB, sRGB->Oklab->sRGB, XYZ->JzAzBz->XYZ, etc.)
- [ ] `test_spaces.py` - Known reference values (e.g., D65 white in every space, ColorChecker patch 19 in every space)
- [ ] `test_spaces.py` - Edge cases (pure black, pure white, out-of-gamut, negative values, NaN handling)
- [ ] `test_spaces.py` - Batch processing (N,3 arrays, image-shaped arrays)
- [ ] `test_tonemap.py` - Monotonicity (brighter input -> brighter output for every operator)
- [ ] `test_tonemap.py` - Black preservation (0 in -> 0 out for every operator)
- [ ] `test_tonemap.py` - White convergence (large input -> approaches 1.0)
- [ ] `test_tonemap.py` - PQ/HLG roundtrip at 100+ luminance levels
- [ ] `test_difference.py` - Published CIEDE2000 test dataset (34 pairs from Sharma et al. 2005)
- [ ] `test_difference.py` - Symmetry (dE(a,b) == dE(b,a) for symmetric metrics)
- [ ] `test_difference.py` - Triangle inequality
- [ ] `test_adaptation.py` - Roundtrip for all 9 methods (D65->D50->D65)
- [ ] `test_adaptation.py` - Known Bradford D65->D50 matrix values (ICC spec)
- [ ] `test_spectral.py` - Planck at known temperatures (D65 ~6504K chromaticity)
- [ ] `test_spectral.py` - CMF integration of equal-energy illuminant -> (1/3, 1/3) chromaticity
- [ ] `test_blindness.py` - Severity=0 returns input unchanged
- [ ] `test_blindness.py` - Severity=1 achromatopsia returns grayscale
- [ ] `test_gamut.py` - In-gamut colors pass through unchanged
- [ ] `test_gamut.py` - Out-of-gamut colors are brought in-gamut
- [ ] `test_harmony.py` - Complementary produces 2 colors, triadic produces 3, tetradic produces 4

### 1.2 Edge Case Hardening
- [ ] All functions handle NaN/Inf gracefully (return NaN, don't crash)
- [ ] All functions handle single values, 1D arrays, 2D arrays, and image-shaped (H,W,3) arrays
- [ ] Division-by-zero protection in every conversion (safe denominators)
- [ ] Negative input handling (clamp or propagate depending on function)
- [ ] Type coercion (accept lists, tuples, float32 arrays - convert internally to float64)

### 1.3 Performance Optimization
- [ ] Vectorize all per-pixel loops (no Python for-loops over image pixels)
- [ ] Benchmark: 1920x1080 image through sRGB->Oklab->gamut map->sRGB in <100ms
- [ ] Optional: numba JIT for hot paths (tone mapping, gamut mapping)

---

## Phase 2: Missing Color Science (Week 1-2)

Features from the Spectrum source that aren't ported yet.

### 2.1 CIECAM02 Complete Model
- [ ] Forward model: XYZ -> J, C, h, Q, M, s, H (all appearance correlates)
- [ ] Inverse model: J, C, h -> XYZ
- [ ] Viewing condition parameters (surround, L_A, Y_b)
- [ ] Hue quadrature (unique hues at 20.14, 90, 164.25, 237.53 degrees)

### 2.2 CAM16-UCS
- [ ] J', a', b' uniform color space
- [ ] CAM16-UCS Delta E (more perceptually uniform than CIEDE2000 for wide-gamut)
- [ ] LCD (large color difference) and SCD (small color difference) variants

### 2.3 ZCAM (HDR Appearance Model)
- [ ] Full forward model for HDR content
- [ ] Viewing condition adaptation
- [ ] Hue composition

### 2.4 ICC Profile Generation
- [ ] Create valid ICC v4 profiles from primaries + TRC
- [ ] Embed VCGT tag
- [ ] Write binary .icc files
- [ ] Validate against ICC spec (file signature, tag table, required tags)

### 2.5 3D LUT Operations
- [ ] Trilinear interpolation
- [ ] Tetrahedral interpolation (higher accuracy)
- [ ] LUT composition (chain two LUTs)
- [ ] LUT inversion (approximate)

### 2.6 Advanced Spectral
- [ ] CIE daylight basis functions (S0, S1, S2) for arbitrary CCT
- [ ] Cone response functions (L, M, S fundamentals)
- [ ] Metamerism index calculation
- [ ] Spectral upsampling (RGB -> SPD via Smits/Mallett)

---

## Phase 3: CLI Tool (Week 2)

A command-line interface for color science operations, like `calibrate-pro` but for color math.

### 3.1 Core Commands
- [ ] `quanta-color convert <color> --from srgb --to oklab` - Convert between any color spaces
- [ ] `quanta-color difference <color1> <color2> --metric ciede2000` - Compute color difference
- [ ] `quanta-color tonemap <image> --operator aces --output out.png` - Apply tone mapping to an image
- [ ] `quanta-color adapt <color> --from D65 --to D50 --method bradford` - Chromatic adaptation
- [ ] `quanta-color blindness <image> --type deuteranopia --output sim.png` - CVD simulation
- [ ] `quanta-color harmony <color> --scheme triadic` - Generate palette
- [ ] `quanta-color gamut <image> --target srgb --method oklab` - Gamut map an image
- [ ] `quanta-color info <color>` - Show color in every space, luminance, CCT, dominant wavelength
- [ ] `quanta-color spectrum --temp 6500 --output d65.csv` - Generate spectral data

### 3.2 Image Processing Commands
- [ ] `quanta-color lut create --from <profile> --size 33 --output cal.cube` - Generate LUT
- [ ] `quanta-color lut apply <image> <lut> --output corrected.png` - Apply LUT to image
- [ ] `quanta-color icc create --primaries r,g,b --gamma 2.2 --output display.icc` - Create ICC profile
- [ ] `quanta-color report <image> --output report.html` - Color analysis report

### 3.3 Entry Point
- [ ] `pyproject.toml` entry: `quanta-color = "quanta_color.cli:main"`
- [ ] argparse with subcommands
- [ ] Color input parsing: hex (#ff0000), rgb(255,0,0), lab(50,25,-10), oklch(0.5,0.15,30)
- [ ] Image I/O via Pillow (PNG, JPEG, TIFF, EXR)

---

## Phase 4: GUI Application (Week 2-3)

PyQt6 application for visual color science exploration.

### 4.1 Color Picker / Inspector
- [ ] Click anywhere on screen to pick a color
- [ ] Show the color in every supported space (sRGB, Lab, Oklab, JzAzBz, HSV, etc.)
- [ ] Show Delta E to nearest named color
- [ ] Show CVD simulation side-by-side
- [ ] Show WCAG contrast ratio against white/black

### 4.2 Gamut Visualizer
- [ ] Interactive CIE 1931 diagram (reuse from Calibrate Pro)
- [ ] Display gamut triangle overlay
- [ ] Planckian locus with CCT labels
- [ ] Click to get xy coordinates

### 4.3 Tone Mapping Preview
- [ ] Load an HDR image (EXR/HDR)
- [ ] Side-by-side comparison of all 12 tone mapping operators
- [ ] Exposure slider
- [ ] Export as SDR PNG

### 4.4 Palette Generator
- [ ] Pick a base color
- [ ] Generate palettes for all 6 harmony schemes
- [ ] Export as CSS, JSON, ASE (Adobe Swatch Exchange)
- [ ] CVD-safe palette checker

### 4.5 Color Blindness Simulator
- [ ] Load image, show side-by-side normal vs all 4 CVD types
- [ ] Severity slider
- [ ] Highlight problematic color pairs

### 4.6 LUT Viewer
- [ ] Load .cube/.clf LUT files
- [ ] Visualize as 3D point cloud (using matplotlib or custom GL)
- [ ] Show hue/saturation/lightness shift per region

### 4.7 Spectral Viewer
- [ ] Plot blackbody curves at different temperatures
- [ ] Show CIE CMFs (x-bar, y-bar, z-bar)
- [ ] Plot daylight SPDs
- [ ] Interactive: drag temperature slider, see chromaticity move on CIE diagram

---

## Phase 5: Documentation & Packaging (Week 3)

### 5.1 README
- [ ] Feature overview with examples
- [ ] Installation instructions (pip, source, standalone)
- [ ] Quick start: 5-line code examples for common tasks
- [ ] CLI command reference table
- [ ] Supported color spaces table
- [ ] Supported tone mapping operators table

### 5.2 API Documentation
- [ ] Docstrings on every public function (already mostly done)
- [ ] Type hints on every function (already done)
- [ ] Usage examples in docstrings
- [ ] Generate HTML docs (sphinx or pdoc)

### 5.3 Standalone Executable
- [ ] PyInstaller spec file
- [ ] Bundle GUI + CLI in one exe
- [ ] Icon (color wheel or spectrum)
- [ ] Test on clean Windows install

### 5.4 Package Publishing
- [ ] Clean up pyproject.toml (classifiers, URLs, keywords)
- [ ] Write CHANGELOG.md
- [ ] Test `pip install` from source
- [ ] Consider PyPI publication

---

## Phase 6: Integration & Ecosystem (Week 3-4)

### 6.1 Calibrate Pro Integration
- [ ] Replace Calibrate Pro's `core/color_math.py` with `import quanta_color`
- [ ] Verify all 197 Calibrate Pro tests still pass
- [ ] Shared dependency: Calibrate Pro depends on quanta-color

### 6.2 Image Format Support
- [ ] PNG/JPEG/TIFF via Pillow
- [ ] OpenEXR (HDR) via openexr or imageio
- [ ] DNG (raw) metadata reading
- [ ] HEIF/AVIF (modern formats)

### 6.3 DaVinci Resolve Integration
- [ ] DCTL (DaVinci Color Transform Language) export from Python color functions
- [ ] Resolve LUT installation helper

### 6.4 Photoshop/Lightroom Integration
- [ ] ICC profile creation for soft proofing
- [ ] Color space conversion presets
- [ ] Export-ready LUT files

### 6.5 Web API (optional)
- [ ] FastAPI server for color conversions
- [ ] JSON input/output
- [ ] Batch processing endpoint
- [ ] Deployed as a microservice for web apps

---

## Phase 7: Advanced Features (Week 4+)

### 7.1 Spectral Upsampling
- [ ] RGB to SPD (Smits 1999, Mallett-Yuksel 2019)
- [ ] Physically accurate spectral rendering
- [ ] Fluorescence modeling

### 7.2 Color Naming
- [ ] Map any color to nearest named color (CSS, Pantone, RAL, NCS)
- [ ] Perceptual naming (Oklab-based nearest neighbor)
- [ ] Custom color dictionaries

### 7.3 Color Palette Analysis
- [ ] Extract dominant colors from image (k-means in Oklab)
- [ ] Palette diversity score
- [ ] Accessibility score (WCAG AA/AAA compliance)
- [ ] Harmony score

### 7.4 GPU Acceleration
- [ ] CUDA/OpenCL kernels for batch operations
- [ ] GPU tone mapping for real-time preview
- [ ] Integration with PyTorch/JAX for differentiable color science

---

## Milestones

| Milestone | Target | Metric |
|-----------|--------|--------|
| **Alpha** | End of Week 1 | 100+ tests, all edge cases handled, CLI with 5 commands |
| **Beta** | End of Week 2 | Full CLI (15 commands), GUI color picker, CIECAM02, ICC profiles |
| **RC1** | End of Week 3 | Standalone exe, full documentation, Calibrate Pro integration |
| **1.0** | End of Week 4 | PyPI published, web API, all advanced features |

## Success Criteria (Calibrate Pro Parity)

- [ ] 10,000+ lines of production code
- [ ] 100+ passing tests
- [ ] Standalone executable (PyInstaller)
- [ ] GUI application (PyQt6)
- [ ] CLI with 15+ commands
- [ ] Complete documentation (README + API docs)
- [ ] pip installable
- [ ] Used by at least one other project (Calibrate Pro)
