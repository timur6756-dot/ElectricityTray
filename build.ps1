$ErrorActionPreference = "Stop"

Set-Location $PSScriptRoot

Write-Host ""
Write-Host "========================================"
Write-Host " ElectricityTray build"
Write-Host "========================================"
Write-Host ""

# ==========================================================
# Paths
# ==========================================================

$Python = Join-Path $PSScriptRoot ".venv\Scripts\python.exe"
$Icon = Join-Path $PSScriptRoot "assets\ElectricityTray.ico"
$VersionFile = Join-Path $PSScriptRoot "version.txt"
$VersionInfo = Join-Path $PSScriptRoot "version_info.txt"
$MainFile = Join-Path $PSScriptRoot "main.py"

# ==========================================================
# Check required files
# ==========================================================

if (-not (Test-Path $Python)) {
    throw ".venv Python not found: $Python"
}

if (-not (Test-Path $Icon)) {
    throw "Icon not found: $Icon"
}

if (-not (Test-Path $VersionFile)) {
    throw "version.txt not found: $VersionFile"
}

if (-not (Test-Path $MainFile)) {
    throw "main.py not found: $MainFile"
}

# ==========================================================
# Read application version
# ==========================================================

$AppVersion = (Get-Content $VersionFile -Raw).Trim()

if ($AppVersion -notmatch '^\d+\.\d+\.\d+$') {
    throw "Invalid version in version.txt: $AppVersion"
}

$VersionParts = $AppVersion.Split(".")

$VersionMajor = [int]$VersionParts[0]
$VersionMinor = [int]$VersionParts[1]
$VersionPatch = [int]$VersionParts[2]

$AppName = "ElectricityTray"
$BuildName = "${AppName}_${AppVersion}"

Write-Host "Application:"
Write-Host "  $AppName"
Write-Host ""

Write-Host "Version:"
Write-Host "  $AppVersion"
Write-Host ""

Write-Host "Output:"
Write-Host "  ${BuildName}.exe"
Write-Host ""

# ==========================================================
# Check whether application is running
# ==========================================================

$RunningProcess = Get-Process `
    -Name $BuildName `
    -ErrorAction SilentlyContinue

if ($RunningProcess) {

    Write-Host ""
    Write-Host "ERROR: ${BuildName}.exe is currently running."
    Write-Host "Close ElectricityTray from the system tray"
    Write-Host "and run build.ps1 again."
    Write-Host ""

    exit 1
}

# Also check older/version-independent builds.

$OtherProcesses = Get-Process `
    -ErrorAction SilentlyContinue |
    Where-Object {
        $_.ProcessName -eq "ElectricityTray" -or
        $_.ProcessName -like "ElectricityTray_*"
    }

if ($OtherProcesses) {

    Write-Host ""
    Write-Host "ERROR: Another ElectricityTray version is running:"
    
    foreach ($Process in $OtherProcesses) {
        Write-Host "  $($Process.ProcessName)"
    }

    Write-Host ""
    Write-Host "Close ElectricityTray from the system tray"
    Write-Host "and run build.ps1 again."
    Write-Host ""

    exit 1
}

# ==========================================================
# Generate Windows version_info.txt
# ==========================================================

Write-Host "Generating Windows version information..."

$VersionInfoContent = @"
# UTF-8
VSVersionInfo(
  ffi=FixedFileInfo(
    filevers=($VersionMajor, $VersionMinor, $VersionPatch, 0),
    prodvers=($VersionMajor, $VersionMinor, $VersionPatch, 0),
    mask=0x3f,
    flags=0x0,
    OS=0x40004,
    fileType=0x1,
    subtype=0x0,
    date=(0, 0)
  ),
  kids=[
    StringFileInfo([
      StringTable(
        '040904B0',
        [
          StringStruct('CompanyName', 'ElectricityTray'),
          StringStruct(
            'FileDescription',
            'Estonia electricity price tray application'
          ),
          StringStruct('FileVersion', '$AppVersion'),
          StringStruct('InternalName', 'ElectricityTray'),
          StringStruct(
            'LegalCopyright',
            'Copyright © 2026'
          ),
          StringStruct(
            'OriginalFilename',
            '${BuildName}.exe'
          ),
          StringStruct(
            'ProductName',
            'ElectricityTray'
          ),
          StringStruct(
            'ProductVersion',
            '$AppVersion'
          )
        ]
      )
    ]),
    VarFileInfo([
      VarStruct(
        'Translation',
        [1033, 1200]
      )
    ])
  ]
)
"@

Set-Content `
    -Path $VersionInfo `
    -Value $VersionInfoContent `
    -Encoding UTF8

Write-Host "Version information generated."
Write-Host ""

# ==========================================================
# Python information
# ==========================================================

Write-Host "Using Python:"
& $Python --version
Write-Host ""

# ==========================================================
# Clean previous build
# ==========================================================

Write-Host "Cleaning previous build..."

Remove-Item `
    -Recurse `
    -Force `
    "build" `
    -ErrorAction SilentlyContinue

Remove-Item `
    -Recurse `
    -Force `
    "dist" `
    -ErrorAction SilentlyContinue

Remove-Item `
    -Force `
    "*.spec" `
    -ErrorAction SilentlyContinue

Write-Host "Cleanup complete."
Write-Host ""

# ==========================================================
# Build
# ==========================================================

Write-Host "Building ${BuildName}.exe..."
Write-Host ""

& $Python -m PyInstaller `
    --clean `
    --noconfirm `
    --noconsole `
    --onefile `
    --name $BuildName `
    --icon $Icon `
    --version-file $VersionInfo `
    --collect-all PIL `
    --collect-all pystray `
    --collect-all tzdata `
    main.py

if ($LASTEXITCODE -ne 0) {
    throw "PyInstaller build failed."
}

# ==========================================================
# Verify result
# ==========================================================

$Exe = Join-Path `
    $PSScriptRoot `
    "dist\${BuildName}.exe"

if (-not (Test-Path $Exe)) {
    throw "EXE was not created: $Exe"
}

$ExeInfo = Get-Item $Exe

$SizeMB = [math]::Round(
    $ExeInfo.Length / 1MB,
    2
)

# ==========================================================
# Success
# ==========================================================

Write-Host ""
Write-Host "========================================"
Write-Host " BUILD SUCCESSFUL"
Write-Host "========================================"
Write-Host ""

Write-Host "Application:"
Write-Host "  $AppName"

Write-Host ""

Write-Host "Version:"
Write-Host "  $AppVersion"

Write-Host ""

Write-Host "Executable:"
Write-Host "  $Exe"

Write-Host ""

Write-Host "Size:"
Write-Host "  $SizeMB MB"

Write-Host ""
Write-Host "========================================"
Write-Host ""