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

### 4. Matrice Multi-Runtime Nativa
* **Windows (PE/DirectX)**: Proton-GE / Wine-TKG con DXVK, VKD3D-Proton, Fsync e shader cache asincrona.
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

---

## 📁 Struttura del Progetto

```
OSify/
├── build/                # Strumenti di generazione ISO (Archiso x86-64-v3 profile)
├── kernel/               # Sysctl, udev rules per controller e storage, moduli
├── network/              # QoS Traffic Shaper (CAKE, BBRv3, nftables DSCP)
├── audio/                # Profili PipeWire Pro-Audio & virtual sinks
├── emulation/            # Launcher ad alte prestazioni con mimalloc & shader cache
├── runtimes/             # Moduli Windows (Proton), Android (Waydroid), macOS (Darling/KVM)
├── streaming/            # Profili OBS Studio & Multi-RTMP broadcast engine
├── desktop/              # Configurazioni KDE Plasma 6 Wayland (HDR, VRR, Tearing)
└── tools/                # 'osify-ctl' CLI per gestione profili istantanei
```
