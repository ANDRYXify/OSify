<p align="center">
  <img src="OSify.png" alt="OSify Logo" width="280"/>
</p>

<h1 align="center">OSify</h1>

<p align="center">
  <b>Distribuzione Linux Specializzata per Performance Estreme e Rigenerazione Hardware Legacy</b><br/>
  <i>Ingegnerizzato da Andrea Taliento (ANDRYXify)</i>
</p>

---

<p align="center">
  <a href="https://github.com/ANDRYXify/OSify/releases/latest/download/OSify-NoUSB-Windows-Installer.zip">
    <img src="https://img.shields.io/badge/Installer_Windows-Senza_USB_(v1.3.0)-0078D6?style=for-the-badge&logo=windows&logoColor=white" alt="Installer Windows Senza USB"/>
  </a>
  &nbsp;
  <a href="https://github.com/ANDRYXify/OSify/releases/latest/download/OSify-x86_64-v3.iso">
    <img src="https://img.shields.io/badge/ISO_Standard-x86--64--v3_(v1.3.0)-7C3AED?style=for-the-badge&logo=linux&logoColor=white" alt="ISO Standard x86_64-v3"/>
  </a>
  &nbsp;
  <a href="https://github.com/ANDRYXify/OSify/releases/latest/download/OSify-Vintage-i686.iso">
    <img src="https://img.shields.io/badge/ISO_Vintage-32--bit_i686_(v1.3.0)-10B981?style=for-the-badge&logo=linux&logoColor=white" alt="ISO Vintage 32-bit i686"/>
  </a>
  &nbsp;
  <a href="https://github.com/ANDRYXify/OSify/releases/latest">
    <img src="https://img.shields.io/badge/Release-v1.3.0_Latest-22C55E?style=for-the-badge&logo=github&logoColor=white" alt="Official Release"/>
  </a>
</p>

<p align="center">
  <a href="https://github.com/ANDRYXify/OSify/pkgs/container/osify">
    <img src="https://img.shields.io/badge/Container-ghcr.io%2Fandryxify%2Fosify:latest-2563EB?style=flat-square&logo=docker&logoColor=white" alt="GitHub Container Registry"/>
  </a>
  &nbsp;
  <a href="https://github.com/ANDRYXify/OSify/actions">
    <img src="https://img.shields.io/badge/Tests-105%2F105_Passed-059669?style=flat-square&logo=githubactions&logoColor=white" alt="Test Suite"/>
  </a>
  &nbsp;
  <a href="#architettura-dei-due-target">
    <img src="https://img.shields.io/badge/Arch-x86__64_|_i686_|_ARM_|_Silicon-6366F1?style=flat-square&logo=archlinux&logoColor=white" alt="Architetture Supportate"/>
  </a>
  &nbsp;
  <a href="LICENSE">
    <img src="https://img.shields.io/badge/License-GPL_v3.0-64748B?style=flat-square&logo=gnu&logoColor=white" alt="Licenza GPLv3"/>
  </a>
</p>

---

## Panoramica del Progetto

OSify è un sistema operativo basato su Linux ingegnerizzato su due target architetturali rigorosamente distinti, per evitare compromessi o dispersioni di risorse:

1. **OSify Standard (x86-64-v3)**: Dedicato a postazioni moderne da gaming, creazione di contenuti e live streaming ad alto bitrate. Compilato con istruzioni vettoriali avanzate (AVX, AVX2, FMA) e kernel Linux BORE a latenza deterministica.
2. **OSify Vintage (i686 / 32-bit)**: Dedicato a computer storici e netbook ultra-compatti (es. Toshiba Dynabook NB200 con Intel Atom N280 e GPU Intel GMA 950). Ottimizzato per operare con un footprint di memoria a riposo di ~115-125 MB, gestendo nativamente schermi WSVGA a bassa risoluzione (1024x600).

---

## Architettura dei Due Target

### 1. OSify Standard (`x86_64-v3`)

* **Kernel**: Linux con scheduler BORE (Burst-Oriented Response Enhancer), `PREEMPT_DYNAMIC`, tickless idle a 1000Hz (`CONFIG_HZ=1000`) e supporto nativo a `futex2 / sys_futex_waitv`.
* **Desktop Environment**: KDE Plasma 6 sotto Wayland, con gestione finestre e multitasking ispirati alla fluidità di macOS (gestures a tre dita, Mission Control rapido, visualizzazione a griglia).
* **Network Traffic Shaper (CAKE QoS)**: Instradamento con algoritmo CAKE e marcatura DSCP a livello kernel (`nftables`). I flussi gaming UDP sono prioritizzati con classe Expedited Forwarding (EF), prevenendo il bufferbloat durante live stream simultanei su Twitch, Kick e YouTube.
* **Sottosistema Audio**: PipeWire Pro-Audio con quantizzazione a 64 campioni @ 48kHz (< 2.5ms di latenza). Separazione dei bus audio virtuali (`OSify-Game`, `OSify-Voice`, `OSify-Music`, `OSify-Mic`) con isolamento della traccia VOD Track 2 di Twitch.
* **Stack Grafico & Runtime**: Vulkan con driver Mesa RADV/NVK, DXVK-Async, Proton-GE, GameScope micro-compositor e container Waydroid LXC per applicazioni Android con accelerazione DRI3.

### 2. OSify Vintage Micro-Edition (`i686 / 32-bit`)

* **Target Hardware Specifico**: Netbook con CPU Intel Atom N270/N280 (famiglia Diamondville), 1GB di memoria DDR2, GPU integrata Intel GMA 950 (chipset Calistoga / 945GME) e display WSVGA 10.1" (1024x600).
* **Kernel & Memoria**: Linux LTS a 32-bit con `CONFIG_HIGHMEM4G=y`. ZRAM compressa con algoritmo rapido `lz4` dimensionata a 1.5x della RAM fisica (1.5 GB di swap compresso in memoria), con `vm.swappiness=100`.
* **Desktop Environment**: Openbox & LXQt ultra-leggero, con compositing XRender leggero (`picom`) privo di blur gaussiani pesanti che saturerebbero la GMA 950.
* **Mitigazioni Display 1024x600**:
  * Pannello inferiore compatto Tint2 a 24 pixel (576 pixel verticali utili).
  * Scorciatoia universale `Alt + Trascinamento sinistro` su qualsiasi punto della finestra per spostare agevolmente finestre di dialogo con altezza superiore a 600px.
  * Window snapping a metà schermo tramite `Super + Freccia Sinistra / Destra`.
* **Applicativi di Base**: Browser Web reale `Falkon` (WebKit/QtWebEngine leggero a basso impatto RAM), lettore documenti `qpdfview`, media player `mpv`, file manager `pcmanfm-qt`.

---

## Struttura del Repository

```
OSify/
├── audio/                   # Routing PipeWire Pro-Audio e script bus virtuali
│   ├── pipewire.conf.d/     # Configurazione quantizzazione a 64 campioni
│   └── osify-audio-setup.sh # Creazione canali isolati per Twitch VOD Track 2
├── blocks/                  # Gestore modulare dei blocchi (JSON + CLI)
├── build/                   # File di build e manifesti pacchetti
│   ├── packages.x86_64      # Lista pacchetti ufficiali per x86_64
│   ├── packages.i686        # Lista pacchetti ufficiali per i686 Vintage
│   ├── generate-live-iso.sh # Generatore immagini ISO ibride avviabili
│   └── release/             # Script di packaging per release GitHub
├── desktop/                 # Configurazioni ambienti desktop
│   ├── branding/            # Sfondi ufficiali con logo OSify (1080p e 1024x600)
│   ├── kde-plasma/          # Ottimizzazioni Wayland e tearing per Plasma 6
│   ├── macos-multitasking/  # Gesti multitouch, Mission Control e scorciatoie
│   └── vintage/             # Configurazione Openbox e Tint2 per netbook Atom
├── kernel/                  # Ottimizzazioni a livello kernel
│   ├── osify-sysctl.conf    # Parametri vm.max_map_count, CAKE e BBR
│   ├── limits.d/            # Priorità real-time e memlock
│   └── udev/                # Regole udev per controller e scheduler I/O
├── network/                 # Traffic Shaper CAKE QoS e regole nftables
├── runtimes/                # Matrice di compatibilità runtime (Proton, Waydroid, Darling)
├── tests/                   # Suite di collaudo automatizzata e simulatori QEMU
└── tools/                   # Toolchain di amministrazione
    ├── osify-ctl            # CLI centrale di gestione del sistema
    ├── hardware/            # Diagnostica predittiva hardware per netbook
    └── windows-installer/   # Installer per Windows senza supporto USB
```

---

## Installazione

### Metodo 1: Da Windows Senza Chiavetta USB
Ideale per netbook o computer sprovvisti di porte USB utilizzabili:
1. Scarica l'archivio [OSify-NoUSB-Windows-Installer.zip](https://github.com/ANDRYXify/OSify/releases/latest/download/OSify-NoUSB-Windows-Installer.zip).
2. Estrai il contenuto in una cartella locale.
3. Fai click destro su `OSify-Setup.bat` e seleziona **Esegui come amministratore**.
4. L'installer analizzerà l'hardware:
   * Se rileva una CPU a 32-bit (es. Atom N280), seleziona l'edizione Vintage.
   * Se rileva una CPU moderna a 64-bit, seleziona l'edizione Standard.
5. Verrà creata una partizione temporanea da 5 GB (`OSIFY_BOOT`) e registrata la voce nel Boot Manager di Windows (BCD). Al riavvio partirà direttamente l'installazione.

### Metodo 2: Immagine ISO Avviabile (USB / Ventoy / BalenaEtcher)
Scarica l'immagine corrispondente all'hardware di destinazione:
* **[OSify-x86_64-v3.iso](https://github.com/ANDRYXify/OSify/releases/latest/download/OSify-x86_64-v3.iso)** per PC moderni.
* **[OSify-Vintage-i686.iso](https://github.com/ANDRYXify/OSify/releases/latest/download/OSify-Vintage-i686.iso)** per netbook Atom e PC a 32-bit.

---

---

## Universal Execution Matrix (UEM) — Sfondamento delle Barriere Architetturali

OSify integra la **Universal Execution Matrix (UEM)**, un'architettura di sistema progettata per abbattere qualsiasi barriera di formato, ISA (Instruction Set Architecture) ed epoca informatica. Attraverso registrazioni kernel dirette (`binfmt_misc`) e un dispatcher polyglot deterministico ad alta efficienza (`osify-universal-dispatcher`), qualsiasi eseguibile può essere lanciato direttamente al doppio clic o da terminale:

| Formato / Ecosistema | Estensione / Magic | Runtime & Strategy OSify | Target Compatibilità |
| :--- | :--- | :--- | :--- |
| **Windows PE (32/64-bit)** | `.exe`, `.msi`, `.dll` (`MZ`) | **Proton-GE + DXVK** (Modern) / **Wine 32 + WineD3D** (Vintage) | Windows 95 fino a Windows 11 |
| **MS-DOS 16-bit** | `.com`, `.exe` (`MZ` 16-bit) | **DOSBox-Staging / DOSEMU2** trasparente con auto-mount | Software industriale SCADA, Turbo C, Giochi storici |
| **Apple Darwin / macOS** | `.app`, Mach-O (`feedface`) | **Darling HQ** translation layer con supporto dyld e Mach kernel | Applicativi macOS CLI e bundle desktop |
| **Android Applications** | `.apk`, `.aab` (`PK\x03\x04`) | **Waydroid LXC Container** con accelerazione hardware Mesa DRI3 | App Android native con forwarding grafico |
| **WebAssembly WASI** | `.wasm` (`\x00asm`) | **Wasmtime / Wasmer / Node WASI** standalone runtime | Moduli serverless, utility cloud-native e WASI |
| **Java Platform** | `.class`, `.jar` (`cafebabe`) | **OpenJDK HotSpot JIT Compiler** nativo | Applicazioni e librerie enterprise JVM |
| **Cross-ISA Linux ELF** | ELF ARM, AArch64, RISC-V | **Box64 / Box86 Dynarec JIT** (con forwarding nativo) o **QEMU User** | Binari compilati per CPU e microarchitetture eterogenee |
| **Polyglot Scripts** | `.py`, `.js`, `.sh`, `.lua` | **OSify Shebang Auto-Sniffer** con permessi dinamici | Script multipiattaforma senza pre-configurazione |

### Radiografia Architetturale dei Binari (`osify-inspect`)

Qualsiasi file binario può essere analizzato istantaneamente per comprendere la sua struttura interna e la strategia di esecuzione pianificata da OSify:

```bash
osify-ctl uem inspect /percorso/del/programma
```

---

## Hardware Adaptation Layer (HAL) & Dynamic Tuning

L'HAL di OSify rileva in tempo reale la topologia hardware all'avvio della macchina e applica un profilo deterministico ad altissima resa:

* **Sistemi Low-Memory / Vintage (< 1.5 GB RAM, es. Toshiba NB200 Atom N280)**:
  * Alloca ZRAM a 1.5x della memoria fisica con algoritmo rapido `lz4` (zero overhead su single-core).
  * Imposta `vm.swappiness=150`, `vm.dirty_ratio=10`, `vm.dirty_background_ratio=5` e `page-cluster=0` per azzerare i blocchi di sistema durante l'I/O su dischi meccanici a 5400 RPM.
  * Scheduler storage impostato automaticamente su `bfq` (Budget Fair Queueing) per mantenere reattiva l'interfaccia utente.
  * Stack grafico forzato su Mesa DRI2 / OpenGL classico (WineD3D), prevenendo crash da tentativi di caricamento Vulkan su Intel GMA 950.
* **Workstation Moderne (> 4 Core, >= 4 GB RAM)**:
  * Scheduler CPU a bassa latenza e throughput elevato.
  * ZRAM con algoritmo `zstd` ad alto rapporto di compressione.
  * `vm.max_map_count=2147483642` per supporto completo a giochi moderni, Steam Proton e motori Unreal Engine 5.
  * Stack Vulkan asincrono nativo (RADV/ANV/NVK).

---

## Suite Web & Browser Shield

OSify non impiega browser fittizi: integra browser open-source completi pre-configurati (`Falkon` per target vintage a bassissimo consumo di RAM, `Firefox` per postazioni moderne). Entrambi beneficiano del profilo **OSify Web Shield**:
* Blocco integrato di telemetria, tracker e annunci pubblicitari (riduzione fino al 60% del carico CPU su pagine web moderne).
* Limitazione dinamica dei processi content su macchine vintage e scaricamento automatico delle schede inattive dalla memoria RAM.
* Accelerazione hardware GPU VA-API/VDPAU su macchine x86_64 moderne.

---

## Strumenti di Amministrazione CLI (`osify-ctl`)

Il sistema include la CLI unificata `osify-ctl` per gestire ogni sottosistema:

```bash
# Universal Execution Matrix (UEM)
osify-ctl uem status                       # Visualizza matrice dei formati supportati
osify-ctl uem run <file-o-bundle>          # Esegue qualsiasi file tramite runner ottimale
osify-ctl uem inspect <file-o-bundle>      # Radiografia architetturale del binario
osify-ctl uem register                     # Ricarica registrazioni binfmt_misc nel kernel

# Hardware Adaptation Layer (HAL)
osify-ctl hal status                       # Diagnostica memoria fisica, ZRAM e scheduler I/O
osify-ctl hal apply                        # Riapplica in tempo reale il tuning hardware ottimale

# Ottimizzazione Navigazione Web
osify-ctl web tune                         # Configura profili browser veloci e anti-telemetria

# Cambio profilo prestazionale in tempo reale
osify-ctl mode gaming                      # Priorita' real-time a bassa latenza
osify-ctl mode streaming                   # Protezione bufferbloat CAKE QoS attiva
osify-ctl mode lowspec                     # Profilo a bassissimo consumo per macchine vintage

# Hardware Intelligence & Autocalibrazione Universale
osify-ctl autotune status                  # Stato dell'architettura rilevata (x86-64 v1-v4, 32-bit, ARM64, Silicon)
osify-ctl autotune detect                  # Audit completo di CPU, GPU, memoria ZRAM e scheduler storage
osify-ctl autotune apply                   # Calibrazione dinamica delle impostazioni kernel per l'hardware attuale

# Context-Aware Workload Governor (Intelligenza dei carichi dinamici)
osify-ctl workload status                  # Profilo di carico attualmente attivo
osify-ctl workload stream-game             # STREAMING + GIOCO ONLINE SIMULTANEO (0ms jitter CAKE + Twitch VOD Track 2)
osify-ctl workload esport                  # eSport gaming competitivo (BORE 1000Hz, tearing unredirect Wayland)
osify-ctl workload workstation             # Sviluppo & compilazione multi-core
osify-ctl workload auto                    # Rilevamento automatico processi in background e adattamento istantaneo

# Omnipotent Polyglot Terminal Shell Environment
osify-ctl shell-env test                   # Collaudo dei comandi Windows (dir, ipconfig, tasklist), macOS (open, sw_vers)
source tools/osify-shell/osify-polyglot-env.sh # Attivazione shell poliglotta universale
# Supporta in modo nativo e trasparente:
# • Windows: dir, cls, ipconfig, tasklist, taskkill, systeminfo, ver, copy, move, del
# • macOS: open, pbcopy, pbpaste, say, sw_vers, mdfind, caffeinate
# • Linux Distro Bridge: apt, pacman, dnf, apk, brew, winget (instradati su osify-pkg)

# Interfaccia Grafica SteamOS Console & KDE Plasma 6
osify-ctl deck                             # Avvio Deck Shell ad alte prestazioni con QAM e Workload switcher

# Gestione architettura modulare
osify-ctl block list
osify-ctl block enable presentation
osify-ctl block enable android

# Verifica compatibilita' Anti-Cheat (Ring-0)
osify-ctl anticheat check Valorant

# Collaudo preventivo tramite test suite e simulatore QEMU
osify-ctl test suite                       # Esecuzione test suite ufficiale (105/105 test verificati)
osify-ctl test hw-check --profile toshiba  # Diagnosi vincoli Toshiba NB200
osify-ctl test vm toshiba                  # Avvio VM con CPU Atom n270 e display 1024x600
```

---

## Integrità e Licenza
* **Integrità Crittografica**: I checksum SHA256 ufficiali di tutti gli asset sono verificabili nel file [SHA256SUMS.txt](https://github.com/ANDRYXify/OSify/releases/latest/download/SHA256SUMS.txt).
* **Licenza**: GNU General Public License v3.0 (GPLv3).
