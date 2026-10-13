#!/usr/bin/env bash
# ==============================================================================
# OSify Web Engine — Browser Profile & Performance Tuning
# ==============================================================================
# Configura in modo automatico e deterministico l'ambiente di navigazione web:
# - Disattivazione telemetria e tracciamento pubblicitario
# - Ottimizzazione footprint RAM in base alla memoria fisica (< 1.5GB vs Workstation)
# - Accelerazione hardware GPU su chip compatibili
# - Creazione lanciatori desktop ufficiali
# ==============================================================================

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

echo "========================================================="
echo "       OSify Web Engine & Browser Optimizer              "
echo "========================================================="

TOTAL_RAM_KB=$(grep MemTotal /proc/meminfo 2>/dev/null | awk '{print $2}' || echo "2097152")
TOTAL_RAM_MB=$(( TOTAL_RAM_KB / 1024 ))

# 1. Configurazione Profilo Firefox / Librewolf
FIREFOX_DIR="$HOME/.mozilla/firefox"
if [[ -d "$FIREFOX_DIR" ]] || command -v firefox >/dev/null 2>&1; then
    mkdir -p "$FIREFOX_DIR/osify-profile"
    USER_JS="$FIREFOX_DIR/osify-profile/user.js"
    
    echo "[+] Generazione configurazione ottimizzata: $USER_JS"
    cat << 'EOF' > "$USER_JS"
// OSify Web Shield & Fast Browsing Profile
user_pref("toolkit.telemetry.enabled", false);
user_pref("browser.discovery.enabled", false);
user_pref("privacy.trackingprotection.enabled", true);
user_pref("privacy.donottrackheader.enabled", true);
user_pref("network.prefetch-next", false);
user_pref("network.dns.disablePrefetch", true);
user_pref("browser.pocket.enabled", false);
user_pref("browser.newtabpage.activity-stream.feeds.telemetry", false);
user_pref("browser.newtabpage.activity-stream.telemetry", false);
EOF

    if [[ "$TOTAL_RAM_MB" -le 1536 ]]; then
        # Profilo Vintage / Netbook (Toshiba NB200 - 1GB RAM)
        echo "[+] Applicazione parametri a basso consumo di memoria (Vintage Profile)..."
        cat << 'EOF' >> "$USER_JS"
// Ottimizzazioni per sistemi con <= 1.5 GB RAM
user_pref("dom.ipc.processCount", 1);
user_pref("browser.cache.memory.enable", true);
user_pref("browser.cache.memory.capacity", 32768);
user_pref("browser.tabs.unloadOnLowMemory", true);
user_pref("layers.acceleration.disabled", true);
user_pref("image.mem.decode_bytes_at_a_time", 16384);
EOF
    else
        # Profilo Moderno High-Performance
        echo "[+] Applicazione parametri accelerazione hardware (Modern Profile)..."
        cat << 'EOF' >> "$USER_JS"
// Accelerazione GPU & Multi-process su sistemi moderni
user_pref("dom.ipc.processCount", 8);
user_pref("media.ffmpeg.vaapi.enabled", true);
user_pref("widget.dmabuf.wayland.enabled", true);
user_pref("gfx.webrender.all", true);
EOF
    fi
fi

# 2. Configurazione Falkon (Browser leggero Qt/QupZilla per Netbook)
FALKON_CONFIG_DIR="$HOME/.config/falkon/profiles/default"
mkdir -p "$FALKON_CONFIG_DIR"
if [[ -f "$FALKON_CONFIG_DIR/settings.ini" ]]; then
    # Assicura adblock attivo di default
    sed -i 's/AdBlockDisabled=true/AdBlockDisabled=false/' "$FALKON_CONFIG_DIR/settings.ini" 2>/dev/null || true
fi

echo "[✓] Configurazione profili web completata con successo."
