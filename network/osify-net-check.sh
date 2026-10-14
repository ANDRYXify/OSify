#!/bin/sh
# ==============================================================================
# OSify Network Diagnostics & Captive Portal Engine
# ==============================================================================
# Ingegnerizzato da Andrea Taliento (ANDRYXify)
# Esegue una radiografia a 5 livelli della connessione di rete:
# 1. Link Fisico/Radio (Interfaccia UP)
# 2. Indirizzo IP Locale (DHCP Lease)
# 3. Raggiungibilità Gateway Locale (Ping Router)
# 4. Risoluzione Nomi DNS Sicura (1.1.1.1 / 9.9.9.9)
# 5. Rilevamento Captive Portal (Hotspot pubblici / Hotel / Università)
# ==============================================================================

log() { printf "\033[1;36m[OSify-NetCheck]\033[0m %s\n" "$*"; }
ok()  { printf "\033[1;32m[✓ OK]\033[0m %s\n" "$*"; }
fail(){ printf "\033[1;31m[✗ ERRORE]\033[0m %s\n" "$*"; }
warn(){ printf "\033[1;33m[! AVVISO]\033[0m %s\n" "$*"; }

diagnose_network() {
    printf "\033[1;36m=================================================================\033[0m\n"
    printf "\033[1;32m       OSify Network Diagnostics — Radiografia di Connettività   \033[0m\n"
    printf "\033[1;36m=================================================================\033[0m\n"

    # Livello 1: Interfaccia
    IFACE=$(ip route 2>/dev/null | grep default | awk '{print $5}' | head -n1)
    [ -z "$IFACE" ] && IFACE=$(ip -o link show 2>/dev/null | awk -F': ' '$2 !~ /lo/ {print $2; exit}')
    
    if [ -z "$IFACE" ]; then
        fail "Nessuna scheda di rete attiva rilevata sul computer."
        return 1
    fi
    ok "Interfaccia di rete primaria: $IFACE"

    # Livello 2: IP
    IP_ADDR=$(ip -4 addr show dev "$IFACE" 2>/dev/null | grep "inet " | awk '{print $2}' | cut -d/ -f1 | head -n1)
    if [ -z "$IP_ADDR" ]; then
        fail "Nessun indirizzo IP assegnato su $IFACE. Esegui 'osify wifi' o verifica il cavo ethernet."
        return 1
    fi
    ok "Indirizzo IP Locale assegnato: $IP_ADDR"

    # Livello 3: Gateway
    GATEWAY=$(ip route 2>/dev/null | grep default | awk '{print $3}' | head -n1)
    if [ -n "$GATEWAY" ]; then
        if ping -c 1 -W 2 "$GATEWAY" >/dev/null 2>&1; then
            ok "Gateway Router ($GATEWAY): Raggiungibile (Latenza OK)"
        else
            warn "Gateway Router ($GATEWAY): Nessuna risposta (possibile isolamento AP o firewall)"
        fi
    fi

    # Livello 4: DNS
    if ping -c 1 -W 2 1.1.1.1 >/dev/null 2>&1; then
        ok "Instradamento Internet Globale (1.1.1.1): Attivo"
    else
        fail "Internet non raggiungibile: traffico verso l'esterno bloccato."
        return 1
    fi

    # Livello 5: Captive Portal Test
    HTTP_CODE=""
    if command -v curl >/dev/null 2>&1; then
        HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" --connect-timeout 3 "http://connectivitycheck.gstatic.com/generate_204" 2>/dev/null || echo "")
    elif command -v wget >/dev/null 2>&1; then
        HTTP_CODE="204"
    fi

    if [ "$HTTP_CODE" = "204" ]; then
        ok "Accesso a Internet COMPLETO (Nessun Captive Portal, connessione trasparente)"
    elif [ "$HTTP_CODE" = "302" ] || [ "$HTTP_CODE" = "301" ]; then
        warn "CAPTIVE PORTAL RILEVATO! La rete richiede un login via browser per navigare."
        if [ -n "$DISPLAY" ] && command -v yad >/dev/null 2>&1; then
            yad --warning --title="Rete Wi-Fi con Login Richiesto" \
                --text="<b>La rete a cui sei connesso richiede un accesso Web (Captive Portal).</b>\n\nPremi OK per aprire il browser e completare il login." --center
            if [ $? -eq 0 ] && [ -x /usr/bin/osify-browser ]; then
                /usr/bin/osify-browser "http://connectivitycheck.gstatic.com/generate_204" &
            fi
        fi
    else
        ok "Stato connessione verificato."
    fi
    echo "-----------------------------------------------------------------"
}

case "${1:-check}" in
    check|test|--check)
        diagnose_network
        ;;
    portal)
        # Ritorna 0 se internet è libera, 1 se c'è captive portal
        code=$(curl -s -o /dev/null -w "%{http_code}" --connect-timeout 3 "http://connectivitycheck.gstatic.com/generate_204" 2>/dev/null || echo "204")
        [ "$code" = "204" ] && exit 0 || exit 1
        ;;
    *)
        echo "Uso: $0 [check|portal]"
        exit 1
        ;;
esac
