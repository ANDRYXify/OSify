#!/bin/sh
# ==============================================================================
# OSify Developer & Code Suite — Ambiente di Programmazione Integrato
# ==============================================================================
# Ingegnerizzato da Andrea Taliento (ANDRYXify)
# Ambiente pronto per programmatori: Python, C, Bash scripting, Git e debug.
# ==============================================================================

set -e

PROJECTS_DIR="$HOME/Progetti"
mkdir -p "$PROJECTS_DIR"

open_editor() {
    file_path="$1"
    if command -v featherpad >/dev/null 2>&1; then
        featherpad "$file_path" &
    elif command -v leafpad >/dev/null 2>&1; then
        leafpad "$file_path" &
    elif command -v nano >/dev/null 2>&1; then
        terminal -geometry 95x28 -T "OSify Code Editor: $(basename "$file_path")" -e nano "$file_path" &
    else
        terminal -geometry 95x28 -T "OSify Editor" -e vi "$file_path" &
    fi
}

start_python_repl() {
    terminal -geometry 90x24 -T "OSify Python 3 REPL" -e /bin/sh -c "
        echo '=== OSify Python 3 Interactive Environment ==='
        python3 -V 2>/dev/null || python -V 2>/dev/null || echo 'Interprete Python nativo'
        echo 'Digita exit() o premi Ctrl+D per uscire.'
        python3 || python || sh
    " &
}

create_template_project() {
    clear
    printf "\033[1;36m=========================================================\033[0m\n"
    printf "\033[1;32m       OSify Developer — Creazione Nuovo Progetto        \033[0m\n"
    printf "\033[1;36m=========================================================\033[0m\n\n"
    echo "1) Progetto C / TinyCC (Compilatore nativo ultra-veloce)"
    echo "2) Progetto Python 3 (Script con automazione e threading)"
    echo "3) Progetto Shell Script POSIX (Automazione di sistema OSify)"
    echo "0) Annulla"
    echo ""
    printf "Seleziona tipo di progetto [1-3]: "
    read -r p_type

    case "$p_type" in
        1)
            printf "Nome del progetto C [es. myapp]: "
            read -r p_name
            [ -z "$p_name" ] && p_name="app_c"
            target_dir="$PROJECTS_DIR/$p_name"
            mkdir -p "$target_dir"
            cat << 'EOF' > "$target_dir/main.c"
#include <stdio.h>

int main(void) {
    printf("\n============================================\n");
    printf("  Benvenuto su OSify Developer Environment! \n");
    printf("  Ingegnerizzato da Andrea Taliento         \n");
    printf("============================================\n\n");
    return 0;
}
EOF
            cat << 'EOF' > "$target_dir/build.sh"
#!/bin/sh
set -e
echo "[+] Compilazione con TCC / GCC..."
if command -v tcc >/dev/null 2>&1; then
    tcc -o main main.c
elif command -v gcc >/dev/null 2>&1; then
    gcc -O2 -o main main.c
else
    echo "Compilatore non trovato nel PATH."
    exit 1
fi
echo "[[OK]] Compilazione completata! Esecuzione:"
./main
EOF
            chmod +x "$target_dir/build.sh"
            echo "[[OK]] Progetto C creato in: $target_dir"
            open_editor "$target_dir/main.c"
            ;;
        2)
            printf "Nome del progetto Python [es. bot_osify]: "
            read -r p_name
            [ -z "$p_name" ] && p_name="app_py"
            target_dir="$PROJECTS_DIR/$p_name"
            mkdir -p "$target_dir"
            cat << 'EOF' > "$target_dir/main.py"
#!/usr/bin/env python3
"""
OSify Python Application Template
Ingegnerizzato da Andrea Taliento (ANDRYXify)
"""
import sys
import os
import platform

def main():
    print("=" * 50)
    print("  OSify Python Runtime System")
    print(f" Sistema   : {platform.system()} {platform.release()} ({platform.machine()})")
    print(f" Python    : {platform.python_version()}")
    print("=" * 50)
    print("Il tuo ambiente di sviluppo è pronto per il codice!\n")

if __name__ == "__main__":
    main()
EOF
            chmod +x "$target_dir/main.py"
            echo "[[OK]] Progetto Python creato in: $target_dir"
            open_editor "$target_dir/main.py"
            ;;
        3)
            printf "Nome dello script Bash [es. auto_backup]: "
            read -r p_name
            [ -z "$p_name" ] && p_name="script_sh"
            target_dir="$PROJECTS_DIR/$p_name"
            mkdir -p "$target_dir"
            cat << 'EOF' > "$target_dir/script.sh"
#!/bin/sh
# OSify POSIX Automation Script
# Ingegnerizzato da Andrea Taliento (ANDRYXify)
set -eu

echo "=== OSify System Automation ==="
echo "Data e ora: $(date)"
echo "Uptime: $(uptime)"
EOF
            chmod +x "$target_dir/script.sh"
            echo "[[OK]] Script Bash creato in: $target_dir"
            open_editor "$target_dir/script.sh"
            ;;
        *)
            return
            ;;
    esac
    sleep 1
}

git_quick_manager() {
    clear
    printf "\033[1;34m=========================================================\033[0m\n"
    printf "\033[1;32m           OSify Developer — Gestore Rapido Git          \033[0m\n"
    printf "\033[1;34m=========================================================\033[0m\n\n"
    echo "1) Clona un repository remoto da GitHub / GitLab"
    echo "2) Visualizza stato Git in una cartella"
    echo "0) Torna al menu"
    echo ""
    printf "Scelta [0-2]: "
    read -r g_opt
    case "$g_opt" in
        1)
            printf "URL del repository Git da clonare: "
            read -r repo_url
            if [ -n "$repo_url" ]; then
                (cd "$PROJECTS_DIR" && git clone "$repo_url")
                printf "\nClonazione completata in $PROJECTS_DIR. Premi INVIO..."
                read -r _
            fi
            ;;
        2)
            printf "Percorso della cartella Git: "
            read -r repo_dir
            [ -z "$repo_dir" ] && repo_dir="$PROJECTS_DIR"
            if [ -d "$repo_dir" ]; then
                (cd "$repo_dir" && git status)
                printf "\nPremi INVIO per continuare..."
                read -r _
            fi
            ;;
        *)
            return
            ;;
    esac
}

if command -v dialog >/dev/null 2>&1; then
    while true; do
        DEV_OPT=$(dialog --stdout --backtitle "OSify Developer Suite — Andrea Taliento" \
            --title "  OSify Developer & Coding Environment " \
            --menu "Cartella Progetti: $PROJECTS_DIR\n\nScegli un'attività di sviluppo:" 16 65 6 \
            "1" "  Crea Nuovo Progetto da Template (C, Python, Bash)" \
            "2" "  Avvia Console Interattiva Python 3 REPL" \
            "3" "  Apri Terminale di Sviluppo & Debug" \
            "4" "  Apri Cartella Personale Progetti ($PROJECTS_DIR)" \
            "5" "  Gestore Version Control Git (Clona / Status)" \
            "0" "  Torna al Desktop" 2>/dev/null || echo "0")

        case "$DEV_OPT" in
            1) create_template_project ;;
            2) start_python_repl ;;
            3) terminal -geometry 95x28 -T "OSify Dev Shell" -e /bin/sh & ;;
            4) pcmanfm "$PROJECTS_DIR" & ;;
            5) git_quick_manager ;;
            0|"") clear; exit 0 ;;
        esac
    done
else
    clear
    echo "========================================================="
    echo "    OSify Developer & Coding Suite                     "
    echo "========================================================="
    echo " 1)  Crea Nuovo Progetto (C, Python, Bash)"
    echo " 2)  Avvia Python 3 REPL"
    echo " 3)  Apri Cyber Terminal"
    echo " 4)  Apri Cartella Progetti ($PROJECTS_DIR)"
    echo " 5)  Git Quick Manager"
    echo " 0)  Esci"
    echo "========================================================="
    read -rp "Selezione [0-5]: " d_opt
    case "$d_opt" in
        1) create_template_project ;;
        2) start_python_repl ;;
        3) terminal & ;;
        4) ls -la "$PROJECTS_DIR"; read -r _ ;;
        5) git_quick_manager ;;
        *) exit 0 ;;
    esac
fi
