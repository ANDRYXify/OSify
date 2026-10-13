@echo off
:: ==============================================================================
:: OSify Windows No-USB Installer Launcher (by Andryx)
:: ==============================================================================
:: Compatibilita universale: Windows 7 SP1, Windows 8, Windows 10, Windows 11
:: ==============================================================================

title OSify Windows Installer - by Andryx
color 0B

:: 1. Controllo Privilegi di Amministratore
net session >nul 2>&1
if %errorlevel% equ 0 goto :RUN_INSTALLER

echo [i] Richiesta privilegi di amministratore UAC in corso...
powershell.exe -Command "Start-Process cmd -ArgumentList '/c \"\"%~f0\"\"' -Verb RunAs"
exit /b

:RUN_INSTALLER
cd /d "%~dp0"

echo =========================================================
echo        OSify Windows Installer Launcher (by Andryx)      
echo =========================================================
echo.

:: 2. Avvio prioritario Interfaccia Grafica WPF
if exist "%~dp0OSify-Windows-Installer-GUI.ps1" (
    echo [i] Avvio interfaccia grafica OSify in corso...
    powershell.exe -NoProfile -ExecutionPolicy Bypass -STA -File "%~dp0OSify-Windows-Installer-GUI.ps1"
    if %errorlevel% equ 0 exit /b
)

:: 3. Fallback automatico su console testuale
echo [i] Avvio installer in modalita console guidata...
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0OSify-NoUSB-Installer.ps1"

echo.
pause
