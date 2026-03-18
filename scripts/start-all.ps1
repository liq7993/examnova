$ErrorActionPreference = "Stop"

$root = Join-Path $PSScriptRoot ".."

Start-Process powershell -ArgumentList "-NoExit", "-Command", "Set-Location '$root\apps\backend'; python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload"
Start-Process powershell -ArgumentList "-NoExit", "-Command", "Set-Location '$root\apps\desktop'; npm run dev"

Write-Output "Started backend on http://127.0.0.1:8000 and desktop on http://127.0.0.1:3000 in separate windows."
