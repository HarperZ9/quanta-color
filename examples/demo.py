"""
Quanta Color — best-effort demo.

Best-effort demo — not runtime-verified by author.

Exercises the real public surface of the package:
  * the Python API (spaces, tonemap, difference, adaptation, appearance, harmony)
  * the `quanta-color` CLI (via `python -m quanta_color.cli`)

Run from the repository root after installing the package (`pip install .`)
or directly from a checkout:

    python examples/demo.py

Only documented, real symbols and commands are used. Numeric output depends on
your numpy version and may differ slightly in the last decimals.
"""

import subprocess
import sys

import numpy as np

from quanta_color.adaptation import ILLUMINANTS, adapt
from quanta_color.appearance import ViewingConditions, ciecam02_forward
from quanta_color.difference import delta_e_2000
from quanta_color.harmony import generate
from quanta_color.spaces import srgb_to_oklab
from quanta_color.tonemap import aces_filmic


def api_demo() -> None:
    print("== Python API ==")

    # sRGB -> Oklab
    oklab = srgb_to_oklab(np.array([0.8, 0.2, 0.1]))
    print(f"srgb_to_oklab([0.8, 0.2, 0.1]) = {np.round(oklab, 4)}")

    # HDR scene-linear -> display via ACES filmic
    sdr = aces_filmic(np.array([0.0, 0.18, 1.0, 4.0, 10.0]))
    print(f"aces_filmic(hdr)              = {np.round(sdr, 4)}")

    # CIEDE2000 color difference in CIELAB
    de = delta_e_2000(np.array([50.0, 25.0, -10.0]), np.array([60.0, 20.0, -5.0]))
    print(f"delta_e_2000(lab1, lab2)      = {float(de):.4f}")

    # Chromatic adaptation D65 -> D50
    d65 = ILLUMINANTS["D65"]
    d50 = ILLUMINANTS["D50"]
    xyz = np.array([0.4596, 0.2985, 0.0614])
    adapted = adapt(xyz, d65, d50, method="cat16")
    print(f"adapt(xyz, D65, D50, cat16)   = {np.round(adapted, 4)}")

    # CIECAM02 appearance correlates
    vc = ViewingConditions(white_point=d65)
    ap = ciecam02_forward(xyz, vc)
    print(f"ciecam02_forward -> J={ap.J:.1f}, C={ap.C:.1f}, h={ap.h:.0f}")

    # Color harmony
    palette = generate(np.array([1.0, 0.3765, 0.1882]), "triadic")
    hexes = ["#" + "".join(f"{int(v * 255):02x}" for v in c) for c in palette]
    print(f"generate(base, 'triadic')     = {hexes}")


def cli_demo() -> None:
    print("\n== CLI (python -m quanta_color.cli) ==")
    commands = [
        ["info", "ff6030"],
        ["convert", "ff6030", "--to", "oklab"],
        ["difference", "ff0000", "00ff00", "--metric", "all"],
        ["harmony", "ff6030", "--scheme", "triadic"],
    ]
    for cmd in commands:
        print(f"\n$ quanta-color {' '.join(cmd)}")
        result = subprocess.run(
            [sys.executable, "-m", "quanta_color.cli", *cmd],
            capture_output=True,
            text=True,
        )
        sys.stdout.write(result.stdout)
        if result.returncode != 0:
            sys.stderr.write(result.stderr)


if __name__ == "__main__":
    api_demo()
    cli_demo()
