$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
$Backend = Join-Path $Root "backend"
$Frontend = Join-Path $Root "frontend"
$Python = Join-Path $Backend ".venv\Scripts\python.exe"

if (-not (Test-Path $Python)) {
    Write-Host "[1/4] 创建 Python 虚拟环境..."
    python -m venv (Join-Path $Backend ".venv")
}

Write-Host "[2/4] 安装/检查后端依赖..."
& $Python -m pip install -r (Join-Path $Backend "requirements.txt")

if (-not (Test-Path (Join-Path $Frontend "node_modules"))) {
    Write-Host "[3/4] 安装前端依赖..."
    Push-Location $Frontend
    npm.cmd install
    Pop-Location
}

Write-Host "[4/4] 启动智学方舟..."
Start-Process -WindowStyle Hidden -FilePath $Python -WorkingDirectory $Backend -ArgumentList "-m", "uvicorn", "app.main:app", "--reload", "--port", "8000"
Start-Process -WindowStyle Hidden -FilePath "npm.cmd" -WorkingDirectory $Frontend -ArgumentList "run", "dev"
Start-Sleep -Seconds 3
Write-Host "前端：http://localhost:5173"
Write-Host "后端文档：http://localhost:8000/docs"
