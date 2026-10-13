@echo off
:: ==============================================================================
:: OSify Windows No-USB Installer Launcher (by Andryx)
:: ==============================================================================
:: Avvia l'installer di OSify con elevazione automatica dei privilegi di amministratore
:: e sblocco della ExecutionPolicy di PowerShell.
:: ==============================================================================

title OSify Windows Installer - by Andryx
color 0B

echo =========================================================
echo        OSify Windows Installer Launcher (by Andryx)      
echo =========================================================
echo.

:: 1. Verifica ed elevazione privilegi di Amministratore (UAC)
net session >nul 2>&1
if %errorLevel% neq 0 (
    echo [i] Richiesta privilegi di amministratore in corso...
    powershell -Command "Start-Process cmd -ArgumentList '/c \"\"%~f0\"\"' -Verb RunAs"
    exit /b
)

:: 2. Esecuzione dello script PowerShell con policy bypassata
cd /d "%~dp0"
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0OSify-NoUSB-Installer.ps1"

echo.
pause
