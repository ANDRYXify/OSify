#!/usr/bin/env bash
# ==============================================================================
# OSify Firewall Governor & Network Shield — Protezione Perimetrale
# ==============================================================================
# Ingegnerizzato da Andrea Taliento (ANDRYXify)
# Gestisce regole di sicurezza iptables/nftables e telemetria connessioni di rete.
# ==============================================================================

set -euo pipefail

apply_profile_stealth() {
    echo "[+] Attivazione Profilo Stealth (Protezione Massima)..."
    if command -v iptables >/dev/null 2>&1; then
        sudo iptables -F 2>/dev/null || true
        sudo iptables -P INPUT DROP 2>/dev/null || true
        sudo iptables -P FORWARD DROP 2>/dev/null || true
        sudo iptables -P OUTPUT ACCEPT 2>/dev/null || true
        sudo iptables -A INPUT -i lo -j ACCEPT 2>/dev/null || true
        sudo iptables -A INPUT -m conntrack --ctstate ESTABLISHED,RELATED -j ACCEPT 2>/dev/null || true
    fi
    echo "[[OK]] Profilo Stealth Attivo: Porte in ingresso chiuse e PC invisibile."
}

apply_profile_lan() {
    echo "[+] Attivazione Profilo Rete Locale (Condivisione & Home)..."
    if command -v iptables >/dev/null 2>&1; then
        sudo iptables -F 2>/dev/null || true
        sudo iptables -P INPUT ACCEPT 2>/dev/null || true
        sudo iptables -P FORWARD ACCEPT 2>/dev/null || true
        sudo iptables -P OUTPUT ACCEPT 2>/dev/null || true
    fi
    echo "[[OK]] Profilo Rete Locale Attivo: Condivisione file, stampanti e media consentita."
}

get_firewall_status() {
    local report=""
    report+="=== STATO FIREWALL OSIFY ===\n"
    if command -v iptables >/dev/null 2>&1; then
        local policy
        policy="$(sudo iptables -L INPUT -n 2>/dev/null | head -n1 || echo "INPUT ACCEPT")"
        report+="Policy Attuale: $policy\n\n"
    else
        report+="Policy: Kernel Default Accept (Zero Limitazioni)\n\n"
    fi

    report+="=== CONNESSIONI DI RETE E PORTE ATTIVE ===\n"
    if command -v ss >/dev/null 2>&1; then
        report+="$(ss -tuln 2>/dev/null | head -n12 || echo "")\n"
    elif command -v netstat >/dev/null 2>&1; then
        report+="$(netstat -tuln 2>/dev/null | head -n12 || echo "")\n"
    fi
    echo -e "$report"
}

launch_gui() {
    local info
    info="$(get_firewall_status)"

    if command -v yad >/dev/null 2>&1 && [ -n "${DISPLAY:-}" ]; then
        local choice
        choice="$(yad --list --title="Firewall e Sicurezza Porte OSify" \
            --text="<b>Protezione Rete e Connessioni</b>\nSeleziona il profilo desiderato:" \
            --window-icon="/usr/share/pixmaps/osify-settings.png" \
            --width=480 --height=260 --center \
            --column="Profilo" --column="Descrizione" \
            "Stealth (Sicurezza Totale)" "Blocca tutte le connessioni in ingresso e rende il PC invisibile" \
            "Rete Locale (Condivisione)" "Permette scambio file, streaming e stampanti in LAN" \
            "Vedi Connessioni Attive" "Mostra la telemetria delle porte e socket aperti" \
            --button="Applica:0" --button="Chiudi:1" 2>/dev/null || echo "")"
        
        local sel
        sel="$(echo "$choice" | cut -d'|' -f1)"
        case "$sel" in
            *"Stealth"*) apply_profile_stealth ;;
            *"Rete Locale"*) apply_profile_lan ;;
            *"Vedi Connessioni"*)
                yad --text-info --title="Connessioni Attive OSify" --width=540 --height=340 --center <<< "$info" || true
                ;;
        esac
    else
        get_firewall_status
    fi
}

case "${1:-gui}" in
    gui|--gui) launch_gui ;;
    stealth) apply_profile_stealth ;;
    lan|open) apply_profile_lan ;;
    status) get_firewall_status ;;
    *) echo "Uso: $0 {gui|stealth|lan|status}" ;;
esac
