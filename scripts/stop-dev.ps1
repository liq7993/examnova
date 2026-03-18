$ErrorActionPreference = "SilentlyContinue"

$ports = 3000, 3001, 8000, 8001

foreach ($port in $ports) {
  $lines = netstat -ano | Select-String ":$port"
  $processIds = @()
  foreach ($line in $lines) {
    $parts = ($line -replace "\s+", " ").Trim().Split(" ")
    $processId = $parts[-1]
    if ($processId -match "^\d+$") {
      $processIds += $processId
    }
  }

  $processIds | Select-Object -Unique | ForEach-Object {
    taskkill /PID $_ /F *> $null
  }
}

Write-Output "Stopped listeners on ports 3000/3001 and 8000/8001 if they were running."
