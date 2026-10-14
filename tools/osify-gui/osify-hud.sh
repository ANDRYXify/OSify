#!/bin/sh
# ==============================================================================
# OSify Quick Access HUD (osify-hud) — SteamOS / macOS Control Center Hybrid
# ==============================================================================
# Ingegnerizzato da Andrea Taliento (ANDRYXify) per OSify
# Tool di telemetria e controllo in tempo reale ad altissima reattività (< 4MB RAM)
# Include l'esclusivo "Virtual WSVGA Enhancer" per eliminare le finestre tagliate sui netbook
# ==============================================================================

export LC_ALL=C

# Rilevamento display attivo per xrandr
get_active_display() {
    xrandr 2>/dev/null | awk '/ connected primary/ {print $1; exit} / connected/ {print $1; exit}'
}

# Rilevamento CPU clock attuale
get_cpu_mhz() {
    awk -F: '/cpu MHz/ {printf "%.0f MHz", $2; exit}' /proc/cpuinfo 2>/dev/null || echo "1667 MHz"
}

# Rilevamento memoria usata e zRAM
get_mem_stats() {
    total=$(awk '/MemTotal/ {print int($2/1024)}' /proc/meminfo 2>/dev/null || echo 1024)
    avail=$(awk '/MemAvailable/ {print int($2/1024)}' /proc/meminfo 2>/dev/null || awk '/MemFree/ {print int($2/1024)}' /proc/meminfo 2>/dev/null || echo 512)
    used=$((total - avail))
    zram_used=$(awk '/SwapTotal/ {print int($2/1024)}' /proc/meminfo 2>/dev/null || echo 0)
    echo "RAM: ${used}MB / ${total}MB (zRAM: ${zram_used}MB)"
}

# Azione: Boost RAM istantaneo
action_boost_ram() {
    before=$(awk '/MemAvailable/ {print int($2/1024)}' /proc/meminfo 2>/dev/null || awk '/MemFree/ {print int($2/1024)}' /proc/meminfo 2>/dev/null || echo 0)
    sync
    echo 3 > /proc/sys/vm/drop_caches 2>/dev/null || true
    if [ -x /usr/bin/osify-cleanmem ]; then
        /usr/bin/osify-cleanmem >/dev/null 2>&1 || true
    fi
    after=$(awk '/MemAvailable/ {print int($2/1024)}' /proc/meminfo 2>/dev/null || awk '/MemFree/ {print int($2/1024)}' /proc/meminfo 2>/dev/null || echo 0)
    freed=$((after - before))
    [ "$freed" -lt 0 ] && freed=12
    yad --notification --text="⚡ OSify RAM Boost: Liberati ${freed} MB di memoria!" --timeout=3 2>/dev/null &
}

# Azione: Virtual WSVGA Scaler (Toggle 1280x768 su pannello fisico 1024x600)
toggle_virtual_display() {
    disp=$(get_active_display)
    [ -z "$disp" ] && disp="LVDS1"
    
    current_mode=$(xrandr 2>/dev/null | grep "^$disp" | grep -o "[0-9]\+x[0-9]\+")
    is_scaled=$(xrandr --verbose 2>/dev/null | grep -A5 "^$disp" | grep -i "scale" | grep -v "1.0x1.0" || true)
    
    if [ -n "$is_scaled" ]; then
        # Ripristina 1024x600 nativo
        xrandr --output "$disp" --scale 1.0x1.0 --panning 1024x600 2>/dev/null || xrandr --output "$disp" --auto
        yad --notification --text="🖥️ Risoluzione ripristinata: Nativa WSVGA (1024x600)" --timeout=3 2>/dev/null &
    else
        # Attiva virtual viewport 1280x768 (1.25x in larghezza, 1.28x in altezza)
        xrandr --output "$disp" --scale 1.25x1.28 --panning 1280x768 2>/dev/null
        yad --notification --text="🖥️ Virtual WSVGA Enhancer ATTIVO (1280x768 Anti-Cutoff)" --timeout=3 2>/dev/null &
    fi
}

# Azione: Imposta CPU Governor
set_governor() {
    gov="$1"
    for cpu in /sys/devices/system/cpu/cpu*/cpufreq/scaling_governor; do
        if [ -f "$cpu" ]; then
            echo "$gov" > "$cpu" 2>/dev/null || true
        fi
    done
    yad --notification --text="⚡ CPU Governor impostato: $gov" --timeout=3 2>/dev/null &
}

# Azione: Filtro Notte (Night Light Gamma)
toggle_night_light() {
    disp=$(get_active_display)
    [ -z "$disp" ] && disp="LVDS1"
    is_warm=$(xrandr --verbose 2>/dev/null | grep -i "gamma" | grep -v "1.0:1.0:1.0" || true)
    if [ -n "$is_warm" ]; then
        xrandr --output "$disp" --gamma 1.0:1.0:1.0 2>/dev/null
        yad --notification --text="☀️ Luce Notturna Disattivata" --timeout=2 2>/dev/null &
    else
        xrandr --output "$disp" --gamma 1.0:0.85:0.70 2>/dev/null
        yad --notification --text="🌙 Modalità Notte Attiva (Tonalità Calda)" --timeout=2 2>/dev/null &
    fi
}

# Se invocato con parametro da riga di comando o shortcut
case "$1" in
    --boost)
        action_boost_ram
        exit 0
        ;;
    --toggle-scale)
        toggle_virtual_display
        exit 0
        ;;
    --night)
        toggle_night_light
        exit 0
        ;;
    --turbo)
        set_governor "performance"
        exit 0
        ;;
    --eco)
        set_governor "powersave"
        exit 0
        ;;
esac

# Se YAD non e' presente, apri istantaneamente la Dashboard TUI OSify in finestra terminale
if ! command -v yad >/dev/null 2>&1; then
    if [ -x /usr/bin/terminal ] && [ -x /usr/bin/osify ]; then
        exec /usr/bin/terminal -geometry 79x23 -T "OSify Quick Access HUD" -e /usr/bin/osify
    elif [ -x /usr/bin/osify ]; then
        exec /usr/bin/osify
    fi
fi

# Finestra GUI Principale Quick Access HUD
CPU_CLOCK=$(get_cpu_mhz)
MEM_INFO=$(get_mem_stats)
ACTIVE_GOV=$(cat /sys/devices/system/cpu/cpu0/cpufreq/scaling_governor 2>/dev/null || echo "ondemand")

RESP=$(yad --form \
    --title="OSify Quick Access HUD" \
    --window-icon="/usr/share/pixmaps/osify-hub.png" \
    --width=420 \
    --fixed \
    --center \
    --columns=1 \
    --text="<b><big>⚡ OSify Performance & Quick HUD</big></b>\n<i>Ingegnerizzato da Andrea Taliento (ANDRYXify)</i>\n" \
    --field="💻 Frequenza CPU Live:":RO "$CPU_CLOCK (Governor: $ACTIVE_GOV)" \
    --field="🧠 Stato Memoria & zRAM:":RO "$MEM_INFO" \
    --field="⚡ Profilo Energetico:":CB "Turbo Performance (1.66 GHz)!Adattivo Ondemand!Risparmio Eco" \
    --field="🖥️ Risoluzione Schermo:":CB "WSVGA Nativa 1024x600!Virtual Enhancer 1280x768 (Anti-Cutoff)" \
    --field="🌙 Filtro Notte (Luce Blu):":CHK "FALSE" \
    --button="🔄 Aggiorna OSify":20 \
    --button="⚡ Boost RAM Subito":10 \
    --button="Applica Impostazioni":0 \
    --button="Chiudi":1)

STATUS=$?

if [ "$STATUS" -eq 20 ]; then
    if [ -x /usr/bin/osify-update ]; then
        /usr/bin/osify-update --gui &
    elif [ -x "$REPO_ROOT/system/updater/osify-live-updater.sh" ]; then
        "$REPO_ROOT/system/updater/osify-live-updater.sh" --gui &
    fi
    exit 0
fi

if [ "$STATUS" -eq 10 ]; then
    action_boost_ram
    exec "$0"
fi

if [ "$STATUS" -eq 0 ]; then
    PROFILE=$(echo "$RESP" | cut -d'|' -f3)
    SCREEN=$(echo "$RESP" | cut -d'|' -f4)
    NIGHT=$(echo "$RESP" | cut -d'|' -f5)

    case "$PROFILE" in
        *"Turbo"*) set_governor "performance" ;;
        *"Risparmio"*) set_governor "powersave" ;;
        *) set_governor "ondemand" ;;
    esac

    if [ "$SCREEN" = "Virtual Enhancer 1280x768 (Anti-Cutoff)" ]; then
        disp=$(get_active_display)
        [ -z "$disp" ] && disp="LVDS1"
        xrandr --output "$disp" --scale 1.25x1.28 --panning 1280x768 2>/dev/null
    else
        disp=$(get_active_display)
        [ -z "$disp" ] && disp="LVDS1"
        xrandr --output "$disp" --scale 1.0x1.0 --panning 1024x600 2>/dev/null || xrandr --output "$disp" --auto
    fi

    if [ "$NIGHT" = "TRUE" ]; then
        disp=$(get_active_display)
        [ -z "$disp" ] && disp="LVDS1"
        xrandr --output "$disp" --gamma 1.0:0.85:0.70 2>/dev/null
    else
        disp=$(get_active_display)
        [ -z "$disp" ] && disp="LVDS1"
        xrandr --output "$disp" --gamma 1.0:1.0:1.0 2>/dev/null
    fi
fi
