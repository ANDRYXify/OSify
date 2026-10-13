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
    echo [i] Richiesta privilegi di amministratore (UAC)...
    powershell -Command "Start-Process cmd -ArgumentList '/c \"\"%~f0\"\"' -Verb RunAs"
    exit /b
)

cd /d "%~dp0"

:: 2. Controllo rapido presenza ISO nella cartella
echo [i] Controllo file immagine nella cartella corrente...
set ISO_FOUND=0
for %%f in (*osify*.iso *.iso) do (
    if exist "%%f" (
        echo [✓] Rilevata immagine di sistema: %%f
        set ISO_FOUND=1
    )
)
if %ISO_FOUND% equ 0 (
    echo [i] Nessuna ISO presente in questa cartella.
    echo     L'installer ti permettera' di scaricarla automaticamente da GitHub
    echo     oppure di indicare il percorso se l'hai gia' scaricata altrove.
)
echo.

:: 3. Esecuzione dello script PowerShell con policy bypassata
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0OSify-NoUSB-Installer.ps1"

echo.
pause
