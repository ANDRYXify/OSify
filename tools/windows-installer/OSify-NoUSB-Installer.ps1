# ==============================================================================
# OSify Windows USB-Less Installer Engine (by Andryx)
# ==============================================================================
# Consente di installare OSify direttamente da Windows senza bisogno di chiavette USB:
# 1. Riduce temporaneamente la partizione C: di 5 GB tramite DiskPart.
# 2. Crea e formatta una partizione FAT32 contrassegnata come 'OSIFY_BOOT'.
# 3. Estrae i file di avvio e il filesystem live di OSify dall'immagine ISO.
# 4. Registra una voce di avvio nel Boot Manager di Windows (BCD).
# 5. Imposta il riavvio diretto nell'installer di OSify.
# ==============================================================================

param(
    [string]$IsoPath = ""
)

$ErrorActionPreference = "Stop"

Write-Host "=========================================================" -ForegroundColor Magenta
Write-Host "       OSify USB-Less Windows Installer (by Andryx)      " -ForegroundColor Cyan
Write-Host "=========================================================" -ForegroundColor Magenta
Write-Host ""

# 1. Verifica Privilegi di Amministratore
$isAdmin = ([Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
if (-not $isAdmin) {
    Write-Host "[ERRORE] Questo installer richiede privilegi di amministratore." -ForegroundColor Red
    Write-Host "Fai click destro su OSify-Setup.bat e scegli 'Esegui come amministratore'." -ForegroundColor Yellow
    exit 1
}

# 2. Diagnostica Architettura Hardware (32-bit vs 64-bit)
$proc = Get-WmiObject Win32_Processor | Select-Object -First 1
$is64BitCapable = ($env:PROCESSOR_ARCHITECTURE -eq "AMD64") -or ($env:PROCESSOR_ARCHITEW6432 -eq "AMD64") -or ($proc.AddressWidth -eq 64)
$cpuName = $proc.Name

Write-Host "[+] Processore Rilevato: $cpuName" -ForegroundColor Cyan

if (-not $is64BitCapable) {
    Write-Host ""
    Write-Host "=========================================================" -ForegroundColor Red
    Write-Host " [ATTENZIONE CRITICA ARCHITETTURA 32-BIT - i686]         " -ForegroundColor Red
    Write-Host "=========================================================" -ForegroundColor Red
    Write-Host "La CPU di questo computer e pura a 32-bit (es. Intel Atom N270 o N280)!" -ForegroundColor Yellow
    Write-Host "La versione standard di OSify a 64-bit non puo avviarsi su questo netbook." -ForegroundColor Yellow
    Write-Host "E richiesta la variante: OSify Vintage 32-Bit Micro-Edition." -ForegroundColor Yellow
    Write-Host ""
}

# 3. Configurazione Sicurezza TLS per download su Windows 7 / 8 / 10
try {
    [System.Net.ServicePointManager]::SecurityProtocol = [System.Net.ServicePointManager]::SecurityProtocol -bor 3072
} catch {}

# 4. Ricerca o Acquisizione dell'Immagine ISO di Sistema
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path

function Search-LocalIso {
    $userProf = if ($env:USERPROFILE) { $env:USERPROFILE } else { [Environment]::GetFolderPath("UserProfile") }
    $searchPaths = @(
        $scriptDir,
        $PWD.Path,
        "$userProf\Downloads",
        "$userProf\Desktop"
    )

    foreach ($p in $searchPaths) {
        if (Test-Path $p) {
            $found = Get-ChildItem -Path $p -Filter "*.iso" -ErrorAction SilentlyContinue | Where-Object { $_.Name -like "*osify*" -or $_.Name -like "*OSify*" } | Select-Object -First 1
            if ($found) {
                return $found.FullName
            }
        }
    }
    return $null
}

if ($IsoPath -eq "" -or -not (Test-Path $IsoPath)) {
    $localCandidate = Search-LocalIso
    if ($localCandidate) {
        Write-Host "[+] Trovata immagine ISO di OSify: $localCandidate" -ForegroundColor Green
        $IsoPath = $localCandidate
    } else {
        Write-Host ""
        Write-Host "=========================================================" -ForegroundColor Yellow
        Write-Host " [ACQUISIZIONE IMMAGINE SISTEMA OPERATIVO OSIFY]         " -ForegroundColor Yellow
        Write-Host "=========================================================" -ForegroundColor Yellow
        Write-Host "L'installer per funzionare necessita del file ISO di sistema di OSify."
        Write-Host "Scegli come procedere:"
        Write-Host "  1) Scarica automaticamente la ISO da GitHub Releases"
        Write-Host "  2) Apri la pagina ufficiale delle release nel browser per scaricarla"
        Write-Host "  3) Seleziona manualmente un file ISO presente sul computer"
        Write-Host ""
        $choice = Read-Host "Seleziona opzione [1, 2, 3]"

        if ($choice -eq "1") {
            $destIso = Join-Path $scriptDir "OSify-x86_64-v3.iso"
            $url = "https://github.com/ANDRYXify/OSify/releases/latest/download/OSify-x86_64-v3.iso"
            if (-not $is64BitCapable) {
                $destIso = Join-Path $scriptDir "OSify-Vintage-i686.iso"
                $url = "https://github.com/ANDRYXify/OSify/releases/latest/download/OSify-Vintage-i686.iso"
            }
            Write-Host "[+] Download in corso da: $url" -ForegroundColor Cyan
            Write-Host "[+] Salvataggio in: $destIso" -ForegroundColor Cyan
            Write-Host "[i] L'operazione potrebbe richiedere alcuni minuti a seconda della connessione..." -ForegroundColor Gray
            try {
                $wc = New-Object System.Net.WebClient
                $wc.DownloadFile($url, $destIso)
                $IsoPath = $destIso
                Write-Host "[OK] Download completato con successo!" -ForegroundColor Green
            } catch {
                Write-Host "[!] Download automatico non riuscito: $($_.Exception.Message)" -ForegroundColor Red
                Write-Host "[i] Apertura pagina delle release nel browser..." -ForegroundColor Yellow
                Start-Process "https://github.com/ANDRYXify/OSify/releases"
                $IsoPath = Read-Host "Inserisci il percorso del file ISO scaricato"
            }
        } elseif ($choice -eq "2") {
            Start-Process "https://github.com/ANDRYXify/OSify/releases"
            Write-Host "[i] Scarica la ISO di OSify e poi indica il percorso qui sotto." -ForegroundColor Cyan
            $IsoPath = Read-Host "Percorso file ISO (es. C:\Downloads\OSify.iso)"
        } else {
            $IsoPath = Read-Host "Inserisci il percorso completo del file ISO"
        }

        # Pulizia apici se l'utente ha fatto drag-and-drop del file nella finestra
        if ($IsoPath -ne $null) {
            $IsoPath = $IsoPath.Trim().Trim('"').Trim("'")
        }

        if (-not (Test-Path $IsoPath)) {
            Write-Host "[ERRORE] File ISO non trovato o percorso non valido: $IsoPath" -ForegroundColor Red
            exit 1
        }
    }
}

Write-Host "[OK] Immagine ISO selezionata: $IsoPath" -ForegroundColor Green
Write-Host ""

# 5. Creazione Partizione Temporanea di Boot con DiskPart
$isoLengthMB = 800
if ($IsoPath -and (Test-Path $IsoPath)) {
    $isoLengthMB = [math]::Round((Get-Item $IsoPath).Length / 1MB)
}
$neededMB = [math]::Max(1200, $isoLengthMB + 350)
Write-Host "[+] Preparazione partizione temporanea per installazione ($neededMB MB richiesti)..." -ForegroundColor Cyan

$partitionReady = $false

# Se l'unità O: esiste già, formattala e riusala direttamente
if (Test-Path 'O:\') {
    Write-Host "[i] Partizione (O:) gia' esistente. Formattazione rapida per installazione..." -ForegroundColor Yellow
    $dpCleanFile = Join-Path $env:TEMP "osify_clean_dp.txt"
    $dpCleanCommands = @(
        "select volume O",
        "format fs=fat32 quick label=OSIFY_BOOT",
        "active"
    )
    [System.IO.File]::WriteAllLines($dpCleanFile, $dpCleanCommands)
    $pInfo = New-Object System.Diagnostics.ProcessStartInfo
    $pInfo.FileName = "diskpart.exe"
    $pInfo.Arguments = "/s `"$dpCleanFile`""
    $pInfo.UseShellExecute = $false
    $pInfo.CreateNoWindow = $true
    $procDp = [System.Diagnostics.Process]::Start($pInfo)
    $procDp.WaitForExit()
    Remove-Item $dpCleanFile -Force -ErrorAction SilentlyContinue
    if (Test-Path 'O:\') {
        $partitionReady = $true
        Write-Host "[OK] Unita (O:) pronta all'uso." -ForegroundColor Green
    }
}

if (-not $partitionReady) {
    $dpFile = Join-Path $env:TEMP "osify_diskpart.txt"
    $dpCommands = @(
        "select volume c",
        "shrink desired=$neededMB minimum=800",
        "create partition primary",
        "format fs=fat32 quick label=OSIFY_BOOT",
        "assign letter=O",
        "active"
    )
    [System.IO.File]::WriteAllLines($dpFile, $dpCommands)

    $pInfo = New-Object System.Diagnostics.ProcessStartInfo
    $pInfo.FileName = "diskpart.exe"
    $pInfo.Arguments = "/s `"$dpFile`""
    $pInfo.UseShellExecute = $false
    $pInfo.CreateNoWindow = $true
    $procDp = [System.Diagnostics.Process]::Start($pInfo)
    $procDp.WaitForExit()
    Remove-Item $dpFile -Force -ErrorAction SilentlyContinue

    if (Test-Path 'O:\') {
        $partitionReady = $true
        Write-Host "[OK] Partizione di avvio (O:) creata e formattata con successo." -ForegroundColor Green
    }
}

if (-not (Test-Path 'O:\')) {
    Write-Host "[ERRORE] Impossibile creare l'unita (O:) per l'avvio temporaneo." -ForegroundColor Red
    Write-Host "Verifica lo spazio libero su C: o se il disco MBR ha gia' raggiunto il limite di 4 partizioni." -ForegroundColor Yellow
    exit 1
}

# 6. Estrazione File da ISO verso l'unità O:\
Write-Host "[+] Estrazione dei file del sistema operativo su unita O:\..." -ForegroundColor Cyan

$extracted = $false

# Metodo A: 7za.exe standalone locale incluso nel pacchetto (100% offline)
$local7za = Join-Path $scriptDir "7za.exe"
if (Test-Path $local7za) {
    Write-Host "[i] Estrazione rapida tramite 7za integrato offline..." -ForegroundColor Cyan
    & $local7za x $IsoPath -oO:\ -y | Out-Null
    if ((Test-Path 'O:\boot') -or (Test-Path 'O:\EFI') -or (Test-Path 'O:\arch') -or (Test-Path 'O:\osify')) {
        $extracted = $true
        Write-Host "[OK] File estratti con successo tramite 7za locale!" -ForegroundColor Green
    }
}

# Metodo B: 7-Zip locale di sistema (se installato su Windows 7 / 8 / 10 / 11)
if (-not $extracted) {
    $7zPaths = @(
        "$env:ProgramFiles\7-Zip\7z.exe",
        "${env:ProgramFiles(x86)}\7-Zip\7z.exe",
        Join-Path $scriptDir "7z.exe"
    )
    foreach ($exe in $7zPaths) {
        if (Test-Path $exe) {
            Write-Host "[i] Estrazione ISO in corso tramite 7-Zip ($exe)..." -ForegroundColor Cyan
            & $exe x $IsoPath -oO:\ -y | Out-Null
            if ((Test-Path 'O:\boot') -or (Test-Path 'O:\EFI') -or (Test-Path 'O:\arch') -or (Test-Path 'O:\osify')) {
                $extracted = $true
                Write-Host "[OK] File estratti con successo tramite 7-Zip!" -ForegroundColor Green
                break
            }
        }
    }
}

# Metodo C: Mount-DiskImage (Windows 8, 10, 11)
if (-not $extracted -and (Get-Command "Mount-DiskImage" -ErrorAction SilentlyContinue)) {
    try {
        Write-Host "[i] Tentativo montaggio ISO tramite Windows DiskImage..." -ForegroundColor Gray
        $mount = Mount-DiskImage -ImagePath $IsoPath -PassThru
        $isoVol = $mount | Get-Volume
        if ($isoVol -and $isoVol.DriveLetter) {
            $isoDrive = $isoVol.DriveLetter + ':\'
            Copy-Item -Path "$isoDrive*" -Destination 'O:\' -Recurse -Force
            Dismount-DiskImage -ImagePath $IsoPath | Out-Null
            $extracted = $true
            Write-Host "[OK] File estratti tramite montaggio nativo." -ForegroundColor Green
        }
    } catch {}
}

if (-not $extracted) {
    Write-Host "[ERRORE] Impossibile estrarre automaticamente la ISO sull'unita (O:)." -ForegroundColor Red
    Write-Host "Puoi estrarre manualmente i file contenuti in $IsoPath all'interno del disco (O:) e rieseguire lo script." -ForegroundColor Yellow
    exit 1
}

# 7. Registrazione Voce di Avvio nel Boot Manager di Windows (BCD)
Write-Host "[+] Configurazione voce di avvio nel Boot Manager..." -ForegroundColor Cyan

$isUefi = $false
if ($env:firmware_type -eq "UEFI" -or (Test-Path "HKLM:\System\CurrentControlSet\Control\SecureBoot\State")) {
    $isUefi = $true
}

if ($isUefi -and (Test-Path 'O:\EFI\BOOT\BOOTX64.EFI')) {
    Write-Host "[i] Sistema UEFI rilevato: creazione entry BCD per BOOTX64.EFI..." -ForegroundColor Yellow
    try {
        $bcdOut = bcdedit /create /d "Installa OSify (Senza USB)" /application bootapp
        $guidMatch = [System.Text.RegularExpressions.Regex]::Match($bcdOut, '\{([0-9a-fA-F-]+)\}')
        if ($guidMatch.Success) {
            $guid = $guidMatch.Value
            bcdedit /set $guid device partition=O:
            bcdedit /set $guid path '\EFI\BOOT\BOOTX64.EFI'
            bcdedit /displayorder $guid /addlast
            bcdedit /bootsequence $guid
            Write-Host "[OK] Voce di boot UEFI registrata con successo: $guid" -ForegroundColor Green
        } else {
            Write-Host "[!] Nota: GUID non trovato in output bcdedit, avvio tramite partizione attiva." -ForegroundColor Yellow
        }
    } catch {
        Write-Host "[!] Nota: Configurazione BCD facoltativa: $($_.Exception.Message)" -ForegroundColor Yellow
    }
} else {
    Write-Host "[i] Sistema Legacy BIOS (MBR) rilevato (es. Toshiba Netbook)." -ForegroundColor Yellow
    Write-Host "[OK] La partizione (O:) e stata contrassegnata come 'Attiva' per il boot diretto." -ForegroundColor Green
}

Write-Host ""
Write-Host "=========================================================" -ForegroundColor Green
Write-Host " [OK] CONFIGURAZIONE COMPLETATA CON SUCCESSO! " -ForegroundColor Green
Write-Host "=========================================================" -ForegroundColor Green
Write-Host "I file di installazione di OSify sono pronti sull'unita (O:)."
Write-Host "Al riavvio del computer partira automaticamente l'installer di OSify."
Write-Host "Terminata l'installazione, la partizione (O:) verra rimossa automaticamente."
Write-Host ""
$reboot = Read-Host "Desideri riavviare il computer adesso? (S/N)"
if ($reboot -match '^[sSyY]') {
    Restart-Computer -Force
}
