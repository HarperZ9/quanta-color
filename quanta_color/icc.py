"""
ICC Profile Generation

Create valid ICC v4 display profiles from primaries and transfer curves.
Used for color management in Photoshop, Lightroom, Windows, macOS.

Usage:
    from quanta_color.icc import create_display_profile
    profile = create_display_profile(
        red_xy=(0.64, 0.33), green_xy=(0.30, 0.60), blue_xy=(0.15, 0.06),
        white_xy=(0.3127, 0.3290), gamma=2.2, name="My Display"
    )
    profile.save("display.icc")
"""

import datetime
import hashlib
import struct
from dataclasses import dataclass

import numpy as np


@dataclass
class ICCProfile:
    """ICC v4 profile data ready for export."""

    data: bytes
    name: str = ""

    def save(self, path: str):
        """Write the ICC profile to a file."""
        with open(path, "wb") as f:
            f.write(self.data)

    @property
    def size(self) -> int:
        return len(self.data)


def create_display_profile(
    red_xy: tuple[float, float] = (0.6400, 0.3300),
    green_xy: tuple[float, float] = (0.3000, 0.6000),
    blue_xy: tuple[float, float] = (0.1500, 0.0600),
    white_xy: tuple[float, float] = (0.3127, 0.3290),
    gamma: float = 2.2,
    name: str = "Quanta Color Display Profile",
    description: str = "",
    copyright: str = "Quanta Universe",
    trc_points: int = 256,
) -> ICCProfile:
    """
    Create an ICC v4 display profile.

    Args:
        red_xy, green_xy, blue_xy: Primary chromaticities (CIE xy)
        white_xy: White point chromaticity
        gamma: Display gamma (2.2 for sRGB, 2.4 for BT.1886)
        name: Profile description
        description: Extended description
        copyright: Copyright string
        trc_points: Number of TRC curve points (256 standard)

    Returns:
        ICCProfile ready to save
    """
    if not description:
        description = name

    # Compute XYZ from chromaticities
    def xy_to_XYZ(x, y):
        return np.array([x / y, 1.0, (1 - x - y) / y])

    R = xy_to_XYZ(*red_xy)
    G = xy_to_XYZ(*green_xy)
    B = xy_to_XYZ(*blue_xy)
    W = xy_to_XYZ(*white_xy)

    # Compute RGB-to-XYZ matrix
    M = np.column_stack([R, G, B])
    S = np.linalg.solve(M, W)
    rgb_to_xyz = M * S[np.newaxis, :]

    # Generate TRC curve
    trc = _generate_trc(gamma, trc_points)

    # Build profile
    tags = {}

    # Profile description
    tags["desc"] = _make_text_tag(name)

    # Copyright
    tags["cprt"] = _make_text_tag(copyright)

    # White point (mediaWhitePointTag)
    wp_xyz = rgb_to_xyz @ np.array([1.0, 1.0, 1.0])
    tags["wtpt"] = _make_xyz_tag(wp_xyz)

    # Red, Green, Blue colorant XYZ
    tags["rXYZ"] = _make_xyz_tag(rgb_to_xyz[:, 0])
    tags["gXYZ"] = _make_xyz_tag(rgb_to_xyz[:, 1])
    tags["bXYZ"] = _make_xyz_tag(rgb_to_xyz[:, 2])

    # TRC curves
    tags["rTRC"] = _make_curve_tag(trc)
    tags["gTRC"] = _make_curve_tag(trc)
    tags["bTRC"] = _make_curve_tag(trc)

    # Chromatic adaptation (D65 -> D50, Bradford)
    from quanta_color.adaptation import ILLUMINANTS, get_adaptation_matrix

    chad = get_adaptation_matrix(ILLUMINANTS["D65"], ILLUMINANTS["D50"], "bradford")
    tags["chad"] = _make_s15f16_matrix_tag(chad)

    # Build the binary profile
    data = _assemble_profile(tags, name)

    return ICCProfile(data=data, name=name)


def _generate_trc(gamma: float, points: int = 256) -> np.ndarray:
    """Generate a tone response curve."""
    t = np.linspace(0, 1, points)
    if abs(gamma - 2.2) < 0.01:
        # Use proper sRGB TRC
        return np.where(t <= 0.04045, t / 12.92, np.power((t + 0.055) / 1.055, 2.4))
    return np.power(t, gamma)


def _make_text_tag(text: str) -> bytes:
    """Create a 'desc' tag (profileDescriptionTag)."""
    text.encode("ascii", errors="replace")
    # mluc (multi-localized unicode) tag type
    sig = b"mluc"
    reserved = b"\x00" * 4
    count = struct.pack(">I", 1)  # 1 record
    record_size = struct.pack(">I", 12)
    # English US
    lang = b"en"
    country = b"US"
    str_bytes = text.encode("utf-16-be")
    str_len = struct.pack(">I", len(str_bytes))
    str_offset = struct.pack(">I", 28)  # offset from tag start

    data = sig + reserved + count + record_size
    data += lang + country + str_len + str_offset
    data += str_bytes

    # Pad to 4-byte boundary
    while len(data) % 4:
        data += b"\x00"
    return data


def _make_xyz_tag(xyz: np.ndarray) -> bytes:
    """Create an XYZ tag."""
    sig = b"XYZ "
    reserved = b"\x00" * 4
    x = _s15f16(xyz[0])
    y = _s15f16(xyz[1])
    z = _s15f16(xyz[2])
    return sig + reserved + x + y + z


def _make_curve_tag(values: np.ndarray) -> bytes:
    """Create a curve tag from an array of values."""
    sig = b"curv"
    reserved = b"\x00" * 4
    count = struct.pack(">I", len(values))
    data = sig + reserved + count
    for v in values:
        data += struct.pack(">H", min(65535, max(0, int(v * 65535 + 0.5))))
    while len(data) % 4:
        data += b"\x00"
    return data


def _make_s15f16_matrix_tag(matrix: np.ndarray) -> bytes:
    """Create a chromaticAdaptationTag (sf32 type with 3x3 matrix)."""
    sig = b"sf32"
    reserved = b"\x00" * 4
    data = sig + reserved
    for row in range(3):
        for col in range(3):
            data += _s15f16(matrix[row, col])
    return data


def _s15f16(value: float) -> bytes:
    """Encode a float as ICC s15Fixed16Number."""
    fixed = int(round(value * 65536))
    return struct.pack(">i", fixed)


def _assemble_profile(tags: dict, description: str) -> bytes:
    """Assemble a complete ICC v4 profile from tags."""
    # Header (128 bytes)
    header = bytearray(128)

    # Tag table
    tag_count = len(tags)
    tag_table = struct.pack(">I", tag_count)

    # Calculate offsets
    header_size = 128
    tag_table_size = 4 + tag_count * 12
    data_offset = header_size + tag_table_size

    # Pad to 4-byte boundary
    while data_offset % 4:
        data_offset += 1

    tag_data_parts = []
    tag_entries = []

    tag_sigs = {
        "desc": b"desc",
        "cprt": b"cprt",
        "wtpt": b"wtpt",
        "rXYZ": b"rXYZ",
        "gXYZ": b"gXYZ",
        "bXYZ": b"bXYZ",
        "rTRC": b"rTRC",
        "gTRC": b"gTRC",
        "bTRC": b"bTRC",
        "chad": b"chad",
    }

    current_offset = data_offset
    for key, tag_data in tags.items():
        sig = tag_sigs.get(key, key.encode("ascii")[:4])
        tag_entries.append(struct.pack(">4sII", sig, current_offset, len(tag_data)))
        tag_data_parts.append(tag_data)
        current_offset += len(tag_data)
        # Align to 4 bytes
        padding = (4 - len(tag_data) % 4) % 4
        if padding:
            tag_data_parts.append(b"\x00" * padding)
            current_offset += padding

    # Total profile size
    profile_size = current_offset

    # Fill header
    struct.pack_into(">I", header, 0, profile_size)  # Profile size
    header[4:8] = b"QNTC"  # Preferred CMM (Quanta Color)
    struct.pack_into(">I", header, 8, 0x04400000)  # Version 4.4
    header[12:16] = b"mntr"  # Device class: monitor
    header[16:20] = b"RGB "  # Color space: RGB
    header[20:24] = b"XYZ "  # PCS: XYZ

    # Date/time
    now = datetime.datetime.now()
    struct.pack_into(">HHHHHH", header, 24, now.year, now.month, now.day, now.hour, now.minute, now.second)

    header[36:40] = b"acsp"  # File signature
    header[40:44] = b"MSFT"  # Primary platform (Windows)
    struct.pack_into(">I", header, 44, 0)  # Flags
    header[48:52] = b"QNTC"  # Device manufacturer
    header[64:68] = b"\x00\x00\xf6\xd6"  # D50 X (0.9642 as s15f16)
    header[68:72] = b"\x00\x01\x00\x00"  # D50 Y (1.0)
    header[72:76] = b"\x00\x00\xd3\x2d"  # D50 Z (0.8249)
    header[80:84] = b"QNTC"  # Profile creator

    # Compute MD5 (profile ID)
    full_data = (
        bytes(header)
        + tag_table
        + b"".join(b"".join(e for e in [entry]) for entry in tag_entries)
        + b"".join(tag_data_parts)
    )

    # Zero out fields that should not be included in ID computation
    id_header = bytearray(header)
    id_header[44:48] = b"\x00" * 4  # Flags
    id_header[84:100] = b"\x00" * 16  # Profile ID field

    id_data = bytes(id_header) + full_data[128:]
    profile_id = hashlib.md5(id_data).digest()
    header[84:100] = profile_id

    # Assemble final
    result = bytes(header) + tag_table
    for entry in tag_entries:
        result += entry
    # Pad to data offset
    while len(result) < data_offset:
        result += b"\x00"
    for part in tag_data_parts:
        result += part

    return result
