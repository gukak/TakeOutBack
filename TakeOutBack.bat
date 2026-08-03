@echo off
setlocal

set "SCRIPT_DIR=%~dp0"
set "PROJECT_DIR=%SCRIPT_DIR%TakeOutBack"

if not exist "%PROJECT_DIR%" (
    echo ERREUR: Dossier TakeOutBack introuvable dans %SCRIPT_DIR%
    echo Installez TakeOutBack avec: install.bat
    pause
    exit /b 1
)

cd /d "%PROJECT_DIR%"

if "%1"=="import" (
    echo Import des exports Takeout...
    python src/main.py --import
) else if "%1"=="search" (
    if "%2"=="" (
        echo Usage: TakeOutBack.bat search ^<nom_de_fichier^>
        exit /b 1
    )
    python src/main.py --search "%2"
) else if "%1"=="verify" (
    echo Verification d'integrite...
    python src/main.py --verify
) else if "%1"=="stats" (
    python src/main.py --stats
) else if "%1"=="update-tools" (
    echo Mise a jour des outils...
    python src/main.py --update-tools
) else (
    echo === TakeOutBack ===
    echo.
    echo Usage: TakeOutBack.bat [command]
    echo.
    echo Commands:
    echo   import              Import Google Takeout exports
    echo   search ^<name^>        Search for a file
    echo   verify              Verify integrity
    echo   stats               Show statistics
    echo   update-tools        Update tools
    echo   (no args)           Launch interactive menu
    echo.
    python src/main.py
)
