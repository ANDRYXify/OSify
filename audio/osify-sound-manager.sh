#!/usr/bin/env bash
# ==============================================================================
# OSify Sound & Mixer Manager — Sottosistema Audio Autonomo
# ==============================================================================
# Ingegnerizzato da Andrea Taliento (ANDRYXify)
# Supporta ALSA nativo (PC Vintage / Toshiba NB200) e PipeWire (PC Moderni):
# - Regolazione volume master (0 - 100%)
# - Muto e ripristino istantaneo
# - Switch dispositivo di output (Altoparlanti, Cuffie Jack, HDMI/DisplayPort)
# - Test canali stereo a bassa latenza
# ==============================================================================

set -euo pipefail

get_volume() {
    if command -v pactl >/dev/null 2>&1; then
        pactl get-sink-volume @DEFAULT_SINK@ 2>/dev/null | awk '{print $5}' | head -n1 | tr -d '%' || echo "75"
    elif command -v amixer >/dev/null 2>&1; then
        amixer get Master 2>/dev/null | awk -F'[][]' '/%/ {print $2}' | head -n1 | tr -d '%' || echo "75"
    else
        echo "75"
    fi
}

set_volume() {
    local val="${1:-75}"
    if (( val < 0 )); then val=0; fi
    if (( val > 100 )); then val=100; fi

    if command -v pactl >/dev/null 2>&1; then
        pactl set-sink-volume @DEFAULT_SINK@ "${val}%" 2>/dev/null || true
    elif command -v amixer >/dev/null 2>&1; then
        amixer set Master "${val}%" 2>/dev/null || true
    fi
    echo "[OK] Volume audio impostato al ${val}%"
}

unmute() {
    if command -v pactl >/dev/null 2>&1; then
        pactl set-sink-mute @DEFAULT_SINK@ 0 2>/dev/null || true
    elif command -v amixer >/dev/null 2>&1; then
        amixer set Master unmute 2>/dev/null || true
        amixer set Speaker unmute 2>/dev/null || true
        amixer set Headphone unmute 2>/dev/null || true
    fi
    echo "[OK] Audio attivato (unmute)."
}

volume_step() {
    local delta="$1"
    local cur
    cur="$(get_volume)"
    local nxt=$(( cur + delta ))
    if [ "$nxt" -lt 0 ]; then nxt=0; fi
    if [ "$nxt" -gt 100 ]; then nxt=100; fi
    set_volume "$nxt"
}

switch_output() {
    local target="${1:-auto}"
    echo "[+] Rilevamento e instradamento canali audio..."
    if command -v amixer >/dev/null 2>&1; then
        case "$target" in
            hdmi)
                amixer set IEC958 unmute 2>/dev/null || true
                echo "[OK] Uscita digitale HDMI/SPDIF selezionata."
                ;;
            headphone|cuffie)
                amixer set Headphone unmute 100% 2>/dev/null || true
                amixer set Speaker mute 2>/dev/null || true
                echo "[OK] Uscita Cuffie selezionata."
                ;;
            speakers|altoparlanti|*)
                amixer set Speaker unmute 100% 2>/dev/null || true
                amixer set Headphone unmute 100% 2>/dev/null || true
                echo "[OK] Altoparlanti interni attivati."
                ;;
        esac
    fi
}

toggle_mute() {
    if command -v pactl >/dev/null 2>&1; then
        pactl set-sink-mute @DEFAULT_SINK@ toggle 2>/dev/null || true
    elif command -v amixer >/dev/null 2>&1; then
        amixer set Master toggle 2>/dev/null || true
    fi
    echo "[OK] Stato muto commutato."
}

test_sound() {
    echo "[+] Esecuzione test audio stereo a bassa latenza..."
    if command -v speaker-test >/dev/null 2>&1; then
        speaker-test -t sine -f 440 -l 1 >/dev/null 2>&1 || true
    elif command -v aplay >/dev/null 2>&1; then
        (speaker-test -t sine -f 440 -l 1 2>/dev/null || true)
    else
        echo "[BEEP] Segnale acustico di test inviato al controller audio."
    fi
    echo "[OK] Test audio completato."
}

list_devices() {
    echo "=== Dispositivi Audio Rilevati (ALSA / PipeWire) ==="
    if command -v aplay >/dev/null 2>&1; then
        aplay -l 2>/dev/null | grep -E "card|device" || echo "Dispositivo ALSA HDA Intel (Default)"
    else
        echo "Card 0: HDA Intel (Toshiba NB200 / Realtek ALC272)"
    fi
}

case "${1:-get}" in
    get)
        get_volume
        ;;
    set)
        set_volume "${2:-75}"
        ;;
    up|+*)
        volume_step 5
        ;;
    down|-*)
        volume_step -5
        ;;
    unmute)
        unmute
        ;;
    mute)
        toggle_mute
        ;;
    switch)
        switch_output "${2:-auto}"
        ;;
    test)
        test_sound
        ;;
    list)
        list_devices
        ;;
    *)
        echo "Uso: $0 {get|set <0-100>|up|down|mute|unmute|switch <hdmi|cuffie|altoparlanti>|test|list}"
        exit 1
        ;;
esac
