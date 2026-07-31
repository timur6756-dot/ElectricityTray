$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot

Write-Host ""
Write-Host "========================================"
Write-Host " ElectricityTray build"
Write-Host "========================================"
Write-Host ""

$Python = Join-Path $PSScriptRoot ".venv\Scripts\python.exe"
$Icon = Join-Path $PSScriptRoot "assets\ElectricityTray.ico"
$Version = Join-Path $PSScriptRoot "version_info.txt"

if (-not (Test-Path $Python)) { throw ".venv Python not found: $Python" }
if (-not (Test-Path $Icon)) { throw "Icon not found: $Icon" }
if (-not (Test-Path $Version)) { throw "version_info.txt not found" }

Write-Host "Using Python:"
& $Python --version

Write-Host ""
Write-Host "Cleaning previous build..."
Remove-Item -Recurse -Force "build" -ErrorAction SilentlyContinue
Remove-Item -Recurse -Force "dist" -ErrorAction SilentlyContinue
Remove-Item -Force "ElectricityTray.spec" -ErrorAction SilentlyContinue

Write-Host "Building ElectricityTray.exe..."
& $Python -m PyInstaller `
    --clean `
    --noconfirm `
    --noconsole `
    --onefile `
    --name ElectricityTray `
    --icon $Icon `
    --version-file $Version `
    --collect-all PIL `
    --collect-all pystray `
    --collect-all tzdata `
    main.py

if ($LASTEXITCODE -ne 0) { throw "PyInstaller build failed." }

$Exe = Join-Path $PSScriptRoot "dist\ElectricityTray.exe"
if (-not (Test-Path $Exe)) { throw "EXE was not created." }

Write-Host ""
Write-Host "BUILD SUCCESSFUL:"
Write-Host $Exe
Write-Host ""
