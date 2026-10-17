#!/usr/bin/env bash
# ==============================================================================
# OSify Instant Windows Fast-Boot (One-Time UEFI BootNext)
# ==============================================================================
# Per giochi con Anti-Cheat Ring-0 ostili (es. Riot Vanguard su VALORANT):
# Rileva la voce UEFI di Windows Boot Manager sul sistema, imposta il flag
# 'BootNext' ed esegue un riavvio istantaneo in Windows.
# Al termine della partita, spegnendo o riavviando il PC si ritorna
# AUTOMATICAMENTE in OSify senza dover premere alcun tasto nel BIOS!
# ==============================================================================

set -euo pipefail

check_root() {
    if [[ $EUID -ne 0 ]]; then
        echo "[ERRORE] Questa operazione richiede privilegi di root." >&2
        exit 1
    fi
}

detect_windows_boot_entry() {
    efibootmgr | grep -i "windows boot manager" | head -n1 | sed -E 's/^Boot([0-9A-Fa-f]+)\*.*/\1/'
}

main() {
    check_root
    echo "========================================================="
    echo "       OSify Fast-Boot: Riavvio One-Time su Windows       "
    echo "========================================================="

    WIN_ENTRY=$(detect_windows_boot_entry || true)

    if [[ -z "$WIN_ENTRY" ]]; then
        echo "[!] Nessuna partizione Windows Boot Manager rilevata nelle variabili UEFI."
        echo "    Verifica che Windows sia installato in modalità UEFI su uno dei dischi."
        exit 1
    fi

    echo "[+] Voce Windows Boot Manager trovata: Boot$WIN_ENTRY"
    echo "[+] Impostazione UEFI BootNext su Boot$WIN_ENTRY..."
    efibootmgr --bootnext "$WIN_ENTRY" >/dev/null

    echo "[✓] Configurazione completata. Riavvio istantaneo in Windows..."
    echo "[i] Al prossimo riavvio da Windows tornerai automaticamente in OSify!"
    
    # Esegue il riavvio controllato se richiesto
    if [[ "${1:-}" == "--reboot" ]]; then
        systemctl reboot
    else
        echo "Esegui 'sudo systemctl reboot' per riavviare adesso."
    fi
}

main "$@"
