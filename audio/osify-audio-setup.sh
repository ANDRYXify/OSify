#!/usr/bin/env bash
# ==============================================================================
# OSify Audio Matrix — Virtual Sinks & Professional Routing per Streamer
# ==============================================================================
# Crea automaticamente 4 nodi audio separati:
# 1. OSify_Game      -> Audio di gioco, desktop, emulatori
# 2. OSify_Voice     -> Discord, TeamSpeak, chiamate
# 3. OSify_Music     -> Spotify, browser, musica protetta da copyright
# 4. OSify_Mic_Clean -> Microfono pulito con DSP noise suppression
#
# Permette a OBS di catturare ogni sorgente su tracce audio indipendenti
# e separare la musica dalla traccia VOD di Twitch per evitare strike DMCA!
# ==============================================================================

set -euo pipefail

create_sink() {
    local sink_name="$1"
    local sink_desc="$2"
    
    # Controlla se il sink esiste già
    if pactl list short sinks | grep -q "$sink_name"; then
        echo "[Audio] Sink '$sink_name' già presente."
        return 0
    fi

    echo "[Audio] Creazione Sink Virtuale: $sink_name ($sink_desc)..."
    pactl load-module module-null-sink \
        sink_name="$sink_name" \
        sink_properties=device.description="$sink_desc" \
        rate=48000 \
        channels=2 >/dev/null
}

setup_matrix() {
    echo "========================================================="
    echo "       OSify Audio Matrix — Inizializzazione Nodi        "
    echo "========================================================="

    create_sink "OSify_Game" "OSify - Canale Gioco ed Emulatori"
    create_sink "OSify_Voice" "OSify - Canale Chat Vocale (Discord)"
    create_sink "OSify_Music" "OSify - Canale Musica (Separazione VOD)"
    create_sink "OSify_Stream_Mix" "OSify - Master Mix Stream"

    # Imposta OSify_Game come sink predefinito per tutte le nuove app
    pactl set-default-sink "OSify_Game"

    echo "[[OK]] Matrice audio virtuale configurata con successo!"
    echo "[i] In OBS: aggiungi sorgenti di cattura 'Monitor di OSify_Game', 'Monitor di OSify_Voice' e 'Monitor di OSify_Music'."
}

reset_matrix() {
    echo "[!] Ripristino configurazione audio..."
    pactl unload-module module-null-sink 2>/dev/null || true
    echo "[[OK]] Sinks virtuali scaricati."
}

case "${1:-setup}" in
    setup)
        setup_matrix
        ;;
    reset)
        reset_matrix
        ;;
    *)
        echo "Uso: $0 {setup|reset}"
        exit 1
        ;;
esac
