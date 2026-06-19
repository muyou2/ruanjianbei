$ErrorActionPreference = "Stop"

# Some Windows hosts expose both "Path" and "PATH". PowerShell 5 treats them
# as duplicate keys when Start-Process builds the child environment.
$MachinePath = [Environment]::GetEnvironmentVariable("Path", "Machine")
$UserPath = [Environment]::GetEnvironmentVariable("Path", "User")
Remove-Item Env:Path -ErrorAction SilentlyContinue
Remove-Item Env:PATH -ErrorAction SilentlyContinue
$env:Path = (($MachinePath, $UserPath) | Where-Object { $_ }) -join ";"

$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
$Backend = Join-Path $Root "backend"
$Frontend = Join-Path $Root "frontend"
$Python = Join-Path $Backend ".venv\Scripts\python.exe"
$Runtime = Join-Path $Backend "runtime"
$BackendLog = Join-Path $Runtime "backend-start.log"
$BackendErrorLog = Join-Path $Runtime "backend-start.error.log"
$FrontendLog = Join-Path $Runtime "frontend-start.log"
$FrontendErrorLog = Join-Path $Runtime "frontend-start.error.log"

function Test-Url([string]$Url) {
    try {
        $response = Invoke-WebRequest -UseBasicParsing -Uri $Url -TimeoutSec 3
        return $response.StatusCode -eq 200
    } catch {
        return $false
    }
}

if (-not (Test-Path $Python)) {
    Write-Host "[1/4] Creating Python virtual environment..."
    python -m venv (Join-Path $Backend ".venv")
}

Write-Host "[2/4] Checking backend dependencies..."
& $Python -m pip install -r (Join-Path $Backend "requirements.txt")

if (-not (Test-Path (Join-Path $Frontend "node_modules"))) {
    Write-Host "[3/4] Installing frontend dependencies..."
    Push-Location $Frontend
    npm.cmd install
    Pop-Location
}

Write-Host "[4/4] Starting Zhixue Ark..."
New-Item -ItemType Directory -Force -Path $Runtime | Out-Null

$BackendReady = Test-Url "http://localhost:8000/api/health"
$FrontendReady = Test-Url "http://localhost:5173"

if ($BackendReady) {
    Write-Host "Backend is already running. Skipping duplicate start."
} else {
    Remove-Item $BackendLog,$BackendErrorLog -ErrorAction SilentlyContinue
    Start-Process -WindowStyle Hidden -FilePath $Python -WorkingDirectory $Backend `
        -ArgumentList "-m", "uvicorn", "app.main:app", "--host", "127.0.0.1", "--port", "8000" `
        -RedirectStandardOutput $BackendLog -RedirectStandardError $BackendErrorLog
}

if ($FrontendReady) {
    Write-Host "Frontend is already running. Skipping duplicate start."
} else {
    Remove-Item $FrontendLog,$FrontendErrorLog -ErrorAction SilentlyContinue
    Start-Process -WindowStyle Hidden -FilePath "npm.cmd" -WorkingDirectory $Frontend `
        -ArgumentList "run", "dev", "--", "--host", "localhost", "--port", "5173", "--strictPort" `
        -RedirectStandardOutput $FrontendLog -RedirectStandardError $FrontendErrorLog
}

Start-Sleep -Seconds 5
$BackendReady = Test-Url "http://localhost:8000/api/health"
$FrontendReady = Test-Url "http://localhost:5173"

if (-not $BackendReady -or -not $FrontendReady) {
    Write-Host ""
    Write-Host "Startup did not complete. Check these logs:" -ForegroundColor Yellow
    if (-not $BackendReady) { Write-Host "Backend logs: $BackendLog / $BackendErrorLog" }
    if (-not $FrontendReady) { Write-Host "Frontend logs: $FrontendLog / $FrontendErrorLog" }
    Write-Host "Common cause: port 5173 or 8000 is occupied by another application."
    exit 1
}

Write-Host ""
Write-Host "Zhixue Ark is ready:" -ForegroundColor Green
Write-Host "Web: http://localhost:5173"
Write-Host "API docs: http://localhost:8000/docs"
