#!/usr/bin/env bash
# ==============================================================================
# OSify Virtual Machine Control Center — Centro Avvio Macchine Virtuali
# ==============================================================================
# Ingegnerizzato da Andrea Taliento (ANDRYXify)
# Menu unificato per avviare le due edizioni di OSify su macchina virtuale:
# [1] Vintage 32-bit (Netbook Intel Atom / Vecchie Glorie)
# [2] Pro 64-bit Modern (Gaming & Streaming x86_64-v3)
# ==============================================================================

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

show_menu() {
    clear
    cat << "EOF"
  ██████╗ ███████╗██╗███████╗██╗   ██╗
 ██╔═══██╗██╔════╝██║██╔════╝╚██╗ ██╔╝
 ██║   ██║███████╗██║█████╗   ╚████╔╝ 
 ██║   ██║╚════██║██║██╔══╝    ╚██╔╝  
 ╚██████╔╝███████║██║██║        ██║   
  ╚═════╝ ╚══════╝╚═╝╚═╝        ╚═╝   
  CENTRO COLLAUDO MACCHINE VIRTUALI
=========================================================
 1) Avvia OSify VINTAGE 32-bit (Netbook & Vecchie Glorie)
    - RAM: 1024 MB | Display: 1024x600 Netbook | 8GB Disco

 2) Avvia OSify PRO 64-bit (x86_64-v3 Modern & Gaming)
    - RAM: 3072 MB | vCPU: 4 | GPU VirtIO | 20GB Disco

 3) Reset / Ripristina Dischi Virtuali (Azzera installazioni di test)
 4) Esci
=========================================================
EOF
    printf "Seleziona un'opzione [1-4]: "
    read -r opt
    case "$opt" in
        1)
            bash "$SCRIPT_DIR/run-vm-vintage.sh"
            ;;
        2)
            bash "$SCRIPT_DIR/run-vm-pro.sh"
            ;;
        3)
            echo "[!] Cancellazione dischi virtuali di test..."
            rm -f "$SCRIPT_DIR/osify-vintage-disk.qcow2" "$SCRIPT_DIR/osify-pro-disk.qcow2"
            echo "[OK] Dischi virtuali azzerati. Verranno ricreati puliti al prossimo avvio."
            sleep 2
            show_menu
            ;;
        4|q|Q)
            echo "Uscita."
            exit 0
            ;;
        *)
            echo "Opzione non valida."
            sleep 1
            show_menu
            ;;
    esac
}

show_menu
