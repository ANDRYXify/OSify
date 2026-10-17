#!/usr/bin/env bash
# ==============================================================================
# OSify Instant Share — Condivisione File Rete Locale & Smartphone (AirDrop-like)
# ==============================================================================
# Ingegnerizzato da Andrea Taliento (ANDRYXify)
# Avvia un micro-server HTTP/WebDAV leggero per scambiare file istantaneamente
# tra OSify, smartphone (Android/iOS) e altri computer sulla stessa rete Wi-Fi.
# ==============================================================================

set -euo pipefail

PORT=8080
TARGET_PATH="${1:-${HOME}/Download}"
PID_FILE="/tmp/osify-share.pid"

get_local_ip() {
    ip route get 1.1.1.1 2>/dev/null | awk '{print $7}' | head -n1 || \
    hostname -I 2>/dev/null | awk '{print $1}' || echo "127.0.0.1"
}

start_share() {
    local target="$1"
    if [ ! -e "$target" ]; then
        echo "[!] Percorso non valido: $target"
        return 1
    fi

    local ip
    ip="$(get_local_ip)"
    local url="http://${ip}:${PORT}"

    # Se già attivo, ferma il precedente
    stop_share >/dev/null 2>&1 || true

    echo "[+] Avvio Condivisione OSify per: $target"
    echo "[+] Accessibile da qualsiasi dispositivo sulla stessa rete all'indirizzo:"
    echo "    $url"

    if [ -d "$target" ]; then
        (cd "$target" && python3 -m http.server "$PORT" >/dev/null 2>&1) &
    else
        local parent_d
        parent_d="$(dirname "$target")"
        local b_file
        b_file="$(basename "$target")"
        url="http://${ip}:${PORT}/${b_file}"
        (cd "$parent_d" && python3 -m http.server "$PORT" >/dev/null 2>&1) &
    fi

    echo $! > "$PID_FILE"

    if command -v yad >/dev/null 2>&1 && [ -n "${DISPLAY:-}" ]; then
        yad --info --title="Condivisione File OSify" \
            --text="<b>Condivisione Rete Locale Attiva!</b>\n\nApri questo indirizzo dal tuo smartphone o da un altro PC:\n\n<big><b>${url}</b></big>\n\n<i>Condivisione di: $(basename "$target")</i>" \
            --window-icon="/usr/share/pixmaps/osify-wifi.png" \
            --width=460 --center \
            --button="Ferma Condivisione:0" 2>/dev/null || true
        stop_share
    else
        echo "[i] Premi Invio per terminare la condivisione..."
        read -r _
        stop_share
    fi
}

stop_share() {
    if [ -f "$PID_FILE" ]; then
        local pid
        pid="$(cat "$PID_FILE" 2>/dev/null || echo "")"
        if [ -n "$pid" ]; then
            kill "$pid" 2>/dev/null || true
        fi
        rm -f "$PID_FILE"
        echo "[[OK]] Condivisione terminata."
    fi
    pkill -f "http.server $PORT" 2>/dev/null || true
}

launch_gui() {
    if command -v yad >/dev/null 2>&1 && [ -n "${DISPLAY:-}" ]; then
        local sel
        sel="$(yad --file-selection --title="OSify Condivisione — Scegli Cartella o File da Condividere" \
            --directory \
            --window-icon="/usr/share/pixmaps/osify-wifi.png" \
            --width=520 --height=340 --center 2>/dev/null || echo "")"
        if [ -n "$sel" ]; then
            start_share "$sel"
        fi
    else
        start_share "$TARGET_PATH"
    fi
}

case "${1:-gui}" in
    gui|--gui) launch_gui ;;
    stop) stop_share ;;
    status)
        if pgrep -f "http.server $PORT" >/dev/null; then
            echo "Condivisione attiva su: http://$(get_local_ip):${PORT}"
        else
            echo "Nessuna condivisione attiva."
        fi ;;
    *)
        if [ -e "$1" ]; then
            start_share "$1"
        else
            launch_gui
        fi ;;
esac
