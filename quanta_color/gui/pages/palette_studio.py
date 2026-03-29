"""
Palette Studio Page

Generate harmonious color palettes from a base color, preview
under color vision deficiency simulations, and export as CSS/JSON.
"""

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QApplication,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from quanta_color.gui.app import C, Card, Heading
from quanta_color.gui.widgets.color_swatch import ColorSwatch


class PaletteStudioPage(QWidget):
    """Palette generation, CVD preview, and export workspace."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._base_r = 0.83
        self._base_g = 0.63
        self._base_b = 0.63
        self._palette_rgb = []  # list of (r, g, b) floats 0-1
        self._current_scheme = "complementary"
        self._build_ui()
        self._generate_palette()

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

        layout.addWidget(Heading("Palette Studio"))

        # --- Base Color Card ---
        base_card, base_lay = Card.with_layout(QHBoxLayout, spacing=16)

        self._base_swatch = ColorSwatch(80, 80)
        self._base_swatch.set_color(self._base_r, self._base_g, self._base_b)
        base_lay.addWidget(self._base_swatch)

        ctrl = QVBoxLayout()
        ctrl.setSpacing(8)

        lbl = QLabel("Base Color")
        lbl.setStyleSheet(f"font-size: 14px; font-weight: 600; color: {C.TEXT};")
        ctrl.addWidget(lbl)

        hex_row = QHBoxLayout()
        hex_lbl = QLabel("Hex:")
        hex_lbl.setStyleSheet(f"font-size: 13px; color: {C.TEXT2};")
        hex_row.addWidget(hex_lbl)

        self._hex_edit = QLineEdit("#d4a0a0")
        self._hex_edit.setMaximumWidth(120)
        self._hex_edit.setStyleSheet(
            f"font-family: 'Cascadia Code', 'Consolas', monospace; font-size: 14px; "
            f"padding: 4px 8px; border: 1px solid {C.BORDER}; border-radius: 6px; "
            f"background: {C.SURFACE2}; color: {C.TEXT};"
        )
        self._hex_edit.textEdited.connect(self._on_hex_changed)
        hex_row.addWidget(self._hex_edit)
        hex_row.addStretch()
        ctrl.addLayout(hex_row)

        base_lay.addLayout(ctrl, stretch=1)
        layout.addWidget(base_card)

        # --- Scheme Selector Card ---
        scheme_card, scheme_lay = Card.with_layout()
        scheme_lay.addWidget(Heading("Harmony Scheme", level=2))

        scheme_row = QHBoxLayout()
        scheme_row.setSpacing(8)

        self._scheme_buttons = {}
        scheme_names = self._get_scheme_names()
        for name in scheme_names:
            btn = QPushButton(name.replace("_", " ").title())
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.setCheckable(True)
            btn.setFixedHeight(34)
            btn.setStyleSheet(self._scheme_btn_style())
            btn.clicked.connect(lambda checked, n=name: self._on_scheme_clicked(n))
            scheme_row.addWidget(btn)
            self._scheme_buttons[name] = btn

        # Select default
        if "complementary" in self._scheme_buttons:
            self._scheme_buttons["complementary"].setChecked(True)

        scheme_lay.addLayout(scheme_row)
        layout.addWidget(scheme_card)

        # --- Palette Display Card ---
        self._palette_card, self._palette_lay = Card.with_layout()
        self._palette_lay.addWidget(Heading("Generated Palette", level=2))

        self._palette_row_widget = QWidget()
        self._palette_row_layout = QHBoxLayout(self._palette_row_widget)
        self._palette_row_layout.setSpacing(12)
        self._palette_row_layout.setContentsMargins(0, 0, 0, 0)
        self._palette_lay.addWidget(self._palette_row_widget)

        layout.addWidget(self._palette_card)

        # --- Accessibility Card ---
        access_card, access_lay = Card.with_layout()
        access_lay.addWidget(Heading("CVD Simulation", level=2))

        access_desc = QLabel("How the palette appears under color vision deficiency")
        access_desc.setStyleSheet(f"font-size: 12px; color: {C.TEXT3};")
        access_lay.addWidget(access_desc)

        self._cvd_container = QWidget()
        self._cvd_layout = QVBoxLayout(self._cvd_container)
        self._cvd_layout.setContentsMargins(0, 0, 0, 0)
        self._cvd_layout.setSpacing(10)
        access_lay.addWidget(self._cvd_container)

        layout.addWidget(access_card)

        # --- Export Card ---
        export_card, export_lay = Card.with_layout()
        export_lay.addWidget(Heading("Export", level=2))

        export_row = QHBoxLayout()
        export_row.setSpacing(12)

        css_btn = QPushButton("Copy CSS")
        css_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        css_btn.setFixedHeight(36)
        css_btn.setStyleSheet(self._secondary_btn_style())
        css_btn.clicked.connect(self._copy_css)
        export_row.addWidget(css_btn)

        json_btn = QPushButton("Copy JSON")
        json_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        json_btn.setFixedHeight(36)
        json_btn.setStyleSheet(self._secondary_btn_style())
        json_btn.clicked.connect(self._copy_json)
        export_row.addWidget(json_btn)

        export_row.addStretch()
        export_lay.addLayout(export_row)
        layout.addWidget(export_card)

        layout.addStretch()
        scroll.setWidget(container)
        outer.addWidget(scroll)

    # ------------------------------------------------------------------
    # Events
    # ------------------------------------------------------------------

    def _on_hex_changed(self, text: str):
        text = text.strip().lstrip("#")
        if len(text) != 6:
            return
        try:
            r = int(text[0:2], 16) / 255.0
            g = int(text[2:4], 16) / 255.0
            b = int(text[4:6], 16) / 255.0
        except ValueError:
            return
        self._base_r, self._base_g, self._base_b = r, g, b
        self._base_swatch.set_color(r, g, b)
        self._generate_palette()

    def _on_scheme_clicked(self, scheme: str):
        self._current_scheme = scheme
        for name, btn in self._scheme_buttons.items():
            btn.setChecked(name == scheme)
        self._generate_palette()

    # ------------------------------------------------------------------
    # Palette generation
    # ------------------------------------------------------------------

    def _generate_palette(self):
        import numpy as np

        base = np.array([self._base_r, self._base_g, self._base_b])

        try:
            from quanta_color.harmony import generate

            colors = generate(base, self._current_scheme)
            self._palette_rgb = [
                (float(np.clip(c[0], 0, 1)), float(np.clip(c[1], 0, 1)), float(np.clip(c[2], 0, 1))) for c in colors
            ]
        except Exception:
            # Fallback: simple hue rotation
            self._palette_rgb = [
                (float(self._base_r), float(self._base_g), float(self._base_b)),
                (float(self._base_g), float(self._base_b), float(self._base_r)),
                (float(self._base_b), float(self._base_r), float(self._base_g)),
            ]

        self._display_palette()
        self._display_cvd()

    def _display_palette(self):
        # Clear old swatches
        while self._palette_row_layout.count():
            item = self._palette_row_layout.takeAt(0)
            w = item.widget()
            if w:
                w.deleteLater()
            elif item.layout():
                self._clear_layout(item.layout())

        for r, g, b in self._palette_rgb[:12]:
            col = QVBoxLayout()
            col.setAlignment(Qt.AlignmentFlag.AlignCenter)
            sw = ColorSwatch(56, 56)
            sw.set_color(r, g, b)

            hex_str = f"#{int(r * 255 + 0.5):02x}{int(g * 255 + 0.5):02x}{int(b * 255 + 0.5):02x}"
            lbl = QLabel(hex_str)
            lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            lbl.setStyleSheet(
                f"font-size: 10px; color: {C.TEXT2}; font-family: 'Cascadia Code', 'Consolas', monospace;"
            )

            wrapper = QWidget()
            wrapper_lay = QVBoxLayout(wrapper)
            wrapper_lay.setContentsMargins(0, 0, 0, 0)
            wrapper_lay.setSpacing(4)
            wrapper_lay.addWidget(sw, alignment=Qt.AlignmentFlag.AlignCenter)
            wrapper_lay.addWidget(lbl)
            self._palette_row_layout.addWidget(wrapper)

        self._palette_row_layout.addStretch()

    def _display_cvd(self):
        # Clear old CVD rows
        while self._cvd_layout.count():
            item = self._cvd_layout.takeAt(0)
            w = item.widget()
            if w:
                w.deleteLater()

        cvd_types = [
            ("Normal", None),
            ("Protanopia", "protanopia"),
            ("Deuteranopia", "deuteranopia"),
            ("Tritanopia", "tritanopia"),
        ]

        for label, deficiency in cvd_types:
            row_widget = QWidget()
            row_lay = QHBoxLayout(row_widget)
            row_lay.setContentsMargins(0, 0, 0, 0)
            row_lay.setSpacing(6)

            type_lbl = QLabel(label)
            type_lbl.setFixedWidth(100)
            type_lbl.setStyleSheet(f"font-size: 11px; font-weight: 600; color: {C.TEXT2};")
            row_lay.addWidget(type_lbl)

            for r, g, b in self._palette_rgb[:12]:
                sw = ColorSwatch(28, 28)
                if deficiency is None:
                    sw.set_color(r, g, b)
                else:
                    try:
                        import numpy as np

                        from quanta_color.blindness import simulate

                        srgb = np.array([r, g, b])
                        sim = simulate(srgb, deficiency, severity=1.0)
                        sim = np.clip(sim, 0.0, 1.0)
                        sw.set_color(float(sim[0]), float(sim[1]), float(sim[2]))
                    except Exception:
                        sw.set_color(r, g, b)
                row_lay.addWidget(sw)

            row_lay.addStretch()
            self._cvd_layout.addWidget(row_widget)

    # ------------------------------------------------------------------
    # Export
    # ------------------------------------------------------------------

    def _copy_css(self):
        lines = [":root {"]
        for i, (r, g, b) in enumerate(self._palette_rgb):
            hex_str = f"#{int(r * 255 + 0.5):02x}{int(g * 255 + 0.5):02x}{int(b * 255 + 0.5):02x}"
            lines.append(f"  --color-{i + 1}: {hex_str};")
        lines.append("}")
        text = "\n".join(lines)
        clipboard = QApplication.clipboard()
        if clipboard:
            clipboard.setText(text)

    def _copy_json(self):
        import json

        data = []
        for r, g, b in self._palette_rgb:
            hex_str = f"#{int(r * 255 + 0.5):02x}{int(g * 255 + 0.5):02x}{int(b * 255 + 0.5):02x}"
            data.append(
                {
                    "hex": hex_str,
                    "rgb": [int(r * 255 + 0.5), int(g * 255 + 0.5), int(b * 255 + 0.5)],
                }
            )
        text = json.dumps(data, indent=2)
        clipboard = QApplication.clipboard()
        if clipboard:
            clipboard.setText(text)

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _get_scheme_names() -> list:
        try:
            from quanta_color.harmony import SCHEMES

            return list(SCHEMES.keys())
        except Exception:
            return [
                "complementary",
                "split_complementary",
                "triadic",
                "tetradic",
                "analogous",
                "monochromatic",
            ]

    @staticmethod
    def _clear_layout(layout):
        while layout.count():
            item = layout.takeAt(0)
            w = item.widget()
            if w:
                w.deleteLater()
            elif item.layout():
                PaletteStudioPage._clear_layout(item.layout())

    @staticmethod
    def _scheme_btn_style() -> str:
        return f"""
            QPushButton {{
                background: {C.SURFACE2};
                border: 1px solid {C.BORDER};
                border-radius: 8px;
                padding: 0 14px;
                font-size: 12px;
                font-weight: 500;
                color: {C.TEXT};
            }}
            QPushButton:hover {{
                border-color: {C.ACCENT};
                color: {C.ACCENT_TX};
            }}
            QPushButton:checked {{
                background: {C.ACCENT};
                color: #ffffff;
                border-color: {C.ACCENT};
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
