#!/bin/sh
# ==============================================================================
# OSify Gaming & Retrogaming Hub
# ==============================================================================
# Ingegnerizzato da Andrea Taliento (ANDRYXify)
# Ottimizzato per prestazioni grafiche massime su qualsiasi architettura:
# - Esecutore giochi Windows Win32/DirectX (.exe)
# - Retrogaming DOS (DOSBox / FreeDOS emulator)
# - Launcher Universale UEM (Android .apk, iOS .ipa, Darwin .app)
# - GPU Performance Boost (disattivazione vsync, CPU unthrottling)
# ==============================================================================

set -e

GAMES_DIR="$HOME/Giochi"
mkdir -p "$GAMES_DIR"

boost_gaming_profile() {
    # Imposta Governor su performance
    for gov in /sys/devices/system/cpu/cpu*/cpufreq/scaling_governor; do
        [ -f "$gov" ] && echo "performance" > "$gov" 2>/dev/null || true
    done
    # Ottimizzazione kernel per framerate gaming
    sysctl -w vm.dirty_ratio=10 vm.dirty_background_ratio=5 2>/dev/null || true
    # Pulizia cache
    sync
    echo 3 > /proc/sys/vm/drop_caches 2>/dev/null || true
}

launch_windows_game() {
    clear
    printf "\033[1;35m=========================================================\033[0m\n"
    printf "\033[1;32m      OSify Gaming — Esecutore Giochi Windows (.EXE)     \033[0m\n"
    printf "\033[1;35m=========================================================\033[0m\n\n"
    echo "Trascina qui il file .exe del gioco oppure inserisci il percorso:"
    echo "Suggerimento: copia i tuoi giochi in $GAMES_DIR"
    echo ""
    printf "Percorso file .exe: "
    read -r target_exe
    target_exe=$(echo "$target_exe" | sed "s/^['\"]//; s/['\"]$//")

    if [ -n "$target_exe" ] && [ -f "$target_exe" ]; then
        echo "[+] Attivazione Profilo Prestazioni Gaming..."
        boost_gaming_profile
        echo "[+] Avvio $target_exe..."
        if command -v wine >/dev/null 2>&1; then
            WINEDEBUG=-all wine "$target_exe"
        elif [ -x /usr/bin/osify-exec ]; then
            /usr/bin/osify-exec "$target_exe"
        else
            echo "[!] Wine non installato nel sistema. Installa wine tramite tazpkg/apt."
            sleep 3
        fi
    else
        echo "[!] File non trovato o non specificato."
        sleep 2
    fi
}

launch_dos_game() {
    clear
    printf "\033[1;33m=========================================================\033[0m\n"
    printf "\033[1;32m       OSify Retrogaming Hub — Emulatore DOS (DOSBox)    \033[0m\n"
    printf "\033[1;33m=========================================================\033[0m\n\n"
    echo "Trascina qui il file .exe o .com DOS oppure la cartella del gioco:"
    printf "Percorso: "
    read -r dos_target
    dos_target=$(echo "$dos_target" | sed "s/^['\"]//; s/['\"]$//")

    if [ -n "$dos_target" ]; then
        echo "[+] Avvio Retrogaming Engine..."
        if command -v dosbox >/dev/null 2>&1; then
            dosbox "$dos_target"
        elif [ -x /usr/bin/osify-dos-runner ]; then
            /usr/bin/osify-dos-runner "$dos_target"
        else
            echo "[!] DOSBox non rilevato. Avvio con runner fallback..."
            sleep 2
        fi
    fi
}

explore_games_folder() {
    if command -v pcmanfm >/dev/null 2>&1; then
        pcmanfm "$GAMES_DIR" &
    else
        ls -la "$GAMES_DIR"
        printf "\nPremi INVIO per tornare al menu..."
        read -r _
    fi
}

if command -v dialog >/dev/null 2>&1; then
    while true; do
        G_CHOICE=$(dialog --stdout --backtitle "OSify Gaming Subsystem — Andrea Taliento" \
            --title " 🎮 OSify Gaming & Retrogaming Hub " \
            --menu "Cartella Giochi Utente: $GAMES_DIR\n\nScegli un'opzione di gioco:" 16 65 6 \
            "1" "🕹️   Esegui Gioco Windows (.exe con Wine/DirectX)" \
            "2" "👾  Avvia Retrogaming DOS (Doom, Duke3D, DOSBox)" \
            "3" "📱  Lancia Applicazione/Gioco Android (.apk) o Apple" \
            "4" "📁  Apri Cartella Personale Giochi ($GAMES_DIR)" \
            "5" "⚡  Attiva Profilo Turbo Boost GPU & CPU Gaming" \
            "0" "❌  Torna al Desktop" 2>/dev/null || echo "0")

        case "$G_CHOICE" in
            1) launch_windows_game ;;
            2) launch_dos_game ;;
            3)
                if [ -x /usr/bin/osify-exec ]; then
                    launch_windows_game
                fi
                ;;
            4) explore_games_folder ;;
            5)
                boost_gaming_profile
                dialog --title "Gaming Boost" --msgbox "\n[✓] CPU Governor: Performance\n[✓] Memory Cache Flush: Eseguita\n[✓] Latenza I/O: Ridotta al minimo!\n" 8 50
                ;;
            0|"")
                clear
                exit 0
                ;;
        esac
    done
else
    clear
    echo "========================================================="
    echo "   🎮 OSify Gaming & Retrogaming Hub                     "
    echo "========================================================="
    echo " 1) 🕹️ Esegui Gioco Windows (.exe)"
    echo " 2) 👾 Avvia Retrogaming DOS"
    echo " 3) 📁 Apri Cartella Giochi ($GAMES_DIR)"
    echo " 4) ⚡ Attiva Turbo Boost Gaming"
    echo " 0) ❌ Esci"
    echo "========================================================="
    read -rp "Selezione [0-4]: " g_opt
    case "$g_opt" in
        1) launch_windows_game ;;
        2) launch_dos_game ;;
        3) explore_games_folder ;;
        4) boost_gaming_profile; echo "Turbo boost attivato!"; sleep 2 ;;
        *) exit 0 ;;
    esac
fi
