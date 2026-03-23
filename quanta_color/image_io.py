"""
Image Loading and Saving

Load and save images as float64 NumPy arrays in 0-1 sRGB range.
Supports PNG (8/16-bit), JPEG, and TIFF via Pillow.

Functions:
    load_image          - Load image file to float64 (H,W,3) array
    save_image          - Save float64 array to PNG/TIFF/JPEG
    resize_for_preview  - Lanczos downscale to a max dimension
    get_image_info      - Get width, height, mode, format without loading pixels
"""

import numpy as np
from pathlib import Path
from typing import Union

try:
    from PIL import Image as PILImage
    _HAS_PILLOW = True
except ImportError:
    _HAS_PILLOW = False


def _require_pillow() -> None:
    """Raise a helpful error if Pillow is not installed."""
    if not _HAS_PILLOW:
        raise ImportError(
            "Pillow is required for image I/O. "
            "Install it with: pip install Pillow  "
            "(or: pip install quanta-color[all])"
        )


def load_image(path: Union[str, Path]) -> np.ndarray:
    """
    Load an image file and return a float64 (H, W, 3) array in 0-1 sRGB.

    Supports PNG (8-bit and 16-bit), JPEG, and TIFF. Alpha channels are
    discarded. Grayscale images are broadcast to 3 channels.

    Args:
        path: Path to the image file.

    Returns:
        np.ndarray of shape (H, W, 3), dtype float64, values in [0, 1].
    """
    _require_pillow()
    path = Path(path)

    img = PILImage.open(path)

    # Determine bit depth from mode
    mode = img.mode

    # Convert palette and other modes to RGB
    if mode == "P":
        img = img.convert("RGB")
        mode = "RGB"
    elif mode == "LA":
        img = img.convert("L")
        mode = "L"
    elif mode in ("RGBA", "PA"):
        img = img.convert("RGB")
        mode = "RGB"

    arr = np.asarray(img)

    # Handle different dtypes
    if arr.dtype == np.uint8:
        result = arr.astype(np.float64) / 255.0
    elif arr.dtype == np.uint16:
        result = arr.astype(np.float64) / 65535.0
    elif arr.dtype == np.int32:
        # Some TIFF files use int32
        result = arr.astype(np.float64) / 2147483647.0
    elif arr.dtype in (np.float32, np.float64):
        result = arr.astype(np.float64)
    else:
        result = arr.astype(np.float64) / float(np.iinfo(arr.dtype).max)

    # Handle grayscale -> 3 channels
    if result.ndim == 2:
        result = np.stack([result, result, result], axis=-1)
    elif result.shape[-1] == 1:
        result = np.repeat(result, 3, axis=-1)
    elif result.shape[-1] == 4:
        # RGBA -> RGB (discard alpha)
        result = result[..., :3]

    return result


def save_image(
    image: np.ndarray,
    path: Union[str, Path],
    bit_depth: int = 8,
) -> None:
    """
    Save a float64 (H, W, 3) image to file.

    Format is determined by file extension:
        .png  - PNG (8-bit or 16-bit)
        .tif/.tiff - TIFF (8-bit or 16-bit)
        .jpg/.jpeg - JPEG (always 8-bit, quality=95)

    Args:
        image: (H, W, 3) float64 array in 0-1 range.
        path: Output file path.
        bit_depth: 8 or 16 (ignored for JPEG).
    """
    _require_pillow()
    path = Path(path)
    image = np.asarray(image, dtype=np.float64)
    image = np.clip(image, 0.0, 1.0)

    ext = path.suffix.lower()

    if ext in (".jpg", ".jpeg"):
        # JPEG is always 8-bit
        arr = (image * 255.0).round().astype(np.uint8)
        img = PILImage.fromarray(arr, mode="RGB")
        img.save(str(path), quality=95)

    elif bit_depth == 16:
        arr = (image * 65535.0).round().astype(np.uint16)
        img = PILImage.fromarray(arr, mode="I;16")
        # For 16-bit, we save each channel and reconstruct
        # Pillow handles 16-bit PNG and TIFF natively for mode I;16
        # but for RGB we need a different approach
        r = PILImage.fromarray(arr[..., 0], mode="I;16")
        g = PILImage.fromarray(arr[..., 1], mode="I;16")
        b = PILImage.fromarray(arr[..., 2], mode="I;16")
        img = PILImage.merge("RGB", [
            r.convert("I"),
            g.convert("I"),
            b.convert("I"),
        ])
        # For 16-bit, use TIFF or PNG
        if ext in (".tif", ".tiff"):
            img.save(str(path), compression="tiff_deflate")
        else:
            img.save(str(path))

    else:
        arr = (image * 255.0).round().astype(np.uint8)
        img = PILImage.fromarray(arr, mode="RGB")
        if ext in (".tif", ".tiff"):
            img.save(str(path), compression="tiff_deflate")
        else:
            img.save(str(path))


def resize_for_preview(
    image: np.ndarray,
    max_dim: int = 1024,
) -> np.ndarray:
    """
    Downscale an image so its largest dimension is at most max_dim.

    Uses Lanczos resampling. If the image is already smaller than
    max_dim, it is returned unchanged.

    Args:
        image: (H, W, 3) float64 array.
        max_dim: Maximum width or height (default 1024).

    Returns:
        Resized (H', W', 3) float64 array.
    """
    _require_pillow()
    image = np.asarray(image, dtype=np.float64)
    h, w = image.shape[:2]

    if max(h, w) <= max_dim:
        return image

    scale = max_dim / max(h, w)
    new_w = max(1, int(round(w * scale)))
    new_h = max(1, int(round(h * scale)))

    # Convert to uint8 for Pillow resize, then back to float
    arr_uint8 = np.clip(image * 255, 0, 255).astype(np.uint8)
    img = PILImage.fromarray(arr_uint8, mode="RGB")
    img = img.resize((new_w, new_h), PILImage.Resampling.LANCZOS)

    return np.asarray(img, dtype=np.float64) / 255.0


def get_image_info(path: Union[str, Path]) -> dict:
    """
    Get basic image metadata without loading full pixel data.

    Args:
        path: Path to image file.

    Returns:
        dict with keys: width, height, mode, format.
    """
    _require_pillow()
    path = Path(path)

    img = PILImage.open(path)
    info = {
        "width": img.width,
        "height": img.height,
        "mode": img.mode,
        "format": img.format,
    }
    img.close()

    return info
