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

try {
    Add-Type -AssemblyName System.IO.Compression.FileSystem
    [System.IO.Compression.ZipFile]::ExtractToDirectory($TEMP_ZIP, $INSTALL_DIR)
} catch {
    Write-Host "ERROR: Decompression failed. Try with 7-Zip first." -ForegroundColor Red
    Remove-Item -Force $TEMP_ZIP -ErrorAction SilentlyContinue
    exit 1
}

# Rename TakeOutBack-main to TakeOutBack
if (Test-Path "$INSTALL_DIR\TakeOutBack-main") {
    Move-Item -Path "$INSTALL_DIR\TakeOutBack-main" -Destination "$INSTALL_DIR\TakeOutBack" -Force
}

Remove-Item -Force $TEMP_ZIP -ErrorAction SilentlyContinue

if (-not (Test-Path "TakeOutBack")) {
    Write-Host "ERROR: Installation failed." -ForegroundColor Red
    exit 1
}

# Move launcher script to drive root
if (Test-Path "TakeOutBack\TakeOutBack.bat") {
    Move-Item -Path "TakeOutBack\TakeOutBack.bat" -Destination "." -Force
    # Convert LF to CRLF (GitHub ZIPs strip CRLF)
    $bytes = [System.IO.File]::ReadAllBytes("TakeOutBack.bat")
    $newBytes = @()
    for ($i = 0; $i -lt $bytes.Length; $i++) {
        if ($bytes[$i] -eq 0x0A -and ($i + 1 -ge $bytes.Length -or $bytes[$i + 1] -ne 0x0D)) {
            $newBytes += 0x0D
        }
        $newBytes += $bytes[$i]
    }
    [System.IO.File]::WriteAllBytes("TakeOutBack.bat", $newBytes)
}

# Create Incoming/ and Archive/ at drive root
if (-not (Test-Path "Incoming")) { New-Item -ItemType Directory -Path "Incoming" | Out-Null }
if (-not (Test-Path "Archive")) { New-Item -ItemType Directory -Path "Archive" | Out-Null }

# Download portable tools directly from GitHub (no Python required)
Write-Host ""
Write-Host "=== Installing portable tools ===" -ForegroundColor Cyan
Write-Host ""

$TOOLS_DIR = "$INSTALL_DIR\TakeOutBack\tools\windows"
New-Item -ItemType Directory -Path "$TOOLS_DIR\python" -Force | Out-Null
New-Item -ItemType Directory -Path "$TOOLS_DIR\7zip" -Force | Out-Null

# Download Python
Write-Host "Downloading Python..." -ForegroundColor Cyan
$pythonUrl = "https://github.com/gukak/TakeOutBack/raw/main/binaries/windows/python/python-3.13.14-embed-amd64.zip"
$pythonDest = "$TOOLS_DIR\python\python-3.13.14-embed-amd64.zip"
try {
    Invoke-WebRequest -Uri $pythonUrl -OutFile $pythonDest -UseBasicParsing
} catch {
    Write-Host "ERROR: Failed to download Python: $_" -ForegroundColor Red
    exit 1
}

Write-Host "Extracting Python..." -ForegroundColor Cyan
try {
    Add-Type -AssemblyName System.IO.Compression.FileSystem
    [System.IO.Compression.ZipFile]::ExtractToDirectory($pythonDest, "$TOOLS_DIR\python")
    Remove-Item -Force $pythonDest -ErrorAction SilentlyContinue
} catch {
    Write-Host "ERROR: Failed to extract Python: $_" -ForegroundColor Red
    exit 1
}

# Download 7-Zip
Write-Host "Downloading 7-Zip..." -ForegroundColor Cyan
$sevenZipUrl = "https://github.com/gukak/TakeOutBack/raw/main/binaries/windows/7zip/7z2301.exe"
$sevenZipDest = "$TOOLS_DIR\7zip\7z.exe"
try {
    Invoke-WebRequest -Uri $sevenZipUrl -OutFile $sevenZipDest -UseBasicParsing
} catch {
    Write-Host "ERROR: Failed to download 7-Zip: $_" -ForegroundColor Red
    exit 1
}

Write-Host "Portable tools installed." -ForegroundColor Green

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
