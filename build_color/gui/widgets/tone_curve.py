"""
Tone Curve Widget

QPainter widget that draws a tone mapping response curve with grid,
identity diagonal, and the actual curve data.  Uses the shared C palette.
"""

from PyQt6.QtCore import QPointF, QRectF, Qt
from PyQt6.QtGui import QColor, QFont, QPainter, QPainterPath, QPen
from PyQt6.QtWidgets import QWidget


# Import C from the app module (lazy to avoid circular imports at module level)
def _C():
    from build_color.gui.app import C

    return C


class ToneCurve(QWidget):
    """Displays a tone mapping response curve inside a styled panel."""

    def __init__(self, width: int = 260, height: int = 260, parent=None):
        super().__init__(parent)
        self.setFixedSize(width, height)
        self._input: list[float] = []
        self._output: list[float] = []

    # --- Public API ---

    def set_data(self, input_values: list[float], output_values: list[float]):
        """
        Set the curve data.

        Args:
            input_values:  Normalized 0-1 input levels (monotonically increasing).
            output_values: Normalized 0-1 output levels corresponding to inputs.
        """
        self._input = list(input_values)
        self._output = list(output_values)
        self.update()

    # --- Painting ---

    def paintEvent(self, event):
        C = _C()
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)

        w = self.width()
        h = self.height()

        margin_l = 36
        margin_b = 24
        margin_t = 12
        margin_r = 12

        plot_x = margin_l
        plot_y = margin_t
        plot_w = w - margin_l - margin_r
        plot_h = h - margin_t - margin_b

        # Background
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(QColor(C.SURFACE))
        p.drawRoundedRect(0, 0, w, h, 10, 10)

        # Border
        p.setPen(QPen(QColor(C.BORDER), 1))
        p.setBrush(Qt.BrushStyle.NoBrush)
        p.drawRoundedRect(0, 0, w, h, 10, 10)

        # Grid lines (5 divisions)
        grid_pen = QPen(QColor(C.BORDER), 0.5, Qt.PenStyle.DotLine)
        p.setPen(grid_pen)
        divisions = 4
        for i in range(1, divisions):
            frac = i / divisions
            # Horizontal
            gy = plot_y + plot_h * (1.0 - frac)
            p.drawLine(QPointF(plot_x, gy), QPointF(plot_x + plot_w, gy))
            # Vertical
            gx = plot_x + plot_w * frac
            p.drawLine(QPointF(gx, plot_y), QPointF(gx, plot_y + plot_h))

        # Axis labels
        label_font = QFont("Segoe UI", 8)
        p.setFont(label_font)
        p.setPen(QColor(C.TEXT3))

        for i in range(divisions + 1):
            frac = i / divisions
            val_str = f"{frac:.1f}"

            # Y-axis (left)
            ly = plot_y + plot_h * (1.0 - frac)
            p.drawText(
                QRectF(0, ly - 7, margin_l - 4, 14),
                Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter,
                val_str,
            )

            # X-axis (bottom)
            lx = plot_x + plot_w * frac
            p.drawText(
                QRectF(lx - 16, plot_y + plot_h + 4, 32, 16),
                Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignTop,
                val_str,
            )

        # Identity diagonal (thin, dashed)
        diag_pen = QPen(QColor(C.TEXT3), 1, Qt.PenStyle.DashLine)
        p.setPen(diag_pen)
        p.drawLine(
            QPointF(plot_x, plot_y + plot_h),
            QPointF(plot_x + plot_w, plot_y),
        )

        # Curve
        if len(self._input) >= 2 and len(self._input) == len(self._output):
            curve_pen = QPen(QColor(C.ACCENT_TX), 2.0)
            curve_pen.setCapStyle(Qt.PenCapStyle.RoundCap)
            curve_pen.setJoinStyle(Qt.PenJoinStyle.RoundJoin)
            p.setPen(curve_pen)
            p.setBrush(Qt.BrushStyle.NoBrush)

            path = QPainterPath()
            for i, (iv, ov) in enumerate(zip(self._input, self._output)):
                px = plot_x + iv * plot_w
                py = plot_y + (1.0 - ov) * plot_h
                if i == 0:
                    path.moveTo(px, py)
                else:
                    path.lineTo(px, py)
            p.drawPath(path)

        p.end()
