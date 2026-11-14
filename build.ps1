# Builds dist\NXPortingKit\NXPortingKit.exe. Put node.exe and hacbrewpack.exe in .\tools first (they ship inside the app).
$ErrorActionPreference = 'Stop'
foreach ($t in 'node.exe', 'hacbrewpack.exe') {
  if (-not (Test-Path "$PSScriptRoot\tools\$t")) { throw "Missing tools\$t" }
}
Get-Process NXPortingKit -ErrorAction SilentlyContinue | Stop-Process -Force
python -m PyInstaller --noconfirm --windowed --name NXPortingKit --icon assets/icon.ico `
  --add-data "qml;qml" --add-data "ports;ports" --add-data "resources;resources" --add-data "tools;tools" --add-data "licenses;licenses" --add-data "assets/icon.png;assets" --add-data "assets/icon.ico;assets" `
  --exclude-module PySide6.QtWebEngineCore --exclude-module PySide6.QtWebEngineWidgets --exclude-module PySide6.QtWebEngineQuick --exclude-module PySide6.QtWebChannel --exclude-module PySide6.QtPdf --exclude-module PySide6.QtPdfWidgets --exclude-module numpy `
  main.py

# Qt's web engine and PDF modules come along through the QML plugins; the app uses neither (about 200 MB).
$qt = "$PSScriptRoot\dist\NXPortingKit\_internal\PySide6"
foreach ($f in 'Qt6WebEngineCore.dll', 'Qt6WebEngineQuick.dll', 'Qt6WebEngineQuickDelegatesQml.dll', 'Qt6Pdf.dll', 'Qt6PdfQuick.dll') {
  Remove-Item "$qt\$f" -Force -ErrorAction SilentlyContinue
}
Remove-Item "$qt\qml\QtWebEngine" -Recurse -Force -ErrorAction SilentlyContinue
