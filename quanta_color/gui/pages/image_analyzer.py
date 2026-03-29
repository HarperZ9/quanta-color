"""
Image Analyzer Page

Load an image and display preview, metadata, and optional
color analysis (gamut coverage, dominant colors) when available.
"""

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QPixmap
from PyQt6.QtWidgets import (
    QFileDialog,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from quanta_color.gui.app import C, Card, Heading
from quanta_color.gui.widgets.color_swatch import ColorSwatch


class ImageAnalyzerPage(QWidget):
    """Image loading, preview, and color analysis."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._image_path = None
        self._build_ui()

    # ------------------------------------------------------------------
    # UI
    # ------------------------------------------------------------------

    def _build_ui(self):
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QScrollArea.Shape.NoFrame)
        scroll.setStyleSheet(f"background: {C.BG};")

        container = QWidget()
        self._layout = QVBoxLayout(container)
        self._layout.setContentsMargins(32, 28, 32, 28)
        self._layout.setSpacing(20)

        self._layout.addWidget(Heading("Image Analyzer"))

        # --- Open Image Card ---
        open_card, open_lay = Card.with_layout(QHBoxLayout, spacing=12)

        open_btn = QPushButton("Open Image")
        open_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        open_btn.setFixedHeight(36)
        open_btn.setStyleSheet(f"""
            QPushButton {{
                background: {C.ACCENT};
                color: #ffffff;
                border: none;
                border-radius: 8px;
                padding: 0 20px;
                font-size: 13px;
                font-weight: 600;
            }}
            QPushButton:hover {{ background: {C.ACCENT_HI}; }}
            QPushButton:pressed {{ background: {C.ACCENT_TX}; }}
        """)
        open_btn.clicked.connect(self._open_image)
        open_lay.addWidget(open_btn)

        self._path_label = QLabel("No image loaded")
        self._path_label.setStyleSheet(
            f"font-size: 12px; color: {C.TEXT3}; font-family: 'Cascadia Code', 'Consolas', monospace;"
        )
        self._path_label.setWordWrap(True)
        open_lay.addWidget(self._path_label, stretch=1)

        self._layout.addWidget(open_card)

        # --- Preview Card (hidden until image loaded) ---
        self._preview_card, preview_lay = Card.with_layout()
        preview_lay.addWidget(Heading("Preview", level=2))

        self._preview_label = QLabel()
        self._preview_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._preview_label.setStyleSheet(f"background: {C.SURFACE2}; border-radius: 8px;")
        self._preview_label.setMinimumHeight(100)
        preview_lay.addWidget(self._preview_label)

        self._preview_card.setVisible(False)
        self._layout.addWidget(self._preview_card)

        # --- Image Info Card (hidden until image loaded) ---
        self._info_card, info_lay = Card.with_layout()
        info_lay.addWidget(Heading("Image Info", level=2))

        self._info_grid = QGridLayout()
        self._info_grid.setSpacing(8)
        self._info_labels = {}

        info_fields = ["Dimensions", "Format", "File Size"]
        for i, name in enumerate(info_fields):
            n_lbl = QLabel(f"{name}:")
            n_lbl.setStyleSheet(f"font-size: 12px; font-weight: 600; color: {C.TEXT2};")
            v_lbl = QLabel("\u2014")
            v_lbl.setStyleSheet(
                f"font-size: 13px; color: {C.TEXT}; font-family: 'Cascadia Code', 'Consolas', monospace;"
            )
            self._info_labels[name] = v_lbl
            self._info_grid.addWidget(n_lbl, i, 0)
            self._info_grid.addWidget(v_lbl, i, 1)

        info_lay.addLayout(self._info_grid)
        self._info_card.setVisible(False)
        self._layout.addWidget(self._info_card)

        # --- Analysis Card (hidden until analysis done) ---
        self._analysis_card, self._analysis_lay = Card.with_layout()
        self._analysis_lay.addWidget(Heading("Color Analysis", level=2))

        self._analysis_status = QLabel("")
        self._analysis_status.setStyleSheet(f"font-size: 12px; color: {C.TEXT2};")
        self._analysis_status.setWordWrap(True)
        self._analysis_lay.addWidget(self._analysis_status)

        self._dominant_row = QHBoxLayout()
        self._dominant_row.setSpacing(8)
        self._analysis_lay.addLayout(self._dominant_row)

        self._analysis_card.setVisible(False)
        self._layout.addWidget(self._analysis_card)

        self._layout.addStretch()
        scroll.setWidget(container)
        outer.addWidget(scroll)

    # ------------------------------------------------------------------
    # Actions
    # ------------------------------------------------------------------

    def _open_image(self):
        path, _ = QFileDialog.getOpenFileName(
            self,
            "Open Image",
            "",
            "Images (*.png *.jpg *.jpeg *.tif *.tiff *.bmp);;All Files (*)",
        )
        if not path:
            return

        self._image_path = path
        self._path_label.setText(path)
        self._load_preview(path)
        self._load_info(path)
        self._run_analysis(path)

    def _load_preview(self, path: str):
        pixmap = QPixmap(path)
        if pixmap.isNull():
            self._preview_label.setText("Failed to load image")
            self._preview_card.setVisible(True)
            return

        scaled = pixmap.scaledToWidth(
            min(600, pixmap.width()),
            Qt.TransformationMode.SmoothTransformation,
        )
        self._preview_label.setPixmap(scaled)
        self._preview_card.setVisible(True)

    def _load_info(self, path: str):
        import os

        pixmap = QPixmap(path)
        if not pixmap.isNull():
            self._info_labels["Dimensions"].setText(f"{pixmap.width()} \u00d7 {pixmap.height()} px")

        # Detect format from extension
        ext = os.path.splitext(path)[1].upper().lstrip(".")
        fmt_map = {"JPG": "JPEG", "TIF": "TIFF"}
        fmt = fmt_map.get(ext, ext)
        self._info_labels["Format"].setText(fmt)

        # File size
        try:
            size_bytes = os.path.getsize(path)
            if size_bytes < 1024:
                size_str = f"{size_bytes} B"
            elif size_bytes < 1024 * 1024:
                size_str = f"{size_bytes / 1024:.1f} KB"
            else:
                size_str = f"{size_bytes / (1024 * 1024):.2f} MB"
            self._info_labels["File Size"].setText(size_str)
        except Exception:
            self._info_labels["File Size"].setText("\u2014")

        self._info_card.setVisible(True)

    def _run_analysis(self, path: str):
        """Attempt color analysis; gracefully degrade if modules unavailable."""
        # Clear previous dominant swatches
        while self._dominant_row.count():
            item = self._dominant_row.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()

        try:
            import numpy as np
            from PIL import Image
        except ImportError:
            self._analysis_status.setText("Install Pillow for image analysis:  pip install Pillow")
            self._analysis_card.setVisible(True)
            return

        try:
            img = Image.open(path).convert("RGB")
            arr = np.array(img, dtype=np.float64) / 255.0

            # Basic stats
            h, w, _ = arr.shape
            pixel_count = h * w

            # Dominant colors via simple quantization
            small = img.resize((64, 64))
            small_arr = np.array(small).reshape(-1, 3)

            # K-means-like: find 6 cluster centers
            from collections import Counter

            quantized = (small_arr // 32) * 32 + 16
            tuples = [tuple(row) for row in quantized.tolist()]
            common = Counter(tuples).most_common(6)

            self._analysis_status.setText(f"Analyzed {pixel_count:,} pixels  \u2014  Top dominant colors:")

            for rgb_tuple, _count in common:
                col_layout = QVBoxLayout()
                col_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
                sw = ColorSwatch(48, 48)
                sw.set_color(rgb_tuple[0] / 255.0, rgb_tuple[1] / 255.0, rgb_tuple[2] / 255.0)
                col_layout.addWidget(sw, alignment=Qt.AlignmentFlag.AlignCenter)
                hex_lbl = QLabel(f"#{int(rgb_tuple[0]):02x}{int(rgb_tuple[1]):02x}{int(rgb_tuple[2]):02x}")
                hex_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
                hex_lbl.setStyleSheet(
                    f"font-size: 10px; color: {C.TEXT2}; font-family: 'Cascadia Code', 'Consolas', monospace;"
                )
                col_layout.addWidget(hex_lbl)
                self._dominant_row.addLayout(col_layout)

            self._dominant_row.addStretch()
            self._analysis_card.setVisible(True)

        except Exception as exc:
            self._analysis_status.setText(f"Analysis error: {exc}")
            self._analysis_card.setVisible(True)
