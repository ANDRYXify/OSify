#!/bin/sh
# ==============================================================================
# OSify Process Commander (osify-taskmanager) — Native Lightweight Task Manager
# ==============================================================================
# Ingegnerizzato da Andrea Taliento (ANDRYXify) per OSify
# Monitor di processi e telemetria hardware in tempo reale (< 4MB RAM, avvio istantaneo)
# ==============================================================================

export LC_ALL=C

# Ciclo principale di visualizzazione processi
while true; do
    # Raccolta processi attivi formattati
    PROCS=$(ps -eo pid,user,%cpu,rss,comm --sort=-%cpu 2>/dev/null | awk 'NR>1 {printf "%s\n%s\n%s%%\n%.1f MB\n%s\n", $1, $2, $3, $4/1024, $5}')

    TOTAL_RAM=$(awk '/MemTotal/ {print int($2/1024)}' /proc/meminfo 2>/dev/null || echo 1024)
    AVAIL_RAM=$(awk '/MemAvailable/ {print int($2/1024)}' /proc/meminfo 2>/dev/null || awk '/MemFree/ {print int($2/1024)}' /proc/meminfo 2>/dev/null || echo 512)
    USED_RAM=$((TOTAL_RAM - AVAIL_RAM))
    CPU_MODEL=$(awk -F: '/model name/ {print $2; exit}' /proc/cpuinfo 2>/dev/null | sed 's/^[ \t]*//' || uname -m)

    SELECTED=$(echo "$PROCS" | yad --list \
        --title="OSify Process Commander — Gestione Attività" \
        --window-icon="utilities-system-monitor" \
        --width=720 \
        --height=480 \
        --center \
        --text="<b><big>📊 OSify Process Commander</big></b>\n<i>CPU: $CPU_MODEL | RAM Usata: ${USED_RAM}MB / ${TOTAL_RAM}MB</i>" \
        --column="PID":NUM \
        --column="Utente":TEXT \
        --column="CPU":TEXT \
        --column="Memoria":TEXT \
        --column="Processo":TEXT \
        --button="⚡ Priorità Turbo (nice -10)":10 \
        --button="🛑 Termina Processo":20 \
        --button="💀 Forza Arresto (Kill -9)":30 \
        --button="🔄 Aggiorna":0 \
        --button="Chiudi":1 \
        --search-column=5 \
        --print-column=1)

    RET=$?
    
    # Uscita se premuto Chiudi o Esc
    [ "$RET" -eq 1 ] && break
    [ "$RET" -eq 252 ] && break

    # Se premuto Aggiorna senza selezione
    [ "$RET" -eq 0 ] && continue

    PID=$(echo "$SELECTED" | cut -d'|' -f1)

    if [ -n "$PID" ] && [ "$PID" -gt 0 ] 2>/dev/null; then
        case "$RET" in
            10) # Turbo priority
                renice -n -10 -p "$PID" >/dev/null 2>&1 || true
                yad --notification --text="🚀 Processo PID $PID impostato a Priorità Turbo (nice -10)" --timeout=2 2>/dev/null &
                ;;
            20) # Graceful kill
                kill -15 "$PID" >/dev/null 2>&1 || true
                yad --notification --text="🛑 Inviato segnale di chiusura a PID $PID" --timeout=2 2>/dev/null &
                ;;
            30) # Force kill
                kill -9 "$PID" >/dev/null 2>&1 || true
                yad --notification --text="💀 Processo PID $PID terminato forzatamente" --timeout=2 2>/dev/null &
                ;;
        esac
    fi
done
