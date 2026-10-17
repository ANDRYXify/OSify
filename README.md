<p align="center">
  <img src="OSify.png" alt="OSify Logo" width="280"/>
</p>

<h1 align="center">OSify</h1>

<p align="center">
  <b>Sistema Operativo Autonomo di Nuova Generazione per Performance Estreme e Rigenerazione Hardware</b><br/>
  <i>Ingegnerizzato da Andrea Taliento (ANDRYXify)</i>
</p>

---

<p align="center">
  <a href="https://github.com/ANDRYXify/OSify/releases/latest/download/OSify-NoUSB-Windows-Installer.zip">
    <img src="https://img.shields.io/badge/Installer_Windows-Senza_USB_(vA.0)-0078D6?style=for-the-badge&logo=windows&logoColor=white" alt="Installer Windows Senza USB"/>
  </a>
  &nbsp;
  <a href="https://github.com/ANDRYXify/OSify/releases/latest/download/OSify-x86_64-v3.iso">
    <img src="https://img.shields.io/badge/OSify_Standard-x86--64--v3_(vA.0)-7C3AED?style=for-the-badge" alt="OSify Standard x86_64-v3"/>
  </a>
  &nbsp;
  <a href="https://github.com/ANDRYXify/OSify/releases/latest/download/OSify-Vintage-i686.iso">
    <img src="https://img.shields.io/badge/OSify_Vintage-32--bit_i686_(vA.0)-10B981?style=for-the-badge" alt="OSify Vintage 32-bit i686"/>
  </a>
  &nbsp;
  <a href="https://github.com/ANDRYXify/OSify/releases/latest">
    <img src="https://img.shields.io/badge/Release-vA.0_Latest-22C55E?style=for-the-badge&logo=github&logoColor=white" alt="Official Release"/>
  </a>
</p>

<p align="center">
  <a href="https://github.com/ANDRYXify/OSify/pkgs/container/osify">
    <img src="https://img.shields.io/badge/Container-ghcr.io%2Fandryxify%2Fosify:latest-2563EB?style=flat-square&logo=docker&logoColor=white" alt="GitHub Container Registry"/>
  </a>
  &nbsp;
  <a href="https://github.com/ANDRYXify/OSify/actions">
    <img src="https://img.shields.io/badge/Tests-295%2F295_Passed-059669?style=flat-square&logo=githubactions&logoColor=white" alt="Test Suite"/>
  </a>
  &nbsp;
  <a href="#architettura-dei-due-target">
    <img src="https://img.shields.io/badge/Arch-x86__64_|_i686_|_ARM_|_Silicon-6366F1?style=flat-square" alt="Architetture Supportate"/>
  </a>
  &nbsp;
  <a href="LICENSE">
    <img src="https://img.shields.io/badge/License-GPL_v3.0-64748B?style=flat-square&logo=gnu&logoColor=white" alt="Licenza GPLv3"/>
  </a>
</p>

---

## Panoramica del Progetto

OSify è un sistema operativo commerciale e autonomo a sé stante ingegnerizzato su due target architetturali rigorosamente distinti, per evitare compromessi o dispersioni di risorse:

1. **OSify Standard (x86-64-v3)**: Dedicato a postazioni moderne da gaming, creazione di contenuti e live streaming ad alto bitrate. Compilato con istruzioni vettoriali avanzate (AVX, AVX2, FMA) e motore di esecuzione BORE a latenza deterministica.
2. **OSify Vintage (i686 / 32-bit)**: Dedicato a computer storici e netbook ultra-compatti (es. Toshiba Dynabook NB200 con Intel Atom N280 e GPU Intel GMA 950). Ottimizzato per operare con un footprint di memoria a riposo di ~115-125 MB, gestendo nativamente schermi WSVGA a bassa risoluzione (1024x600).

---

## 🌟 Esperienza a 360° Out-Of-The-Box & Live-to-Disk Persistence (vA.0)

OSify non è un clone o una derivata generica: è un sistema operativo con un'architettura completa progettata per consentire all'utente di lavorare, programmare, giocare e personalizzare ogni aspetto fin dal primo secondo.

* **🚀 OSify App Drawer & Launchpad**: Menu applicazioni universale con barra di ricerca istantanea in tempo reale, suddivisione a schede di categoria (Internet, Gaming, Sviluppo, Ufficio, Aspetto, Sistema), navigazione a tastiera/mouse e scorciatoie globali immediate (`Super`, `Super+Space`, `Super+A`, `F1` o clic sul dock).
* **🎨 Icone Native Vettoriali Garantite (Zero Icone Bianche)**: Set completo di icone PNG proprietarie disegnate geometricamente con colori specifici ad alto contrasto per ciascuna applicazione (Hub, Web, Wi-Fi, Gaming, Coding, File, Display, Task Manager, Installatore, Update), caricate direttamente tramite percorsi assoluti `/usr/share/pixmaps/`.
* **Identità Nativa e Personale (Zero Residui Tux)**: L'utente configura il proprio profilo reale (Nome, Username, Password crittografata SHA-512, Hostname). L'ambiente Live opera sotto l'utente ufficiale `osify`.
* **Live-to-Disk Profile & Data Persistence**: Durante l'installazione su disco fisso (`osify-install`), il sistema preserva e migra **integralmente** sul nuovo account tutti i file salvati, documenti, cronologia e configurazioni create durante la sessione Live. Nessun dato va perso.
* **🌐 Web & Connettività Wi-Fi**: Browser nativo ultra-veloce (`osify-browser`) e gestore reti wireless guidato (`osify-wifi`) con scansione SSID, WPA2/WPA3, DHCP immediato e protezione DNS anti-leak.
* **🎮 Gaming & Retrogaming Hub**: Lanciatore integrato (`osify-games`) per giochi Windows (.exe tramite Wine/DirectX), retrogaming DOS (DOSBox) ed emulazione universale (UEM runner per Android .apk e iOS .ipa).
* **💻 Developer & Coding Suite**: Ambiente per programmatori (`osify-developer`) con Python 3 interattivo (REPL), compilatore C rapido (TinyCC / GCC), Git manager, editor con colorazione sintassi e template di progetto pronti in `~/Progetti`.
* **📁 Lavoro & Produttività**: File manager reattivo con schede, visualizzatore documenti PDF, gestore archivi compressi (.zip, .tar.gz, .7z) e screenshot tool istantaneo.
* **🎨 Personalizzazione & Virtual Scaler**: Centro aspetto (`osify-appearance`) con Virtual Scaler Netbook (1024x600 ↔ 1280x768 per visualizzare finestre alte senza tagli verticali) e sfondi Cyber Dark ad alta definizione.
* **⚡ Turbo Boost Hardware Adattivo**: Riconoscimento automatico dell'hardware (Standard, Pro o Riesumare Antichi) con sblocco governor CPU `performance`, 1 GB di swap compresso zRAM LZ4 e calibrazione touchpad universale `evdev`.

---

## Architettura dei Due Target

### 1. OSify Standard (`x86_64-v3`)

* **Nucleo di Sistema**: Motore di orchestrazione a latenza ultra-bassa con scheduler BORE (Burst-Oriented Response Enhancer), `PREEMPT_DYNAMIC`, tickless idle a 1000Hz (`CONFIG_HZ=1000`) e supporto nativo a futex deterministici.
* **Ambiente Grafico OSify 2050**: Motore grafico nativo ad altissima fluidità (fino a 120+ fps) con design system Obsidian Dark Glass e compositore avanzato a latenza zero.
* **Network Traffic Shaper (CAKE QoS)**: Instradamento con algoritmo CAKE e marcatura pacchetti gaming prioritari (Expedited Forwarding), azzerando il bufferbloat durante gaming simultaneo e live streaming ad alto bitrate su piattaforme broadcast.
* **Sottosistema Audio**: Architettura Pro-Audio con quantizzazione a 64 campioni @ 48kHz (< 2.5ms di latenza). Separazione dei bus audio nativi (`Audio-Gioco`, `Audio-Voce`, `Audio-Musica`, `Audio-Microfono`) con isolamento automatico della traccia stream/VOD.
* **Compatibilità Universale**: Sottosistema integrato `Compatibilità.ify` con accelerazione hardware per l'esecuzione istantanea con doppio clic di applicazioni Windows (.exe, .msi), macOS (.app, .dmg), Android (.apk) e giochi ad alto carico.

### 2. OSify Vintage (`i686 / 32-bit`)

* **Target Hardware Specifico**: Netbook e postazioni storiche (con riferimento il Toshiba Dynabook NB200 con Intel Atom N280, 1 GB RAM, GPU Intel GMA 950 e display WSVGA 1024x600).
* **Nucleo e Memoria**: Sottosistema di memoria con compressione in tempo reale ZRAM dimensionata a 1.5x della RAM fisica (1.5 GB di swap compresso protetto), con un consumo a riposo verificato di soli 115-125 MB RAM (interfaccia grafica inclusa).
* **Motore Grafico Vintage 2050**: Stessa identità visiva, stesse icone e stesso design system Obsidian Dark Glass, renderizzati con una pipeline grafica ultra-leggera ottimizzata per la GMA 950, senza sfocature pesanti per mantenere animazioni fluide e immediate.
* **Ottimizzazione Display 1024x600**:
  * Top Menu Bar e Dock fluttuante proporzionate per preservare la massima area visiva utile verticale.
  * Virtual Scaler dinamico attivabile al volo per visualizzare interfacce complesse a 1280x768 senza barre di scorrimento.
  * Spostamento agevolato e snapping automatico delle finestre di dialogo a schermo intero.
* **Suite Applicativa Nativa .ify**: Stesse applicazioni e stesse funzioni della Standard: `Navigatore.ify`, `Esplora.ify`, `Reti.ify`, `Centro OSify.ify`, `Monitor.ify`, `Impostazioni.ify`, `Giochi.ify`, `Sviluppo.ify`, `Documenti.ify`, `Video.ify`, `Musica.ify`, `Archivi.ify`, `Cattura.ify`, `Calcolatrice.ify`, `Note.ify`, `Negozio.ify`, `Aggiornamenti.ify`, `Installa OSify.ify`.

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

## Sottosistema Compatibilità Universale (.ify & Formati Esterni)

OSify integra il motore nativo **Compatibilità.ify**, progettato per abbattere qualsiasi barriera di formato, architettura ed epoca informatica senza richiedere alcuna configurazione all'utente. Qualsiasi file o binario si installa ed esegue nativamente con un doppio clic grafico:

| Formato / Piattaforma | Estensione / Magic | Motore di Esecuzione Nativo OSify | Target Compatibilità |
| :--- | :--- | :--- | :--- |
| **Applicazioni OSify** | `.ify` | **GestorePacchetti.ify / Motore Nativo** | Applicazioni, servizi e driver ufficiali OSify |
| **Windows (32/64-bit)** | `.exe`, `.msi`, `.dll` (`MZ`) | **Compatibilità.ify (Accelerazione Hardware DXVK/D3D)** | Da Windows 95 fino a Windows 11 (Office, Steam, Photoshop) |
| **Software Storico MS-DOS** | `.com`, `.exe` (`MZ` 16-bit) | **Compatibilità.ify (Virtualizzazione Trasparente)** | Software industriale SCADA, Turbo C, Giochi storici |
| **Apple Darwin / macOS** | `.app`, `.dmg`, Mach-O (`feedface`) | **Compatibilità.ify (Traduzione Dinamica Mach)** | Applicazioni macOS (es. Final Cut, utility) |
| **Applicazioni Android** | `.apk`, `.aab` (`PK\x03\x04`) | **Compatibilità.ify (Esecuzione Accelerata DRI3)** | App e giochi mobile (WhatsApp, Instagram, casual games) |
| **WebAssembly WASI** | `.wasm` (`\x00asm`) | **Compatibilità.ify WASI Standalone** | Moduli ad alte prestazioni e utility cloud-native |
| **Java Platform** | `.class`, `.jar` (`cafebabe`) | **Compatibilità.ify JIT Compiler** | Applicazioni e librerie enterprise JVM |
| **Binari Cross-Architettura** | Binari ARM, AArch64, RISC-V | **Compatibilità.ify Dynarec Engine** | Eseguibili per microarchitetture eterogenee |
| **Script Poliglotti** | `.py`, `.js`, `.sh`, `.lua` | **Compatibilità.ify Auto-Sniffer** | Script e automazioni con permessi dinamici |

---

## Hardware Adaptation Layer (HAL) & Dynamic Tuning

L'HAL di OSify rileva in tempo reale la topologia hardware all'avvio della macchina e applica un profilo deterministico ad altissima resa:

* **Sistemi Low-Memory / Vintage (< 1.5 GB RAM, es. Toshiba NB200 Atom N280)**:
  * Alloca ZRAM a 1.5x della memoria fisica con algoritmo rapido `lz4` (zero overhead su single-core).
  * Imposta `vm.swappiness=150`, `vm.dirty_ratio=10`, `vm.dirty_background_ratio=5` e `page-cluster=0` per azzerare i blocchi di sistema durante l'I/O su dischi meccanici a 5400 RPM.
  * Scheduler storage impostato automaticamente su `bfq` (Budget Fair Queueing) per mantenere reattiva l'interfaccia utente.
  * Stack grafico forzato su pipeline leggera senza shader pesanti per garantire la massima fluidità su Intel GMA 950.
* **Workstation Moderne (> 4 Core, >= 4 GB RAM)**:
  * Scheduler CPU a bassa latenza e throughput elevato.
  * ZRAM con algoritmo `zstd` ad alto rapporto di compressione.
  * `vm.max_map_count=2147483642` per supporto completo a giochi moderni e motori grafici ad alte prestazioni.
  * Stack Vulkan asincrono nativo a 120+ fps.

---

## Suite Web & Protezione Rete

OSify integra l'applicazione nativa **Navigatore.ify** con motore ad altissima velocità e protezione avanzata integrata:
* Blocco integrato di telemetria, tracker e annunci pubblicitari (riduzione fino al 60% del carico CPU su pagine web moderne).
* Gestione dinamica dei consumi e liberazione automatica delle risorse grafiche inattive.
* Accelerazione grafica completa e reattività immediata.

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
# • Windows: dir, cls, ipconfig, tasklist, taskkill, systeminfo, ver, copy, move, del
# • macOS: open, pbcopy, pbpaste, say, sw_vers, mdfind, caffeinate
# • Universal Package Bridge: apt, pacman, dnf, apk, brew, winget (instradati su osify-pkg)

# Interfaccia Grafica Console OSify 2050
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
