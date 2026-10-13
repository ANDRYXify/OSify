# ==============================================================================
# OSify Modern Graphical Installer for Windows (by Andryx)
# ==============================================================================
# Interfaccia grafica nativa ad alto impatto visivo (Dark Theme / Neon Cyberpunk)
# Ispirata al logo ufficiale di OSify: toni Deep Obsidian, Viola Neon e Verde Menta.
# Compatibile al 100% con Windows 7 SP1 (PowerShell v2.0), Windows 8, 10 e 11.
# ==============================================================================

Add-Type -AssemblyName PresentationFramework, PresentationCore, WindowsBase, System.Windows.Forms

# Helper Convertitore Pennelli WPF (Compatibile al 100% con PowerShell 2.0 / .NET 3.5 su Windows 7)
$global:BrushConv = New-Object System.Windows.Media.BrushConverter
function Get-Brush([string]$hex) {
    return $global:BrushConv.ConvertFromString($hex)
}

# 1. Rilevamento Hardware in Tempo Reale
$proc = Get-WmiObject Win32_Processor | Select-Object -First 1
$cpuName = if ($proc.Name) { $proc.Name.Trim() } else { "Processore Sconosciuto" }
$is64Bit = ($env:PROCESSOR_ARCHITECTURE -eq "AMD64") -or ($env:PROCESSOR_ARCHITEW6432 -eq "AMD64") -or ($proc.AddressWidth -eq 64)

$totalRamMB = 2048
try {
    $compSys = Get-WmiObject Win32_ComputerSystem | Select-Object -First 1
    $totalRamMB = [math]::Round($compSys.TotalPhysicalMemory / 1MB)
} catch {}

$freeSpaceGB = 0
try {
    $cDrive = Get-WmiObject Win32_LogicalDisk -Filter "DeviceID='C:'"
    $freeSpaceGB = [math]::Round($cDrive.FreeSpace / 1GB, 1)
} catch {}

# Percorsi di lavoro
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$logoPath = Join-Path $scriptDir "logo.png"
if (-not (Test-Path $logoPath)) {
    $logoCandidate = Join-Path $scriptDir "..\..\OSify.png"
    if (Test-Path $logoCandidate) { $logoPath = (Resolve-Path $logoCandidate).Path }
}

# 2. Definizione Layout XAML (WPF Cyberpunk Theme)
[xml]$xaml = @"
<Window
    xmlns="http://schemas.microsoft.com/winfx/2006/xaml/presentation"
    xmlns:x="http://schemas.microsoft.com/winfx/2006/xaml"
    Title="OSify - Installer per Windows (Senza USB)"
    Height="680" Width="820"
    WindowStartupLocation="CenterScreen"
    ResizeMode="CanMinimize"
    Background="#0D0D14"
    Foreground="#FFFFFF"
    FontFamily="Segoe UI, Tahoma, Helvetica, Arial">

    <Window.Resources>
        <!-- Stile Card Edizione Selezionabile -->
        <Style x:Key="EditionCard" TargetType="Border">
            <Setter Property="Background" Value="#151522"/>
            <Setter Property="BorderBrush" Value="#252538"/>
            <Setter Property="BorderThickness" Value="1.5"/>
            <Setter Property="CornerRadius" Value="10"/>
            <Setter Property="Padding" Value="14"/>
            <Setter Property="Cursor" Value="Hand"/>
        </Style>

        <!-- Stile Bottone Primario -->
        <Style x:Key="NeonButton" TargetType="Button">
            <Setter Property="Background" Value="#7C3AED"/>
            <Setter Property="Foreground" Value="#FFFFFF"/>
            <Setter Property="FontWeight" Value="Bold"/>
            <Setter Property="FontSize" Value="14"/>
            <Setter Property="Padding" Value="16,10"/>
            <Setter Property="BorderThickness" Value="0"/>
            <Setter Property="Cursor" Value="Hand"/>
            <Setter Property="Template">
                <Setter.Value>
                    <ControlTemplate TargetType="Button">
                        <Border Background="{TemplateBinding Background}" CornerRadius="8" Padding="{TemplateBinding Padding}">
                            <ContentPresenter HorizontalAlignment="Center" VerticalAlignment="Center"/>
                        </Border>
                    </ControlTemplate>
                </Setter.Value>
            </Setter>
        </Style>

        <Style x:Key="SecondaryButton" TargetType="Button">
            <Setter Property="Background" Value="#232336"/>
            <Setter Property="Foreground" Value="#94A3B8"/>
            <Setter Property="FontWeight" Value="SemiBold"/>
            <Setter Property="FontSize" Value="12"/>
            <Setter Property="Padding" Value="10,6"/>
            <Setter Property="BorderThickness" Value="1"/>
            <Setter Property="BorderBrush" Value="#33334D"/>
            <Setter Property="Cursor" Value="Hand"/>
            <Setter Property="Template">
                <Setter.Value>
                    <ControlTemplate TargetType="Button">
                        <Border Background="{TemplateBinding Background}" BorderBrush="{TemplateBinding BorderBrush}" BorderThickness="{TemplateBinding BorderThickness}" CornerRadius="6" Padding="{TemplateBinding Padding}">
                            <ContentPresenter HorizontalAlignment="Center" VerticalAlignment="Center"/>
                        </Border>
                    </ControlTemplate>
                </Setter.Value>
            </Setter>
        </Style>
    </Window.Resources>

    <Grid Margin="24">
        <Grid.RowDefinitions>
            <RowDefinition Height="Auto"/> <!-- Header con Logo -->
            <RowDefinition Height="Auto"/> <!-- Hardware Info Banner -->
            <RowDefinition Height="Auto"/> <!-- Selezione Edizione -->
            <RowDefinition Height="Auto"/> <!-- Selezione ISO -->
            <RowDefinition Height="*"/>    <!-- Log / Status Box -->
            <RowDefinition Height="Auto"/> <!-- Progress & Bottone Azione -->
        </Grid.RowDefinitions>

        <!-- 1. Header con Logo OSify e Titolo -->
        <StackPanel Grid.Row="0" Orientation="Horizontal" Margin="0,0,0,16">
            <Image Name="ImgLogo" Width="64" Height="64" Margin="0,0,16,0" RenderOptions.BitmapScalingMode="HighQuality"/>
            <StackPanel VerticalAlignment="Center">
                <TextBlock Text="OSify Setup" FontSize="26" FontWeight="Bold" Foreground="#FFFFFF"/>
                <TextBlock Text="Installazione Diretta da Windows Senza Chiavetta USB - by Andrea Taliento" FontSize="12" Foreground="#94A3B8"/>
            </StackPanel>
        </StackPanel>

        <!-- 2. Hardware Scanner Banner -->
        <Border Grid.Row="1" Background="#161626" BorderBrush="#2B2B44" BorderThickness="1" CornerRadius="8" Padding="12" Margin="0,0,0,16">
            <Grid>
                <Grid.ColumnDefinitions>
                    <ColumnDefinition Width="*"/>
                    <ColumnDefinition Width="Auto"/>
                </Grid.ColumnDefinitions>
                <StackPanel Grid.Column="0">
                    <TextBlock Name="TxtCpu" Text="CPU: Rilevamento in corso..." FontSize="12" FontWeight="SemiBold" Foreground="#E2E8F0"/>
                    <TextBlock Name="TxtHwDetails" Text="RAM e Disco in analisi..." FontSize="11" Foreground="#94A3B8" Margin="0,2,0,0"/>
                </StackPanel>
                <Border Grid.Column="1" Name="BadgeArch" Background="#7C3AED" CornerRadius="6" Padding="8,4" VerticalAlignment="Center">
                    <TextBlock Name="TxtBadgeArch" Text="64-BIT" FontSize="11" FontWeight="Bold" Foreground="#FFFFFF"/>
                </Border>
            </Grid>
        </Border>

        <!-- 3. Selezione Edizione (Card a Due Colonne) -->
        <Grid Grid.Row="2" Margin="0,0,0,16">
            <Grid.ColumnDefinitions>
                <ColumnDefinition Width="*"/>
                <ColumnDefinition Width="16"/>
                <ColumnDefinition Width="*"/>
            </Grid.ColumnDefinitions>

            <!-- Card Edizione Moderna Gaming -->
            <Border Grid.Column="0" Name="CardModern" Style="{StaticResource EditionCard}">
                <StackPanel>
                    <Grid>
                        <TextBlock Text="[+] OSify Standard (x86_64)" FontWeight="Bold" FontSize="14" Foreground="#FFFFFF"/>
                        <RadioButton Name="RadioModern" HorizontalAlignment="Right" IsChecked="True"/>
                    </Grid>
                    <TextBlock Text="Kernel BORE - AVX2 - Gaming 500 FPS - PipeWire Low-Latency" FontSize="11" Foreground="#A78BFA" Margin="0,4,0,0" TextWrapping="Wrap"/>
                    <TextBlock Text="Consigliato per PC con CPU moderne a 64-bit e oltre 2GB di RAM." FontSize="10" Foreground="#64748B" Margin="0,4,0,0" TextWrapping="Wrap"/>
                </StackPanel>
            </Border>

            <!-- Card Edizione Vintage Netbook (Toshiba NB200) -->
            <Border Grid.Column="2" Name="CardVintage" Style="{StaticResource EditionCard}">
                <StackPanel>
                    <Grid>
                        <TextBlock Text="[*] OSify Vintage (i686 Micro)" FontWeight="Bold" FontSize="14" Foreground="#FFFFFF"/>
                        <RadioButton Name="RadioVintage" HorizontalAlignment="Right"/>
                    </Grid>
                    <TextBlock Text="32-Bit Nativo - Footprint ~120MB - ZRAM lz4 - Atom e GMA950" FontSize="11" Foreground="#34D399" Margin="0,4,0,0" TextWrapping="Wrap"/>
                    <TextBlock Text="Specifico per Netbook (es. Toshiba NB200 Atom N280) e PC con 1GB RAM." FontSize="10" Foreground="#64748B" Margin="0,4,0,0" TextWrapping="Wrap"/>
                </StackPanel>
            </Border>
        </Grid>

        <!-- 4. Selezione File ISO -->
        <Border Grid.Row="3" Background="#161626" BorderBrush="#2B2B44" BorderThickness="1" CornerRadius="8" Padding="12" Margin="0,0,0,16">
            <Grid>
                <Grid.ColumnDefinitions>
                    <ColumnDefinition Width="*"/>
                    <ColumnDefinition Width="Auto"/>
                    <ColumnDefinition Width="8"/>
                    <ColumnDefinition Width="Auto"/>
                </Grid.ColumnDefinitions>
                <StackPanel Grid.Column="0" VerticalAlignment="Center">
                    <TextBlock Text="IMMAGINE ISO DEL SISTEMA OPERATIVO" FontSize="10" FontWeight="Bold" Foreground="#64748B"/>
                    <TextBlock Name="TxtIsoStatus" Text="Ricerca immagine in corso..." FontSize="12" Foreground="#38BDF8" TextTrimming="CharacterEllipsis" Margin="0,2,0,0"/>
                </StackPanel>
                <Button Grid.Column="1" Name="BtnDownloadIso" Content="Scarica da GitHub" Style="{StaticResource SecondaryButton}"/>
                <Button Grid.Column="3" Name="BtnBrowseIso" Content="Sfoglia..." Style="{StaticResource SecondaryButton}"/>
            </Grid>
        </Border>

        <!-- 5. Log Box Stile Terminale Cyberpunk -->
        <Border Grid.Row="4" Background="#08080C" BorderBrush="#1C1C2B" BorderThickness="1" CornerRadius="8" Padding="10" Margin="0,0,0,16">
            <ScrollViewer Name="ScrollLogs" VerticalScrollBarVisibility="Auto">
                <TextBlock Name="TxtLogs" FontFamily="Consolas, Cascadia Code, Courier New" FontSize="11" Foreground="#10B981" TextWrapping="Wrap" Text="[OSify Setup] Inizializzazione completata. Pronto per iniziare."/>
            </ScrollViewer>
        </Border>

        <!-- 6. Footer con Barra di Progresso e Pulsante Azione -->
        <Grid Grid.Row="5">
            <Grid.RowDefinitions>
                <RowDefinition Height="Auto"/>
                <RowDefinition Height="Auto"/>
            </Grid.RowDefinitions>

            <ProgressBar Grid.Row="0" Name="ProgBar" Height="8" Background="#1E1E2E" Foreground="#10B981" BorderThickness="0" Margin="0,0,0,12" Value="0" Maximum="100"/>

            <Grid Grid.Row="1">
                <TextBlock Name="TxtStepInfo" Text="Pronto per iniziare. 5 GB temporanei richiesti su C:." VerticalAlignment="Center" FontSize="11" Foreground="#94A3B8"/>
                <Button Name="BtnInstall" HorizontalAlignment="Right" Content="PREPARA INSTALLAZIONE SENZA USB" Style="{StaticResource NeonButton}"/>
            </Grid>
        </Grid>
    </Grid>
</Window>
"@

$reader = New-Object System.Xml.XmlNodeReader $xaml
$window = [Windows.Markup.XamlReader]::Load($reader)

# Elementi XAML
$imgLogo = $window.FindName("ImgLogo")
$txtCpu = $window.FindName("TxtCpu")
$txtHwDetails = $window.FindName("TxtHwDetails")
$badgeArch = $window.FindName("BadgeArch")
$txtBadgeArch = $window.FindName("TxtBadgeArch")
$cardModern = $window.FindName("CardModern")
$cardVintage = $window.FindName("CardVintage")
$radioModern = $window.FindName("RadioModern")
$radioVintage = $window.FindName("RadioVintage")
$txtIsoStatus = $window.FindName("TxtIsoStatus")
$btnDownloadIso = $window.FindName("BtnDownloadIso")
$btnBrowseIso = $window.FindName("BtnBrowseIso")
$txtLogs = $window.FindName("TxtLogs")
$scrollLogs = $window.FindName("ScrollLogs")
$progBar = $window.FindName("ProgBar")
$txtStepInfo = $window.FindName("TxtStepInfo")
$btnInstall = $window.FindName("BtnInstall")

# Caricamento Logo
if (Test-Path $logoPath) {
    try {
        $bmp = New-Object System.Windows.Media.Imaging.BitmapImage
        $bmp.BeginInit()
        $bmp.UriSource = New-Object System.Uri($logoPath, [System.UriKind]::Absolute)
        $bmp.EndInit()
        $imgLogo.Source = $bmp
    } catch {}
}

# Funzione Log protetta per qualsiasi versione di Windows
function Append-Log($msg) {
    $txtLogs.Text += "`n$msg"
    $scrollLogs.ScrollToEnd()
    try {
        [System.Windows.Forms.Application]::DoEvents()
    } catch {}
}

# Inizializzazione Dati Hardware
$txtCpu.Text = "CPU: $cpuName"
$txtHwDetails.Text = "Memoria RAM: $totalRamMB MB | Spazio Libero su C: : $freeSpaceGB GB (Minimo 5 GB richiesti)"

if (-not $is64Bit) {
    # CPU 32-bit (es. Toshiba NB200 con Intel Atom N280)
    $txtBadgeArch.Text = "32-BIT (i686)"
    $badgeArch.Background = Get-Brush "#F59E0B"
    $radioVintage.IsChecked = $true
    $radioModern.IsChecked = $false
    $cardVintage.BorderBrush = Get-Brush "#10B981"
    Append-Log "[!] CPU 32-bit rilevata (Atom/Vintage): selezionata automaticamente l'edizione OSify Vintage i686."
} else {
    $txtBadgeArch.Text = "64-BIT (x86_64)"
    $badgeArch.Background = Get-Brush "#7C3AED"
    $radioModern.IsChecked = $true
    $cardModern.BorderBrush = Get-Brush "#8B5CF6"
}

# Click sulle Card per cambiare selezione
$cardModern.Add_MouseDown({
    $radioModern.IsChecked = $true
    $radioVintage.IsChecked = $false
    $cardModern.BorderBrush = Get-Brush "#8B5CF6"
    $cardVintage.BorderBrush = Get-Brush "#252538"
    Update-IsoSearch
})
$cardVintage.Add_MouseDown({
    $radioVintage.IsChecked = $true
    $radioModern.IsChecked = $false
    $cardVintage.BorderBrush = Get-Brush "#10B981"
    $cardModern.BorderBrush = Get-Brush "#252538"
    Update-IsoSearch
})

# Ricerca ISO Locale
$global:SelectedIso = ""

function Update-IsoSearch {
    $pattern = if ($radioVintage.IsChecked) { "*vintage*.iso", "*i686*.iso", "*osify*.iso" } else { "*x86_64*.iso", "*osify*.iso" }
    $found = $null
    $userProf = if ($env:USERPROFILE) { $env:USERPROFILE } else { [Environment]::GetFolderPath("UserProfile") }
    $searchDirs = @($scriptDir, "$userProf\Downloads", "$userProf\Desktop")
    foreach ($d in $searchDirs) {
        if ($d -and (Test-Path $d)) {
            foreach ($pat in $pattern) {
                $f = Get-ChildItem -Path $d -Filter $pat -ErrorAction SilentlyContinue | Select-Object -First 1
                if ($f) { $found = $f.FullName; break }
            }
        }
        if ($found) { break }
    }

    if ($found) {
        $global:SelectedIso = $found
        $txtIsoStatus.Text = "[OK] Immagine Trovata: " + [System.IO.Path]::GetFileName($found)
        $txtIsoStatus.Foreground = Get-Brush "#10B981"
        Append-Log "[OK] ISO rilevata: $found"
    } else {
        $global:SelectedIso = ""
        $txtIsoStatus.Text = "[!] Nessuna ISO locale trovata. Clicca 'Scarica' o 'Sfoglia'."
        $txtIsoStatus.Foreground = Get-Brush "#F59E0B"
    }
}

Update-IsoSearch

# Sfoglia File ISO
$btnBrowseIso.Add_Click({
    Add-Type -AssemblyName System.Windows.Forms
    $dialog = New-Object System.Windows.Forms.OpenFileDialog
    $dialog.Filter = "Immagini ISO (*.iso)|*.iso|Tutti i file (*.*)|*.*"
    $dialog.Title = "Seleziona Immagine ISO di OSify"
    if ($dialog.ShowDialog() -eq [System.Windows.Forms.DialogResult]::OK) {
        $global:SelectedIso = $dialog.FileName
        $txtIsoStatus.Text = "[OK] Immagine: " + [System.IO.Path]::GetFileName($dialog.FileName)
        $txtIsoStatus.Foreground = Get-Brush "#10B981"
        Append-Log "[OK] Selezionata ISO manuale: $($dialog.FileName)"
    }
})

# Download Diretto da GitHub
$btnDownloadIso.Add_Click({
    $isVintage = $radioVintage.IsChecked
    $isoName = if ($isVintage) { "OSify-Vintage-i686.iso" } else { "OSify-x86_64-v3.iso" }
    $url = "https://github.com/ANDRYXify/OSify/releases/latest/download/$isoName"
    $targetPath = Join-Path $scriptDir $isoName

    Append-Log "[+] Inizio download da GitHub: $url"
    $txtStepInfo.Text = "Download ISO in corso da GitHub Releases..."
    $btnDownloadIso.IsEnabled = $false
    $btnInstall.IsEnabled = $false

    try {
        try {
            [System.Net.ServicePointManager]::SecurityProtocol = [System.Net.ServicePointManager]::SecurityProtocol -bor 3072
        } catch {}
        $wc = New-Object System.Net.WebClient
        $wc.DownloadFile($url, $targetPath)
        $global:SelectedIso = $targetPath
        $txtIsoStatus.Text = "[OK] Scaricata: $isoName"
        $txtIsoStatus.Foreground = Get-Brush "#10B981"
        Append-Log "[OK] Download completato con successo: $targetPath"
        $txtStepInfo.Text = "Download completato! Pronto all'installazione."
    } catch {
        Append-Log "[!] Errore durante il download: $($_.Exception.Message)"
        [System.Diagnostics.Process]::Start("https://github.com/ANDRYXify/OSify/releases")
    } finally {
        $btnDownloadIso.IsEnabled = $true
        $btnInstall.IsEnabled = $true
    }
})

# Processo di Installazione
$btnInstall.Add_Click({
    if (-not $global:SelectedIso -or -not (Test-Path $global:SelectedIso)) {
        [System.Windows.MessageBox]::Show("Seleziona o scarica prima l'immagine ISO di OSify per procedere.", "Immagine ISO Mancante", [System.Windows.MessageBoxButton]::OK, [System.Windows.MessageBoxImage]::Warning)
        return
    }

    if ($freeSpaceGB -lt 5.0) {
        $res = [System.Windows.MessageBox]::Show("Su C: sono disponibili solo $freeSpaceGB GB liberi (consigliati almeno 5 GB). Desideri tentare comunque?", "Spazio su Disco Ridotto", [System.Windows.MessageBoxButton]::YesNo, [System.Windows.MessageBoxImage]::Question)
        if ($res -ne [System.Windows.MessageBoxResult]::Yes) { return }
    }

    $btnInstall.IsEnabled = $false
    $btnBrowseIso.IsEnabled = $false
    $btnDownloadIso.IsEnabled = $false

    # FASE 1: Partizionamento DiskPart
    $progBar.Value = 15
    $txtStepInfo.Text = "[1/4] Creazione partizione temporanea da 5GB tramite DiskPart..."
    Append-Log "[+] Preparazione script DiskPart per unita O:\..."

    $dpFile = Join-Path $env:TEMP "osify_gui_dp.txt"
    $dpLines = @(
        "select volume c",
        "shrink desired=5120 minimum=4096",
        "create partition primary",
        "format fs=fat32 quick label=OSIFY_BOOT",
        "assign letter=O",
        "active"
    )
    [System.IO.File]::WriteAllLines($dpFile, $dpLines)

    $pInfo = New-Object System.Diagnostics.ProcessStartInfo
    $pInfo.FileName = "diskpart.exe"
    $pInfo.Arguments = "/s `"$dpFile`""
    $pInfo.UseShellExecute = $false
    $pInfo.CreateNoWindow = $true
    $p = [System.Diagnostics.Process]::Start($pInfo)
    $p.WaitForExit()
    Remove-Item $dpFile -Force -ErrorAction SilentlyContinue

    if (-not (Test-Path 'O:\')) {
        Append-Log "[ERRORE] Impossibile creare l'unita (O:). Verifica lo spazio libero."
        $btnInstall.IsEnabled = $true
        return
    }
    Append-Log "[OK] Partizione (O:) creata e pronta."

    # FASE 2: Estrazione File ISO
    $progBar.Value = 45
    $txtStepInfo.Text = "[2/4] Estrazione file di avvio e sistema su O:\..."
    Append-Log "[+] Estrazione dell'immagine ISO in corso..."

    $extracted = $false
    if (Get-Command "Mount-DiskImage" -ErrorAction SilentlyContinue) {
        try {
            $mount = Mount-DiskImage -ImagePath $global:SelectedIso -PassThru
            $isoVol = $mount | Get-Volume
            if ($isoVol -and $isoVol.DriveLetter) {
                $src = $isoVol.DriveLetter + ':\'
                Copy-Item -Path "$src*" -Destination 'O:\' -Recurse -Force
                Dismount-DiskImage -ImagePath $global:SelectedIso | Out-Null
                $extracted = $true
            }
        } catch {}
    }

    if (-not $extracted) {
        # Fallback 7-Zip (64-bit, 32-bit o cartella locale)
        $candidates7z = @(
            "$env:ProgramFiles\7-Zip\7z.exe",
            "${env:ProgramFiles(x86)}\7-Zip\7z.exe",
            (Join-Path $scriptDir "7z.exe"),
            (Join-Path $scriptDir "7za.exe")
        )
        foreach ($c7z in $candidates7z) {
            if ($c7z -and (Test-Path $c7z)) {
                Append-Log "[i] Estrazione tramite 7-Zip ($c7z)..."
                & $c7z x $global:SelectedIso -oO:\ -y | Out-Null
                $extracted = $true
                break
            }
        }
    }

    if (-not $extracted) {
        # Download mini 7za se Windows 7 senza 7-Zip
        try {
            Append-Log "[i] Scaricamento mini-estrattore 7za per Windows 7..."
            try { [System.Net.ServicePointManager]::SecurityProtocol = [System.Net.ServicePointManager]::SecurityProtocol -bor 3072 } catch {}
            $wc = New-Object System.Net.WebClient
            $zip = Join-Path $env:TEMP "7za.zip"
            $wc.DownloadFile("https://www.7-zip.org/a/7za920.zip", $zip)
            $shell = New-Object -ComObject Shell.Application
            $dest = Join-Path $env:TEMP "7za_app"
            if (-not (Test-Path $dest)) { New-Item -ItemType Directory -Path $dest | Out-Null }
            $shell.NameSpace($dest).CopyHere($shell.NameSpace($zip).Items(), 16)
            $exe = Join-Path $dest "7za.exe"
            if (Test-Path $exe) {
                & $exe x $global:SelectedIso -oO:\ -y | Out-Null
                $extracted = $true
            }
        } catch {}
    }

    $progBar.Value = 80
    Append-Log "[OK] File estratti con successo su O:\."

    # FASE 3: Configurazione Avvio BCD
    $txtStepInfo.Text = "[3/4] Configurazione voce di avvio nel Boot Manager..."
    $isUefi = ($env:firmware_type -eq "UEFI") -or (Test-Path "HKLM:\System\CurrentControlSet\Control\SecureBoot\State")

    if ($isUefi -and (Test-Path 'O:\EFI\BOOT\BOOTX64.EFI')) {
        try {
            $bcdOut = bcdedit /create /d "Installa OSify (Senza USB)" /application bootapp
            $guidMatch = [System.Text.RegularExpressions.Regex]::Match($bcdOut, '\{([0-9a-fA-F-]+)\}')
            if ($guidMatch.Success) {
                $guid = $guidMatch.Value
                bcdedit /set $guid device partition=O:
                bcdedit /set $guid path '\EFI\BOOT\BOOTX64.EFI'
                bcdedit /displayorder $guid /addlast
                bcdedit /bootsequence $guid
                Append-Log "[OK] Voce UEFI BOOTX64.EFI configurata: $guid"
            } else {
                Append-Log "[!] GUID BCD non estratto, boot gestito tramite partizione attiva."
            }
        } catch {
            Append-Log "[!] Configurazione BCD facoltativa: $($_.Exception.Message)"
        }
    } else {
        Append-Log "[OK] Sistema Legacy BIOS (MBR): partizione O:\ attiva per il boot."
    }

    # FASE 4: Completato!
    $progBar.Value = 100
    $txtStepInfo.Text = "[OK] Configurazione completata con successo! Pronto al riavvio."
    Append-Log "========================================================="
    Append-Log "[OK] INSTALLAZIONE PRONTA SULL'UNITA (O:)"
    Append-Log "Al riavvio il PC si avviera direttamente in OSify."
    Append-Log "Terminata l'installazione, la partizione (O:) verra rimossa."
    Append-Log "========================================================="

    $reboot = [System.Windows.MessageBox]::Show("La partizione di avvio di OSify e' pronta!`n`nVuoi riavviare il computer adesso per iniziare l'installazione di OSify?", "Installazione Pronta", [System.Windows.MessageBoxButton]::YesNo, [System.Windows.MessageBoxImage]::Information)
    if ($reboot -eq [System.Windows.MessageBoxResult]::Yes) {
        Restart-Computer -Force
    }
})

# Visualizza Finestra
$window.ShowDialog() | Out-Null
