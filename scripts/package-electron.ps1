$ErrorActionPreference = "Stop"

$repoRoot = Split-Path -Parent $PSScriptRoot
$backendDir = Join-Path $repoRoot "apps\backend"
$desktopDir = Join-Path $repoRoot "apps\desktop"
$backendDistDir = Join-Path $repoRoot "apps\backend-dist"
$env:ELECTRON_MIRROR = "https://npmmirror.com/mirrors/electron/"
$env:ELECTRON_BUILDER_BINARIES_MIRROR = "https://npmmirror.com/mirrors/electron-builder-binaries/"

Write-Output "Building ExamNova backend executable..."
Push-Location $backendDir
python -m pip install -e .
python -m pip install pyinstaller
if (Test-Path $backendDistDir) {
  Remove-Item -Recurse -Force $backendDistDir
}
pyinstaller `
  --noconfirm `
  --clean `
  --onefile `
  --name examnova-backend `
  --distpath $backendDistDir `
  run_backend.py
Pop-Location

Write-Output "Building ExamNova desktop..."
Push-Location $desktopDir
npm install --cache .npm-cache
npm run build
npx electron-builder --win nsis --config.win.signAndEditExecutable=false
Pop-Location
