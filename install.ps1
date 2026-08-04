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
}

# Create Incoming/ and Archive/ at drive root
if (-not (Test-Path "Incoming")) { New-Item -ItemType Directory -Path "Incoming" | Out-Null }
if (-not (Test-Path "Archive")) { New-Item -ItemType Directory -Path "Archive" | Out-Null }

# Download and install portable tools
Write-Host ""
Write-Host "=== Installing portable tools ===" -ForegroundColor Cyan
Write-Host ""

$toolsDir = "$INSTALL_DIR\TakeOutBack\tools\windows"
$pythonDir = "$toolsDir\python"
$sevenZipDir = "$toolsDir\7zip"

# Download Python embeddable (latest stable 3.x)
$pythonUrls = @(
    "https://www.python.org/ftp/python/3.12.4/python-3.12.4-embed-amd64.zip",
    "https://www.python.org/ftp/python/3.11.9/python-3.11.9-embed-amd64.zip",
    "https://www.python.org/ftp/python/3.10.15/python-3.10.15-embed-amd64.zip"
)
$pythonZip = "$INSTALL_DIR\python_embed.zip"
$pythonDownloaded = $false

Write-Host "Downloading Python embeddable..." -ForegroundColor Cyan
foreach ($url in $pythonUrls) {
    try {
        Invoke-WebRequest -Uri $url -OutFile $pythonZip -UseBasicParsing -ErrorAction Stop
        $pythonDownloaded = $true
        Write-Host "Python downloaded successfully." -ForegroundColor Green
        break
    } catch {
        Write-Host "WARNING: Failed to download $url" -ForegroundColor Yellow
        continue
    }
}

if (-not $pythonDownloaded) {
    Write-Host "ERROR: Could not download any Python version." -ForegroundColor Red
    Write-Host "Please install Python manually from https://www.python.org/downloads/" -ForegroundColor Red
    exit 1
}

if (Test-Path $pythonZip) {
    New-Item -ItemType Directory -Force -Path $pythonDir | Out-Null
    try {
        Add-Type -AssemblyName System.IO.Compression.FileSystem
        [System.IO.Compression.ZipFile]::ExtractToDirectory($pythonZip, $pythonDir)
        Remove-Item -Force $pythonZip -ErrorAction SilentlyContinue

        # Enable pip for the embeddable Python
        if (Test-Path "$pythonDir\python.exe") {
            & "$pythonDir\python.exe" -m ensurepip 2>$null
        }
        Write-Host "Python 3.11.5 installed." -ForegroundColor Green
    } catch {
        Write-Host "WARNING: Python extraction failed: $_" -ForegroundColor Yellow
    }
}

# Download 7-Zip (latest stable)
$sevenZipUrls = @(
    "https://www.7-zip.org/a/7z2301-extra.7z",
    "https://www.7-zip.org/a/7z2201-extra.7z",
    "https://www.7-zip.org/a/7z1900-extra.7z"
)
$sevenZipFile = "$INSTALL_DIR\7z.7z"
$sevenZipDownloaded = $false

Write-Host "Downloading 7-Zip..." -ForegroundColor Cyan
foreach ($url in $sevenZipUrls) {
    try {
        Invoke-WebRequest -Uri $url -OutFile $sevenZipFile -UseBasicParsing -ErrorAction Stop
        $sevenZipDownloaded = $true
        Write-Host "7-Zip downloaded successfully." -ForegroundColor Green
        break
    } catch {
        Write-Host "WARNING: Failed to download $url" -ForegroundColor Yellow
        continue
    }
}

if (-not $sevenZipDownloaded) {
    Write-Host "ERROR: Could not download any 7-Zip version." -ForegroundColor Red
    exit 1
}

if (Test-Path $sevenZipFile) {
    New-Item -ItemType Directory -Force -Path $sevenZipDir | Out-Null
    try {
        Add-Type -AssemblyName System.IO.Compression.FileSystem
        [System.IO.Compression.ZipFile]::ExtractToDirectory($sevenZipFile, $sevenZipDir)
        Remove-Item -Force $sevenZipFile -ErrorAction SilentlyContinue
        Write-Host "7-Zip 23.01 installed." -ForegroundColor Green
    } catch {
        Write-Host "WARNING: 7-Zip extraction failed: $_" -ForegroundColor Yellow
    }
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
