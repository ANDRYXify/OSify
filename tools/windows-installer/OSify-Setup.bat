@echo off
:: ==============================================================================
:: OSify Windows No-USB Installer Launcher (by Andryx)
:: ==============================================================================
:: Avvia l'installer grafico di OSify con elevazione automatica dei privilegi
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
    echo [i] Richiesta privilegi di amministratore (UAC)...
    powershell -Command "Start-Process cmd -ArgumentList '/c \"\"%~f0\"\"' -Verb RunAs"
    exit /b
)

cd /d "%~dp0"

:: 2. Avvio Interfaccia Grafica Moderna (WPF Cyberpunk Theme)
echo [i] Avvio interfaccia grafica di installazione OSify in corso...
if exist "%~dp0OSify-Windows-Installer-GUI.ps1" (
    powershell.exe -NoProfile -ExecutionPolicy Bypass -STA -File "%~dp0OSify-Windows-Installer-GUI.ps1"
    if %errorLevel% equ 0 exit /b
)

:: 3. Fallback Modalita Testuale se la GUI non e disponibile
echo [i] Avvio modalita guidata da riga di comando...
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0OSify-NoUSB-Installer.ps1"

echo.
pause
