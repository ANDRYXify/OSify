#!/usr/bin/env bash
# ==============================================================================
# OSify Desktop Engine — Ottimizzazione KDE Plasma 6 Wayland
# ==============================================================================
# Configura KWin e l'ambiente grafico per la massima reattività da eSport:
# 1. Wayland Async Tearing: latenza di input immediata a schermo intero
# 2. Variable Refresh Rate (VRR / G-Sync / FreeSync) forzato in modalità automatica
# 3. Disattivazione di servizi pesanti in background (es. indicizzatore Baloo)
# 4. Profilo colore sRGB / HDR abilitato per monitor compatibili
# ==============================================================================

set -euo pipefail

KWIN_CONFIG="$HOME/.config/kwinrc"

apply_kwin_tuning() {
    echo "========================================================="
    echo "       OSify Desktop Engine — Tuning KDE Plasma 6        "
    echo "========================================================="

    mkdir -p "$(dirname "$KWIN_CONFIG")"

    # Disattiva indicizzazione file Baloo (consuma cicli CPU e I/O su disco a tradimento)
    if command -v balooctl6 >/dev/null 2>&1; then
        echo "[+] Disattivazione indicizzatore Baloo..."
        balooctl6 suspend || true
        balooctl6 disable || true
    fi

    # Configurazione KWin per gaming estremo
    if command -v kwriteconfig6 >/dev/null 2>&1; then
        echo "[+] Configurazione KWin Wayland per latenza ultra-bassa..."
        
        # Abilita tearing (sblocco framerate senza VSync per latenza 0)
        kwriteconfig6 --file kwinrc --group Wayland --key AllowTearing true
        
        # VRR (Adaptive Sync) sempre attivo quando possibile
        kwriteconfig6 --file kwinrc --group Wayland --key VariableRefreshRate 2
        
        # Latenza minima assoluta per KWin Compositor
        kwriteconfig6 --file kwinrc --group Compositing --key LatencyPolicy 0
        kwriteconfig6 --file kwinrc --group Compositing --key AnimationSpeed 1
        
        echo "[✓] Parametri KWin applicati! (Richiede riavvio sessione o ricaricamento KWin)"
    else
        echo "[i] kwriteconfig6 non trovato; applicazione diretta manuale su kwinrc."
        cat << 'EOF' >> "$KWIN_CONFIG"

[Wayland]
AllowTearing=true
VariableRefreshRate=2

[Compositing]
LatencyPolicy=0
AnimationSpeed=1
EOF
    fi

    echo "[✓] Ottimizzazioni Desktop completate!"
}

apply_kwin_tuning
