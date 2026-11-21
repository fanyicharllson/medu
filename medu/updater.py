"""
Updates: `medu upgrade`, `medu downgrade <version>`, and the "new version" notice.

Owner: Charllson

Medu works offline first. Nothing here ever blocks or breaks Medu:
    - the notice checks GitHub at most once a day, in the background, with a
      short timeout; with no internet it stays silent
    - only `medu upgrade` / `medu downgrade` download anything, and only when
      the user types them

Where versions come from: the GitHub Releases of fanyicharllson/medu.
Each release carries Medu-Setup-<version>.exe (preferred) and/or medu.exe.
"""

from __future__ import annotations

import json
import os
import re
import subprocess
import sys
import tempfile
import threading
import time
import urllib.error
import urllib.request
from dataclasses import dataclass
from pathlib import Path

from medu import __version__, ui

API = "https://api.github.com/repos/fanyicharllson/medu/releases"
CHECK_EVERY = 24 * 3600          # seconds between automatic checks
TIMEOUT = 3                      # seconds; a slow network never holds Medu up


@dataclass
class Release:
    version: str                 # "1.1.0"
    notes: str
    setup_url: str | None        # Medu-Setup-1.1.0.exe
    exe_url: str | None          # medu.exe
    page: str


# ---------------------------------------------------------------------------
# Versions
# ---------------------------------------------------------------------------

def parse_version(text: str) -> tuple[int, ...]:
    """'v1.2.0' -> (1, 2, 0). Anything unreadable sorts lowest."""
    nums = re.findall(r"\d+", text)
    return tuple(int(n) for n in nums[:3]) or (0,)


def is_newer(candidate: str, current: str = __version__) -> bool:
    return parse_version(candidate) > parse_version(current)


def _from_api(data: dict) -> Release:
    setup = exe = None
    for asset in data.get("assets", []):
        name = asset.get("name", "").lower()
        if name.startswith("medu-setup") and name.endswith(".exe"):
            setup = asset["browser_download_url"]
        elif name == "medu.exe":
            exe = asset["browser_download_url"]
    return Release(data.get("tag_name", "").lstrip("v"), data.get("body") or "",
                   setup, exe, data.get("html_url", ""))


def _get(url: str):
    req = urllib.request.Request(url, headers={"Accept": "application/vnd.github+json",
                                               "User-Agent": f"medu/{__version__}"})
    with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
        return json.loads(resp.read().decode("utf-8"))


def fetch_release(version: str | None = None) -> Release | None:
    """Latest release, or a given version. None when offline or not found."""
    try:
        if version:
            return _from_api(_get(f"{API}/tags/v{version.lstrip('v')}"))
        return _from_api(_get(f"{API}/latest"))
    except (urllib.error.URLError, OSError, ValueError, KeyError):
        return None


def list_versions() -> list[str] | None:
    try:
        return [r["tag_name"].lstrip("v") for r in _get(API) if not r.get("draft")]
    except (urllib.error.URLError, OSError, ValueError, KeyError, TypeError):
        return None


# ---------------------------------------------------------------------------
# Background notice
# ---------------------------------------------------------------------------

def _state_file() -> Path:
    return ui.config_path().with_name("update.json")


def _due() -> bool:
    try:
        last = json.loads(_state_file().read_text(encoding="utf-8")).get("checked", 0)
    except (OSError, ValueError):
        last = 0
    return time.time() - last > CHECK_EVERY


def _remember_check() -> None:
    try:
        path = _state_file()
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps({"checked": time.time()}), encoding="utf-8")
    except OSError:
        pass


class UpdateNotice:
    """Starts a quiet check in the background; message() returns the notice
    once, when a newer version was found. Never raises, never waits."""

    def __init__(self, force: bool = False) -> None:
        self.found: Release | None = None
        self.shown = False
        if os.environ.get("MEDU_NO_UPDATE_CHECK") or not (force or _due()):
            self.thread = None
            return
        self.thread = threading.Thread(target=self._check, daemon=True)
        self.thread.start()

    def _check(self) -> None:
        release = fetch_release()
        if release is not None:
            _remember_check()
            if is_newer(release.version):
                self.found = release

    def message(self) -> str | None:
        if self.shown or self.found is None:
            return None
        self.shown = True
        return (ui.paint(f"  ↑ Medu {self.found.version} is available (you have {__version__}). ",
                         ui.OCHRE, ui.BOLD)
                + ui.paint("Run: medu upgrade", ui.INDIGO, ui.BOLD))


# ---------------------------------------------------------------------------
# medu upgrade / downgrade
# ---------------------------------------------------------------------------

def _download(url: str, dest: Path) -> None:
    req = urllib.request.Request(url, headers={"User-Agent": f"medu/{__version__}"})
    with urllib.request.urlopen(req, timeout=60) as resp, open(dest, "wb") as out:
        total = int(resp.headers.get("Content-Length") or 0)
        done = 0
        while chunk := resp.read(64 * 1024):
            out.write(chunk)
            done += len(chunk)
            if total:
                print(f"\r  downloading… {done * 100 // total:3d}%", end="", flush=True)
    print()


def install(version: str | None = None, allow_older: bool = False) -> int:
    """medu upgrade [version] / medu downgrade <version>."""
    if not getattr(sys, "frozen", False):
        print(ui.note("You are running Medu from the source code: update it with  git pull"))
        return 1
    print(ui.note("Looking for " + (f"Medu {version}" if version else "the latest Medu") + " on GitHub…"))
    release = fetch_release(version)
    if release is None:
        if version:
            print(ui.paint(f"Version {version} was not found, or there is no internet connection.", ui.RED))
            versions = list_versions()
            if versions:
                print(ui.note("Available versions: " + ", ".join(versions)))
        else:
            print(ui.paint("No internet connection, or GitHub cannot be reached. Try again later.", ui.RED))
        return 1
    if release.version == __version__:
        print(ui.result(f"You already have Medu {__version__}."))
        return 0
    if not is_newer(release.version) and not allow_older:
        print(ui.note(f"Medu {release.version} is older than yours ({__version__}). "
                      f"To go back to it, run: medu downgrade {release.version}"))
        return 1
    url = release.setup_url or release.exe_url
    if not url:
        print(ui.paint(f"Release {release.version} has no Windows download yet: {release.page}", ui.RED))
        return 1

    print(ui.label("Version") + f" {__version__} → {release.version}")
    tmp = Path(tempfile.gettempdir()) / f"medu-{release.version}-{Path(url).name}"
    try:
        _download(url, tmp)
    except (urllib.error.URLError, OSError) as err:
        print(ui.paint(f"Download failed: {err}", ui.RED))
        return 1

    if release.setup_url:
        # The installer replaces Medu, keeps PATH and the user's settings.
        subprocess.Popen([str(tmp), "/SILENT", "/SUPPRESSMSGBOXES", "/CLOSEAPPLICATIONS"],
                         close_fds=True)
        print(ui.result(f"Installing Medu {release.version}… open a new terminal when it finishes."))
        return 0

    # Only medu.exe in the release: swap the file next to the running one.
    # Windows lets a running .exe be renamed, not overwritten.
    current = Path(sys.executable)
    old = current.with_name("medu.old.exe")
    try:
        if old.exists():
            old.unlink()
        current.rename(old)
        tmp.replace(current)
    except OSError as err:
        print(ui.paint(f"Could not replace {current}: {err}", ui.RED))
        return 1
    print(ui.result(f"Medu {release.version} is installed. Run medu again to use it."))
    return 0
