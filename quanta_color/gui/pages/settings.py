"""
Settings Page

Application preferences, about information, and keyboard shortcut reference.
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QLineEdit, QComboBox, QScrollArea, QFormLayout, QFileDialog,
    QGridLayout,
)
from PyQt6.QtCore import Qt

from quanta_color.gui.app import C, Card, Heading, Stat


class SettingsPage(QWidget):
    """Application settings, about info, and keyboard shortcuts."""

    def __init__(self, parent=None):
        super().__init__(parent)
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
        layout = QVBoxLayout(container)
        layout.setContentsMargins(32, 28, 32, 28)
        layout.setSpacing(20)

        layout.addWidget(Heading("Settings"))

        # --- Preferences Card ---
        pref_card, pref_lay = Card.with_layout()
        pref_lay.addWidget(Heading("Preferences", level=2))

        form = QFormLayout()
        form.setSpacing(12)
        form.setLabelAlignment(Qt.AlignmentFlag.AlignRight)

        # Default LUT size
        self._lut_size_combo = QComboBox()
        self._lut_size_combo.setStyleSheet(self._combo_style())
        self._lut_size_combo.setCursor(Qt.CursorShape.PointingHandCursor)
        for s in ["17", "33", "65"]:
            self._lut_size_combo.addItem(s)
        self._lut_size_combo.setCurrentText("33")
        lut_lbl = QLabel("Default LUT Size:")
        lut_lbl.setStyleSheet(f"font-size: 13px; color: {C.TEXT2};")
        form.addRow(lut_lbl, self._lut_size_combo)

        # Default export directory
        dir_row = QHBoxLayout()
        self._export_dir_edit = QLineEdit()
        self._export_dir_edit.setPlaceholderText("Select export directory...")
        self._export_dir_edit.setStyleSheet(
            f"font-family: 'Cascadia Code', 'Consolas', monospace; font-size: 13px; "
            f"padding: 4px 8px; border: 1px solid {C.BORDER}; border-radius: 6px; "
            f"background: {C.SURFACE2}; color: {C.TEXT};"
        )
        dir_row.addWidget(self._export_dir_edit, stretch=1)

        browse_btn = QPushButton("Browse")
        browse_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        browse_btn.setFixedHeight(32)
        browse_btn.setStyleSheet(f"""
            QPushButton {{
                background: {C.SURFACE2};
                border: 1px solid {C.BORDER};
                border-radius: 6px;
                padding: 0 14px;
                font-size: 12px;
                color: {C.TEXT};
            }}
            QPushButton:hover {{
                border-color: {C.ACCENT};
                color: {C.ACCENT_TX};
            }}
        """)
        browse_btn.clicked.connect(self._browse_export_dir)
        dir_row.addWidget(browse_btn)

        dir_lbl = QLabel("Export Directory:")
        dir_lbl.setStyleSheet(f"font-size: 13px; color: {C.TEXT2};")
        form.addRow(dir_lbl, dir_row)

        pref_lay.addLayout(form)
        layout.addWidget(pref_card)

        # --- About Card ---
        about_card, about_lay = Card.with_layout()
        about_lay.addWidget(Heading("About", level=2))

        about_items = [
            ("Quanta Color v1.0.0", f"font-size: 16px; font-weight: 600; color: {C.TEXT};"),
            ("Professional color science for Python", f"font-size: 13px; color: {C.TEXT2}; margin-bottom: 8px;"),
            ("Author: Zain Harper", f"font-size: 12px; color: {C.TEXT2};"),
            ("\u00a9 2026 Quanta Universe. All rights reserved.", f"font-size: 11px; color: {C.TEXT3};"),
        ]
        for text, style in about_items:
            lbl = QLabel(text)
            lbl.setStyleSheet(style)
            about_lay.addWidget(lbl)

        # Module status
        about_lay.addWidget(Heading("Modules", level=3))

        module_grid = QGridLayout()
        module_grid.setSpacing(6)

        module_names = [
            "spaces", "tonemap", "appearance", "difference",
            "adaptation", "spectral", "icc", "blindness",
            "gamut", "harmony",
        ]
        for i, name in enumerate(module_names):
            row, col = divmod(i, 5)
            status = self._check_module(name)
            dot_color = C.GREEN if status else C.RED
            lbl = QLabel(f"\u25cf {name}")
            lbl.setStyleSheet(
                f"font-size: 11px; color: {dot_color}; "
                f"font-family: 'Cascadia Code', 'Consolas', monospace;"
            )
            module_grid.addWidget(lbl, row, col)

        about_lay.addLayout(module_grid)
        layout.addWidget(about_card)

        # --- Keyboard Shortcuts Card ---
        shortcuts_card, shortcuts_lay = Card.with_layout()
        shortcuts_lay.addWidget(Heading("Keyboard Shortcuts", level=2))

        shortcuts = [
            ("Ctrl+1", "Dashboard"),
            ("Ctrl+2", "Image Analyzer"),
            ("Ctrl+3", "Color Inspector"),
            ("Ctrl+4", "LUT Workshop"),
            ("Ctrl+5", "Palette Studio"),
            ("Ctrl+6", "Settings"),
            ("Ctrl+O", "Open Image"),
            ("Ctrl+L", "Open LUT"),
            ("F5", "Refresh"),
            ("Escape", "Close"),
        ]

        grid = QGridLayout()
        grid.setSpacing(6)

        for i, (key, desc) in enumerate(shortcuts):
            row, col = divmod(i, 2)

            key_lbl = QLabel(key)
            key_lbl.setStyleSheet(
                f"font-size: 12px; font-weight: 600; color: {C.ACCENT_TX}; "
                f"font-family: 'Cascadia Code', 'Consolas', monospace; "
                f"background: {C.SURFACE2}; border: 1px solid {C.BORDER}; "
                f"border-radius: 4px; padding: 2px 8px;"
            )
            key_lbl.setFixedWidth(90)

            desc_lbl = QLabel(desc)
            desc_lbl.setStyleSheet(f"font-size: 12px; color: {C.TEXT2};")

            grid.addWidget(key_lbl, row, col * 2)
            grid.addWidget(desc_lbl, row, col * 2 + 1)

        shortcuts_lay.addLayout(grid)
        layout.addWidget(shortcuts_card)

        layout.addStretch()
        scroll.setWidget(container)
        outer.addWidget(scroll)

    # ------------------------------------------------------------------
    # Actions
    # ------------------------------------------------------------------

    def _browse_export_dir(self):
        path = QFileDialog.getExistingDirectory(self, "Select Export Directory")
        if path:
            self._export_dir_edit.setText(path)

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _check_module(name: str) -> bool:
        try:
            __import__(f"quanta_color.{name}")
            return True
        except Exception:
            return False

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
                min-width: 100px;
            }}
            QComboBox:hover {{ border-color: {C.ACCENT}; }}
            QComboBox::drop-down {{
                border: none;
                width: 24px;
            }}
        """
