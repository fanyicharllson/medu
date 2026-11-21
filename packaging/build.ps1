# Builds medu.exe and the Windows installer.
#
#   .\packaging\build.ps1            full medu command (needs cli.py finished)
#   .\packaging\build.ps1 -Mode2     test build: medu.exe starts Mode 2 directly
#
# Output:  dist\medu.exe   and   dist\Medu-Setup-<version>.exe (if Inno Setup is installed)

param([switch]$Mode2)
$clock = [System.Diagnostics.Stopwatch]::StartNew()
$ErrorActionPreference = "Continue"   # native tools write notices to stderr; we check exit codes
$root = Split-Path -Parent $PSScriptRoot
Set-Location $root

$version = (Select-String -Path "medu\__init__.py" -Pattern '__version__ = "(.+?)"').Matches[0].Groups[1].Value
Write-Host "Building Medu $version" -ForegroundColor Cyan

Write-Host "1/3  Running the tests"
python -m pytest -q
if ($LASTEXITCODE -ne 0) { throw "Tests failed: fix them before building." }

Write-Host "2/3  Building dist\medu.exe (PyInstaller)"
python -m pip install -q --disable-pip-version-check -r requirements-build.txt
if ($LASTEXITCODE -ne 0) { throw "Could not install PyInstaller." }
if ($Mode2) { $env:MEDU_ENTRY = "mode2" } else { Remove-Item Env:MEDU_ENTRY -ErrorAction SilentlyContinue }
python -m PyInstaller packaging\medu.spec --noconfirm --clean --distpath dist --workpath build --log-level WARN
if ($LASTEXITCODE -ne 0) { throw "PyInstaller failed." }
Remove-Item Env:MEDU_ENTRY -ErrorAction SilentlyContinue

Write-Host "3/3  Building the installer (Inno Setup)"
$iscc = @("${env:ProgramFiles(x86)}\Inno Setup 6\ISCC.exe", "$env:ProgramFiles\Inno Setup 6\ISCC.exe",
          "$env:LOCALAPPDATA\Programs\Inno Setup 6\ISCC.exe") | Where-Object { Test-Path $_ } | Select-Object -First 1
if ($iscc) {
    & $iscc "/DAppVersion=$version" packaging\installer.iss | Out-Null
    Write-Host "Done: dist\medu.exe and dist\Medu-Setup-$version.exe" -ForegroundColor Green
} else {
    Write-Host "Done: dist\medu.exe" -ForegroundColor Green
    Write-Host "Install Inno Setup 6 (free, jrsoftware.org) to also build Medu-Setup-$version.exe" -ForegroundColor Yellow
}

$clock.Stop()
Write-Host ("Build finished in {0:N1} s (tests, exe and installer)" -f $clock.Elapsed.TotalSeconds) -ForegroundColor Cyan
