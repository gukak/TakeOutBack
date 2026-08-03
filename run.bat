@echo off
REM Script de lancement pour Windows
REM TakeOutBack - Archivage Google Takeout

echo ========================================
echo   TakeOutBack - Lancement
echo ========================================
echo.

REM Vérifier que Python portable existe
if not exist "Tools\windows\python\python.exe" (
    echo ERREUR: Python portable introuvable!
    echo Exécutez setup.py pour installer les outils portables.
    pause
    exit /b 1
)

REM Lancer le programme avec Python portable
Tools\windows\python\python.exe src\main.py %*

pause
