#!/usr/bin/env bash
# ==============================================================================
# OSify Standalone Session Initializer — Avvio Diretto Sistema Operativo
# ==============================================================================
# Ingegnerizzato da Andrea Taliento (ANDRYXify)
# Viene eseguito al boot da PID 1 / systemd / inittab per lanciare la sessione
# grafica autonoma a pieno schermo senza finestre di terminale intermedie:
# 1. Inizializzazione Hardware Abstraction Layer (ZRAM, BORE, Mesa DRI2/DRI3)
# 2. Registrazione kernel dei formati UEM (Windows, Android, DOS, WASM, Mach-O)
# 3. Avvio server grafico Gamescope / X11 con risoluzione nativa
# 4. Esecuzione a schermo intero della Deck Shell & KDE Plasma Dual Environment
# ==============================================================================

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"

log() { echo -e "\e[1;34m[OSify-Session]\e[0m $*"; }

log "Inizializzazione sottosistemi di sistema OSify..."

# 1. Hardware Abstraction Layer (HAL)
if [[ -x "$REPO_ROOT/uem/hal/osify-hal.sh" ]]; then
    log "Applicazione profilo hardware e ottimizzazioni ZRAM/BORE..."
    "$REPO_ROOT/uem/hal/osify-hal.sh" apply 2>/dev/null || true
fi

# 2. Registrazione UEM Kernel Binfmt
if [[ -x "$REPO_ROOT/uem/binfmt/osify-binfmt-register.sh" ]]; then
    log "Attivazione Universal Execution Matrix nel kernel..."
    "$REPO_ROOT/uem/binfmt/osify-binfmt-register.sh" 2>/dev/null || true
fi

# 3. Rete CAKE QoS e protezione DNS
if [[ -x "$REPO_ROOT/network/osify-wifi-manager.sh" ]]; then
    "$REPO_ROOT/network/osify-wifi-manager.sh" status >/dev/null 2>&1 || true
fi

# 4. Audio Mixer
if [[ -x "$REPO_ROOT/audio/osify-sound-manager.sh" ]]; then
    "$REPO_ROOT/audio/osify-sound-manager.sh" set 75 >/dev/null 2>&1 || true
fi

# 5. Avvio Shell Grafica (OSify Deck Shell)
log "Lancio OSify Deck Shell (SteamOS & KDE Plasma Dual Experience)..."
export DISPLAY="${DISPLAY:-:0}"
export XDG_CURRENT_DESKTOP="SteamOS:KDE"
export XDG_SESSION_TYPE="x11"

SHELL_BIN="$REPO_ROOT/tools/osify-gui/osify-deck-shell.py"

if [[ -f "$SHELL_BIN" ]]; then
    exec python3 "$SHELL_BIN"
else
    log "Esecuzione fallback su terminale grafico..."
    exec bash
fi
