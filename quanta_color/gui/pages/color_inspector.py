"""
Color Inspector Page

Comprehensive color analysis tool with bidirectional input controls,
multi-space conversion, CVD simulation, and color difference metrics.
"""

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QScrollArea,
    QSlider,
    QVBoxLayout,
    QWidget,
)

from quanta_color.gui.app import C, Card, Heading
from quanta_color.gui.widgets.color_swatch import ColorSwatch

# CSS named colors for nearest-name fallback
_CSS_COLORS = {
    "black": (0, 0, 0),
    "white": (255, 255, 255),
    "red": (255, 0, 0),
    "lime": (0, 255, 0),
    "blue": (0, 0, 255),
    "yellow": (255, 255, 0),
    "cyan": (0, 255, 255),
    "magenta": (255, 0, 255),
    "silver": (192, 192, 192),
    "gray": (128, 128, 128),
    "maroon": (128, 0, 0),
    "olive": (128, 128, 0),
    "green": (0, 128, 0),
    "purple": (128, 0, 128),
    "teal": (0, 128, 128),
    "navy": (0, 0, 128),
    "orange": (255, 165, 0),
    "coral": (255, 127, 80),
    "salmon": (250, 128, 114),
    "gold": (255, 215, 0),
    "khaki": (240, 230, 140),
    "orchid": (218, 112, 214),
    "plum": (221, 160, 221),
    "violet": (238, 130, 238),
    "indigo": (75, 0, 130),
    "tomato": (255, 99, 71),
    "sienna": (160, 82, 45),
    "chocolate": (210, 105, 30),
    "peru": (205, 133, 63),
    "tan": (210, 180, 140),
    "pink": (255, 192, 203),
    "crimson": (220, 20, 60),
    "linen": (250, 240, 230),
    "beige": (245, 245, 220),
    "ivory": (255, 255, 240),
    "snow": (255, 250, 250),
    "honeydew": (240, 255, 240),
    "azure": (240, 255, 255),
    "lavender": (230, 230, 250),
    "wheat": (245, 222, 179),
    "cornsilk": (255, 248, 220),
    "bisque": (255, 228, 196),
    "mistyrose": (255, 228, 225),
    "seashell": (255, 245, 238),
    "mintcream": (245, 255, 250),
    "slategray": (112, 128, 144),
    "steelblue": (70, 130, 180),
    "royalblue": (65, 105, 225),
    "dodgerblue": (30, 144, 255),
    "skyblue": (135, 206, 235),
    "turquoise": (64, 224, 208),
    "springgreen": (0, 255, 127),
    "limegreen": (50, 205, 50),
    "forestgreen": (34, 139, 34),
    "darkgreen": (0, 100, 0),
    "darkred": (139, 0, 0),
    "firebrick": (178, 34, 34),
    "rosybrown": (188, 143, 143),
    "darkgoldenrod": (184, 134, 11),
    "goldenrod": (218, 165, 32),
}


def _nearest_css_name(r: int, g: int, b: int) -> str:
    """Find the closest CSS color name by Euclidean distance."""
    try:
        from quanta_color.naming import nearest_css_name

        return nearest_css_name(r, g, b)
    except Exception:
        pass
    best_name = "black"
    best_dist = float("inf")
    for name, (cr, cg, cb) in _CSS_COLORS.items():
        d = (r - cr) ** 2 + (g - cg) ** 2 + (b - cb) ** 2
        if d < best_dist:
            best_dist = d
            best_name = name
    return best_name


class ColorInspectorPage(QWidget):
    """Full-featured color inspector with multi-space display and CVD preview."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._updating = False
        self._r = 128
        self._g = 100
        self._b = 180
        self._build_ui()
        self._sync_from_rgb()

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

        layout.addWidget(Heading("Color Inspector"))

        # --- Input Card ---
        input_card, input_lay = Card.with_layout(QHBoxLayout, spacing=16)

        # Swatch
        self._swatch = ColorSwatch(120, 120)
        input_lay.addWidget(self._swatch)

        # Controls column
        ctrl_col = QVBoxLayout()
        ctrl_col.setSpacing(8)

        # Hex input
        hex_row = QHBoxLayout()
        hex_lbl = QLabel("Hex:")
        hex_lbl.setStyleSheet(f"font-size: 13px; color: {C.TEXT2};")
        hex_row.addWidget(hex_lbl)
        self._hex_edit = QLineEdit("#8064b4")
        self._hex_edit.setMaximumWidth(120)
        self._hex_edit.setStyleSheet(
            f"font-family: 'Cascadia Code', 'Consolas', monospace; font-size: 14px; "
            f"padding: 4px 8px; border: 1px solid {C.BORDER}; border-radius: 6px; "
            f"background: {C.SURFACE2}; color: {C.TEXT};"
        )
        self._hex_edit.textEdited.connect(self._on_hex_changed)
        hex_row.addWidget(self._hex_edit)

        # Color name
        self._name_lbl = QLabel("")
        self._name_lbl.setStyleSheet(f"font-size: 12px; color: {C.TEXT3}; font-style: italic;")
        hex_row.addWidget(self._name_lbl)
        hex_row.addStretch()
        ctrl_col.addLayout(hex_row)

        # RGB sliders
        slider_names = [("R", C.RED), ("G", C.GREEN), ("B", C.CYAN)]
        self._sliders = []
        self._slider_labels = []
        for name, color in slider_names:
            row = QHBoxLayout()
            lbl = QLabel(name)
            lbl.setFixedWidth(16)
            lbl.setStyleSheet(f"font-size: 12px; font-weight: 600; color: {color};")
            row.addWidget(lbl)

            slider = QSlider(Qt.Orientation.Horizontal)
            slider.setRange(0, 255)
            slider.setStyleSheet(self._slider_style(color))
            slider.valueChanged.connect(self._on_slider_changed)
            row.addWidget(slider)

            val_lbl = QLabel("128")
            val_lbl.setFixedWidth(32)
            val_lbl.setAlignment(Qt.AlignmentFlag.AlignRight)
            val_lbl.setStyleSheet(
                f"font-size: 12px; color: {C.TEXT}; font-family: 'Cascadia Code', 'Consolas', monospace;"
            )
            row.addWidget(val_lbl)

            self._sliders.append(slider)
            self._slider_labels.append(val_lbl)
            ctrl_col.addLayout(row)

        input_lay.addLayout(ctrl_col, stretch=1)
        layout.addWidget(input_card)

        # --- Color Spaces Card ---
        spaces_card, spaces_lay = Card.with_layout()
        spaces_lay.addWidget(Heading("Color Spaces", level=2))

        self._space_grid = QGridLayout()
        self._space_grid.setSpacing(6)
        self._space_labels = {}

        space_names = [
            "sRGB",
            "XYZ",
            "xyY",
            "Lab (D65)",
            "Oklab",
            "Oklch",
            "JzAzBz",
            "HSV",
        ]
        for i, name in enumerate(space_names):
            row, col = divmod(i, 2)
            name_lbl = QLabel(f"{name}:")
            name_lbl.setStyleSheet(f"font-size: 12px; font-weight: 600; color: {C.TEXT2};")
            val_lbl = QLabel("\u2014")
            val_lbl.setStyleSheet(
                f"font-size: 12px; color: {C.TEXT}; font-family: 'Cascadia Code', 'Consolas', monospace;"
            )
            val_lbl.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
            self._space_labels[name] = val_lbl
            self._space_grid.addWidget(name_lbl, row, col * 2)
            self._space_grid.addWidget(val_lbl, row, col * 2 + 1)

        spaces_lay.addLayout(self._space_grid)
        layout.addWidget(spaces_card)

        # --- Metrics Card ---
        metrics_card, metrics_lay = Card.with_layout()
        metrics_lay.addWidget(Heading("Metrics", level=2))

        self._metrics_grid = QGridLayout()
        self._metrics_grid.setSpacing(6)
        self._metric_labels = {}

        metric_names = [
            "Luminance",
            "Dominant WL",
            "Contrast (white)",
            "Contrast (black)",
            "WCAG Grade",
            "",
        ]
        for i, name in enumerate(metric_names):
            if not name:
                continue
            row, col = divmod(i, 2)
            n_lbl = QLabel(f"{name}:")
            n_lbl.setStyleSheet(f"font-size: 12px; font-weight: 600; color: {C.TEXT2};")
            v_lbl = QLabel("\u2014")
            v_lbl.setStyleSheet(
                f"font-size: 12px; color: {C.TEXT}; font-family: 'Cascadia Code', 'Consolas', monospace;"
            )
            self._metric_labels[name] = v_lbl
            self._metrics_grid.addWidget(n_lbl, row, col * 2)
            self._metrics_grid.addWidget(v_lbl, row, col * 2 + 1)

        metrics_lay.addLayout(self._metrics_grid)
        layout.addWidget(metrics_card)

        # --- CVD Preview Card ---
        cvd_card, cvd_lay = Card.with_layout()
        cvd_lay.addWidget(Heading("Color Vision Deficiency Preview", level=2))

        cvd_row = QHBoxLayout()
        cvd_row.setSpacing(16)
        self._cvd_swatches = {}
        for label in ["Normal", "Protan", "Deutan", "Tritan"]:
            col = QVBoxLayout()
            col.setAlignment(Qt.AlignmentFlag.AlignCenter)
            sw = ColorSwatch(60, 60)
            col.addWidget(sw, alignment=Qt.AlignmentFlag.AlignCenter)
            lbl = QLabel(label)
            lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            lbl.setStyleSheet(f"font-size: 11px; color: {C.TEXT2};")
            col.addWidget(lbl)
            self._cvd_swatches[label] = sw
            cvd_row.addLayout(col)
        cvd_row.addStretch()

        cvd_lay.addLayout(cvd_row)
        layout.addWidget(cvd_card)

        # --- Color Difference Card ---
        diff_card, diff_lay = Card.with_layout()
        diff_lay.addWidget(Heading("Color Difference", level=2))

        comp_row = QHBoxLayout()
        comp_lbl = QLabel("Compare with:")
        comp_lbl.setStyleSheet(f"font-size: 13px; color: {C.TEXT2};")
        comp_row.addWidget(comp_lbl)
        self._hex2_edit = QLineEdit("#ffffff")
        self._hex2_edit.setMaximumWidth(120)
        self._hex2_edit.setStyleSheet(
            f"font-family: 'Cascadia Code', 'Consolas', monospace; font-size: 14px; "
            f"padding: 4px 8px; border: 1px solid {C.BORDER}; border-radius: 6px; "
            f"background: {C.SURFACE2}; color: {C.TEXT};"
        )
        self._hex2_edit.textEdited.connect(self._update_difference)
        comp_row.addWidget(self._hex2_edit)

        self._swatch2 = ColorSwatch(40, 40)
        self._swatch2.set_color(1.0, 1.0, 1.0)
        comp_row.addWidget(self._swatch2)
        comp_row.addStretch()
        diff_lay.addLayout(comp_row)

        self._diff_grid = QGridLayout()
        self._diff_grid.setSpacing(6)
        self._diff_labels = {}
        diff_names = ["CIE76", "CIE94", "CIEDE2000", "CMC(2:1)", "HyAB"]
        for i, name in enumerate(diff_names):
            row, col = divmod(i, 3)
            n_lbl = QLabel(f"\u0394E {name}:")
            n_lbl.setStyleSheet(f"font-size: 12px; font-weight: 600; color: {C.TEXT2};")
            v_lbl = QLabel("\u2014")
            v_lbl.setStyleSheet(
                f"font-size: 13px; color: {C.TEXT}; font-family: 'Cascadia Code', 'Consolas', monospace;"
            )
            self._diff_labels[name] = v_lbl
            self._diff_grid.addWidget(n_lbl, row, col * 2)
            self._diff_grid.addWidget(v_lbl, row, col * 2 + 1)

        diff_lay.addLayout(self._diff_grid)
        layout.addWidget(diff_card)

        layout.addStretch()
        scroll.setWidget(container)
        outer.addWidget(scroll)

    # ------------------------------------------------------------------
    # Sync logic
    # ------------------------------------------------------------------

    def _on_hex_changed(self, text: str):
        if self._updating:
            return
        text = text.strip().lstrip("#")
        if len(text) != 6:
            return
        try:
            r = int(text[0:2], 16)
            g = int(text[2:4], 16)
            b = int(text[4:6], 16)
        except ValueError:
            return
        self._r, self._g, self._b = r, g, b
        self._sync_from_rgb()

    def _on_slider_changed(self):
        if self._updating:
            return
        self._r = self._sliders[0].value()
        self._g = self._sliders[1].value()
        self._b = self._sliders[2].value()
        self._sync_from_rgb()

    def _sync_from_rgb(self):
        self._updating = True
        try:
            r, g, b = self._r, self._g, self._b
            rf, gf, bf = r / 255.0, g / 255.0, b / 255.0

            # Update swatch
            self._swatch.set_color(rf, gf, bf)

            # Update hex
            hex_str = f"#{r:02x}{g:02x}{b:02x}"
            self._hex_edit.setText(hex_str)

            # Update sliders
            for i, val in enumerate([r, g, b]):
                self._sliders[i].setValue(val)
                self._slider_labels[i].setText(str(val))

            # Update color name
            self._name_lbl.setText(_nearest_css_name(r, g, b))

            # Update color spaces
            self._update_spaces(rf, gf, bf)

            # Update metrics
            self._update_metrics(rf, gf, bf)

            # Update CVD
            self._update_cvd(rf, gf, bf)

            # Update difference
            self._update_difference()
        finally:
            self._updating = False

    # ------------------------------------------------------------------
    # Color space conversions
    # ------------------------------------------------------------------

    def _update_spaces(self, r: float, g: float, b: float):
        try:
            import numpy as np

            from quanta_color import spaces

            srgb = np.array([r, g, b])

            self._space_labels["sRGB"].setText(f"({r:.3f}, {g:.3f}, {b:.3f})")

            xyz = spaces.srgb_to_xyz(srgb)
            self._space_labels["XYZ"].setText(f"({xyz[0]:.4f}, {xyz[1]:.4f}, {xyz[2]:.4f})")

            xyY = spaces.xyz_to_xyY(xyz)
            self._space_labels["xyY"].setText(f"({xyY[0]:.4f}, {xyY[1]:.4f}, {xyY[2]:.4f})")

            lab = spaces.xyz_to_lab(xyz, white=spaces.D65)
            self._space_labels["Lab (D65)"].setText(f"({lab[0]:.2f}, {lab[1]:.2f}, {lab[2]:.2f})")

            oklab = spaces.srgb_to_oklab(srgb)
            self._space_labels["Oklab"].setText(f"({oklab[0]:.4f}, {oklab[1]:.4f}, {oklab[2]:.4f})")

            oklch = spaces.oklab_to_oklch(oklab)
            self._space_labels["Oklch"].setText(f"({oklch[0]:.4f}, {oklch[1]:.4f}, {oklch[2]:.1f})")

            jzazbz = spaces.xyz_to_jzazbz(xyz)
            self._space_labels["JzAzBz"].setText(f"({jzazbz[0]:.4f}, {jzazbz[1]:.4f}, {jzazbz[2]:.4f})")

            hsv = spaces.rgb_to_hsv(srgb)
            self._space_labels["HSV"].setText(f"({hsv[0]:.1f}\u00b0, {hsv[1]:.1%}, {hsv[2]:.1%})")

        except Exception:
            for lbl in self._space_labels.values():
                lbl.setText("\u2014")

    def _update_metrics(self, r: float, g: float, b: float):
        try:
            import numpy as np

            from quanta_color import difference, spaces

            srgb = np.array([r, g, b])
            xyz = spaces.srgb_to_xyz(srgb)

            # Relative luminance (Y)
            lum = xyz[1]
            self._metric_labels["Luminance"].setText(f"{lum:.4f}")

            # Dominant wavelength — approximate from xy chromaticity
            xyY = spaces.xyz_to_xyY(xyz)
            x, y = xyY[0], xyY[1]
            # Simplified dominant wavelength from chromaticity
            if y > 0:
                import math

                angle = math.atan2(y - 0.3333, x - 0.3333)
                wl = 475 + (angle + math.pi) / (2 * math.pi) * 300
                wl = wl % 700
                if wl < 380:
                    wl += 380
                self._metric_labels["Dominant WL"].setText(f"~{wl:.0f} nm")
            else:
                self._metric_labels["Dominant WL"].setText("\u2014")

            # Contrast ratios
            L = lum
            white_cr = difference.contrast_ratio(1.0, L)
            black_cr = difference.contrast_ratio(L, 0.0)
            self._metric_labels["Contrast (white)"].setText(f"{white_cr:.2f}:1")
            self._metric_labels["Contrast (black)"].setText(f"{black_cr:.2f}:1")

            # WCAG grade
            cr = max(white_cr, black_cr)
            if cr >= 7.0:
                grade = "AAA"
            elif cr >= 4.5:
                grade = "AA"
            elif cr >= 3.0:
                grade = "AA Large"
            else:
                grade = "Fail"
            self._metric_labels["WCAG Grade"].setText(grade)

        except Exception:
            for lbl in self._metric_labels.values():
                lbl.setText("\u2014")

    def _update_cvd(self, r: float, g: float, b: float):
        self._cvd_swatches["Normal"].set_color(r, g, b)
        try:
            import numpy as np

            from quanta_color.blindness import simulate

            srgb = np.array([r, g, b])
            for label, deficiency in [
                ("Protan", "protanopia"),
                ("Deutan", "deuteranopia"),
                ("Tritan", "tritanopia"),
            ]:
                sim = simulate(srgb, deficiency, severity=1.0)
                sim = np.clip(sim, 0.0, 1.0)
                self._cvd_swatches[label].set_color(float(sim[0]), float(sim[1]), float(sim[2]))
        except Exception:
            for label in ["Protan", "Deutan", "Tritan"]:
                self._cvd_swatches[label].set_color(r, g, b)

    def _update_difference(self):
        text = self._hex2_edit.text().strip().lstrip("#")
        if len(text) != 6:
            return
        try:
            r2 = int(text[0:2], 16)
            g2 = int(text[2:4], 16)
            b2 = int(text[4:6], 16)
        except ValueError:
            return

        rf2, gf2, bf2 = r2 / 255.0, g2 / 255.0, b2 / 255.0
        self._swatch2.set_color(rf2, gf2, bf2)

        try:
            import numpy as np

            from quanta_color import difference, spaces

            srgb1 = np.array([self._r / 255.0, self._g / 255.0, self._b / 255.0])
            srgb2 = np.array([rf2, gf2, bf2])

            xyz1 = spaces.srgb_to_xyz(srgb1)
            xyz2 = spaces.srgb_to_xyz(srgb2)
            lab1 = spaces.xyz_to_lab(xyz1, white=spaces.D65)
            lab2 = spaces.xyz_to_lab(xyz2, white=spaces.D65)

            results = difference.compare_all(lab1, lab2)
            for name, val in results.items():
                if name in self._diff_labels:
                    self._diff_labels[name].setText(f"{val:.4f}")
        except Exception:
            for lbl in self._diff_labels.values():
                lbl.setText("\u2014")

    # ------------------------------------------------------------------
    # Slider styling
    # ------------------------------------------------------------------

    @staticmethod
    def _slider_style(color: str) -> str:
        return f"""
            QSlider::groove:horizontal {{
                background: {C.SURFACE2};
                height: 6px;
                border-radius: 3px;
                border: 1px solid {C.BORDER};
            }}
            QSlider::handle:horizontal {{
                background: {color};
                width: 16px;
                height: 16px;
                margin: -6px 0;
                border-radius: 8px;
                border: 2px solid {C.SURFACE};
            }}
            QSlider::sub-page:horizontal {{
                background: {color};
                border-radius: 3px;
            }}
        """
