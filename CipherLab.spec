# PyInstaller build spec for Cipher Lab.
#
#     pyinstaller CipherLab.spec
#
# Produces a self-contained app with Python, Tk and PyNaCl inside, so the
# person running it installs nothing. One spec covers both platforms because
# PyInstaller cannot cross-compile: the macOS .app must be built on macOS and
# the Windows .exe on Windows. The CI workflow in .github/workflows does both.

import sys

from PyInstaller.utils.hooks import collect_all

APP_NAME = "Cipher Lab"

# PyNaCl is a CFFI binding to libsodium, so it ships a compiled _sodium
# extension. collect_all drags that binary in; a plain import scan misses it
# and the app would then start fine and fail only on the Public key cipher.
datas, binaries, hiddenimports = [], [], []
for package in ("nacl",):
    package_datas, package_binaries, package_hidden = collect_all(package)
    datas += package_datas
    binaries += package_binaries
    hiddenimports += package_hidden

hiddenimports += ["_cffi_backend"]

analysis = Analysis(
    ["main.py"],
    pathex=[],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    runtime_hooks=[],
    # Nothing here needs these, and they are large.
    excludes=["numpy", "pytest", "PIL", "matplotlib", "pydoc_data", "unittest"],
    noarchive=False,
)

pyz = PYZ(analysis.pure)

if sys.platform == "darwin":
    # macOS wants a directory bundle, which BUNDLE wraps into the .app.
    executable = EXE(
        pyz,
        analysis.scripts,
        [],
        exclude_binaries=True,
        name=APP_NAME,
        debug=False,
        strip=False,
        upx=False,
        console=False,
    )
    collected = COLLECT(
        executable,
        analysis.binaries,
        analysis.datas,
        strip=False,
        upx=False,
        name=APP_NAME,
    )
    app = BUNDLE(
        collected,
        name=APP_NAME + ".app",
        icon=None,
        bundle_identifier="local.cipherlab.app",
        info_plist={
            "CFBundleName": APP_NAME,
            "CFBundleDisplayName": APP_NAME,
            "CFBundleShortVersionString": "1.0.0",
            "CFBundleVersion": "1.0.0",
            "NSHighResolutionCapable": True,
            # Tk apps are not document-based; without this macOS can show the
            # app as though it wants a file association.
            "LSApplicationCategoryType": "public.app-category.utilities",
        },
    )
else:
    # Windows: a single .exe is friendlier than a folder of files.
    executable = EXE(
        pyz,
        analysis.scripts,
        analysis.binaries,
        analysis.datas,
        [],
        name=APP_NAME,
        debug=False,
        strip=False,
        upx=False,
        console=False,
    )
