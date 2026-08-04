@echo off
setlocal

set "SCRIPT_DIR=%~dp0"
set "PROJECT_DIR=%SCRIPT_DIR%TakeOutBack"
set "PYTHON=%PROJECT_DIR%\tools\windows\python\python.exe"

if not exist "%PROJECT_DIR%" (
    echo ERROR: TakeOutBack folder not found in %SCRIPT_DIR%
    echo Install TakeOutBack with: install.bat
    pause
    exit /b 1
)

if not exist "%PYTHON%" (
    echo ERROR: Python not found at %PYTHON%
    echo Run setup.py first to install portable tools.
    pause
    exit /b 1
)

cd /d "%PROJECT_DIR%"

if "%1"=="import" (
    echo Importing Takeout exports...
    "%PYTHON%" src\main.py --import
) else if "%1"=="search" (
    if "%2"=="" (
        echo Usage: TakeOutBack.bat search ^<filename^>
        exit /b 1
    )
    "%PYTHON%" src\main.py --search "%2"
) else if "%1"=="verify" (
    echo Verifying integrity...
    "%PYTHON%" src\main.py --verify
) else if "%1"=="stats" (
    "%PYTHON%" src\main.py --stats
) else if "%1"=="update-tools" (
    echo Updating tools...
    "%PYTHON%" src\main.py --update-tools
) else (
    echo === TakeOutBack ===
    echo.
    echo Usage: TakeOutBack.bat [command]
    echo.
    echo Commands:
    echo   import              Import Takeout exports
    echo   search ^<name^>       Search for a file
    echo   verify              Verify integrity
    echo   stats               Show statistics
    echo   update-tools        Update tools
    echo   (no args)           Launch interactive menu
    echo.
    "%PYTHON%" src\main.py
)
