"""
LUT File I/O

Read and write 3D/1D lookup tables in .cube and CLF formats.
Includes LUT generation, identity creation, and trilinear
interpolation for applying 3D LUTs to images.

Formats:
    .cube   - Adobe/Resolve standard (TITLE, LUT_3D_SIZE, LUT_1D_SIZE)
    .clf    - ACES Common LUT Format (XML ProcessList/LUT3D/Array)

Classes:
    LUT3D   - 3D lookup table (size, size, size, 3)
    LUT1D   - 1D lookup table (size, 3)

Functions:
    read_cube       - Parse .cube files
    write_cube      - Write .cube files
    read_clf        - Parse CLF XML
    write_clf       - Write CLF XML
    identity_lut    - Create identity (passthrough) 3D LUT
    apply_lut       - Apply 3D LUT with trilinear interpolation
    lut_from_function - Bake a color transform function into a LUT
"""

import xml.etree.ElementTree as ET
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

import numpy as np


@dataclass
class LUT3D:
    """3D Lookup Table."""

    data: np.ndarray  # (size, size, size, 3) float64
    size: int
    title: str = ""

    def __post_init__(self):
        self.data = np.asarray(self.data, dtype=np.float64)
        expected = (self.size, self.size, self.size, 3)
        if self.data.shape != expected:
            raise ValueError(
                f"LUT3D data shape {self.data.shape} does not match expected {expected} for size={self.size}"
            )


@dataclass
class LUT1D:
    """1D Lookup Table."""

    data: np.ndarray  # (size, 3) float64
    size: int
    title: str = ""

    def __post_init__(self):
        self.data = np.asarray(self.data, dtype=np.float64)
        expected = (self.size, 3)
        if self.data.shape != expected:
            raise ValueError(
                f"LUT1D data shape {self.data.shape} does not match expected {expected} for size={self.size}"
            )


# =============================================================================
# .cube I/O
# =============================================================================


def read_cube(path: str | Path) -> LUT3D | LUT1D:
    """
    Parse a .cube LUT file.

    Handles TITLE, LUT_3D_SIZE, LUT_1D_SIZE, DOMAIN_MIN, DOMAIN_MAX,
    and data lines. Domain scaling is applied so output is always 0-1.

    Args:
        path: Path to .cube file.

    Returns:
        LUT3D or LUT1D depending on file contents.
    """
    path = Path(path)
    title = ""
    lut_3d_size = 0
    lut_1d_size = 0
    domain_min = np.array([0.0, 0.0, 0.0])
    domain_max = np.array([1.0, 1.0, 1.0])
    data_lines: list[np.ndarray] = []

    with open(path) as f:
        for line in f:
            line = line.strip()

            # Skip empty lines and comments
            if not line or line.startswith("#"):
                continue

            if line.startswith("TITLE"):
                # TITLE "Some Title" or TITLE Some Title
                title = line[5:].strip().strip('"')
                continue

            if line.startswith("LUT_3D_SIZE"):
                lut_3d_size = int(line.split()[-1])
                continue

            if line.startswith("LUT_1D_SIZE"):
                lut_1d_size = int(line.split()[-1])
                continue

            if line.startswith("DOMAIN_MIN"):
                parts = line.split()[1:]
                domain_min = np.array([float(x) for x in parts[:3]])
                continue

            if line.startswith("DOMAIN_MAX"):
                parts = line.split()[1:]
                domain_max = np.array([float(x) for x in parts[:3]])
                continue

            # Try to parse as data line (three floats)
            try:
                parts = line.split()
                if len(parts) >= 3:
                    values = np.array([float(parts[0]), float(parts[1]), float(parts[2])])
                    data_lines.append(values)
            except ValueError:
                continue

    if not data_lines:
        raise ValueError(f"No data found in {path}")

    raw = np.array(data_lines)

    # Normalize from domain range to 0-1
    domain_range = domain_max - domain_min
    domain_range = np.where(domain_range == 0, 1.0, domain_range)
    normalized = (raw - domain_min) / domain_range

    if lut_3d_size > 0:
        expected = lut_3d_size**3
        if len(normalized) != expected:
            raise ValueError(f"Expected {expected} data lines for 3D LUT size {lut_3d_size}, got {len(normalized)}")
        # .cube 3D order: R varies fastest, then G, then B
        data = normalized.reshape(lut_3d_size, lut_3d_size, lut_3d_size, 3)
        return LUT3D(data=data, size=lut_3d_size, title=title)

    elif lut_1d_size > 0:
        if len(normalized) != lut_1d_size:
            raise ValueError(f"Expected {lut_1d_size} data lines for 1D LUT, got {len(normalized)}")
        return LUT1D(data=normalized, size=lut_1d_size, title=title)

    else:
        # Guess from data count
        n = len(normalized)
        # Check if it's a perfect cube
        size = round(n ** (1.0 / 3.0))
        if size**3 == n:
            data = normalized.reshape(size, size, size, 3)
            return LUT3D(data=data, size=size, title=title)
        else:
            return LUT1D(data=normalized, size=n, title=title)


def write_cube(lut: LUT3D | LUT1D, path: str | Path) -> None:
    """
    Write a LUT to .cube format.

    Args:
        lut: LUT3D or LUT1D to write.
        path: Output file path.
    """
    path = Path(path)
    lines: list[str] = []

    if lut.title:
        lines.append(f'TITLE "{lut.title}"')
    lines.append("")

    if isinstance(lut, LUT3D):
        lines.append(f"LUT_3D_SIZE {lut.size}")
        lines.append("")
        lines.append("DOMAIN_MIN 0.0 0.0 0.0")
        lines.append("DOMAIN_MAX 1.0 1.0 1.0")
        lines.append("")

        # Write data: R fastest, then G, then B
        for b_idx in range(lut.size):
            for g_idx in range(lut.size):
                for r_idx in range(lut.size):
                    r, g, b = lut.data[b_idx, g_idx, r_idx]
                    lines.append(f"{r:.10f} {g:.10f} {b:.10f}")

    elif isinstance(lut, LUT1D):
        lines.append(f"LUT_1D_SIZE {lut.size}")
        lines.append("")
        lines.append("DOMAIN_MIN 0.0 0.0 0.0")
        lines.append("DOMAIN_MAX 1.0 1.0 1.0")
        lines.append("")

        for i in range(lut.size):
            r, g, b = lut.data[i]
            lines.append(f"{r:.10f} {g:.10f} {b:.10f}")

    with open(path, "w", newline="\n") as f:
        f.write("\n".join(lines))
        f.write("\n")


# =============================================================================
# CLF (Common LUT Format) I/O
# =============================================================================


def read_clf(path: str | Path) -> LUT3D:
    """
    Parse a CLF (Common LUT Format) XML file.

    Expects a ProcessList containing a LUT3D element with an Array child.

    Args:
        path: Path to .clf file.

    Returns:
        LUT3D parsed from the file.
    """
    path = Path(path)
    tree = ET.parse(path)
    root = tree.getroot()

    # Handle namespace
    ns = ""
    if root.tag.startswith("{"):
        ns = root.tag.split("}")[0] + "}"

    # Find LUT3D element
    lut3d_elem = root.find(f".//{ns}LUT3D")
    if lut3d_elem is None:
        raise ValueError(f"No LUT3D element found in {path}")

    # Get size from inBitDepth or array dimensions
    size = 0
    array_elem = lut3d_elem.find(f"{ns}Array")
    if array_elem is None:
        raise ValueError(f"No Array element found in LUT3D in {path}")

    dim_attr = array_elem.get("dim")
    if dim_attr:
        dims = dim_attr.split()
        if len(dims) >= 1:
            total = int(dims[0])
            size = round(total ** (1.0 / 3.0))

    # Parse data
    text = array_elem.text
    if not text:
        raise ValueError(f"Array element is empty in {path}")

    raw_values: list[float] = []
    for line in text.strip().split("\n"):
        line = line.strip()
        if not line:
            continue
        parts = line.split()
        for p in parts:
            raw_values.append(float(p))

    values = np.array(raw_values, dtype=np.float64)
    n_triplets = len(values) // 3

    if size == 0:
        size = round(n_triplets ** (1.0 / 3.0))

    if size**3 != n_triplets:
        raise ValueError(f"Data count {n_triplets} does not match a valid 3D LUT size")

    data = values.reshape(size, size, size, 3)

    # Get title
    title = ""
    desc = root.find(f".//{ns}Description")
    if desc is not None and desc.text:
        title = desc.text.strip()

    return LUT3D(data=data, size=size, title=title)


def write_clf(lut: LUT3D, path: str | Path) -> None:
    """
    Write a 3D LUT to CLF (Common LUT Format) XML.

    Args:
        lut: LUT3D to write.
        path: Output file path.
    """
    path = Path(path)

    ns = "urn:AMPAS:CLF:v3.0"
    root = ET.Element(
        "ProcessList",
        attrib={
            "xmlns": ns,
            "compCLFversion": "3.0",
            "id": lut.title or "build_color_lut",
        },
    )

    if lut.title:
        desc = ET.SubElement(root, "Description")
        desc.text = lut.title

    lut3d_elem = ET.SubElement(
        root,
        "LUT3D",
        attrib={
            "inBitDepth": "32f",
            "outBitDepth": "32f",
            "interpolation": "trilinear",
        },
    )

    total = lut.size**3
    array_elem = ET.SubElement(
        lut3d_elem,
        "Array",
        attrib={
            "dim": f"{total} 3",
        },
    )

    # Build data text
    lines = []
    for b_idx in range(lut.size):
        for g_idx in range(lut.size):
            for r_idx in range(lut.size):
                r, g, b = lut.data[b_idx, g_idx, r_idx]
                lines.append(f"{r:.10f} {g:.10f} {b:.10f}")

    array_elem.text = "\n" + "\n".join(lines) + "\n"

    tree = ET.ElementTree(root)
    ET.indent(tree, space="  ")
    tree.write(str(path), xml_declaration=True, encoding="utf-8")


# =============================================================================
# LUT generation and application
# =============================================================================


def identity_lut(size: int = 33) -> LUT3D:
    """
    Create an identity (passthrough) 3D LUT.

    Each lattice point maps input RGB to the same output RGB.

    Args:
        size: Grid size per axis (default 33, common for color grading).

    Returns:
        LUT3D where output == input at every lattice point.
    """
    coords = np.linspace(0.0, 1.0, size, dtype=np.float64)
    r, g, b = np.meshgrid(coords, coords, coords, indexing="ij")
    # Reshape so data[b][g][r] layout matches .cube convention
    data = np.empty((size, size, size, 3), dtype=np.float64)
    data[..., 0] = np.transpose(r, (2, 1, 0))
    data[..., 1] = np.transpose(g, (2, 1, 0))
    data[..., 2] = np.transpose(b, (2, 1, 0))

    # Simpler correct approach: iterate the output axes
    data = np.zeros((size, size, size, 3), dtype=np.float64)
    for bi in range(size):
        for gi in range(size):
            for ri in range(size):
                data[bi, gi, ri] = [
                    coords[ri],
                    coords[gi],
                    coords[bi],
                ]

    return LUT3D(data=data, size=size, title="Identity")


def apply_lut(image: np.ndarray, lut: LUT3D) -> np.ndarray:
    """
    Apply a 3D LUT to an image using trilinear interpolation.

    Args:
        image: (H, W, 3) float64 image in 0-1 range.
        lut: LUT3D to apply.

    Returns:
        (H, W, 3) float64 transformed image.
    """
    image = np.asarray(image, dtype=np.float64)
    h, w, _ = image.shape
    s = lut.size - 1

    # Clamp input to valid range
    img = np.clip(image, 0.0, 1.0)

    # Scale to LUT indices
    r_scaled = img[..., 0] * s
    g_scaled = img[..., 1] * s
    b_scaled = img[..., 2] * s

    # Integer indices (floor)
    r0 = np.floor(r_scaled).astype(int)
    g0 = np.floor(g_scaled).astype(int)
    b0 = np.floor(b_scaled).astype(int)

    # Clamp to valid range
    r0 = np.clip(r0, 0, s - 1)
    g0 = np.clip(g0, 0, s - 1)
    b0 = np.clip(b0, 0, s - 1)

    r1 = r0 + 1
    g1 = g0 + 1
    b1 = b0 + 1

    # Fractional parts
    rf = r_scaled - r0
    gf = g_scaled - g0
    bf = b_scaled - b0

    rf = rf[..., np.newaxis]
    gf = gf[..., np.newaxis]
    bf = bf[..., np.newaxis]

    # Trilinear interpolation: 8 corners of the cube
    # lut.data is indexed [b, g, r, channel]
    c000 = lut.data[b0, g0, r0]
    c001 = lut.data[b0, g0, r1]
    c010 = lut.data[b0, g1, r0]
    c011 = lut.data[b0, g1, r1]
    c100 = lut.data[b1, g0, r0]
    c101 = lut.data[b1, g0, r1]
    c110 = lut.data[b1, g1, r0]
    c111 = lut.data[b1, g1, r1]

    # Interpolate along R
    c00 = c000 * (1 - rf) + c001 * rf
    c01 = c010 * (1 - rf) + c011 * rf
    c10 = c100 * (1 - rf) + c101 * rf
    c11 = c110 * (1 - rf) + c111 * rf

    # Interpolate along G
    c0 = c00 * (1 - gf) + c01 * gf
    c1 = c10 * (1 - gf) + c11 * gf

    # Interpolate along B
    result = c0 * (1 - bf) + c1 * bf

    return result


def lut_from_function(
    fn: Callable[[np.ndarray], np.ndarray],
    size: int = 33,
) -> LUT3D:
    """
    Bake a color transform function into a 3D LUT.

    The function should accept and return sRGB arrays in 0-1 range
    with shape (3,) or (N, 3).

    Args:
        fn: Transform function fn(rgb) -> rgb, both in 0-1 sRGB.
        size: Grid size per axis (default 33).

    Returns:
        LUT3D encoding the function at each lattice point.
    """
    coords = np.linspace(0.0, 1.0, size, dtype=np.float64)
    data = np.zeros((size, size, size, 3), dtype=np.float64)

    # Build all lattice points as a batch
    raw_points: list[list[float]] = []
    for bi in range(size):
        for gi in range(size):
            for ri in range(size):
                raw_points.append([coords[ri], coords[gi], coords[bi]])

    points = np.array(raw_points, dtype=np.float64)

    # Try batch processing first
    try:
        results = fn(points)
        if results.shape == points.shape:
            idx = 0
            for bi in range(size):
                for gi in range(size):
                    for ri in range(size):
                        data[bi, gi, ri] = results[idx]
                        idx += 1
            return LUT3D(data=data, size=size)
    except (ValueError, TypeError):
        pass

    # Fall back to per-point processing
    for bi in range(size):
        for gi in range(size):
            for ri in range(size):
                inp = np.array([coords[ri], coords[gi], coords[bi]])
                data[bi, gi, ri] = fn(inp)

    return LUT3D(data=data, size=size)
