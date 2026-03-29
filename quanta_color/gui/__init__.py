"""
Quanta Color — GUI Package

Launch the application with quanta_color.gui.launch()
"""


def launch():
    import sys

    from PyQt6.QtWidgets import QApplication

    from quanta_color.gui.app import QuantaColorWindow

    # Windows taskbar icon fix
    try:
        import ctypes

        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID("quanta.quantacolor.1")
    except Exception:
        pass

    app = QApplication(sys.argv)
    app.setApplicationName("Quanta Color")
    app.setOrganizationName("Quanta Universe")

    window = QuantaColorWindow()
    window.show()
    return app.exec()
