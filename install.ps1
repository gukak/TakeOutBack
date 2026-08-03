# Script d'installation de TakeOutBack pour Windows
# Télécharge et installe TakeOutBack sur le système

$ErrorActionPreference = "Stop"

$INSTALL_DIR = if ($env:INSTALL_DIR) { $env:INSTALL_DIR } else { (Get-Location).Path }
$REPO_URL = "https://github.com/gukak/TakeOutBack"
$ZIP_URL = "https://github.com/gukak/TakeOutBack/archive/refs/heads/main.zip"
$TEMP_ZIP = "$INSTALL_DIR\takeoutback.zip"

Write-Host "=== Installation de TakeOutBack ===" -ForegroundColor Cyan
Write-Host ""

if (-not (Test-Path $INSTALL_DIR)) {
    Write-Host "ERREUR: Le dossier d'installation n'existe pas: $INSTALL_DIR" -ForegroundColor Red
    exit 1
}

Set-Location $INSTALL_DIR

Write-Host "Dossier d'installation: $INSTALL_DIR" -ForegroundColor Cyan
Write-Host ""

if (Test-Path "TakeOutBack") {
    Write-Host "Un dossier TakeOutBack existe déjà." -ForegroundColor Yellow
    $answer = Read-Host "Voulez-vous le réinstaller ? (o/N)"
    if ($answer -ne 'o' -and $answer -ne 'O') {
        Write-Host "Installation annulée."
        exit 0
    }
    Write-Host "Suppression de l'ancienne version..."
    Remove-Item -Recurse -Force TakeOutBack
}

Write-Host "Téléchargement de TakeOutBack..." -ForegroundColor Cyan

try {
    Invoke-WebRequest -Uri $ZIP_URL -OutFile $TEMP_ZIP -UseBasicParsing
} catch {
    Write-Host "ERREUR: Échec du téléchargement: $_" -ForegroundColor Red
    exit 1
}

Write-Host "Décompression..."

$extractDir = "$INSTALL_DIR\TakeOutBack-temp"
New-Item -ItemType Directory -Force -Path $extractDir | Out-Null

try {
    Add-Type -AssemblyName System.IO.Compression.FileSystem
    [System.IO.Compression.ZipFile]::ExtractToDirectory($TEMP_ZIP, $extractDir)
} catch {
    Write-Host "ERREUR: Échec de la décompression. Essayez avec 7-Zip d'abord." -ForegroundColor Red
    exit 1
}

$extractedFolder = Get-ChildItem -Path $extractDir -Directory | Select-Object -First 1
if ($extractedFolder) {
    Move-Item -Path $extractedFolder.FullName -Destination "$INSTALL_DIR\TakeOutBack" -Force
} else {
    Write-Host "ERREUR: Dossier extrait introuvable." -ForegroundColor Red
    exit 1
}

Remove-Item -Recurse -Force $extractDir
Remove-Item -Force $TEMP_ZIP -ErrorAction SilentlyContinue

if (-not (Test-Path "TakeOutBack")) {
    Write-Host "ERREUR: Échec de l'installation." -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "=== Installation terminée ===" -ForegroundColor Green
Write-Host ""
Write-Host "Structure créée :" -ForegroundColor Cyan
Write-Host "  $INSTALL_DIR\TakeOutBack\    - Logiciel"
Write-Host "  $INSTALL_DIR\Incoming\       - Exports à traiter"
Write-Host "  $INSTALL_DIR\Archive\        - Archives"
Write-Host ""
Write-Host "Lancez TakeOutBack avec:" -ForegroundColor Cyan
Write-Host "  $INSTALL_DIR\TakeOutBack\TakeOutBack.bat"
Write-Host ""
Write-Host "Ou en mode non-interactive:" -ForegroundColor Cyan
Write-Host "  TakeOutBack.bat import"
Write-Host "  TakeOutBack.bat search <nom>"
Write-Host "  TakeOutBack.bat verify"
Write-Host "  TakeOutBack.bat stats"
