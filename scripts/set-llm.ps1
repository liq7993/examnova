$ErrorActionPreference = "Stop"

Write-Output "ExamNova LLM setup (MiniMax)"
$baseUrl = Read-Host "Base URL (default: https://api.minimaxi.com/v1)"
if ([string]::IsNullOrWhiteSpace($baseUrl)) {
  $baseUrl = "https://api.minimaxi.com/v1"
}

$model = Read-Host "Model (default: MiniMax-M2.5)"
if ([string]::IsNullOrWhiteSpace($model)) {
  $model = "MiniMax-M2.5"
}

$demoInput = Read-Host "Demo mode (no external calls) [Y/n]"
$demoMode = $true
if ($demoInput -match '^[Nn]') {
  $demoMode = $false
}

$secureKey = Read-Host "API Key (press Enter to skip in demo mode)" -AsSecureString
$ptr = [Runtime.InteropServices.Marshal]::SecureStringToBSTR($secureKey)
$apiKey = [Runtime.InteropServices.Marshal]::PtrToStringBSTR($ptr)
[Runtime.InteropServices.Marshal]::ZeroFreeBSTR($ptr)

$payload = @{
  provider = "minimax"
  base_url = $baseUrl
  model = $model
  api_key = $apiKey
  demo_mode = $demoMode
} | ConvertTo-Json

$backendUrl = "http://127.0.0.1:8000/api/settings/save"

try {
  Invoke-WebRequest -UseBasicParsing -Uri $backendUrl -Method POST -ContentType "application/json" -Body $payload | Out-Null
  Write-Output "Saved settings via backend API."
} catch {
  $localAppData = if ($env:LOCALAPPDATA) { $env:LOCALAPPDATA } else { Join-Path $HOME "AppData\\Local" }
  $dataDir = Join-Path $localAppData "ExamNova"
  if (!(Test-Path $dataDir)) {
    New-Item -ItemType Directory -Path $dataDir | Out-Null
  }
  $settingsPath = Join-Path $dataDir "settings.json"
  $payload | Out-File -FilePath $settingsPath -Encoding utf8
  Write-Output "Backend not reachable. Saved settings locally to $settingsPath."
}
