# Builds dist\NXPortingKit\NXPortingKit.exe. Put node.exe and hacbrewpack.exe in .\tools first (they ship inside the app).
$ErrorActionPreference = 'Stop'
foreach ($t in 'node.exe', 'hacbrewpack.exe') {
  if (-not (Test-Path "$PSScriptRoot\tools\$t")) { throw "Missing tools\$t" }
}
Get-Process NXPortingKit -ErrorAction SilentlyContinue | Stop-Process -Force
python -m PyInstaller --noconfirm --windowed --name NXPortingKit --icon assets/icon.ico `
  --add-data "qml;qml" --add-data "ports;ports" --add-data "resources;resources" --add-data "tools;tools" `
  --exclude-module PySide6.QtWebEngineCore --exclude-module PySide6.QtWebEngineWidgets `
  main.py
