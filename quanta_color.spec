# Quanta Color — PyInstaller Build Spec
# Build: pyinstaller quanta_color.spec --clean --noconfirm

import os
block_cipher = None

a = Analysis(
    ['quanta_color/cli.py'],
    pathex=[os.path.abspath('.')],
    binaries=[],
    datas=[],
    hiddenimports=[
        'quanta_color', 'quanta_color.spaces', 'quanta_color.tonemap',
        'quanta_color.difference', 'quanta_color.adaptation',
        'quanta_color.appearance', 'quanta_color.spectral',
        'quanta_color.blindness', 'quanta_color.gamut',
        'quanta_color.harmony', 'quanta_color.icc', 'quanta_color.gui',
        'numpy', 'PyQt6', 'PyQt6.QtWidgets', 'PyQt6.QtCore', 'PyQt6.QtGui',
    ],
    excludes=[],
    noarchive=False,
)
pyz = PYZ(a.pure, cipher=block_cipher)
exe = EXE(pyz, a.scripts, [], exclude_binaries=True,
          name='quanta-color', console=True, icon=None)
coll = COLLECT(exe, a.binaries, a.datas, name='quanta-color')
