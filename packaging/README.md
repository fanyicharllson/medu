# Building and releasing Medu (Charllson)

## What you get

| File | What it is |
|---|---|
| `dist\medu.exe` | Medu in one file. Runs without Python. Icon, author "Charllson" and version in its Properties |
| `dist\Medu-Setup-<version>.exe` | The installer students download: adds `medu` to PATH, opens `.med` / `.mdt` files with Medu, adds a Start-menu entry and an uninstaller |

## One-time setup

1. Python virtual environment active (see CONTRIBUTING.md)
2. Install **Inno Setup 6** (free): https://jrsoftware.org/isdl.php. Only needed for the Setup file.

## Build

From the `medu` folder, in PowerShell:

```powershell
.\packaging\build.ps1           # the full medu command (once cli.py is finished)
.\packaging\build.ps1 -Mode2    # test build now: medu.exe opens Mode 2 directly
```

The script runs the tests first and stops if any fail, so a broken version is never packaged.

Try it: `.\dist\medu.exe samples\sentences.mdt`, or run `dist\Medu-Setup-0.1.0.exe` to install it like a student would.

## Release on GitHub

1. Set the version in `medu\__init__.py` (e.g. `__version__ = "1.0.0"`) and build.
2. Publish:

```powershell
gh release create v1.0.0 dist\Medu-Setup-1.0.0.exe dist\medu.exe --title "Medu 1.0.0" --notes "Medu: a compiler for Medumba."
```

Students then download **Medu-Setup-1.0.0.exe** from the repo's Releases page.

## Good to know

- **Windows SmartScreen** warns about unsigned programs ("Windows protected your PC"). Tell users: **More info → Run anyway**. Removing the warning needs a paid code-signing certificate.
- Files: `medu.spec` (PyInstaller recipe, author and version details), `installer.iss` (installer), `medu.ico` (icon).
- To change the author name shown in Properties and the installer, edit `CompanyName` in `medu.spec` and `AppPublisher` in `installer.iss`.

## Updates for users

Users never need to come back to GitHub by hand:

- `medu upgrade`: downloads the newest release's `Medu-Setup-<version>.exe` (or `medu.exe`) and installs it
- `medu upgrade 1.2.0` / `medu downgrade 1.0.0`: install a specific version
- Inside `medu>`, Medu checks GitHub quietly at most once a day and shows
  *"Medu 1.1.0 is available. Run: medu upgrade"*. With no internet it says nothing.
  Set `MEDU_NO_UPDATE_CHECK=1` to switch the check off.

So every release must attach `Medu-Setup-<version>.exe` (preferred) or `medu.exe`, and its tag must be `v<version>`.

## Version numbers

- `1.0.0`: Mode 2 (sentences → English)
- `1.x.0`: dictionary and grammar improvements
- `2.0.0`: Mode 1 (programs) from Adrien
