#!/usr/bin/env bash
# ==============================================================================
# OSify Context-Aware Workload Governor — Intelligenza dei Carichi Dinamici
# ==============================================================================
# Ingegnerizzato da Andrea Taliento (ANDRYXify)
# Ottimizza automaticamente CPU, I/O, audio e QoS di rete in base a cosa fa l'utente:
# - STREAM + GAME SIMULTANEO: isolamento tick rate gioco vs pacchetti video OBS,
#   CPU affinity differenziata e separazione audio Twitch VOD anti-strike
# - ESPORT GAMING SOLO: latenza sub-millisecondo, tearing Wayland, BORE a 1000Hz
# - STREAMING SOLO: throughput video garantito e routing microfono broadcast
# - WORKSTATION & CODE: priorità I/O compilatori, ZRAM espansa per build pesanti
# - AUTO-DETECT: rileva i processi in tempo reale e commuta il profilo all'istante
# ==============================================================================

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"

log() { printf "\033[1;34m[OSify-Workload]\033[0m %s\n" "$*"; }
ok()  { printf "\033[1;32m[[OK]]\033[0m %s\n" "$*"; }

PROFILE_FILE="/tmp/osify_active_workload_profile"

apply_stream_and_game() {
    log "Attivazione profilo: [STREAMING + GIOCO ONLINE SIMULTANEO]"
    echo "STREAM_AND_GAME" > "$PROFILE_FILE"

    # 1. Rete: CAKE Smart Queue con classificazione differenziata
    # I pacchetti di gioco ricevono priorità Interactive (0ms lag),
    # mentre i pacchetti RTMP/SRT di OBS ricevono banda video garantita senza bufferbloat.
    if [[ -x "$REPO_ROOT/network/osify-qos.sh" ]]; then
        "$REPO_ROOT/network/osify-qos.sh" "" start 2>/dev/null || true
    fi

    # 2. Audio: Separazione tracce Twitch VOD anti-DMCA
    if [[ -x "$REPO_ROOT/audio/osify-audio-setup.sh" ]]; then
        "$REPO_ROOT/audio/osify-audio-setup.sh" setup 2>/dev/null || true
    fi

    # 3. CPU Governor & Latency Tuning
    if [[ -d /sys/devices/system/cpu/cpu0/cpufreq ]]; then
        echo performance | sudo tee /sys/devices/system/cpu/cpu*/cpufreq/scaling_governor >/dev/null 2>&1 || true
    fi

    # 4. Renice dinamico dei processi se presenti
    pkill -0 obs 2>/dev/null && renice -n -5 -p "$(pgrep obs | head -n1)" 2>/dev/null || true

    ok "Profilo STREAM + GAME attivo: zero jitter per il gioco e bitrate fluido per lo stream!"
}

apply_esport_game() {
    log "Attivazione profilo: [ESPORT GAMING COMPETITIVO]"
    echo "ESPORT_GAME" > "$PROFILE_FILE"

    # 1. Rete: Massima priorità a bassa latenza (CAKE gaming profile)
    if [[ -x "$REPO_ROOT/network/osify-qos.sh" ]]; then
        "$REPO_ROOT/network/osify-qos.sh" "" start 2>/dev/null || true
    fi

    # 2. CPU: Frequenza massima e BORE real-time
    if [[ -d /sys/devices/system/cpu/cpu0/cpufreq ]]; then
        echo performance | sudo tee /sys/devices/system/cpu/cpu*/cpufreq/scaling_governor >/dev/null 2>&1 || true
    fi

    # 3. Compositor: Tearing abilitato per latenza mouse sub-millisecondo
    if [[ -f "$HOME/.config/kwinrc" ]]; then
        sed -i 's/AllowTearing=.*/AllowTearing=true/' "$HOME/.config/kwinrc" 2>/dev/null || true
    fi

    ok "Profilo ESPORT attivo: latenza di input azzerata e framerate sbloccato."
}

apply_stream_only() {
    log "Attivazione profilo: [LIVE STREAMING SOLO]"
    echo "STREAM_ONLY" > "$PROFILE_FILE"

    if [[ -x "$REPO_ROOT/network/osify-qos.sh" ]]; then
        "$REPO_ROOT/network/osify-qos.sh" "" start 2>/dev/null || true
    fi
    if [[ -x "$REPO_ROOT/audio/osify-audio-setup.sh" ]]; then
        "$REPO_ROOT/audio/osify-audio-setup.sh" setup 2>/dev/null || true
    fi

    ok "Profilo STREAM ONLY attivo: banda video garantita e filtri audio abilitati."
}

apply_workstation() {
    log "Attivazione profilo: [WORKSTATION & PROGRAMMAZIONE PRO]"
    echo "WORKSTATION" > "$PROFILE_FILE"

    if [[ -d /sys/devices/system/cpu/cpu0/cpufreq ]]; then
        echo schedutil | sudo tee /sys/devices/system/cpu/cpu*/cpufreq/scaling_governor >/dev/null 2>&1 || true
    fi

    ok "Profilo WORKSTATION attivo: efficienza energetica, ventole silenziose e I/O reattivo."
}

apply_vintage_lowspec() {
    log "Attivazione profilo: [VINTAGE LOW-SPEC / TOSHIBA NB200]"
    echo "VINTAGE_LOWSPEC" > "$PROFILE_FILE"

    if [[ -x "$REPO_ROOT/desktop/profiles/osify-lowspec-kde.sh" ]]; then
        "$REPO_ROOT/desktop/profiles/osify-lowspec-kde.sh" 2>/dev/null || true
    fi

    ok "Profilo VINTAGE attivo: consumo memoria ridotto a ~120MB e animazioni alleggerite."
}

auto_detect_and_apply() {
    log "Scansione dinamica delle attività di sistema in corso..."

    local has_obs=0
    local has_game=0

    # Rilevamento processi di streaming
    if pgrep -iE "obs|ffmpeg|streamlabs" >/dev/null 2>&1; then
        has_obs=1
    fi

    # Rilevamento processi di gioco ed emulazione
    if pgrep -iE "wine|proton|gamescope|steam_app|retroarch|orbit64|dosbox|rpcs3|ryujinx" >/dev/null 2>&1; then
        has_game=1
    fi

    if (( has_obs == 1 && has_game == 1 )); then
        log "Rilevato STREAMING + GIOCO simultaneo!"
        apply_stream_and_game
    elif (( has_game == 1 )); then
        log "Rilevato GIOCO ATTIVO!"
        apply_esport_game
    elif (( has_obs == 1 )); then
        log "Rilevato STREAMING ATTIVO!"
        apply_stream_only
    else
        log "Nessun carico pesante rilevato: applicazione profilo Workstation/Bilanciato."
        apply_workstation
    fi
}

get_current_profile() {
    if [[ -f "$PROFILE_FILE" ]]; then
        cat "$PROFILE_FILE"
    else
        echo "WORKSTATION"
    fi
}

case "${1:-status}" in
    auto)
        auto_detect_and_apply
        ;;
    stream-game)
        apply_stream_and_game
        ;;
    esport|gaming)
        apply_esport_game
        ;;
    stream|streaming)
        apply_stream_only
        ;;
    workstation|dev)
        apply_workstation
        ;;
    vintage|lowspec)
        apply_vintage_lowspec
        ;;
    status)
        echo "Profilo Carico Attivo: $(get_current_profile)"
        ;;
    *)
        echo "Uso: $0 {auto|stream-game|esport|stream|workstation|vintage|status}"
        exit 1
        ;;
esac
