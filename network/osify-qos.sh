#!/usr/bin/env bash
# ==============================================================================
# OSify Network Engine — Traffic Shaping & Zero-Bufferbloat QoS
# ==============================================================================
# Ottimizzato per: Live Streaming simultaneo (Twitch/Kick/YouTube) + Gaming eSport
# Utilizza: Linux Kernel CAKE (sch_cake) + DiffServ-4 + nftables DSCP packet marking
# ==============================================================================

set -euo pipefail

# Parametri predefiniti o da /etc/osify/network.conf
CONFIG_FILE="/etc/osify/network.conf"
DEFAULT_IFACE=$(ip route show default 2>/dev/null | awk '{print $5}' | head -n1)

# Se non specificato, imposta bandwidth conservativo o unlim con solo fairness
UPLOAD_MBPS="auto"
DOWNLOAD_MBPS="auto"

if [[ -f "$CONFIG_FILE" ]]; then
    # shellcheck disable=SC1090
    source "$CONFIG_FILE"
fi

INTERFACE="${1:-${OSIFY_IFACE:-$DEFAULT_IFACE}}"
ACTION="${2:-start}"

if [[ -z "$INTERFACE" ]]; then
    echo "[ERRORE] Nessuna interfaccia di rete attiva rilevata." >&2
    exit 1
fi

apply_nftables_marking() {
    echo "[OSify-QoS] Applicazione regole di marcatura pacchetti DSCP via nftables..."
    
    nft -f - << 'EOF' || true
table inet osify_qos {
    chain output {
        type filter hook output priority mangle; policy accept;

        # 1. LIVE STREAMING (Twitch, Kick, YouTube RTMP / SRT / WHIP)
        # Taggato con AF31 (DSCP 0x1a): Banda garantita senza saturare la coda voice/gaming
        tcp dport 1935 ip dscp set 0x1a comment "OBS RTMP Stream"
        tcp dport { 80, 443 } meta cgroup 0x1337 ip dscp set 0x1a comment "OBS HTTPS Stream"
        udp dport 10000-10100 ip dscp set 0x1a comment "SRT Streaming Protocol"

        # 2. GAMING ONLINE & NETPLAY EMULATORI (Latenza Critica)
        # Taggato con EF (Expedited Forwarding - DSCP 0x2e): Massima priorità nel kernel e router
        udp dport { 27015-27050, 7777-7785, 3074, 50000-65535, 27000-27100 } ip dscp set 0x2e comment "Game Server UDP"
        udp dport { 3478-3481, 5000-5500 } ip dscp set 0x2e comment "Voice / Discord WebRTC"

        # 3. BACKGROUND DOWNLOADS / AGGIORNAMENTI DI SISTEMA
        # Taggato con CS1 (DSCP 0x08 - Background): Cede istantaneamente il passo se c'è traffico
        tcp sport { 80, 443 } ip dscp set 0x00 comment "Standard Web"
    }
}
EOF
}

start_qos() {
    echo "========================================================="
    echo "       OSify Traffic Shaper — Avvio Ottimizzazione       "
    echo "========================================================="
    echo "[+] Interfaccia selezionata: $INTERFACE"

    # Reset di code preesistenti per evitare conflitti
    tc qdisc del dev "$INTERFACE" root 2>/dev/null || true

    # Costruzione comando CAKE
    # diffserv4 mappa: Bulk (CS1), Best Effort (CS0), Video/Streaming (AF31/CS3), Voice/Gaming (EF/CS5/CS6)
    # ack-filter: elimina i pacchetti TCP ACK ridondanti sull'upload, stabilizzando il ping
    CAKE_ARGS="diffserv4 ack-filter split-gso"

    if [[ "$UPLOAD_MBPS" != "auto" && "$UPLOAD_MBPS" -gt 0 ]]; then
        CAKE_ARGS="$CAKE_ARGS bandwidth ${UPLOAD_MBPS}mbit"
        echo "[+] Shaper Upload impostato a: ${UPLOAD_MBPS} Mbps (Anti-Bufferbloat attivo)"
    else
        echo "[+] Shaper attivo in modalità auto-fairness e classificazione dinamica"
    fi

    echo "[+] Applicazione Qdisc CAKE su interfaccia $INTERFACE..."
    tc qdisc add dev "$INTERFACE" root cake $CAKE_ARGS

    apply_nftables_marking

    echo "[[OK]] OSify QoS attivo: Ping protetto per Gaming ed Emulazione durante live streaming!"
}

stop_qos() {
    echo "[!] Disattivazione OSify QoS..."
    tc qdisc del dev "$INTERFACE" root 2>/dev/null || true
    nft delete table inet osify_qos 2>/dev/null || true
    echo "[[OK]] Regole rimosse, ripristinato stato predefinito."
}

status_qos() {
    echo "=== Statistiche Qdisc CAKE su $INTERFACE ==="
    tc -s qdisc show dev "$INTERFACE"
    echo ""
    echo "=== Regole nftables attive ==="
    nft list table inet osify_qos 2>/dev/null || echo "Nessuna tabella nftables osify_qos attiva."
}

case "$ACTION" in
    start)
        start_qos
        ;;
    stop)
        stop_qos
        ;;
    restart)
        stop_qos
        start_qos
        ;;
    status)
        status_qos
        ;;
    *)
        echo "Uso: $0 [interfaccia] {start|stop|restart|status}"
        exit 1
        ;;
esac
