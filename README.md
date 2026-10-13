# OSify — Sistema Operativo per Gaming Estremo, Live Streaming e Multi-Runtime

**OSify** è un sistema operativo basato su architettura Linux a microarchitettura compilata (**`x86-64-v3`** e **`x86-64-v4`**), ingegnerizzato specificamente per massimizzare le prestazioni nel **gaming ad alto refresh-rate**, nel **live streaming multi-piattaforma** (Twitch, Kick, YouTube) senza lag di rete, nell'**emulazione console moderna** (PS3, Switch, PS2, Xbox 360, Wii U) e nell'esecuzione unificata di ambienti **Windows, Android e macOS**.

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

---

## 📁 Struttura del Progetto

```
OSify/
├── build/                # Strumenti di generazione ISO (Archiso x86-64-v3 profile)
│   └── docker/           # Builder Docker per compilare la ISO da macOS o Linux
├── kernel/               # Sysctl, udev rules per controller e storage, moduli
├── network/              # QoS Traffic Shaper (CAKE, BBRv3, nftables DSCP)
├── audio/                # Profili PipeWire Pro-Audio & virtual sinks
├── emulation/            # Launcher ad alte prestazioni con mimalloc & shader cache
├── runtimes/             # Moduli Windows (Proton), Android (Waydroid), macOS (Darling/KVM)
├── streaming/            # Profili OBS Studio & Multi-RTMP relay zero-overhead
│   └── relay/            # Relay simultaneo Twitch + Kick + YouTube
├── services/             # Demone di rilevamento e ottimizzazione automatica
├── system/storage/       # Layout Btrfs, subvolumi, No-CoW e configurazioni Snapper
├── desktop/              # Configurazioni KDE Plasma 6 Wayland (HDR, VRR, Tearing)
└── tools/                # CLI ('osify-ctl') e Control Center GUI per KDE Plasma 6
    └── osify-gui/        # Dashboard grafica moderna in PyQt6 per KDE Plasma
```

---

## 🚀 Utilizzo Rapido

### 1. Control Center Grafico (KDE Plasma 6)
```bash
python3 tools/osify-gui/osify-control-center.py
```

### 2. Gestione Profili da Terminale (CLI)
```bash
# Verifica diagnostica di sistema
osify-ctl status

# Attivazione profilo live streaming con protezione ping
osify-ctl mode streaming

# Attivazione profilo gaming eSport
osify-ctl mode gaming

# Avvio frontend console TV con Gamescope
osify-ctl mode emulation
```

### 3. Compilazione Immagine ISO (da Mac o Linux via Docker)
```bash
cd build/docker && ./run-build.sh
```

