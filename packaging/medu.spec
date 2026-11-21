# PyInstaller recipe for medu.exe. Build with:  packaging\build.ps1
# (or: pyinstaller packaging\medu.spec --noconfirm)
#
# MEDU_ENTRY=mode2 builds a test exe that starts Mode 2 directly
# (useful before cli.py is finished). Default: the full `medu` command.

import os
import re
from pathlib import Path

ROOT = Path(SPECPATH).parent
version = re.search(r'__version__ = "(.+?)"', (ROOT / "medu" / "__init__.py").read_text()).group(1)
nums = [int(x) for x in version.split(".")] + [0] * (4 - len(version.split(".")))

entry = "medu/mode2.py" if os.environ.get("MEDU_ENTRY") == "mode2" else "medu/__main__.py"

# Windows file properties (right-click medu.exe -> Properties -> Details)
version_file = ROOT / "build" / "version_info.txt"
version_file.parent.mkdir(exist_ok=True)
version_file.write_text(f"""
VSVersionInfo(
  ffi=FixedFileInfo(filevers={tuple(nums)}, prodvers={tuple(nums)}),
  kids=[
    StringFileInfo([StringTable('040904B0', [
      StringStruct('CompanyName', 'CharlseEmpire Tech'),
      StringStruct('FileDescription', 'Medu - compiler for Medumba'),
      StringStruct('FileVersion', '{version}'),
      StringStruct('InternalName', 'medu'),
      StringStruct('LegalCopyright', 'Copyright (c) 2026 Charllson & Adrien Tello. GPL-3.0.'),
      StringStruct('OriginalFilename', 'medu.exe'),
      StringStruct('ProductName', 'Medu'),
      StringStruct('ProductVersion', '{version}')])]),
    VarFileInfo([VarStruct('Translation', [1033, 1200])])
  ]
)
""", encoding="utf-8")

a = Analysis(
    [str(ROOT / entry)],
    pathex=[str(ROOT)],
    datas=[(str(ROOT / "data" / "languages"), "data/languages")],
    hiddenimports=["medu.mode2", "medu.cli", "medu.mode1", "medu.updater", "medu.window"],
    excludes=["tkinter", "unittest", "pytest", "PIL"],
)
pyz = PYZ(a.pure)
exe = EXE(
    pyz, a.scripts, a.binaries, a.datas,
    name="medu",
    console=True,                 # a terminal program
    icon=str(ROOT / "packaging" / "medu.ico"),
    version=str(version_file),
    upx=False,
)
