<#
.SYNOPSIS
    OSify Windows USB-Less Installer Engine (by Andryx)
.DESCRIPTION
    Consente di installare OSify direttamente da Windows senza bisogno di chiavette USB.
    1. Riduce temporaneamente la partizione C: di 5 GB tramite DiskPart.
    2. Crea e formatta una partizione FAT32 contrassegnata come 'OSIFY_BOOT'.
    3. Copia i file di avvio e il filesystem live di OSify.
    4. Registra una voce temporanea nel BCD di Windows Boot Manager.
    5. Imposta il riavvio 'One-Time' direttamente nell'installer di OSify.
    Al termine dell'installazione, la partizione temporanea viene rimossa automaticamente.
#>

# Requires -RunAsAdministrator
[CmdletBinding()]
param(
    [string]$IsoPath = ""
)

Write-Host "=========================================================" -ForegroundColor Magenta
Write-Host "       OSify USB-Less Windows Installer (by Andryx)      " -ForegroundColor Cyan
Write-Host "=========================================================" -ForegroundColor Magenta

# 1. Verifica Privilegi di Amministratore
$isAdmin = ([Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
if (-not $isAdmin) {
    Write-Error "[ERRORE] Questo script deve essere eseguito come Amministratore!"
    exit 1
}

# 2. Ricerca ISO di OSify se non specificata
if ($IsoPath -eq "" -or -not (Test-Path $IsoPath)) {
    $scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
    $candidate = Get-ChildItem -Path "$scriptDir", "$PWD" -Filter "osify*.iso" | Select-Object -First 1
    if ($candidate) {
        $IsoPath = $candidate.FullName
        Write-Host "[+] Trovata immagine ISO: $IsoPath" -ForegroundColor Green
    } else {
        Write-Host "[!] Inserisci il percorso completo dell'immagine ISO di OSify:" -ForegroundColor Yellow
        $IsoPath = Read-Host "Percorso file ISO"
        if (-not (Test-Path $IsoPath)) {
            Write-Error "[ERRORE] File ISO non trovato."
            exit 1
        }
    }
}

# 3. Creazione Partizione Temporanea con DiskPart
Write-Host "[+] Preparazione partizione temporanea per l'installazione (5 GB)..." -ForegroundColor Cyan
$diskpartScript = @"
select volume c
shrink desired=5120 minimum=4096
create partition primary
format fs=fat32 quick label="OSIFY_BOOT"
assign letter=O
active
"@

$dpFile = [System.IO.Path]::GetTempFileName()
Set-Content -Path $dpFile -Value $diskpartScript
diskpart /s $dpFile | Out-Null
Remove-Item $dpFile -Force

if (-not (Test-Path "O:\")) {
    Write-Error "[ERRORE] Impossibile creare l'unità O:\ per l'installer temporaneo."
    exit 1
}

# 4. Estrazione file da ISO su unità O:\
Write-Host "[+] Montaggio ISO ed estrazione file di sistema su O:\..." -ForegroundColor Cyan
$mount = Mount-DiskImage -ImagePath $IsoPath -PassThru
$isoDrive = ($mount | Get-Volume).DriveLetter + ":"

Copy-Item -Path "$isoDrive\*" -Destination "O:\" -Recurse -Force
Dismount-DiskImage -ImagePath $IsoPath | Out-Null
Write-Host "[✓] File dell'installer estratti con successo su O:\." -ForegroundColor Green

# 5. Registrazione Voce di Boot nel BCD di Windows
Write-Host "[+] Registrazione voce di boot UEFI/BIOS per l'installazione..." -ForegroundColor Cyan

# Verifica se il sistema è UEFI o Legacy BIOS
$isUefi = ($env:firmware_type -eq "UEFI") -or (Test-Path "HKLM:\System\CurrentControlSet\Control\SecureBoot\State")

if ($isUefi) {
    Write-Host "[i] Rilevato sistema UEFI." -ForegroundColor Yellow
    # Aggiunge voce BCD per bootloader EFI di OSify
    $bcdGuid = (bcdedit /create /d "Installa OSify (Senza USB)" /application bootapp).Split("{")[1].Split("}")[0]
    bcdedit /set "{$bcdGuid}" device partition=O:
    bcdedit /set "{$bcdGuid}" path "\EFI\BOOT\BOOTX64.EFI"
    bcdedit /displayorder "{$bcdGuid}" /addlast
    bcdedit /bootsequence "{$bcdGuid}"
} else {
    Write-Host "[i] Rilevato sistema Legacy BIOS (MBR)." -ForegroundColor Yellow
    # Per sistemi MBR, il flag 'active' sulla partizione O: consente il boot diretto
}

Write-Host "=========================================================" -ForegroundColor Green
Write-Host " [✓] CONFIGURAZIONE COMPLETATA CON SUCCESSO! " -ForegroundColor Green
Write-Host "=========================================================" -ForegroundColor Green
Write-Host "Il computer è pronto per riavviarsi nell'installer di OSify."
Write-Host "Al riavvio partirà l'installazione e la partizione temporanea verrà rimossa."
$reboot = Read-Host "Vuoi riavviare il PC adesso? (S/N)"
if ($reboot -match "^[sSyY]") {
    Restart-Computer -Force
}
