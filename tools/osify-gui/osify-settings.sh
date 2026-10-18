#!/bin/sh
# ==============================================================================
# OSify Control Center — Centro di Controllo e Impostazioni di Sistema
# ==============================================================================
# Ingegnerizzato per OSify Operating System
# ==============================================================================

# Se lanciato dal desktop, apri xterm
if [ -n "$DISPLAY" ] && [ ! -t 0 ]; then
    if command -v xterm >/dev/null 2>&1; then
        exec xterm -title "Centro di Controllo OSify" -geometry 80x25 -bg "#0b0d14" -fg "#38bdf8" -cr "#10b981" +sb -e "$0" --run-tui
    fi
fi

OSIFY_VER=$(cat /etc/osify-version 2>/dev/null || echo "A.1")
CPU_INFO=$(awk -F: '/model name/ {print $2; exit}' /proc/cpuinfo 2>/dev/null | sed 's/^[ \t]*//' || uname -m)
RAM_INFO=$(awk '/MemTotal/ {print int($2/1024)" MB"}' /proc/meminfo 2>/dev/null || echo "1024 MB")
KERNEL_INFO=$(uname -srm)

if command -v dialog >/dev/null 2>&1; then
    while true; do
        OPT=$(dialog --backtitle "OSify Operating System — Centro di Controllo" \
            --title " Impostazioni di Sistema OSify " \
            --menu "\nSeleziona la categoria da configurare:\n" 17 68 6 \
            "1" "Risoluzione Display (Nativa 1024x600 / Virtual HD 1280x768)" \
            "2" "Touchpad e Puntatore (Tap-to-Click ed Edge Scroll)" \
            "3" "Audio e Volume (Regola Volume e Sblocca ALSA)" \
            "4" "Profilo Prestazioni (Turbo Performance / Risparmio Batteria)" \
            "5" "Pulizia Memoria RAM e zRAM Compressa" \
            "6" "Informazioni Hardware e Sistema" \
            3>&1 1>&2 2>&3)
        [ $? -ne 0 ] && break

        case "$OPT" in
            1)
                disp=$(xrandr 2>/dev/null | grep " connected" | awk '{print $1}' | head -n1)
                RES_CHOICE=$(dialog --backtitle "OSify — Schermo" \
                    --title " Risoluzione Schermo " \
                    --menu "\nScegli la modalita di visualizzazione:\n" 14 65 3 \
                    "1" "1024x600 (Risoluzione Nativa WSVGA Netbook)" \
                    "2" "1280x768 (Virtual Scaler Anti-Finestre Tagliate)" \
                    "3" "Ripristino Configurazione Automatica (xrandr --auto)" \
                    3>&1 1>&2 2>&3)
                if [ "$RES_CHOICE" = "1" ]; then
                    [ -n "$disp" ] && xrandr --output "$disp" --scale 1.0x1.0 --panning 1024x600 2>/dev/null || true
                    dialog --msgbox "\nRisoluzione impostata a 1024x600 nativa." 7 50
                elif [ "$RES_CHOICE" = "2" ]; then
                    [ -n "$disp" ] && xrandr --output "$disp" --scale 1.25x1.28 --panning 1280x768 2>/dev/null || true
                    dialog --msgbox "\nVirtual Scaler 1280x768 attivato." 7 50
                elif [ "$RES_CHOICE" = "3" ]; then
                    [ -n "$disp" ] && xrandr --output "$disp" --auto 2>/dev/null || true
                    dialog --msgbox "\nDisplay reimpostato in modalita automatica." 7 50
                fi
                ;;
            2)
                dialog --backtitle "OSify — Touchpad" \
                    --title " Configurazione Touchpad " \
                    --yesno "\nVuoi abilitare il Tap-to-Click (tocco per cliccare) e lo scorrimento sul bordo destro del touchpad?" 10 65
                if [ $? -eq 0 ]; then
                    if command -v synclient >/dev/null 2>&1; then
                        synclient TapButton1=1 TapButton2=3 TapButton3=2 VertEdgeScroll=1 HorizEdgeScroll=1 2>/dev/null || true
                    fi
                    dialog --msgbox "\nTouchpad configurato: Tap-to-Click ed Edge Scroll attivati." 7 60
                fi
                ;;
            3)
                VOL=$(dialog --backtitle "OSify — Audio" \
                    --title " Regolazione Volume " \
                    --inputbox "\nInserisci il livello di volume desiderato in percentuale (0 - 100):" 10 60 "85" \
                    3>&1 1>&2 2>&3)
                if [ -n "$VOL" ]; then
                    if command -v amixer >/dev/null 2>&1; then
                        amixer set Master unmute 2>/dev/null || true
                        amixer set Master "${VOL}%" 2>/dev/null || true
                    fi
                    dialog --msgbox "\nVolume impostato a ${VOL}% e canali ALSA sbloccati." 7 55
                fi
                ;;
            4)
                PERF=$(dialog --backtitle "OSify — Prestazioni" \
                    --title " Gestione Energetica CPU " \
                    --menu "\nSeleziona il profilo di carico desiderato:\n" 13 60 2 \
                    "1" "Turbo Mode (Massime Prestazioni CPU 1.66GHz)" \
                    "2" "Eco Mode (Risparmio Batteria e Basse Temperature)" \
                    3>&1 1>&2 2>&3)
                if [ "$PERF" = "1" ]; then
                    for gov in /sys/devices/system/cpu/cpu*/cpufreq/scaling_governor; do
                        [ -f "$gov" ] && echo "performance" > "$gov" 2>/dev/null || true
                    done
                    dialog --msgbox "\nModalita Turbo attivata: CPU impostata su Performance." 7 60
                elif [ "$PERF" = "2" ]; then
                    for gov in /sys/devices/system/cpu/cpu*/cpufreq/scaling_governor; do
                        [ -f "$gov" ] && echo "powersave" > "$gov" 2>/dev/null || true
                    done
                    dialog --msgbox "\nModalita Eco attivata: CPU impostata su Powersave." 7 60
                fi
                ;;
            5)
                sync
                if [ -w /proc/sys/vm/drop_caches ]; then
                    echo 3 > /proc/sys/vm/drop_caches 2>/dev/null || true
                elif command -v sudo >/dev/null 2>&1; then
                    sudo sh -c 'echo 3 > /proc/sys/vm/drop_caches' 2>/dev/null || true
                fi
                dialog --msgbox "\nMemoria RAM sincronizzata e cache di sistema liberate con successo!" 7 65
                ;;
            6)
                dialog --backtitle "OSify Operating System" \
                    --title " Informazioni di Sistema " \
                    --msgbox "\nSistema: OSify GNU/Linux v$OSIFY_VER\nKernel: $KERNEL_INFO\nCPU: $CPU_INFO\nRAM Totale: $RAM_INFO\nDesktop: Openbox + PCManFM\n" 11 60
                ;;
        esac
    done
    exit 0
fi

# Fallback testuale
if [ -x /usr/bin/osify ]; then
    exec /usr/bin/osify
fi
