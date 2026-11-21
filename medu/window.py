"""
The Medu window: when Medu is opened from its icon, it styles its own window.

Owner: Charllson

Opened from the Start menu, the desktop, the installer or a double-clicked
.mdt file, Windows gives Medu a console window of its own. Medu then:
    - sets the title "Medu · Medumba compiler" (the taskbar shows the Medu icon,
      which is built into medu.exe)
    - paints it in the Medu colours (deep indigo-black background)
    - picks a font that can show Medumba letters (ɛ̌ ʉ ŋ ɑ ʼ)
    - keeps the window open at the end with "Press Enter to close"

Started from someone's own cmd / PowerShell / Windows Terminal, Medu shares
their window and changes nothing. Every step is optional: if Windows refuses
one, Medu simply carries on.
"""

from __future__ import annotations

import ctypes
import os
import sys

TITLE = "Medu · Medumba compiler"

# Colour table of the console, as 0x00BBGGRR. Only the base colours change;
# Medu's own 256-colour text (indigo, ochre, green) looks the same everywhere.
THEME = {
    0: 0x00211110,   # background: #10111f deep indigo-black
    7: 0x00E6DAD8,   # normal text: #d8dae6
    8: 0x00786058,   # dim text: #586078
    15: 0x00FFFFFF,  # bright text
}
FONTS = ("Cascadia Mono", "Consolas")   # both have ɛ ʉ ŋ ɑ ʼ and tone marks


def _kernel32():
    if os.name != "nt":
        return None
    try:
        return ctypes.windll.kernel32
    except (AttributeError, OSError):
        return None


def owns_console() -> bool:
    """True when Windows opened this window just for Medu (icon, double-click),
    False inside the user's own terminal."""
    k = _kernel32()
    if k is None or not sys.stdout.isatty():
        return False
    try:
        processes = (ctypes.c_uint32 * 4)()
        count = k.GetConsoleProcessList(processes, 4)
        # medu.exe is two processes (a small unpacker + Medu itself);
        # from source: python.exe (+ the py launcher). More means a shell is there.
        return count <= 2
    except (AttributeError, OSError):
        return False


class _COORD(ctypes.Structure):
    _fields_ = [("X", ctypes.c_short), ("Y", ctypes.c_short)]


class _SMALL_RECT(ctypes.Structure):
    _fields_ = [("Left", ctypes.c_short), ("Top", ctypes.c_short),
                ("Right", ctypes.c_short), ("Bottom", ctypes.c_short)]


class _BUFFER_INFO_EX(ctypes.Structure):
    _fields_ = [("cbSize", ctypes.c_ulong), ("dwSize", _COORD),
                ("dwCursorPosition", _COORD), ("wAttributes", ctypes.c_ushort),
                ("srWindow", _SMALL_RECT), ("dwMaximumWindowSize", _COORD),
                ("wPopupAttributes", ctypes.c_ushort),
                ("bFullscreenSupported", ctypes.c_int),
                ("ColorTable", ctypes.c_ulong * 16)]


class _FONT_INFO_EX(ctypes.Structure):
    _fields_ = [("cbSize", ctypes.c_ulong), ("nFont", ctypes.c_ulong),
                ("dwFontSize", _COORD), ("FontFamily", ctypes.c_uint),
                ("FontWeight", ctypes.c_uint), ("FaceName", ctypes.c_wchar * 32)]


def _set_colours(k, handle) -> None:
    info = _BUFFER_INFO_EX()
    info.cbSize = ctypes.sizeof(_BUFFER_INFO_EX)
    if not k.GetConsoleScreenBufferInfoEx(handle, ctypes.byref(info)):
        return
    for index, colour in THEME.items():
        info.ColorTable[index] = colour
    info.srWindow.Right += 1        # Windows shrinks the window by one otherwise
    info.srWindow.Bottom += 1
    k.SetConsoleScreenBufferInfoEx(handle, ctypes.byref(info))


def _set_font(k, handle) -> None:
    for face in FONTS:
        font = _FONT_INFO_EX()
        font.cbSize = ctypes.sizeof(_FONT_INFO_EX)
        font.dwFontSize = _COORD(0, 18)
        font.FontFamily = 54          # FF_MODERN | TMPF_TRUETYPE | fixed pitch
        font.FontWeight = 400
        font.FaceName = face
        if k.SetCurrentConsoleFontEx(handle, False, ctypes.byref(font)):
            return


def title_for(activity: str = "") -> str:
    """'Medu 1.0.0  ·  Mode 2 · Sentences → English'"""
    from medu import __version__
    return f"Medu {__version__}  ·  {activity}" if activity else f"Medu {__version__}  ·  {TITLE}"


def brand(activity: str = "") -> bool:
    """Style the window if it is Medu's own. Returns True when it did.
    activity is shown in the title bar, e.g. 'Mode 2 · Sentences → English'."""
    if os.environ.get("MEDU_PLAIN_WINDOW") or not owns_console():
        return False
    k = _kernel32()
    try:
        k.SetConsoleTitleW(title_for(activity))
        handle = k.GetStdHandle(-11)
        _set_font(k, handle)
        _set_colours(k, handle)
        os.system("cls")              # repaint everything in the new colours
        return True
    except (AttributeError, OSError, ValueError):
        return False


def keep_open() -> None:
    """In Medu's own window, wait before closing so the result can be read."""
    if not owns_console():
        return
    try:
        from medu import ui
        input("\n" + ui.note("Press Enter to close…"))
    except (EOFError, KeyboardInterrupt):
        pass
