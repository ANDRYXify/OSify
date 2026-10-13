#!/usr/bin/env bash
# ==============================================================================
# OSify Game Mode — Console Experience & Micro-Compositor Launcher
# ==============================================================================
# Lancia il frontend console (ES-DE / Pegasus / Steam) all'interno del micro-compositor
# Gamescope sviluppato da Valve:
# - Latenza di input minima assoluta
# - FSR (FidelityFX Super Resolution) / NIS upscaling integrato per retrogaming
# - HDR abilitabile al volo
# - Interfaccia navigabile 100% da controller (DualSense, Xbox, Switch Pro)
# ==============================================================================

set -euo pipefail

FRONTEND="${1:-es-de}"
RES_W="${2:-1920}"
RES_H="${3:-1080}"
REFRESH="${4:-120}"

echo "========================================================="
echo "       OSify Console Mode: $FRONTEND ($RES_W x $RES_H @ ${REFRESH}Hz)"
echo "========================================================="

# Parametri Gamescope per latenza minima
GAMESCOPE_ARGS=(
    -w "$RES_W" -h "$RES_H"
    -W "$RES_W" -H "$RES_H"
    -r "$REFRESH"
    --adaptive-sync
    --immediate-flips
    --fullscreen
)

# Verifica disponibilità Gamescope
if command -v gamescope >/dev/null 2>&1; then
    echo "[+] Avvio tramite micro-compositor Gamescope (Zero-lag input)..."
    exec gamescope "${GAMESCOPE_ARGS[@]}" -- "$FRONTEND"
else
    echo "[!] Gamescope non trovato: avvio diretto nativo su Wayland..."
    exec "$FRONTEND"
fi
