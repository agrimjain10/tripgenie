$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$runPath = Join-Path $projectRoot '.run'
New-Item -ItemType Directory -Force -Path $runPath | Out-Null
$pythonPath = Join-Path $projectRoot 'backend\.venv\Scripts\python.exe'
$nodePath = (Get-Command node -ErrorAction Stop).Source
if (-not (Test-Path -LiteralPath $pythonPath)) { throw 'Run the backend setup in README.md first.' }
if (-not (Test-Path -LiteralPath (Join-Path $projectRoot 'frontend\.next\BUILD_ID'))) { Push-Location (Join-Path $projectRoot 'frontend'); try { npm run build; if($LASTEXITCODE -ne 0){throw 'Frontend build failed.'} } finally { Pop-Location } }
if (-not (Get-NetTCPConnection -LocalPort 8000 -State Listen -ErrorAction SilentlyContinue)) {
 Start-Process -FilePath $pythonPath -ArgumentList '-m','uvicorn','main:app','--host','127.0.0.1','--port','8000' -WorkingDirectory (Join-Path $projectRoot 'backend') -WindowStyle Hidden -RedirectStandardOutput (Join-Path $runPath 'backend.log') -RedirectStandardError (Join-Path $runPath 'backend-error.log')
}
if (-not (Get-NetTCPConnection -LocalPort 3000 -State Listen -ErrorAction SilentlyContinue)) {
 $nextScript=Join-Path $projectRoot 'frontend\node_modules\next\dist\bin\next'
 Start-Process -FilePath $nodePath -ArgumentList $nextScript,'start','--port','3000' -WorkingDirectory (Join-Path $projectRoot 'frontend') -WindowStyle Hidden -RedirectStandardOutput (Join-Path $runPath 'frontend.log') -RedirectStandardError (Join-Path $runPath 'frontend-error.log')
}
Write-Output 'TripGenie: http://localhost:3000'
