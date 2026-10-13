# ==============================================================================
# OSify Modern Graphical Installer for Windows (by Andryx)
# ==============================================================================
# Interfaccia grafica nativa ad alto impatto visivo (Dark Theme / Neon Cyberpunk)
# Ispirata al logo ufficiale di OSify: toni Deep Obsidian, Viola Neon e Verde Menta.
# Compatibile al 100% con Windows 7 SP1 (PowerShell v2.0), Windows 8, 10 e 11.
# Ottimizzata per netbook a bassa risoluzione (Toshiba NB200 WSVGA 1024x600).
# ==============================================================================

# Caricamento Assembly WPF e Win32
Add-Type -AssemblyName PresentationFramework, PresentationCore, WindowsBase, System.Drawing

# Abilitazione preventivo protocolli TLS 1.2 su Windows 7 SP1 / .NET 3.5
try {
    $tlsKey = "HKLM:\SYSTEM\CurrentControlSet\Control\SecurityProviders\SCHANNEL\Protocols\TLS 1.2\Client"
    if (-not (Test-Path $tlsKey)) { New-Item -Path $tlsKey -Force | Out-Null }
    Set-ItemProperty -Path $tlsKey -Name "DisabledByDefault" -Value 0 -Type DWord -Force -ErrorAction SilentlyContinue
    Set-ItemProperty -Path $tlsKey -Name "Enabled" -Value 1 -Type DWord -Force -ErrorAction SilentlyContinue

    $netKeys = @(
        "HKLM:\SOFTWARE\Microsoft\.NETFramework\v2.0.50727",
        "HKLM:\SOFTWARE\Microsoft\.NETFramework\v4.0.30319",
        "HKLM:\SOFTWARE\Wow6432Node\Microsoft\.NETFramework\v2.0.50727",
        "HKLM:\SOFTWARE\Wow6432Node\Microsoft\.NETFramework\v4.0.30319"
    )
    foreach ($nk in $netKeys) {
        if (Test-Path $nk) {
            Set-ItemProperty -Path $nk -Name "SystemDefaultTlsVersions" -Value 1 -Type DWord -Force -ErrorAction SilentlyContinue
            Set-ItemProperty -Path $nk -Name "SchUseStrongCrypto" -Value 1 -Type DWord -Force -ErrorAction SilentlyContinue
        }
    }
    [System.Net.ServicePointManager]::SecurityProtocol = [System.Net.ServicePointManager]::SecurityProtocol -bor 3072
} catch {}

# Helper Convertitore Pennelli WPF (Compatibile con PowerShell 2.0 / .NET 3.5)
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

# 2. Definizione Layout XAML (Ottimizzato per schermi WSVGA 1024x600 e risoluzioni standard)
[xml]$xaml = @"
<Window
    xmlns="http://schemas.microsoft.com/winfx/2006/xaml/presentation"
    xmlns:x="http://schemas.microsoft.com/winfx/2006/xaml"
    Title="OSify - Installer per Windows (Senza USB)"
    Height="530" Width="760"
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
            <Setter Property="CornerRadius" Value="8"/>
            <Setter Property="Padding" Value="10,8"/>
            <Setter Property="Cursor" Value="Hand"/>
        </Style>

        <!-- Stile Bottone Primario -->
        <Style x:Key="NeonButton" TargetType="Button">
            <Setter Property="Background" Value="#7C3AED"/>
            <Setter Property="Foreground" Value="#FFFFFF"/>
            <Setter Property="FontWeight" Value="Bold"/>
            <Setter Property="FontSize" Value="13"/>
            <Setter Property="Padding" Value="16,8"/>
            <Setter Property="BorderThickness" Value="0"/>
            <Setter Property="Cursor" Value="Hand"/>
            <Setter Property="Template">
                <Setter.Value>
                    <ControlTemplate TargetType="Button">
                        <Border Background="{TemplateBinding Background}" CornerRadius="6" Padding="{TemplateBinding Padding}">
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
            <Setter Property="FontSize" Value="11"/>
            <Setter Property="Padding" Value="10,5"/>
            <Setter Property="BorderThickness" Value="1"/>
            <Setter Property="BorderBrush" Value="#33334D"/>
            <Setter Property="Cursor" Value="Hand"/>
            <Setter Property="Template">
                <Setter.Value>
                    <ControlTemplate TargetType="Button">
                        <Border Background="{TemplateBinding Background}" BorderBrush="{TemplateBinding BorderBrush}" BorderThickness="{TemplateBinding BorderThickness}" CornerRadius="5" Padding="{TemplateBinding Padding}">
                            <ContentPresenter HorizontalAlignment="Center" VerticalAlignment="Center"/>
                        </Border>
                    </ControlTemplate>
                </Setter.Value>
            </Setter>
        </Style>
    </Window.Resources>

    <Grid Margin="16,10,16,10">
        <Grid.RowDefinitions>
            <RowDefinition Height="Auto"/> <!-- Header con Logo -->
            <RowDefinition Height="Auto"/> <!-- Hardware Info Banner -->
            <RowDefinition Height="Auto"/> <!-- Selezione Edizione -->
            <RowDefinition Height="Auto"/> <!-- Selezione ISO -->
            <RowDefinition Height="*"/>    <!-- Log / Status Box -->
            <RowDefinition Height="Auto"/> <!-- Progress & Bottone Azione -->
        </Grid.RowDefinitions>

        <!-- 1. Header con Logo OSify e Titolo -->
        <StackPanel Grid.Row="0" Orientation="Horizontal" Margin="0,0,0,10">
            <Image Name="ImgLogo" Width="48" Height="48" Margin="0,0,12,0" RenderOptions.BitmapScalingMode="HighQuality"/>
            <StackPanel VerticalAlignment="Center">
                <TextBlock Text="OSify Setup" FontSize="22" FontWeight="Bold" Foreground="#FFFFFF"/>
                <TextBlock Text="Installazione Diretta da Windows Senza USB - Ingegnerizzato da Andrea Taliento" FontSize="11" Foreground="#94A3B8"/>
            </StackPanel>
        </StackPanel>

        <!-- 2. Hardware Scanner Banner -->
        <Border Grid.Row="1" Background="#161626" BorderBrush="#2B2B44" BorderThickness="1" CornerRadius="6" Padding="10,6" Margin="0,0,0,10">
            <Grid>
                <Grid.ColumnDefinitions>
                    <ColumnDefinition Width="*"/>
                    <ColumnDefinition Width="Auto"/>
                </Grid.ColumnDefinitions>
                <StackPanel Grid.Column="0">
                    <TextBlock Name="TxtCpu" Text="CPU: Rilevamento in corso..." FontSize="11" FontWeight="SemiBold" Foreground="#E2E8F0"/>
                    <TextBlock Name="TxtHwDetails" Text="RAM e Disco in analisi..." FontSize="10" Foreground="#94A3B8" Margin="0,2,0,0"/>
                </StackPanel>
                <Border Grid.Column="1" Name="BadgeArch" Background="#7C3AED" CornerRadius="5" Padding="8,3" VerticalAlignment="Center">
                    <TextBlock Name="TxtBadgeArch" Text="64-BIT" FontSize="10" FontWeight="Bold" Foreground="#FFFFFF"/>
                </Border>
            </Grid>
        </Border>

        <!-- 3. Selezione Edizione (Card Compatte a Due Colonne) -->
        <Grid Grid.Row="2" Margin="0,0,0,10">
            <Grid.ColumnDefinitions>
                <ColumnDefinition Width="*"/>
                <ColumnDefinition Width="12"/>
                <ColumnDefinition Width="*"/>
            </Grid.ColumnDefinitions>

            <!-- Card Edizione Moderna Gaming -->
            <Border Grid.Column="0" Name="CardModern" Style="{StaticResource EditionCard}">
                <StackPanel>
                    <Grid>
                        <TextBlock Text="[+] OSify Standard (x86_64)" FontWeight="Bold" FontSize="12" Foreground="#FFFFFF"/>
                        <RadioButton Name="RadioModern" HorizontalAlignment="Right" IsChecked="True"/>
                    </Grid>
                    <TextBlock Text="Kernel BORE - AVX2 - Gaming 500 FPS - PipeWire Low-Latency" FontSize="10" Foreground="#A78BFA" Margin="0,2,0,0" TextWrapping="Wrap"/>
                    <TextBlock Text="Consigliato per PC moderni a 64-bit con oltre 2GB di RAM." FontSize="9" Foreground="#64748B" Margin="0,2,0,0" TextWrapping="Wrap"/>
                </StackPanel>
            </Border>

            <!-- Card Edizione Vintage Netbook (Toshiba NB200) -->
            <Border Grid.Column="2" Name="CardVintage" Style="{StaticResource EditionCard}">
                <StackPanel>
                    <Grid>
                        <TextBlock Text="[*] OSify Vintage (i686 Micro)" FontWeight="Bold" FontSize="12" Foreground="#FFFFFF"/>
                        <RadioButton Name="RadioVintage" HorizontalAlignment="Right"/>
                    </Grid>
                    <TextBlock Text="32-Bit Nativo - Footprint ~120MB - ZRAM lz4 - Atom e GMA950" FontSize="10" Foreground="#34D399" Margin="0,2,0,0" TextWrapping="Wrap"/>
                    <TextBlock Text="Specifico per Netbook (Toshiba NB200 Atom N280) e PC con 1GB RAM." FontSize="9" Foreground="#64748B" Margin="0,2,0,0" TextWrapping="Wrap"/>
                </StackPanel>
            </Border>
        </Grid>

        <!-- 4. Selezione File ISO (con TextBox Modificabile, Drag&Drop e Pulsanti Azione) -->
        <Border Grid.Row="3" Background="#161626" BorderBrush="#2B2B44" BorderThickness="1" CornerRadius="6" Padding="10,8" Margin="0,0,0,10">
            <Grid>
                <Grid.RowDefinitions>
                    <RowDefinition Height="Auto"/>
                    <RowDefinition Height="Auto"/>
                </Grid.RowDefinitions>
                
                <Grid Grid.Row="0" Margin="0,0,0,6">
                    <Grid.ColumnDefinitions>
                        <ColumnDefinition Width="*"/>
                        <ColumnDefinition Width="Auto"/>
                    </Grid.ColumnDefinitions>
                    <TextBlock Text="IMMAGINE ISO DEL SISTEMA OPERATIVO OSIFY" FontSize="10" FontWeight="Bold" Foreground="#64748B" VerticalAlignment="Center"/>
                    <TextBlock Grid.Column="1" Name="TxtIsoStatus" Text="Nessun file selezionato" FontSize="10" Foreground="#F59E0B" FontWeight="SemiBold"/>
                </Grid>

                <Grid Grid.Row="1">
                    <Grid.ColumnDefinitions>
                        <ColumnDefinition Width="*"/>
                        <ColumnDefinition Width="6"/>
                        <ColumnDefinition Width="Auto"/>
                        <ColumnDefinition Width="6"/>
                        <ColumnDefinition Width="Auto"/>
                    </Grid.ColumnDefinitions>
                    <TextBox Grid.Column="0" Name="TxtIsoPath" Height="26" Background="#0C0C14" Foreground="#E2E8F0" BorderBrush="#33334D" BorderThickness="1" Padding="6,3" FontSize="11" VerticalContentAlignment="Center" AllowDrop="True"/>
                    <Button Grid.Column="2" Name="BtnBrowseIso" Content="Sfoglia..." Style="{StaticResource SecondaryButton}"/>
                    <Button Grid.Column="4" Name="BtnDownloadIso" Content="Scarica ISO" Style="{StaticResource SecondaryButton}"/>
                </Grid>
            </Grid>
        </Border>

        <!-- 5. Log Box Stile Terminale Cyberpunk -->
        <Border Grid.Row="4" Background="#08080C" BorderBrush="#1C1C2B" BorderThickness="1" CornerRadius="6" Padding="8" Margin="0,0,0,10">
            <ScrollViewer Name="ScrollLogs" VerticalScrollBarVisibility="Auto">
                <TextBlock Name="TxtLogs" FontFamily="Consolas, Cascadia Code, Courier New" FontSize="10" Foreground="#10B981" TextWrapping="Wrap" Text="[OSify Setup] Inizializzazione completata. Pronto per iniziare."/>
            </ScrollViewer>
        </Border>

        <!-- 6. Footer con Barra di Progresso e Pulsante Azione -->
        <Grid Grid.Row="5">
            <Grid.RowDefinitions>
                <RowDefinition Height="Auto"/>
                <RowDefinition Height="Auto"/>
            </Grid.RowDefinitions>

            <ProgressBar Grid.Row="0" Name="ProgBar" Height="6" Background="#1E1E2E" Foreground="#10B981" BorderThickness="0" Margin="0,0,0,8" Value="0" Maximum="100"/>

            <Grid Grid.Row="1">
                <TextBlock Name="TxtStepInfo" Text="Pronto per iniziare. 1.5 GB minimi richiesti per la partizione di avvio." VerticalAlignment="Center" FontSize="10" Foreground="#94A3B8"/>
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
$txtIsoPath = $window.FindName("TxtIsoPath")
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

# Funzione Refresh UI in tempo reale per evitare freeze della finestra
function Refresh-UI {
    try {
        [System.Windows.Threading.Dispatcher]::CurrentDispatcher.Invoke(
            [System.Windows.Threading.DispatcherPriority]::Background,
            [Action]{}
        )
    } catch {}
}

# Funzione Log protetta con scroll e refresh immediato
function Append-Log($msg) {
    $txtLogs.Text += "`n$msg"
    $scrollLogs.ScrollToEnd()
    Refresh-UI
}

# Inizializzazione Dati Hardware
$txtCpu.Text = "CPU: $cpuName"
$txtHwDetails.Text = "Memoria RAM: $totalRamMB MB | Spazio Libero su C: : $freeSpaceGB GB"

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
    if (-not $txtIsoPath.Text) { Update-IsoSearch }
})
$cardVintage.Add_MouseDown({
    $radioVintage.IsChecked = $true
    $radioModern.IsChecked = $false
    $cardVintage.BorderBrush = Get-Brush "#10B981"
    $cardModern.BorderBrush = Get-Brush "#252538"
    if (-not $txtIsoPath.Text) { Update-IsoSearch }
})

# Gestione Percorso ISO e Validazione
$global:SelectedIso = ""

function Set-SelectedIso([string]$path) {
    if ($path -and (Test-Path $path)) {
        $global:SelectedIso = (Resolve-Path $path).Path
        $txtIsoPath.Text = $global:SelectedIso
        $fileSizeMB = [math]::Round((Get-Item $global:SelectedIso).Length / 1MB, 1)
        $txtIsoStatus.Text = "[OK] Immagine Rilevata ($fileSizeMB MB)"
        $txtIsoStatus.Foreground = Get-Brush "#10B981"
        Append-Log "[OK] Immagine ISO selezionata: $global:SelectedIso ($fileSizeMB MB)"
    } else {
        $global:SelectedIso = ""
        $txtIsoStatus.Text = "[!] File ISO non trovato"
        $txtIsoStatus.Foreground = Get-Brush "#F59E0B"
    }
}

$txtIsoPath.Add_TextChanged({
    $cleanPath = $txtIsoPath.Text.Trim().Trim('"').Trim("'")
    if ($cleanPath -and (Test-Path $cleanPath)) {
        $global:SelectedIso = $cleanPath
        $fileSizeMB = [math]::Round((Get-Item $cleanPath).Length / 1MB, 1)
        $txtIsoStatus.Text = "[OK] File Valido ($fileSizeMB MB)"
        $txtIsoStatus.Foreground = Get-Brush "#10B981"
    } else {
        $global:SelectedIso = ""
        $txtIsoStatus.Text = "[!] Inserisci o seleziona un file .iso esistente"
        $txtIsoStatus.Foreground = Get-Brush "#F59E0B"
    }
})

# Supporto Drag and Drop del file ISO nella finestra
$window.AllowDrop = $true
$window.Add_Drop({
    param($s, $e)
    if ($e.Data.GetDataPresent([System.Windows.DataFormats]::FileDrop)) {
        $files = $e.Data.GetData([System.Windows.DataFormats]::FileDrop)
        if ($files -and $files.Length -gt 0) {
            Set-SelectedIso $files[0]
        }
    }
})

# Ricerca Automatica ISO Locale
function Update-IsoSearch {
    if ($txtIsoPath.Text -and (Test-Path $txtIsoPath.Text)) { return }
    $pattern = if ($radioVintage.IsChecked) { "*vintage*.iso", "*i686*.iso", "*osify*.iso" } else { "*x86_64*.iso", "*osify*.iso" }
    $found = $null
    $userProf = if ($env:USERPROFILE) { $env:USERPROFILE } else { [Environment]::GetFolderPath("UserProfile") }
    $searchDirs = @($scriptDir, "$userProf\Downloads", "$userProf\Desktop", "C:\Downloads")
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
        Set-SelectedIso $found
    } else {
        $txtIsoStatus.Text = "[!] Nessuna ISO trovata. Clicca 'Sfoglia' o 'Scarica'."
        $txtIsoStatus.Foreground = Get-Brush "#F59E0B"
    }
}

Update-IsoSearch

# Sfoglia File ISO (Usa Microsoft.Win32.OpenFileDialog nativo di WPF)
$btnBrowseIso.Add_Click({
    try {
        $dialog = New-Object Microsoft.Win32.OpenFileDialog
        $dialog.Filter = "Immagini ISO (*.iso)|*.iso|Tutti i file (*.*)|*.*"
        $dialog.Title = "Seleziona Immagine ISO di OSify"
        if ($dialog.ShowDialog()) {
            Set-SelectedIso $dialog.FileName
        }
    } catch {
        # Fallback WinForms
        Add-Type -AssemblyName System.Windows.Forms
        $wfDialog = New-Object System.Windows.Forms.OpenFileDialog
        $wfDialog.Filter = "Immagini ISO (*.iso)|*.iso|Tutti i file (*.*)|*.*"
        $wfDialog.Title = "Seleziona Immagine ISO di OSify"
        if ($wfDialog.ShowDialog() -eq [System.Windows.Forms.DialogResult]::OK) {
            Set-SelectedIso $wfDialog.FileName
        }
    }
})

# Download Diretto da GitHub con Gestione Robustezza & Fallback Browser
$btnDownloadIso.Add_Click({
    $isVintage = $radioVintage.IsChecked
    $isoName = if ($isVintage) { "OSify-Vintage-i686.iso" } else { "OSify-x86_64-v3.iso" }
    $url = "https://github.com/ANDRYXify/OSify/releases/latest/download/$isoName"
    $targetPath = Join-Path $scriptDir $isoName

    Append-Log "[+] Inizio download da GitHub: $url"
    $txtStepInfo.Text = "Download ISO in corso da GitHub Releases..."
    $btnDownloadIso.IsEnabled = $false
    $btnInstall.IsEnabled = $false

    $downloadSuccess = $false
    try {
        $wc = New-Object System.Net.WebClient
        $wc.Headers.Add("User-Agent", "Mozilla/5.0 (Windows NT 6.1; Win64; x64)")
        Append-Log "[i] Connessione al server di rilascio in corso..."
        Refresh-UI
        $wc.DownloadFile($url, $targetPath)
        if (Test-Path $targetPath) {
            Set-SelectedIso $targetPath
            $downloadSuccess = $true
            Append-Log "[OK] Download completato con successo: $targetPath"
            $txtStepInfo.Text = "Download completato! Pronto per l'installazione."
        }
    } catch {
        Append-Log "[!] Download diretto non riuscito tramite WebClient: $($_.Exception.Message)"
        Append-Log "[i] Apertura del browser web predefinito per il download manuale..."
        try {
            [System.Diagnostics.Process]::Start($url)
        } catch {
            [System.Diagnostics.Process]::Start("https://github.com/ANDRYXify/OSify/releases")
        }
        [System.Windows.MessageBox]::Show("Il download diretto non puo' completarsi tramite i certificati di rete di Windows 7.`n`nE' stata aperta la pagina di download nel tuo browser.`nUna volta completato il download del file '$isoName', clicca 'Sfoglia' per selezionarlo.", "Download nel Browser", [System.Windows.MessageBoxButton]::OK, [System.Windows.MessageBoxImage]::Information)
    } finally {
        $btnDownloadIso.IsEnabled = $true
        $btnInstall.IsEnabled = $true
    }
})

# Helper per esecuzione comandi esterni senza congelamento della finestra
function Run-ToolWithOutput([string]$exePath, [string]$argString, [string]$description) {
    Append-Log "[+] $description..."
    $pInfo = New-Object System.Diagnostics.ProcessStartInfo
    $pInfo.FileName = $exePath
    $pInfo.Arguments = $argString
    $pInfo.UseShellExecute = $false
    $pInfo.RedirectStandardOutput = $true
    $pInfo.RedirectStandardError = $true
    $pInfo.CreateNoWindow = $true

    $proc = [System.Diagnostics.Process]::Start($pInfo)
    while (-not $proc.HasExited) {
        $line = $proc.StandardOutput.ReadLine()
        if ($line) {
            $trimmed = $line.Trim()
            if ($trimmed) { Append-Log "  > $trimmed" }
        }
        Refresh-UI
        [System.Threading.Thread]::Sleep(40)
    }
    $remaining = $proc.StandardOutput.ReadToEnd()
    if ($remaining) {
        foreach ($rLine in $remaining.Split("`n")) {
            $t = $rLine.Trim()
            if ($t) { Append-Log "  > $t" }
        }
    }
    return $proc.ExitCode
}

# Processo di Installazione
$btnInstall.Add_Click({
    # 1. Verifica selezione ISO
    if (-not $global:SelectedIso -or -not (Test-Path $global:SelectedIso)) {
        [System.Windows.MessageBox]::Show("Seleziona o indica prima il file ISO di OSify per procedere.`nPuoi cliccare 'Sfoglia' o trascinare il file nella finestra.", "Immagine ISO Mancante", [System.Windows.MessageBoxButton]::OK, [System.Windows.MessageBoxImage]::Warning)
        return
    }

    # 2. Calcolo dello spazio strettamente necessario (per Vintage bastano ~1.5 GB)
    $isoLengthMB = [math]::Round((Get-Item $global:SelectedIso).Length / 1MB)
    $neededMB = [math]::Max(1200, $isoLengthMB + 350)
    $neededGB = [math]::Round($neededMB / 1024, 1)

    if ($freeSpaceGB -lt $neededGB -and -not (Test-Path 'O:\')) {
        $res = [System.Windows.MessageBox]::Show("Su C: sono rilevati $freeSpaceGB GB liberi (spazio raccomandato: $neededGB GB).`nDesideri tentare comunque il partizionamento?", "Spazio su Disco Ridotto", [System.Windows.MessageBoxButton]::YesNo, [System.Windows.MessageBoxImage]::Question)
        if ($res -ne [System.Windows.MessageBoxResult]::Yes) { return }
    }

    $btnInstall.IsEnabled = $false
    $btnBrowseIso.IsEnabled = $false
    $btnDownloadIso.IsEnabled = $false

    # FASE 1: Partizionamento o Preparazione Unità O:
    $progBar.Value = 15
    $txtStepInfo.Text = "[1/4] Configurazione partizione temporanea per l'avvio..."

    $partitionReady = $false

    # Controllo se l'unita O: esiste gia
    if (Test-Path 'O:\') {
        # Controllo se i file sono stati estratti in una sottocartella di O: (es. estrazione WinRAR/7-Zip con cartella)
        try {
            $nested = Get-ChildItem 'O:\' -Directory -ErrorAction SilentlyContinue | Where-Object { 
                (Test-Path "$($_.FullName)\boot") -or (Test-Path "$($_.FullName)\osify") -or (Test-Path "$($_.FullName)\isolinux") 
            } | Select-Object -First 1
            if ($nested) {
                Append-Log "[i] File OSify rilevati nella sottocartella $($nested.Name): spostamento alla radice di (O:)..."
                Get-ChildItem $nested.FullName | Move-Item -Destination 'O:\' -Force
                Remove-Item $nested.FullName -Recurse -Force -ErrorAction SilentlyContinue
            }
        } catch {}

        # CONTROLLO FONDAMENTALE: se l'utente ha gia estratto i file su O: NON cancellarli!
        $hasOsifyFiles = (Test-Path 'O:\boot') -or (Test-Path 'O:\osify') -or (Test-Path 'O:\EFI') -or (Test-Path 'O:\isolinux') -or (Test-Path 'O:\arch') -or (Test-Path 'O:\OSify-Setup.bat')
        if ($hasOsifyFiles) {
            Append-Log "[OK] File di installazione di OSify gia' presenti sull'unita (O:)! Preservazione in corso..."
            $partitionReady = $true
            # Garantisci che la partizione sia attiva per il boot senza formattarla
            $dpActFile = Join-Path $env:TEMP "osify_act_dp.txt"
            [System.IO.File]::WriteAllLines($dpActFile, @("select volume O", "active"))
            $null = Run-ToolWithOutput "diskpart.exe" "/s `"$dpActFile`"" "Attivazione partizione (O:) per il boot"
            Remove-Item $dpActFile -Force -ErrorAction SilentlyContinue
        } else {
            Append-Log "[i] Unita (O:) rilevata. Formattazione rapida per installazione..."
            $dpCleanFile = Join-Path $env:TEMP "osify_clean_dp.txt"
            $dpCleanLines = @(
                "select volume O",
                "format fs=fat32 quick label=OSIFY_BOOT",
                "active"
            )
            [System.IO.File]::WriteAllLines($dpCleanFile, $dpCleanLines)
            $code = Run-ToolWithOutput "diskpart.exe" "/s `"$dpCleanFile`"" "Formattazione rapida unita (O:)"
            Remove-Item $dpCleanFile -Force -ErrorAction SilentlyContinue
            if (Test-Path 'O:\') {
                $partitionReady = $true
                Append-Log "[OK] Unita (O:) formattata e pronta per i file di installazione."
            }
        }
    }

    if (-not $partitionReady) {
        Append-Log "[+] Creazione partizione temporanea tramite DiskPart (Dimensione richiesta: $neededMB MB)..."
        $dpFile = Join-Path $env:TEMP "osify_gui_dp.txt"
        $dpLines = @(
            "select volume c",
            "shrink desired=$neededMB minimum=800",
            "create partition primary",
            "format fs=fat32 quick label=OSIFY_BOOT",
            "assign letter=O",
            "active"
        )
        [System.IO.File]::WriteAllLines($dpFile, $dpLines)

        $code = Run-ToolWithOutput "diskpart.exe" "/s `"$dpFile`"" "Esecuzione DiskPart su volume C:"
        Remove-Item $dpFile -Force -ErrorAction SilentlyContinue

        if (Test-Path 'O:\') {
            $partitionReady = $true
            Append-Log "[OK] Partizione (O:) creata con successo e pronta."
        } else {
            # Tentativo fallback con dimensione minima per netbook con poco spazio
            Append-Log "[!] Tentativo creazione con dimensione ultra-compatta (800MB)..."
            $dpFbFile = Join-Path $env:TEMP "osify_fb_dp.txt"
            $dpFbLines = @(
                "select volume c",
                "shrink desired=800 minimum=500",
                "create partition primary",
                "format fs=fat32 quick label=OSIFY_BOOT",
                "assign letter=O",
                "active"
            )
            [System.IO.File]::WriteAllLines($dpFbFile, $dpFbLines)
            $code = Run-ToolWithOutput "diskpart.exe" "/s `"$dpFbFile`"" "Tentativo DiskPart ridotto"
            Remove-Item $dpFbFile -Force -ErrorAction SilentlyContinue

            if (Test-Path 'O:\') {
                $partitionReady = $true
                Append-Log "[OK] Partizione (O:) creata al secondo tentativo."
            }
        }
    }

    if (-not (Test-Path 'O:\')) {
        Append-Log "[ERRORE] Impossibile creare o trovare l'unita (O:)."
        Append-Log "Suggerimento: Verifica che il disco non abbia gia' 4 partizioni primarie (limite MBR)."
        [System.Windows.MessageBox]::Show("Impossibile creare automaticamente la partizione O:\.`n`nMotivo probabile: il disco MBR ha gia' raggiunto il limite di 4 partizioni, oppure C: non ha spazio non frammentato da ridurre.", "Errore Partizione", [System.Windows.MessageBoxButton]::OK, [System.Windows.MessageBoxImage]::Error)
        $btnInstall.IsEnabled = $true
        $btnBrowseIso.IsEnabled = $true
        $btnDownloadIso.IsEnabled = $true
        return
    }

    # FASE 2: Estrazione File ISO
    $progBar.Value = 45
    $txtStepInfo.Text = "[2/4] Estrazione file di sistema e bootloader su (O:)..."
    Append-Log "[+] Controllo ed estrazione dei file del sistema operativo..."

    $extracted = $false

    # Controllo se i file sono già estratti (es. estrazione manuale o precedente)
    try {
        $nested = Get-ChildItem 'O:\' -Directory -ErrorAction SilentlyContinue | Where-Object { 
            (Test-Path "$($_.FullName)\boot") -or (Test-Path "$($_.FullName)\osify") -or (Test-Path "$($_.FullName)\isolinux") 
        } | Select-Object -First 1
        if ($nested) {
            Append-Log "[i] File trovati nella sottocartella $($nested.Name): riposizionamento in corso..."
            Get-ChildItem $nested.FullName | Move-Item -Destination 'O:\' -Force
            Remove-Item $nested.FullName -Recurse -Force -ErrorAction SilentlyContinue
        }
    } catch {}

    if ((Test-Path 'O:\boot') -or (Test-Path 'O:\osify') -or (Test-Path 'O:\EFI') -or (Test-Path 'O:\isolinux') -or (Test-Path 'O:\arch') -or (Test-Path 'O:\OSify-Setup.bat')) {
        $extracted = $true
        Append-Log "[OK] I file di avvio di OSify sono gia' presenti e pronti su (O:)!"
    }

    # Metodo A: 7z.exe completo con 7z.dll incluso nel pacchetto (Supporto ISO nativo, 100% offline)
    $local7z = Join-Path $scriptDir "7z.exe"
    if (-not $extracted -and (Test-Path $local7z)) {
        Append-Log "[+] Estrazione ISO in corso con 7-Zip nativo integrato..."
        $code = Run-ToolWithOutput $local7z "x `"$global:SelectedIso`" -oO:\ -y" "Estrazione ISO tramite 7-Zip completo integrato"
        if ((Test-Path 'O:\boot') -or (Test-Path 'O:\EFI') -or (Test-Path 'O:\arch') -or (Test-Path 'O:\osify')) {
            $extracted = $true
            Append-Log "[OK] File ISO estratti con successo su (O:) tramite 7-Zip integrato!"
        }
    }

    # Metodo B: 7-Zip installato nel sistema
    if (-not $extracted) {
        $candidates7z = @(
            "$env:ProgramFiles\7-Zip\7z.exe",
            "${env:ProgramFiles(x86)}\7-Zip\7z.exe"
        )
        foreach ($c7z in $candidates7z) {
            if ($c7z -and (Test-Path $c7z)) {
                $code = Run-ToolWithOutput $c7z "x `"$global:SelectedIso`" -oO:\ -y" "Estrazione tramite 7-Zip di sistema"
                if ((Test-Path 'O:\boot') -or (Test-Path 'O:\EFI') -or (Test-Path 'O:\arch') -or (Test-Path 'O:\osify')) {
                    $extracted = $true
                    break
                }
            }
        }
    }

    # Metodo C: Mount-DiskImage (Windows 8, 10, 11)
    if (-not $extracted -and (Get-Command "Mount-DiskImage" -ErrorAction SilentlyContinue)) {
        try {
            Append-Log "[i] Tentativo di montaggio nativo tramite Mount-DiskImage..."
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
        Append-Log "[ERRORE] Impossibile estrarre automaticamente i file della ISO sull'unita (O:)."
        Append-Log "[i] Suggerimento: Puoi estrarre i file contenuti nella ISO direttamente dentro l'unita (O:), poi clicca 'PREPARA INSTALLAZIONE SENZA USB' e i file verranno preservati automaticamente!"
        [System.Windows.MessageBox]::Show("Estrazione automatica non completata.`n`nPuoi estrarre i file della ISO direttamente nell'unita O:\ con qualsiasi programma, poi ricliccare 'PREPARA INSTALLAZIONE SENZA USB': l'installer li riconoscera' e non li cancellera'.", "Estrazione File", [System.Windows.MessageBoxButton]::OK, [System.Windows.MessageBoxImage]::Warning)
        $btnInstall.IsEnabled = $true
        return
    }

    $progBar.Value = 80
    Append-Log "[OK] Tutti i file di avvio sono stati posizionati su (O:)."

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
        Append-Log "[OK] Sistema Legacy BIOS (MBR): partizione O:\ contrassegnata come attiva per l'avvio diretto."
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
