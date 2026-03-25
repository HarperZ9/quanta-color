"""
Quanta Color — Main Application

Professional color science workbench with sidebar navigation,
page transitions, and the shared Calibrate Pro visual framework.
"""

import logging
import sys
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QFrame, QStackedWidget, QMenuBar, QMenu,
    QStatusBar, QMessageBox, QFileDialog, QScrollArea,
    QSizePolicy, QGridLayout, QGroupBox, QProgressBar,
    QGraphicsDropShadowEffect, QGraphicsOpacityEffect,
)
from PyQt6.QtCore import (
    Qt, QSize, QTimer, pyqtSignal, QSettings,
    QPropertyAnimation, QEasingCurve, QPoint,
)
from PyQt6.QtGui import (
    QAction, QFont, QColor, QIcon, QPixmap, QPainter, QPen,
    QLinearGradient, QPolygonF, QShortcut, QKeySequence,
)
from PyQt6.QtCore import QPointF, QRectF

from quanta_ui.theme import C, STYLE
from quanta_ui.widgets import Card, StatusDot, Heading, Stat, NavButton, Sidebar, ToastNotification


APP_NAME = "Quanta Color"
APP_VERSION = "1.0.0"
APP_ORG = "Quanta Universe"


# =============================================================================
# Application Icon — color spectrum arc
# =============================================================================

def make_app_icon() -> QIcon:
    """
    Create the application icon programmatically.

    A stylized color wheel / spectrum arc rendered at multiple
    sizes for crisp display at any DPI.
    """
    icon = QIcon()
    for size in [16, 24, 32, 48, 64, 128, 256]:
        pm = QPixmap(size, size)
        pm.fill(QColor(0, 0, 0, 0))

        p = QPainter(pm)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)

        s = size
        cx = s * 0.5
        cy = s * 0.5

        # Outer ring — spectrum arcs
        radius = s * 0.38
        arc_width = max(2.0, s * 0.09)

        spectrum = [
            (0,   "#d4a0a0"),   # soft pink
            (45,  "#e0c87a"),   # buttercream
            (90,  "#92ad7e"),   # sage green
            (135, "#95b3ba"),   # powder blue
            (180, "#b07878"),   # muted rose
            (225, "#d08888"),   # soft coral
            (270, "#deb0b0"),   # light pink
            (315, "#a3be90"),   # sage bright
        ]

        for angle_start, color in spectrum:
            pen = QPen(QColor(color), arc_width)
            pen.setCapStyle(Qt.PenCapStyle.FlatCap)
            p.setPen(pen)
            p.setBrush(Qt.BrushStyle.NoBrush)
            arc_rect = QRectF(cx - radius, cy - radius, radius * 2, radius * 2)
            p.drawArc(arc_rect, angle_start * 16, 50 * 16)

        # Center dot
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(QColor("#fdf9f5"))
        inner_r = s * 0.18
        p.drawEllipse(QPointF(cx, cy), inner_r, inner_r)

        # Tiny accent dot in center
        p.setBrush(QColor("#d4a0a0"))
        dot_r = s * 0.06
        p.drawEllipse(QPointF(cx, cy), dot_r, dot_r)

        p.end()
        icon.addPixmap(pm)

    return icon


# =============================================================================
# Placeholder Page (fallback for unbuilt pages)
# =============================================================================

class PlaceholderPage(QWidget):
    def __init__(self, title: str, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(32, 28, 32, 28)
        layout.addWidget(Heading(title))

        desc = QLabel("This page is under construction.")
        desc.setStyleSheet(f"font-size: 13px; color: {C.TEXT2};")
        layout.addWidget(desc)

        layout.addStretch()


# =============================================================================
# Main Window
# =============================================================================

PAGE_NAMES = [
    "Dashboard",
    "Image Analyzer",
    "Color Inspector",
    "LUT Workshop",
    "Palette Studio",
    "Settings",
]

PAGE_SHORTCUTS = ["Ctrl+1", "Ctrl+2", "Ctrl+3", "Ctrl+4", "Ctrl+5", "Ctrl+6"]

PAGE_MENU_NAMES = [
    "&Dashboard",
    "&Image Analyzer",
    "&Color Inspector",
    "&LUT Workshop",
    "&Palette Studio",
    "&Settings",
]


class QuantaColorWindow(QMainWindow):
    """Main application window."""

    def __init__(self):
        super().__init__()
        self.settings = QSettings(APP_ORG, APP_NAME)
        self.setWindowTitle(f"{APP_NAME} v{APP_VERSION}")
        self.setMinimumSize(1000, 700)
        self.resize(1200, 800)
        self.setStyleSheet(STYLE)
        self._app_icon = make_app_icon()
        self.setWindowIcon(self._app_icon)

        self._build_menubar()
        self._build_central()
        self._build_statusbar()
        self._setup_shortcuts()
        self._restore_geometry()

    # --- Keyboard Shortcuts ---

    def _setup_shortcuts(self):
        """Register keyboard shortcuts not already attached to menu actions."""
        sc_escape = QShortcut(QKeySequence("Escape"), self)
        sc_escape.activated.connect(self.close)

    def _shortcut_switch_page(self, index: int):
        """Switch to a page by index and update sidebar."""
        self._switch_page(index)
        self.sidebar._on_click(index)

    # --- Menu Bar ---

    def _build_menubar(self):
        mb = self.menuBar()

        # File
        file_menu = mb.addMenu("&File")
        file_menu.addAction(
            QAction("&Open Image...", self, shortcut="Ctrl+O",
                    triggered=self._open_image)
        )
        file_menu.addAction(
            QAction("Open &LUT...", self, shortcut="Ctrl+L",
                    triggered=self._open_lut)
        )
        file_menu.addSeparator()
        file_menu.addAction(
            QAction("E&xit", self, shortcut="Alt+F4",
                    triggered=self.close)
        )

        # View — page navigation shortcuts
        view = mb.addMenu("&View")
        for i, (name, sc) in enumerate(zip(PAGE_MENU_NAMES, PAGE_SHORTCUTS)):
            act = QAction(name, self)
            act.setShortcut(QKeySequence(sc))
            act.triggered.connect(
                lambda checked, idx=i: self._shortcut_switch_page(idx)
            )
            view.addAction(act)
        view.addSeparator()
        view.addAction(
            QAction("&Refresh", self, shortcut="F5",
                    triggered=self._refresh_current)
        )

        # Help
        help_menu = mb.addMenu("&Help")
        help_menu.addAction(
            QAction("&About", self, triggered=self._about)
        )

    # --- Central Widget ---

    def _build_central(self):
        central = QWidget()
        main_layout = QHBoxLayout(central)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # Sidebar
        self.sidebar = Sidebar(PAGE_NAMES, app_name=APP_NAME, app_version=APP_VERSION)
        self.sidebar.page_changed.connect(self._switch_page)
        main_layout.addWidget(self.sidebar)

        # Page stack
        self.stack = QStackedWidget()
        self.stack.setStyleSheet(f"background: {C.BG};")

        # Page 0: Dashboard
        try:
            from quanta_color.gui.pages.dashboard import DashboardPage
            self.stack.addWidget(DashboardPage())
        except Exception as e:
            logger.warning("Failed to load DashboardPage: %s", e)
            self.stack.addWidget(PlaceholderPage("Dashboard"))

        # Page 1: Image Analyzer
        try:
            from quanta_color.gui.pages.image_analyzer import ImageAnalyzerPage
            self.stack.addWidget(ImageAnalyzerPage())
        except Exception as e:
            logger.warning("Failed to load ImageAnalyzerPage: %s", e)
            self.stack.addWidget(PlaceholderPage("Image Analyzer"))

        # Page 2: Color Inspector
        try:
            from quanta_color.gui.pages.color_inspector import ColorInspectorPage
            self.stack.addWidget(ColorInspectorPage())
        except Exception as e:
            logger.warning("Failed to load ColorInspectorPage: %s", e)
            self.stack.addWidget(PlaceholderPage("Color Inspector"))

        # Page 3: LUT Workshop
        try:
            from quanta_color.gui.pages.lut_workshop import LUTWorkshopPage
            self.stack.addWidget(LUTWorkshopPage())
        except Exception as e:
            logger.warning("Failed to load LUTWorkshopPage: %s", e)
            self.stack.addWidget(PlaceholderPage("LUT Workshop"))

        # Page 4: Palette Studio
        try:
            from quanta_color.gui.pages.palette_studio import PaletteStudioPage
            self.stack.addWidget(PaletteStudioPage())
        except Exception as e:
            logger.warning("Failed to load PaletteStudioPage: %s", e)
            self.stack.addWidget(PlaceholderPage("Palette Studio"))

        # Page 5: Settings
        try:
            from quanta_color.gui.pages.settings import SettingsPage
            self.stack.addWidget(SettingsPage())
        except Exception as e:
            logger.warning("Failed to load SettingsPage: %s", e)
            self.stack.addWidget(PlaceholderPage("Settings"))

        main_layout.addWidget(self.stack, stretch=1)
        self.setCentralWidget(central)

    # --- Status Bar ---

    def _build_statusbar(self):
        sb = self.statusBar()
        self._status = QLabel("Ready")
        sb.addWidget(self._status, 1)

    # --- Page Switching ---

    def _switch_page(self, index: int):
        """Switch page with a subtle opacity fade transition."""
        if index == self.stack.currentIndex():
            return
        target = self.stack.widget(index)
        if target:
            try:
                effect = QGraphicsOpacityEffect(target)
                target.setGraphicsEffect(effect)
                effect.setOpacity(0.3)
                self.stack.setCurrentIndex(index)

                anim = QPropertyAnimation(effect, b"opacity")
                anim.setDuration(150)
                anim.setStartValue(0.3)
                anim.setEndValue(1.0)
                anim.setEasingCurve(QEasingCurve.Type.OutCubic)
                anim.finished.connect(lambda: target.setGraphicsEffect(None))
                self._page_anim = anim  # prevent GC
                anim.start()
            except Exception:
                self.stack.setCurrentIndex(index)
        else:
            self.stack.setCurrentIndex(index)

    # --- Toast ---

    def show_toast(self, message: str, level: str = "info"):
        """Show a toast notification in the bottom-right corner."""
        toast = ToastNotification(message, level, parent=self)
        margin = 16
        x = self.width() - toast.width() - margin
        y = self.height() - toast.height() - margin
        toast.move(x, y)
        toast.slide_in()

    # --- Actions ---

    def _open_image(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "Open Image", "",
            "Images (*.png *.jpg *.jpeg *.tif *.tiff *.exr *.hdr *.bmp)"
        )
        if path:
            self._status.setText(f"Loaded: {Path(path).name}")

    def _open_lut(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "Open LUT", "",
            "LUT Files (*.cube *.3dl *.csp *.spi3d)"
        )
        if path:
            self._status.setText(f"Loaded: {Path(path).name}")

    def _refresh_current(self):
        page = self.stack.currentWidget()
        if hasattr(page, 'refresh'):
            page.refresh()
        self._status.setText("Refreshed")

    def _about(self):
        QMessageBox.about(
            self, f"About {APP_NAME}",
            f"<h2>{APP_NAME}</h2>"
            f"<p>Version {APP_VERSION}</p>"
            f"<p>Professional color science workbench for<br>"
            f"image analysis, LUT creation, and color grading.</p>"
            f"<p>Color science: Oklab, JzAzBz, CAM16, PQ/HLG, ACES</p>"
            f"<p>&copy; 2022-2026 Zain Dana Harper</p>"
        )

    # --- Geometry Persistence ---

    def _restore_geometry(self):
        geo = self.settings.value("window/geometry")
        if geo:
            self.restoreGeometry(geo)

    def closeEvent(self, event):
        self.settings.setValue("window/geometry", self.saveGeometry())
        event.accept()


# =============================================================================
# Entry Point
# =============================================================================

if __name__ == "__main__":
    from quanta_color.gui import launch
    sys.exit(launch())
