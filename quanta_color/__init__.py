"""
Quanta Color — Professional Color Science Library

Comprehensive color science toolkit for display calibration, HDR processing,
color grading, and image processing.

Modules:
    spaces      - Color space conversions (sRGB, XYZ, Lab, Oklab, JzAzBz, ICtCp, CAM16)
    adaptation  - Chromatic adaptation (Bradford, CAT16, CMCCAT2000, Von Kries, Sharp)
    tonemap     - Tone mapping operators (ACES, Reinhard, AgX, Hable, BT.2390)
    difference  - Color difference metrics (CIEDE2000, CIE94, CMC, HyAB, JzAzBz, Oklab)
    appearance  - Color appearance models (CIECAM02, CAM16-UCS, ZCAM)
    gamut       - Gamut mapping (chroma reduction, Oklab, JzAzBz)
    blindness   - Color vision deficiency simulation (Brettel et al.)
    spectral    - Spectral rendering (Planck, daylight, CIE CMFs)
    harmony     - Color harmony generation (complementary, triadic, analogous)
    hdr         - HDR metadata and processing (PQ, HLG, BT.2390, BT.2446)
    gui         - PyQt6 interactive workbench (launch with quanta_color.gui.launch())
"""

__version__ = "1.0.0"
