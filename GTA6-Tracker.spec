# PyInstaller spec for GTA 6 Tracker.
#
# Build with:  pyinstaller --noconfirm GTA6-Tracker.spec
#
# Produces dist/GTA6-Tracker/ (onedir) containing GTA6-Tracker.exe.
# Chromium is NOT bundled on purpose: the app uses the user's installed Chrome
# (channel="chrome"). Only Playwright's own driver is bundled via collect_all.

from PyInstaller.utils.hooks import collect_all

# Pull in Playwright's package data, binaries and hidden imports (the Node
# driver that Playwright needs at runtime).
pw_datas, pw_binaries, pw_hiddenimports = collect_all("playwright")

a = Analysis(
    ["gta6_tracker.py"],
    pathex=[],
    binaries=pw_binaries,
    datas=pw_datas,
    hiddenimports=pw_hiddenimports + ["bs4", "dotenv"],
    hookspath=[],
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="GTA6-Tracker",
    console=True,
    disable_windowed_traceback=False,
    icon="assets/icons/GTA6-Tracker.ico",
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=False,
    name="GTA6-Tracker",
)
