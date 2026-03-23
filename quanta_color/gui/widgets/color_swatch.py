"""
Color Swatch Widget

A clickable color swatch that displays a solid color as a rounded rectangle.
Hover shows the hex value as a tooltip; left-click copies hex to clipboard;
right-click offers Copy Hex / Copy RGB / Copy Oklab.
"""

from PyQt6.QtWidgets import QWidget, QMenu, QApplication
from PyQt6.QtCore import Qt, QRectF
from PyQt6.QtGui import QColor, QPainter, QPen, QAction


class ColorSwatch(QWidget):
    """Configurable color swatch with copy-to-clipboard support."""

    def __init__(self, width: int = 100, height: int = 100, parent=None):
        super().__init__(parent)
        self.setFixedSize(width, height)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self._r = 0.5
        self._g = 0.5
        self._b = 0.5
        self._update_tooltip()

    # --- Public API ---

    def set_color(self, r: float, g: float, b: float):
        """Set the swatch color in 0-1 float range."""
        self._r = max(0.0, min(1.0, r))
        self._g = max(0.0, min(1.0, g))
        self._b = max(0.0, min(1.0, b))
        self._update_tooltip()
        self.update()

    # --- Internals ---

    def _hex(self) -> str:
        return "#{:02x}{:02x}{:02x}".format(
            int(self._r * 255 + 0.5),
            int(self._g * 255 + 0.5),
            int(self._b * 255 + 0.5),
        )

    def _rgb_str(self) -> str:
        return "rgb({}, {}, {})".format(
            int(self._r * 255 + 0.5),
            int(self._g * 255 + 0.5),
            int(self._b * 255 + 0.5),
        )

    def _oklab_str(self) -> str:
        """Approximate Oklab from linear sRGB."""
        # Linearize
        def lin(v):
            return v / 12.92 if v <= 0.04045 else ((v + 0.055) / 1.055) ** 2.4

        rl, gl, bl = lin(self._r), lin(self._g), lin(self._b)

        l_ = 0.4122214708 * rl + 0.5363325363 * gl + 0.0514459929 * bl
        m_ = 0.2119034982 * rl + 0.6806995451 * gl + 0.1073969566 * bl
        s_ = 0.0883024619 * rl + 0.2817188376 * gl + 0.6299787005 * bl

        l_c = l_ ** (1.0 / 3.0) if l_ >= 0 else -((-l_) ** (1.0 / 3.0))
        m_c = m_ ** (1.0 / 3.0) if m_ >= 0 else -((-m_) ** (1.0 / 3.0))
        s_c = s_ ** (1.0 / 3.0) if s_ >= 0 else -((-s_) ** (1.0 / 3.0))

        L = 0.2104542553 * l_c + 0.7936177850 * m_c - 0.0040720468 * s_c
        a = 1.9779984951 * l_c - 2.4285922050 * m_c + 0.4505937099 * s_c
        b = 0.0259040371 * l_c + 0.7827717662 * m_c - 0.8086757660 * s_c

        return f"oklab({L:.4f}, {a:.4f}, {b:.4f})"

    def _update_tooltip(self):
        self.setToolTip(self._hex())

    def _copy_to_clipboard(self, text: str):
        clipboard = QApplication.clipboard()
        if clipboard:
            clipboard.setText(text)

    # --- Events ---

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)

        # Border
        border_color = QColor("#ede4da")
        p.setPen(QPen(border_color, 1.5))

        # Fill
        fill = QColor.fromRgbF(self._r, self._g, self._b)
        p.setBrush(fill)

        radius = min(self.width(), self.height()) * 0.12
        rect = QRectF(1, 1, self.width() - 2, self.height() - 2)
        p.drawRoundedRect(rect, radius, radius)
        p.end()

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self._copy_to_clipboard(self._hex())

    def contextMenuEvent(self, event):
        menu = QMenu(self)

        hex_act = QAction(f"Copy Hex  ({self._hex()})", self)
        hex_act.triggered.connect(lambda: self._copy_to_clipboard(self._hex()))
        menu.addAction(hex_act)

        rgb_act = QAction(f"Copy RGB  ({self._rgb_str()})", self)
        rgb_act.triggered.connect(lambda: self._copy_to_clipboard(self._rgb_str()))
        menu.addAction(rgb_act)

        oklab_act = QAction(f"Copy Oklab", self)
        oklab_act.triggered.connect(lambda: self._copy_to_clipboard(self._oklab_str()))
        menu.addAction(oklab_act)

        menu.exec(event.globalPos())
