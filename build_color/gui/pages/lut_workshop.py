"""
LUT Workshop Page

Generate, preview, and export Look-Up Tables using
the tone mapping operators from build_color.tonemap.
"""

import numpy as np
from PyQt6.QtCore import QRectF, Qt
from PyQt6.QtGui import QColor, QLinearGradient, QPainter
from PyQt6.QtWidgets import (
    QComboBox,
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from build_color.gui.app import C, Card, Heading
from build_color.gui.widgets.tone_curve import ToneCurve


class GradientPreview(QWidget):
    """Horizontal gradient bar showing input mapped through a tone operator."""

    def __init__(self, width: int = 400, height: int = 40, parent=None):
        super().__init__(parent)
        self.setFixedSize(width, height)
        self._mapped: np.ndarray | None = None  # numpy array of mapped 0-1 values

    def set_mapping(self, mapped: np.ndarray):
        """Set mapped output values (same length as pixel columns)."""
        self._mapped = mapped
        self.update()

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)

        w = self.width()
        h = self.height()

        # Background
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(QColor(C.SURFACE2))
        p.drawRoundedRect(0, 0, w, h, 6, 6)

        if self._mapped is not None and len(self._mapped) > 0:
            # Draw column by column
            n = len(self._mapped)
            col_w = w / n
            for i in range(n):
                v = float(np.clip(self._mapped[i], 0.0, 1.0))
                color = QColor.fromRgbF(v, v, v)
                p.setBrush(color)
                p.drawRect(QRectF(i * col_w, 0, col_w + 1, h))
        else:
            # Default: linear gradient
            grad = QLinearGradient(0, 0, w, 0)
            grad.setColorAt(0.0, QColor(0, 0, 0))
            grad.setColorAt(1.0, QColor(255, 255, 255))
            p.setBrush(grad)
            p.drawRoundedRect(0, 0, w, h, 6, 6)

        # Border
        from PyQt6.QtGui import QPen

        p.setBrush(Qt.BrushStyle.NoBrush)
        p.setPen(QPen(QColor(C.BORDER), 1))
        p.drawRoundedRect(0, 0, w, h, 6, 6)

        p.end()


class LUTWorkshopPage(QWidget):
    """LUT generation, preview, and export workspace."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._lut_data: np.ndarray | None = None
        self._lut_size = 33
        self._build_ui()
        self._update_preview()

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
        layout = QVBoxLayout(container)
        layout.setContentsMargins(32, 28, 32, 28)
        layout.setSpacing(20)

        layout.addWidget(Heading("LUT Workshop"))

        # --- Transform Settings Card ---
        settings_card, settings_lay = Card.with_layout()
        settings_lay.addWidget(Heading("Transform Settings", level=2))

        row1 = QHBoxLayout()
        row1.setSpacing(12)

        # Operator combo
        op_lbl = QLabel("Tone Map:")
        op_lbl.setStyleSheet(f"font-size: 13px; color: {C.TEXT2};")
        row1.addWidget(op_lbl)

        self._op_combo = QComboBox()
        self._op_combo.setStyleSheet(self._combo_style())
        self._op_combo.setCursor(Qt.CursorShape.PointingHandCursor)
        self._load_operators()
        self._op_combo.currentTextChanged.connect(lambda: self._update_preview())
        row1.addWidget(self._op_combo)

        # Size combo
        size_lbl = QLabel("LUT Size:")
        size_lbl.setStyleSheet(f"font-size: 13px; color: {C.TEXT2};")
        row1.addWidget(size_lbl)

        self._size_combo = QComboBox()
        self._size_combo.setStyleSheet(self._combo_style())
        self._size_combo.setCursor(Qt.CursorShape.PointingHandCursor)
        for s in ["17", "33", "65"]:
            self._size_combo.addItem(s)
        self._size_combo.setCurrentText("33")
        row1.addWidget(self._size_combo)

        row1.addStretch()

        # Generate button
        gen_btn = QPushButton("Generate LUT")
        gen_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        gen_btn.setFixedHeight(36)
        gen_btn.setStyleSheet(f"""
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
        gen_btn.clicked.connect(self._generate_lut)
        row1.addWidget(gen_btn)

        settings_lay.addLayout(row1)
        layout.addWidget(settings_card)

        # --- Tone Curve Preview Card ---
        curve_card, curve_lay = Card.with_layout()
        curve_lay.addWidget(Heading("Tone Curve Preview", level=2))

        self._tone_curve = ToneCurve(320, 260)
        curve_lay.addWidget(self._tone_curve, alignment=Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(curve_card)

        # --- Gradient Preview Card ---
        grad_card, grad_lay = Card.with_layout()
        grad_lay.addWidget(Heading("Gradient Preview", level=2))

        grad_desc = QLabel("Input 0\u20141 mapped through the selected operator")
        grad_desc.setStyleSheet(f"font-size: 12px; color: {C.TEXT3};")
        grad_lay.addWidget(grad_desc)

        self._gradient = GradientPreview(400, 40)
        grad_lay.addWidget(self._gradient, alignment=Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(grad_card)

        # --- Export Card ---
        export_card, export_lay = Card.with_layout()
        export_lay.addWidget(Heading("Export", level=2))

        export_row = QHBoxLayout()
        export_row.setSpacing(12)

        cube_btn = QPushButton("Export .cube")
        cube_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        cube_btn.setFixedHeight(36)
        cube_btn.setStyleSheet(self._secondary_btn_style())
        cube_btn.clicked.connect(lambda: self._export_lut("cube"))
        export_row.addWidget(cube_btn)

        clf_btn = QPushButton("Export .clf")
        clf_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        clf_btn.setFixedHeight(36)
        clf_btn.setStyleSheet(self._secondary_btn_style())
        clf_btn.clicked.connect(lambda: self._export_lut("clf"))
        export_row.addWidget(clf_btn)

        export_row.addStretch()
        export_lay.addLayout(export_row)
        layout.addWidget(export_card)

        # --- Status ---
        self._status_label = QLabel("")
        self._status_label.setStyleSheet(f"font-size: 12px; color: {C.TEXT2};")
        self._status_label.setWordWrap(True)
        layout.addWidget(self._status_label)

        layout.addStretch()
        scroll.setWidget(container)
        outer.addWidget(scroll)

    # ------------------------------------------------------------------
    # Operators
    # ------------------------------------------------------------------

    def _load_operators(self):
        try:
            from build_color.tonemap import OPERATORS

            for name in OPERATORS:
                self._op_combo.addItem(name)
        except Exception:
            for name in [
                "reinhard",
                "reinhard_extended",
                "aces",
                "aces_hill",
                "hable",
                "lottes",
                "uchimura",
                "agx",
                "pbr_neutral",
                "bt2390",
                "bt2446",
                "knee",
            ]:
                self._op_combo.addItem(name)

    # ------------------------------------------------------------------
    # Preview
    # ------------------------------------------------------------------

    def _update_preview(self):
        op_name = self._op_combo.currentText()
        if not op_name:
            return

        try:
            from build_color.tonemap import OPERATORS

            op_fn = OPERATORS.get(op_name)
        except Exception:
            op_fn = None

        n = 256
        x = np.linspace(0.0, 1.0, n)

        if op_fn is not None:
            try:
                y = op_fn(x)
                y = np.clip(np.asarray(y, dtype=np.float64), 0.0, 1.0)
            except Exception:
                y = x.copy()
        else:
            y = x.copy()

        self._tone_curve.set_data(x.tolist(), y.tolist())
        self._gradient.set_mapping(y)

    # ------------------------------------------------------------------
    # Generate
    # ------------------------------------------------------------------

    def _generate_lut(self):
        op_name = self._op_combo.currentText()
        size = int(self._size_combo.currentText())
        self._lut_size = size

        try:
            from build_color.tonemap import OPERATORS

            op_fn = OPERATORS.get(op_name)
        except Exception:
            op_fn = None

        if op_fn is None:
            self._status_label.setText(f"Operator '{op_name}' not available.")
            return

        # Build 3D LUT (size^3 entries)
        grid = np.linspace(0.0, 1.0, size)
        lut = np.zeros((size, size, size, 3))
        for ri in range(size):
            for gi in range(size):
                for bi in range(size):
                    rgb = np.array([grid[ri], grid[gi], grid[bi]])
                    try:
                        mapped = op_fn(rgb)
                        mapped = np.clip(mapped, 0.0, 1.0)
                    except Exception:
                        mapped = rgb
                    lut[ri, gi, bi] = mapped

        self._lut_data = lut
        total = size**3
        self._status_label.setText(f"Generated {size}\u00b3 LUT ({total:,} entries) using {op_name} operator.")
        self._update_preview()

    # ------------------------------------------------------------------
    # Export
    # ------------------------------------------------------------------

    def _export_lut(self, fmt: str):
        if self._lut_data is None:
            self._status_label.setText("Generate a LUT first before exporting.")
            return

        if fmt == "cube":
            ext_filter = "Cube LUT (*.cube)"
            default_ext = ".cube"
        else:
            ext_filter = "CLF LUT (*.clf)"
            default_ext = ".clf"

        path, _ = QFileDialog.getSaveFileName(self, f"Export {fmt.upper()}", f"build_lut{default_ext}", ext_filter)
        if not path:
            return

        try:
            # Try library exporter first
            from build_color.lut_io import LUT3D, write_clf, write_cube

            lut3d = LUT3D(data=self._lut_data, size=self._lut_size)
            if fmt == "cube":
                write_cube(lut3d, path)
            else:
                write_clf(lut3d, path)
            self._status_label.setText(f"Exported to {path}")
        except ImportError:
            # Fallback: write basic .cube format manually
            if fmt == "cube":
                self._write_cube_fallback(path)
            else:
                self._status_label.setText("CLF export requires the lut_io module. Try .cube instead.")
        except Exception as exc:
            self._status_label.setText(f"Export error: {exc}")

    def _write_cube_fallback(self, path: str):
        """Write a basic .cube file without the lut_io module."""
        size = self._lut_size
        lut = self._lut_data
        try:
            with open(path, "w") as f:
                f.write("# Generated by Build Color\n")
                f.write('TITLE "Build Color LUT"\n')
                f.write(f"LUT_3D_SIZE {size}\n")
                f.write("DOMAIN_MIN 0.0 0.0 0.0\n")
                f.write("DOMAIN_MAX 1.0 1.0 1.0\n\n")
                for bi in range(size):
                    for gi in range(size):
                        for ri in range(size):
                            r, g, b = lut[ri, gi, bi]
                            f.write(f"{r:.6f} {g:.6f} {b:.6f}\n")
            self._status_label.setText(f"Exported to {path}")
        except Exception as exc:
            self._status_label.setText(f"Export error: {exc}")

    # ------------------------------------------------------------------
    # Styling helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _combo_style() -> str:
        return f"""
            QComboBox {{
                background: {C.SURFACE2};
                border: 1px solid {C.BORDER};
                border-radius: 6px;
                padding: 4px 12px;
                font-size: 13px;
                color: {C.TEXT};
                min-width: 120px;
            }}
            QComboBox:hover {{ border-color: {C.ACCENT}; }}
            QComboBox::drop-down {{
                border: none;
                width: 24px;
            }}
        """

    @staticmethod
    def _secondary_btn_style() -> str:
        return f"""
            QPushButton {{
                background: {C.SURFACE2};
                border: 1px solid {C.BORDER};
                border-radius: 8px;
                padding: 0 20px;
                font-size: 13px;
                font-weight: 500;
                color: {C.TEXT};
            }}
            QPushButton:hover {{
                background: {C.ACCENT};
                color: #ffffff;
                border-color: {C.ACCENT};
            }}
            QPushButton:pressed {{
                background: {C.ACCENT_TX};
                color: #ffffff;
            }}
        """
