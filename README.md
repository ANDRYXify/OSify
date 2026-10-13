<p align="center">
  <img src="OSify.png" alt="OSify Logo by Andryx" width="320"/>
</p>

<h1 align="center">OSify — Sistema Operativo per Gaming Estremo, Live Streaming e Multi-Runtime</h1>

<p align="center">
  <b>Ingegnerizzato da Andrea Taliento (ANDRYXify)</b><br/>
  <i>Gaming a 500 FPS • Live Multi-Stream (Twitch/Kick/YT) • Architettura a Blocchi • Multi-Runtime (Win/Android/Mac) • Resurrezione PC Vintage</i>
</p>

---

<p align="center">
  <a href="https://github.com/ANDRYXify/OSify/releases/latest/download/OSify-NoUSB-Windows-Installer.zip">
    <img src="https://img.shields.io/badge/Download_Installer-Windows_Senza_USB_(ZIP)-0078D6?style=for-the-badge&logo=windows&logoColor=white" alt="Download Windows No-USB Installer"/>
  </a>
  &nbsp;&nbsp;
  <a href="https://github.com/ANDRYXify/OSify/releases/latest/download/OSify-x86_64-v3.iso">
    <img src="https://img.shields.io/badge/Download_ISO-OSify_x86--64--v3_(Live)-9333EA?style=for-the-badge&logo=linux&logoColor=white" alt="Download OSify ISO"/>
  </a>
</p>

---



## 🏛️ Pilastri Architetturali

### 1. Base ad Altissime Prestazioni: Microarchitettura `x86-64-v3` & Kernel BORE
A differenza dei sistemi operativi tradizionali compilati per la generica baseline `x86-64-v1` (compatibile con CPU del 2003), OSify utilizza una toolchain compilata interamente con istruzioni vettoriali avanzate (**AVX, AVX2, FMA, BMI1/2** e opzionalmente **AVX-512**).
* **Kernel**: Linux con scheduler **BORE (Burst-Oriented Response Enhancer)**, `PREEMPT_DYNAMIC`, tickless idle a 1000Hz (`CONFIG_HZ=1000`) e supporto a `futex2 / sys_futex_waitv`.
* **Allocatore memoria**: Supporto trasparente a **mimalloc** per emulatori e motori di gioco.
* **Memoria**: Pagine Hugepages trasparenti (THP 2MB) con deframmentazione asincrona e ZRAM compressa in `zstd`.

### 2. Zero-Lag Live Streaming & Network Traffic Shaper (CAKE QoS)
Durante le live ad alto bitrate (1080p60 o 4K a 8-15 Mbps verso Twitch/Kick/YouTube), la saturazione della banda di upload provoca normalmente il fenomeno del **bufferbloat** (il ping nei giochi salta da 15ms a 200ms+).
* **Soluzione OSify**: Modulo QoS basato su algoritmo di accodamento **CAKE** (Common Applications Kept Enhanced) e marcatura pacchetti **DSCP** a livello kernel (`nftables`).
* **Priorità assoluta**: I pacchetti UDP dei giochi sono marcati come `Expedited Forwarding (EF / CS5)`. Il flusso RTMP/SRT/WHIP di OBS è instradato con banda garantita ma cede il passo ai pacchetti a latenza critica.

### 3. Sottosistema Audio Professionale per Streamer (PipeWire Pro-Audio)
Architettura PipeWire con quantizzazione a bassissima latenza (buffer a 64 campioni @ 48kHz, latenza < 2.5ms) e creazione automatica di **bus audio virtuali isolati**:
* `OSify-Game`: Audio di gioco e desktop.
* `OSify-Voice`: Discord / chat vocale.
* `OSify-Music`: Canale musicale (Spotify/Browser) escludibile dalla traccia VOD di Twitch per evitare strike da copyright.
* `OSify-Mic-DSP`: Canale microfono con riduzione rumore neurale in tempo reale (DeepFilterNet/RNNoise) ed equalizzatore.
* `OSify-Stream-Master`: Bus di cattura unificato per OBS Studio.

### 4. Matrice Multi-Runtime & Gestione Anti-Cheat Ring-0
* **Windows (PE/DirectX)**: Proton-GE / Wine-TKG con DXVK, VKD3D-Proton, Fsync e shader cache asincrona.
* **Gestione Anti-Cheat a Livello Kernel (Ring-0)**:
  * **Anti-Cheat supportati da Proton**: Easy Anti-Cheat (EAC) e BattlEye con modulo nativo bridge abilitato (es. *Elden Ring*, *War Thunder*).
  * **Anti-Cheat Ring-0 bloccanti (*Riot Vanguard*, *Ricochet*, *EA AC*)**:
    * **Soluzione 1 (KVM Cloaked Stealth)**: Profilo macchina virtuale con mascheramento ipervisore (CPUID leaf hidden, spoofing SMBIOS ASUS ROG reale, modulo TPM 2.0 emulato e passthrough PCIe VFIO).
    * **Soluzione 2 (Fast-Boot UEFI)**: Script one-time `osify-ctl anticheat boot-windows` che imposta `BootNext` nella NVRAM UEFI ed effettua il reboot su Windows. Al successivo spegnimento/riavvio, il sistema torna automaticamente in OSify senza toccare il BIOS.
* **Android (APK)**: Waydroid containerizzato in LXC con condivisione diretta del kernel Linux host e accelerazione GPU Mesa dri3 (zero emulazione virtuale; bridge libndk per binari ARM).
* **macOS (Mach-O)**: Layer Darling per toolchain Darwin e modulo KVM-VFIO per istanze macOS isolate con passthrough hardware.


### 5. Emulazione Console di Nuova Generazione
Stack ottimizzato per emulatori vettoriali:
* **RPCS3** (PS3) con supporto AVX2/AVX-512 e compilazione shader asincrona.
* **Ryujinx** (Nintendo Switch) con Vulkan GPL.
* **PCSX2** (PS2), **Dolphin** (GameCube/Wii), **DuckStation** (PS1), **Xenia** (Xbox 360), **Cemu** (Wii U).
* Frontend unificato a 10-foot UI (**ES-DE** - EmulationStation Desktop Edition) integrato con controller DualSense (haptic feedback), Xbox e Switch Pro.

### 6. Desktop Environment: KDE Plasma 6 Wayland
* Supporto nativo **HDR** e gestione spazio colore.
* **VRR (Variable Refresh Rate)** indipendente per monitor.
* **Tearing Protocol** sbloccato per latenza minima negli esport competitivi.
* Profilo grafico ad altissimo contrasto e zero compositing lag in modalità fullscreen.

### 7. Filesystem Btrfs con Snapshot Atomici & No-CoW per Gaming
* **Subvolumi dedicati**: `@` (sistema protetto), `@home` (dati utente indipendenti), `@games_wine` e `@waydroid`.
* **Attributo `nodatacow` (`chattr +C`)**: disabilita il Copy-on-Write sui file enormi dei giochi e sulle macchine virtuali, azzerando la frammentazione del disco e garantendo I/O costante.
* **Rollback in 5 secondi**: Snapshot automatici prima di ogni aggiornamento con Snapper, avviabili direttamente dal bootloader in caso di regressione dei driver.

### 8. Relay Multi-Broadcast Zero-Overhead (Twitch + Kick + YouTube)
* Modulo [`streaming/relay/osify-stream-relay.py`](file:///Users/andryxify/OSify/streaming/relay/osify-stream-relay.py):
* OBS trasmette **una sola volta** in locale (`rtmp://127.0.0.1:1935/live/stream`) con il proprio encoder preferito.
* Il demuxer duplica il bitstream in parallelo a livello socket verso Twitch, Kick e YouTube con **0% di carico aggiuntivo su CPU/GPU**.

### 9. Demone Intelligente di Performance (osify-daemon)
* Servizio in background [`services/osify-daemon.py`](file:///Users/andryxify/OSify/services/osify-daemon.py):
* Rileva istantaneamente l'avvio di giochi ed emulatori, forza il governor CPU su `performance`, attiva il quantum PipeWire a 64 campioni e scala la priorità interattiva via BORE.
* Ripristina la modalità powersave alla chiusura della sessione.

### 10. Resurrezione PC Vintage & Compatibilità Hardware Universale (dal 2003 ad oggi)
* **Compatibilità CPU Universale**: Grazie al supporto `glibc-hwcaps`, il sistema si avvia su qualsiasi processore a 64-bit dal 2003 (Core 2 Duo, Athlon 64, Nehalem), abilitando dinamicamente le librerie vettoriali `v3`/`v4` solo quando l'hardware lo supporta.
* **Supporto Boot Ibrido**: Immagine ISO compatibile sia con **UEFI moderno** sia con **Legacy BIOS (MBR)** per schede madri storiche.
* **GPU Legacy Sbloccate su Vulkan**: Modulo [`kernel/legacy/99-osify-legacy-gpu.conf`](file:///Users/andryxify/OSify/kernel/legacy/99-osify-legacy-gpu.conf) che forza il driver moderno `amdgpu` sulle schede AMD GCN 1.0/2.0 (serie HD 7000, R7, R9), regalando supporto Vulkan e DXVK a schede grafiche di oltre 12 anni fa.
* **Low-Spec Mode per 2GB-4GB di RAM**: Attivabile via `osify-ctl mode lowspec`, configura ZRAM compressa in `zstd` (espandendo virtualmente la memoria senza usurare dischi HDD meccanici) e imposta KDE Plasma 6 in modalità alleggerita con footprint a soli **~400MB di RAM**.
* **Hardware Probe Automatico**: [`kernel/legacy/osify-hardware-detect.sh`](file:///Users/andryxify/OSify/kernel/legacy/osify-hardware-detect.sh) scansiona l'hardware e tara il sistema in tempo reale.


### 11. Architettura Modulare "A Blocchi" (Lego-Style)
* **Personalizzazione istantanea e dichiarativa**: il sistema è suddiviso in blocchi indipendenti gestiti via JSON ([`blocks/osify-blocks.json`](file:///Users/andryxify/OSify/blocks/osify-blocks.json)).
* **Composizione on-demand**: puoi comporre il tuo OSify attivando o disattivando con un singolo comando i blocchi:
  * `gaming`: Gamescope, Steam, GameMode, Proton-GE.
  * `streaming`: OBS Studio, Multi-RTMP relay, CAKE QoS, PipeWire VOD sinks.
  * `presentation`: PowerPoint, EasyWorship, NDI bridge, font Microsoft, clicker USB.
  * `emulation`: RPCS3, Ryujinx, PCSX2, Dolphin, mimalloc wrapper.
  * `android`: Waydroid LXC container con bridge ARM.
  * `darwin`: Darling CLI e profili OSX-KVM VFIO.
  * `vintage`: ZRAM zstd e KDE Plasma Low-Spec.
* Comando rapido: `osify-ctl block list` oppure `osify-ctl block enable <blocco>`.

### 12. Stage & Event Presentation Suite (PowerPoint & EasyWorship)
* **Prefix Wine Multimediale**: [`presentation/osify-presentation-setup.sh`](file:///Users/andryxify/OSify/presentation/osify-presentation-setup.sh) configura un ambiente dedicato con DirectShow, MediaFoundation, LAVFilters e WMP11 per eseguire sfondi video e transizioni complesse in **EasyWorship** e **PowerPoint**.
* **Tipografia Microsoft Fedele al 100%**: Font Calibri, Cambria, Segoe UI e Arial installati per prevenire sfasamenti di testo e interruzioni di riga durante le presentazioni.
* **Uscita NDI Video (Network Device Interface)**: Le slide vengono trasmesse direttamente via rete IP a OBS Studio senza richiedere schede di acquisizione fisiche, consentendo overlay di testi trasparenti per la live.
* **Multi-Display & Stage Display**: Gestione a 3 schermi (Console Operatore, Schermo Sala/Proiettore borderless e Confidence Monitor per i relatori sul palco).
### 13. Installer Windows Senza Chiavetta USB (No-USB Engine)
* **Installazione diretta da Windows**: Per utenti con vecchi PC privi di pendrive USB, lo script [`tools/windows-installer/OSify-NoUSB-Installer.ps1`](file:///Users/andryxify/OSify/tools/windows-installer/OSify-NoUSB-Installer.ps1):
  1. Riduce temporaneamente `C:` di 5 GB tramite `diskpart` e crea una partizione `OSIFY_BOOT`.
  2. Estrae l'immagine di OSify e registra una voce temporanea nel BCD di Windows Boot Manager.
  3. Imposta un riavvio one-time che parte direttamente nell'installer di OSify.
* **Auto-Cancellazione Post-Install**: Il modulo [`system/installer/osify-cleanup-temp-partition.sh`](file:///Users/andryxify/OSify/system/installer/osify-cleanup-temp-partition.sh) rileva la partizione temporanea al termine dell'installazione, la cancella ed espande il disco principale per non sprecare nemmeno un byte.

### 14. Multitasking & Gestione Finestre Stile MacBook
* Script: [`desktop/macos-multitasking/kwin-macos-gestures.sh`](file:///Users/andryxify/OSify/desktop/macos-multitasking/kwin-macos-gestures.sh)
* **Mission Control & Spaces su Wayland**:
  * **Swipe a 3-4 dita verso l'alto**: Apre la panoramica interattiva (Mission Control) con tutti i desktop virtuali allineati in alto.
  * **Swipe orizzontale a 3 dita**: Scorrimento cinematico fluido 1:1 tra i diversi spazi di lavoro (Spaces).
  * **Hot Corners (Angoli Attivi)**: In alto a sinistra per Mission Control, in basso a destra per mostrare la scrivania.
  * **Trackpad fluido**: Tap-to-click, scrolling naturale e pinch-to-zoom Wayland abilitati di default.

### 15. Touchscreen, Tablet 2-in-1 & Microsoft Surface Suite
* Script e regole: [`system/touchscreen/osify-touch-surface.sh`](file:///Users/andryxify/OSify/system/touchscreen/osify-touch-surface.sh) e [`system/touchscreen/99-osify-surface.rules`](file:///Users/andryxify/OSify/system/touchscreen/99-osify-surface.rules)
* **Supporto Hardware Microsoft Surface**: Integrazione driver per digitalizzatori Intel IPTS, sensori batteria `surface_aggregator` e penne stilo con livelli di pressione (Surface Pen / MPP).
* **Tastiera Virtuale a Comparsa Automatica**: Tastiera Maliit Wayland integrata che compare toccando campi di testo se la tastiera fisica è staccata o ripiegata.
* **Auto-Rotazione & Accelerometro**: `iio-sensor-proxy` ruota automaticamente lo schermo e il digitalizzatore touch in base all'orientamento fisico del dispositivo.
* **Tablet Mode Switch**: Distaccando la Type Cover o ribaltando il display a 360°, KWin ingrandisce i pulsanti dell'interfaccia per il tocco delle dita.

---


## 📁 Struttura del Progetto

```
OSify/
├── blocks/               # Architettura modulare a blocchi (osify-blocks.json & manager)
├── build/                # Strumenti di generazione ISO (Archiso x86-64-v3 profile)
│   └── docker/           # Builder Docker per compilare la ISO da macOS o Linux
├── kernel/               # Sysctl, udev rules per controller e storage, moduli
│   └── legacy/           # Rilevamento hardware dinamico e sblocco GPU storiche
├── presentation/         # Suite presentazioni (EasyWorship, PowerPoint, NDI, clicker)
├── network/              # QoS Traffic Shaper (CAKE, BBRv3, nftables DSCP)
├── audio/                # Profili PipeWire Pro-Audio & virtual sinks
├── emulation/            # Launcher ad alte prestazioni con mimalloc & shader cache
├── runtimes/             # Moduli Windows (Proton), Android (Waydroid), macOS (Darling/KVM)
│   └── windows/anticheat # Database Anti-Cheat Ring-0, KVM Stealth e Fast-Boot UEFI
├── streaming/            # Profili OBS Studio & Multi-RTMP relay zero-overhead
│   └── relay/            # Relay simultaneo Twitch + Kick + YouTube
├── services/             # Demone di rilevamento e ottimizzazione automatica
├── system/storage/       # Layout Btrfs, subvolumi, No-CoW e configurazioni Snapper
├── desktop/              # Configurazioni KDE Plasma 6 Wayland (HDR, VRR, Tearing)
│   └── profiles/         # Profilo grafico Low-Spec per macchine con 2GB-4GB RAM
├── tests/                # Test suite ingegneristica automatizzata (29 verifiche)
└── tools/                # CLI ('osify-ctl') e Control Center GUI per KDE Plasma 6
    └── osify-gui/        # Dashboard grafica moderna in PyQt6 per KDE Plasma
```

---

## 🚀 Utilizzo Rapido

### 1. Control Center Grafico (KDE Plasma 6)
```bash
python3 tools/osify-gui/osify-control-center.py
```

### 2. Gestione del Sistema da Terminale (CLI)
```bash
# Diagnostica hardware e supporto CPU (v1, v2, v3, v4)
osify-ctl hw-detect

# Gestione architettura a blocchi
osify-ctl block list
osify-ctl block enable presentation
osify-ctl block enable android

# Verifica compatibilità anti-cheat (Ring-0)
osify-ctl anticheat check Valorant

# Modalità presentazioni dal vivo (PowerPoint / EasyWorship)
osify-ctl presentation mode on

# Profili istantanei
osify-ctl mode streaming   # Live Twitch/Kick/YT con protezione ping
osify-ctl mode gaming      # eSport a latenza minima
osify-ctl mode lowspec     # Resurrezione PC vintage (~400MB RAM)
```

### 3. Esecuzione Test Suite Automatizzata
```bash
./tests/osify-test-suite.sh
```

### 4. Compilazione Immagine ISO Avviabile (via Docker da Mac o Linux)
```bash
cd build/docker && ./run-build.sh
```


