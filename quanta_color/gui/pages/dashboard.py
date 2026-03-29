"""
Dashboard Page

Overview page with quick stats, navigation shortcuts,
and library information.
"""

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import (
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from quanta_color.gui.app import C, Card, Heading, Stat


class DashboardPage(QWidget):
    """Main dashboard with stats, quick actions, and library info."""

    navigate = pyqtSignal(int)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._build_ui()

    # ------------------------------------------------------------------
    # UI Construction
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

        # --- Page heading ---
        layout.addWidget(Heading("Dashboard"))

        # --- Stats row ---
        stats_card, stats_lay = Card.with_layout(QHBoxLayout, spacing=16)
        stats_lay.addWidget(Stat("Color Spaces", "16", C.ACCENT_TX))
        stats_lay.addWidget(Stat("Tone Mappers", "12", C.GREEN))
        stats_lay.addWidget(Stat("Adaptation Methods", "9", C.CYAN))
        layout.addWidget(stats_card)

        # --- Quick Actions ---
        actions_card, actions_lay = Card.with_layout()
        actions_lay.addWidget(Heading("Quick Actions", level=2))

        btn_row = QHBoxLayout()
        btn_row.setSpacing(12)

        actions = [
            ("Inspect Color", 2),
            ("Generate Palette", 4),
            ("Create LUT", 3),
            ("Open Settings", 5),
        ]
        for label, page_idx in actions:
            btn = self._make_action_button(label)
            btn.clicked.connect(lambda checked, idx=page_idx: self.navigate.emit(idx))
            btn_row.addWidget(btn)

        actions_lay.addLayout(btn_row)
        layout.addWidget(actions_card)

        # --- Library Info ---
        info_card, info_lay = Card.with_layout()
        info_lay.addWidget(Heading("Library Info", level=2))

        info_grid = QGridLayout()
        info_grid.setSpacing(8)

        info_items = [
            ("Version", "1.0.0"),
            ("Modules", self._count_modules()),
            ("Test Coverage", self._count_tests()),
        ]
        for col, (key, val) in enumerate(info_items):
            key_lbl = QLabel(key)
            key_lbl.setStyleSheet(f"font-size: 12px; color: {C.TEXT2};")
            val_lbl = QLabel(val)
            val_lbl.setStyleSheet(
                f"font-size: 13px; font-weight: 500; color: {C.TEXT}; "
                f"font-family: 'Cascadia Code', 'Consolas', monospace;"
            )
            info_grid.addWidget(key_lbl, 0, col)
            info_grid.addWidget(val_lbl, 1, col)

        info_lay.addLayout(info_grid)

        # Module list
        modules_lbl = QLabel(
            "spaces \u00b7 tonemap \u00b7 difference \u00b7 harmony \u00b7 "
            "blindness \u00b7 adaptation \u00b7 spectral \u00b7 appearance \u00b7 "
            "icc \u00b7 gamut"
        )
        modules_lbl.setWordWrap(True)
        modules_lbl.setStyleSheet(
            f"font-size: 12px; color: {C.TEXT3}; margin-top: 6px; font-family: 'Cascadia Code', 'Consolas', monospace;"
        )
        info_lay.addWidget(modules_lbl)
        layout.addWidget(info_card)

        # --- Stretch ---
        layout.addStretch()

        scroll.setWidget(container)
        outer.addWidget(scroll)

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _make_action_button(text: str) -> QPushButton:
        btn = QPushButton(text)
        btn.setCursor(Qt.CursorShape.PointingHandCursor)
        btn.setFixedHeight(38)
        btn.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        btn.setStyleSheet(f"""
            QPushButton {{
                background: {C.SURFACE2};
                border: 1px solid {C.BORDER};
                border-radius: 8px;
                padding: 0 16px;
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
        """)
        return btn

    @staticmethod
    def _count_modules() -> str:
        count = 0
        module_names = [
            "spaces",
            "tonemap",
            "difference",
            "harmony",
            "blindness",
            "adaptation",
            "spectral",
            "appearance",
            "icc",
            "gamut",
        ]
        for name in module_names:
            try:
                __import__(f"quanta_color.{name}")
                count += 1
            except Exception:
                pass
        return str(count)

    @staticmethod
    def _count_tests() -> str:
        try:
            from pathlib import Path

            test_dir = Path(__file__).resolve().parents[2] / "tests"
            if test_dir.is_dir():
                tests = list(test_dir.glob("test_*.py"))
                return f"{len(tests)} files"
        except Exception:
            pass
        return "\u2014"
