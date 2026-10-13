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
    <img src="https://img.shields.io/badge/Installer-Windows_Senza_USB-0078D6?style=flat-square&logo=windows&logoColor=white" alt="Installer Windows"/>
  </a>
  &nbsp;
  <a href="https://github.com/ANDRYXify/OSify/releases/latest/download/OSify-x86_64-v3.iso">
    <img src="https://img.shields.io/badge/ISO-Standard_x86--64--v3-7C3AED?style=flat-square&logo=linux&logoColor=white" alt="ISO x86_64"/>
  </a>
  &nbsp;
  <a href="https://github.com/ANDRYXify/OSify/releases/latest/download/OSify-Vintage-i686.iso">
    <img src="https://img.shields.io/badge/ISO-Vintage_32--bit_i686-10B981?style=flat-square&logo=linux&logoColor=white" alt="ISO i686"/>
  </a>
  &nbsp;
  <a href="https://github.com/ANDRYXify/OSify/releases/tag/v1.0.0">
    <img src="https://img.shields.io/badge/Release-v1.0.0-334155?style=flat-square&logo=github&logoColor=white" alt="Release"/>
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

## Strumenti di Amministrazione CLI (`osify-ctl`)

Il sistema include la CLI unificata `osify-ctl` per gestire ogni sottosistema:

```bash
# Diagnostica hardware della macchina
osify-ctl hw-detect

# Cambio profilo prestazionale in tempo reale
osify-ctl mode gaming      # Priorita' real-time a bassa latenza
osify-ctl mode streaming   # Protezione bufferbloat CAKE QoS attiva
osify-ctl mode lowspec     # Profilo a bassissimo consumo per macchine vintage

# Gestione architettura modulare
osify-ctl block list
osify-ctl block enable presentation
osify-ctl block enable android

# Verifica compatibilita' Anti-Cheat (Ring-0)
osify-ctl anticheat check Valorant

# Collaudo preventivo tramite simulatore QEMU
osify-ctl test hw-check --profile toshiba  # Diagnosi vincoli Toshiba NB200
osify-ctl test vm toshiba                  # Avvio VM con CPU Atom n270 e display 1024x600
osify-ctl test suite                       # Esecuzione test suite (40/40 verifiche)
```

---

## Integrità e Licenza
* **Integrità Crittografica**: I checksum SHA256 ufficiali di tutti gli asset sono verificabili nel file [SHA256SUMS.txt](https://github.com/ANDRYXify/OSify/releases/latest/download/SHA256SUMS.txt).
* **Licenza**: GNU General Public License v3.0 (GPLv3).
