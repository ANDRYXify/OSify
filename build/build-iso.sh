#!/usr/bin/env bash
# ==============================================================================
# OSify ISO Builder — Generatore di Immagini Avviabili x86-64-v3
# ==============================================================================
# Utilizza la toolchain mkarchiso integrando:
# 1. Repository compilati per microarchitettura x86-64-v3 (AVX2/FMA)
# 2. Kernel BORE a bassa latenza (linux-cachyos-bore)
# 3. Pacchetti KDE Plasma 6 Wayland pre-configurati
# 4. Moduli OSify (sysctl, QoS, PipeWire pro-audio, udev controller rules)
# ==============================================================================

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
WORK_DIR="/tmp/osify-iso-work"
OUT_DIR="$SCRIPT_DIR/out"
PROFILE_DIR="$SCRIPT_DIR/profile"

check_dependencies() {
    echo "[Build] Verifica dipendenze di compilazione ISO..."
    if ! command -v mkarchiso >/dev/null 2>&1; then
        echo "[!] 'mkarchiso' non trovato nel sistema host."
        echo "    Nota: L'immagine finale va generata su un ambiente Linux con archiso installato."
        echo "    Se ti trovi su macOS, puoi eseguire questa build dentro un container Docker o VM QEMU/KVM."
    fi
}

prepare_profile() {
    echo "[Build] Preparazione directory di profilo per sistema operativo autonomo..."
    mkdir -p "$PROFILE_DIR/airootfs/etc/sysctl.d"
    mkdir -p "$PROFILE_DIR/airootfs/etc/udev/rules.d"
    mkdir -p "$PROFILE_DIR/airootfs/etc/pipewire/pipewire.conf.d"
    mkdir -p "$PROFILE_DIR/airootfs/etc/modprobe.d"
    mkdir -p "$PROFILE_DIR/airootfs/etc/systemd/system/multi-user.target.wants"
    mkdir -p "$PROFILE_DIR/airootfs/etc/profile.d"
    mkdir -p "$PROFILE_DIR/airootfs/etc/skel"
    mkdir -p "$PROFILE_DIR/airootfs/usr/local/bin"
    mkdir -p "$PROFILE_DIR/airootfs/usr/share/applications"
    mkdir -p "$PROFILE_DIR/airootfs/opt/osify"
    mkdir -p "$OUT_DIR"

    # Copia delle configurazioni kernel OSify
    cp "$SCRIPT_DIR/../kernel/osify-sysctl.conf" "$PROFILE_DIR/airootfs/etc/sysctl.d/99-osify.conf"
    cp "$SCRIPT_DIR/../kernel/udev/99-osify-controllers.rules" "$PROFILE_DIR/airootfs/etc/udev/rules.d/"
    cp "$SCRIPT_DIR/../kernel/udev/99-osify-storage.rules" "$PROFILE_DIR/airootfs/etc/udev/rules.d/"
    cp "$SCRIPT_DIR/../kernel/legacy/99-osify-legacy-gpu.conf" "$PROFILE_DIR/airootfs/etc/modprobe.d/"
    cp "$SCRIPT_DIR/../audio/pipewire.conf.d/99-osify-proaudio.conf" "$PROFILE_DIR/airootfs/etc/pipewire/pipewire.conf.d/"

    # Copia dell'intero albero di sistema OSify in /opt/osify
    for d in audio desktop emulation etc kernel network presentation runtimes security services streaming system tools uem; do
        if [[ -d "$SCRIPT_DIR/../$d" ]]; then
            cp -r "$SCRIPT_DIR/../$d" "$PROFILE_DIR/airootfs/opt/osify/"
        fi
    done
    cp "$SCRIPT_DIR/../OSify.png" "$PROFILE_DIR/airootfs/opt/osify/" 2>/dev/null || true

    # Toolchain CLI & Binari di Sistema in /usr/local/bin
    cp "$SCRIPT_DIR/../tools/osify-ctl" "$PROFILE_DIR/airootfs/usr/local/bin/osify-ctl"
    cp "$SCRIPT_DIR/../network/osify-qos.sh" "$PROFILE_DIR/airootfs/usr/local/bin/osify-qos"
    cp "$SCRIPT_DIR/../audio/osify-audio-setup.sh" "$PROFILE_DIR/airootfs/usr/local/bin/osify-audio"
    cp "$SCRIPT_DIR/../kernel/legacy/osify-hardware-detect.sh" "$PROFILE_DIR/airootfs/usr/local/bin/osify-hwdetect"
    
    # Wrapper veloci per i comandi di sistema OSify
    cat << 'EOF' > "$PROFILE_DIR/airootfs/usr/local/bin/osify-session"
#!/usr/bin/env bash
exec /opt/osify/system/session/osify-session-start.sh "$@"
EOF

    cat << 'EOF' > "$PROFILE_DIR/airootfs/usr/local/bin/osify-update"
#!/usr/bin/env bash
exec /opt/osify/system/updater/osify-live-updater.sh "$@"
EOF

    cat << 'EOF' > "$PROFILE_DIR/airootfs/usr/local/bin/osify-shield"
#!/usr/bin/env bash
exec /opt/osify/security/shield/osify-shield.sh "$@"
EOF

    cat << 'EOF' > "$PROFILE_DIR/airootfs/usr/local/bin/osify-adblock"
#!/usr/bin/env bash
exec /opt/osify/security/adblock/osify-adblock.sh "$@"
EOF

    cat << 'EOF' > "$PROFILE_DIR/airootfs/usr/local/bin/osify-auth"
#!/usr/bin/env bash
exec python3 /opt/osify/security/auth/osify-auth-gateway.py "$@"
EOF

    cat << 'EOF' > "$PROFILE_DIR/airootfs/usr/local/bin/osify-tune"
#!/usr/bin/env bash
exec /opt/osify/system/autotune/osify-autotune.sh "$@"
EOF

    cat << 'EOF' > "$PROFILE_DIR/airootfs/usr/local/bin/osify-install"
#!/usr/bin/env bash
exec /opt/osify/system/installer/osify-disk-installer.sh "$@"
EOF

    cat << 'EOF' > "$PROFILE_DIR/airootfs/usr/local/bin/osify-power"
#!/usr/bin/env bash
exec /opt/osify/system/power/osify-power.sh "$@"
EOF

    cat << 'EOF' > "$PROFILE_DIR/airootfs/usr/local/bin/osify-first-boot"
#!/usr/bin/env bash
exec /opt/osify/system/session/osify-first-boot.sh "$@"
EOF

    cat << 'EOF' > "$PROFILE_DIR/airootfs/usr/local/bin/osify-exec"
#!/usr/bin/env bash
exec /opt/osify/uem/runners/osify-universal-dispatcher.sh "$@"
EOF

    cat << 'EOF' > "$PROFILE_DIR/airootfs/usr/local/bin/osify-automount"
#!/usr/bin/env bash
exec /opt/osify/system/storage/osify-automount.sh "$@"
EOF

    cat << 'EOF' > "$PROFILE_DIR/airootfs/usr/local/bin/osify-bluetooth"
#!/usr/bin/env bash
exec /opt/osify/network/osify-bluetooth.sh "$@"
EOF

    cat << 'EOF' > "$PROFILE_DIR/airootfs/usr/local/bin/osify-snapshot"
#!/usr/bin/env bash
exec /opt/osify/system/snapshot/osify-snapshot.sh "$@"
EOF

    cat << 'EOF' > "$PROFILE_DIR/airootfs/usr/local/bin/osify-net-check"
#!/usr/bin/env bash
exec /opt/osify/network/osify-net-check.sh "$@"
EOF

    # Registrazione Associazioni MIME UEM
    mkdir -p "$PROFILE_DIR/airootfs/usr/share/mime/packages" "$PROFILE_DIR/airootfs/usr/share/applications" "$PROFILE_DIR/airootfs/etc/xdg"
    cp "$SCRIPT_DIR/../desktop/mime/osify-uem.xml" "$PROFILE_DIR/airootfs/usr/share/mime/packages/osify-uem.xml" 2>/dev/null || true
    cp "$SCRIPT_DIR/../desktop/mime/mimeapps.list" "$PROFILE_DIR/airootfs/usr/share/applications/mimeapps.list" 2>/dev/null || true
    cp "$SCRIPT_DIR/../desktop/mime/mimeapps.list" "$PROFILE_DIR/airootfs/etc/xdg/mimeapps.list" 2>/dev/null || true
    cp "$SCRIPT_DIR/../desktop/applications/osify-uem-runner.desktop" "$PROFILE_DIR/airootfs/usr/share/applications/osify-uem-runner.desktop" 2>/dev/null || true
    cp "$SCRIPT_DIR/../desktop/applications/osify-bluetooth.desktop" "$PROFILE_DIR/airootfs/usr/share/applications/osify-bluetooth.desktop" 2>/dev/null || true

    chmod +x "$PROFILE_DIR/airootfs/usr/local/bin/"*

    # Configurazione Systemd: Timer Live Updater & Servizi Sicurezza
    cat << 'EOF' > "$PROFILE_DIR/airootfs/etc/systemd/system/osify-live-updater.service"
[Unit]
Description=OSify Live Zero-Reboot Git Hot-Updater
After=network-online.target
Wants=network-online.target

[Service]
Type=oneshot
ExecStart=/opt/osify/system/updater/osify-live-updater.sh check-update
EOF

    cat << 'EOF' > "$PROFILE_DIR/airootfs/etc/systemd/system/osify-live-updater.timer"
[Unit]
Description=Timer per Aggiornamenti Live Git OSify

[Timer]
OnBootSec=3min
OnUnitActiveSec=15min
Persistent=true

[Install]
WantedBy=timers.target
EOF

    cat << 'EOF' > "$PROFILE_DIR/airootfs/etc/systemd/system/osify-adblock.service"
[Unit]
Description=OSify AdShield DNS Sinkhole Service
After=network.target

[Service]
Type=oneshot
RemainAfterExit=yes
ExecStart=/opt/osify/security/adblock/osify-adblock.sh enable
ExecStop=/opt/osify/security/adblock/osify-adblock.sh disable

[Install]
WantedBy=multi-user.target
EOF

    cat << 'EOF' > "$PROFILE_DIR/airootfs/etc/systemd/system/osify-auth-gateway.service"
[Unit]
Description=OSify Smartphone WebAuthn & Passkey Authentication Gateway
After=network.target

[Service]
Type=simple
ExecStart=/usr/bin/python3 /opt/osify/security/auth/osify-auth-gateway.py start
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF

    # Polyglot Shell Hook per tutte le shell del sistema
    cat << 'EOF' > "$PROFILE_DIR/airootfs/etc/profile.d/osify-polyglot.sh"
if [ -f /opt/osify/tools/osify-shell/osify-polyglot-env.sh ]; then
    . /opt/osify/tools/osify-shell/osify-polyglot-env.sh
fi
EOF
    chmod +x "$PROFILE_DIR/airootfs/etc/profile.d/osify-polyglot.sh"

    # Copia pacchetti
    cp "$SCRIPT_DIR/packages.x86_64" "$PROFILE_DIR/packages.x86_64"

    echo "[[OK]] Profilo ISO autonomo OSify assemblato con successo."
}

build_iso() {
    prepare_profile
    check_dependencies
    
    if command -v mkarchiso >/dev/null 2>&1; then
        echo "[+] Avvio compilazione ISO tramite mkarchiso..."
        sudo mkarchiso -v -w "$WORK_DIR" -o "$OUT_DIR" "$PROFILE_DIR"
        echo "[[OK]] ISO generata con successo in: $OUT_DIR/"
    else
        echo "[i] Struttura profilo completata con successo. Per lanciare il build su Linux: 'sudo ./build-iso.sh'"
    fi
}

case "${1:-build}" in
    prepare)
        prepare_profile
        ;;
    build)
        build_iso
        ;;
    clean)
        rm -rf "$WORK_DIR" "$PROFILE_DIR"
        echo "[[OK]] Directory temporanee rimosse."
        ;;
    *)
        echo "Uso: $0 {build|prepare|clean}"
        exit 1
        ;;
esac
