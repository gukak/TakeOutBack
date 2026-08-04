# TakeOutBack installation script for Windows
# Downloads and installs TakeOutBack on the system

$ErrorActionPreference = "Stop"

$INSTALL_DIR = if ($env:INSTALL_DIR) { $env:INSTALL_DIR } else { (Get-Location).Path }
$REPO_URL = "https://github.com/gukak/TakeOutBack"
$ZIP_URL = "https://github.com/gukak/TakeOutBack/archive/refs/heads/main.zip"
$TEMP_ZIP = "$INSTALL_DIR\takeoutback.zip"

Write-Host "=== TakeOutBack Installation ===" -ForegroundColor Cyan
Write-Host ""

if (-not (Test-Path $INSTALL_DIR)) {
    Write-Host "ERROR: Installation directory does not exist: $INSTALL_DIR" -ForegroundColor Red
    exit 1
}

Set-Location $INSTALL_DIR

Write-Host "Installation directory: $INSTALL_DIR" -ForegroundColor Cyan
Write-Host ""

if (Test-Path "TakeOutBack") {
    Write-Host "TakeOutBack directory already exists." -ForegroundColor Yellow
    $answer = Read-Host "Do you want to reinstall? (y/N)"
    if ($answer -ne 'y' -and $answer -ne 'Y') {
        Write-Host "Installation cancelled."
        exit 0
    }
    Write-Host "Removing old version..."
    Remove-Item -Recurse -Force TakeOutBack
}

Write-Host "Downloading TakeOutBack..." -ForegroundColor Cyan

try {
    Invoke-WebRequest -Uri $ZIP_URL -OutFile $TEMP_ZIP -UseBasicParsing
} catch {
    Write-Host "ERROR: Download failed: $_" -ForegroundColor Red
    exit 1
}

Write-Host "Extracting..."

$extractDir = "$INSTALL_DIR\TakeOutBack-temp"
New-Item -ItemType Directory -Force -Path $extractDir | Out-Null

try {
    Add-Type -AssemblyName System.IO.Compression.FileSystem
    [System.IO.Compression.ZipFile]::ExtractToDirectory($TEMP_ZIP, $extractDir)
} catch {
    Write-Host "ERROR: Decompression failed. Try with 7-Zip first." -ForegroundColor Red
    exit 1
}

$extractedFolder = Get-ChildItem -Path $extractDir -Directory | Select-Object -First 1
if ($extractedFolder) {
    Move-Item -Path $extractedFolder.FullName -Destination "$INSTALL_DIR\TakeOutBack" -Force
} else {
    Write-Host "ERROR: Extracted folder not found." -ForegroundColor Red
    exit 1
}

Remove-Item -Recurse -Force $extractDir
Remove-Item -Force $TEMP_ZIP -ErrorAction SilentlyContinue

if (-not (Test-Path "TakeOutBack")) {
    Write-Host "ERROR: Installation failed." -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "=== Installation complete ===" -ForegroundColor Green
Write-Host ""
Write-Host "Created structure:" -ForegroundColor Cyan
Write-Host "  $INSTALL_DIR\TakeOutBack\    - Software"
Write-Host "  $INSTALL_DIR\Incoming\       - Exports to process"
Write-Host "  $INSTALL_DIR\Archive\        - Archives"
Write-Host ""
Write-Host "Run TakeOutBack with:" -ForegroundColor Cyan
Write-Host "  $INSTALL_DIR\TakeOutBack\TakeOutBack.bat"
Write-Host ""
Write-Host "Or in non-interactive mode:" -ForegroundColor Cyan
Write-Host "  TakeOutBack.bat import"
Write-Host "  TakeOutBack.bat search <name>"
Write-Host "  TakeOutBack.bat verify"
Write-Host "  TakeOutBack.bat stats"
