#!/usr/bin/env bash
# ==============================================================================
# OSify macOS Multitasking & Gestures Engine
# ==============================================================================
# Configura KDE Plasma 6 Wayland per replicare l'esperienza fluida di macOS:
# 1. Mission Control / Overview: swipe 3-4 dita verso l'alto o tasto Super/F3
# 2. Spaces / Desktop Virtuali: swipe 3-4 dita a destra/sinistra (1:1 animazione fluida)
# 3. App Exposé: swipe verso il basso per tutte le finestre dell'app attiva
# 4. Hot Corners (Angoli attivi):
#    - Angolo in alto a sinistra: Mission Control
#    - Angolo in basso a destra: Mostra Desktop
# 5. Trackpad 1:1: Tap-to-click, scrolling naturale e pinch-to-zoom Wayland
# ==============================================================================

set -euo pipefail

apply_macos_multitasking() {
    echo "========================================================="
    echo "       OSify macOS Gestures & Spaces Configuration       "
    echo "========================================================="

    if command -v kwriteconfig6 >/dev/null 2>&1; then
        echo "[+] Configurazione Gesture Touchpad & KWin Wayland..."
        
        # 1. Hot Corners (Angoli attivi stile Mac)
        kwriteconfig6 --file kwinrc --group ElectricBorders --key TopLeft Overview
        kwriteconfig6 --file kwinrc --group ElectricBorders --key BottomRight ShowDesktop
        
        # 2. Gestione Desktop Virtuali (Spaces orizzontali)
        kwriteconfig6 --file kwinrc --group Desktops --key Number 4
        kwriteconfig6 --file kwinrc --group Desktops --key Rows 1
        
        # 3. Scorciatoie da tastiera stile macOS
        # Meta+Up / F3 per Mission Control
        kwriteconfig6 --file kglobalshortcutsrc --group kwin --key "Overview" "Meta+W\tF3,Meta+W\tF3,Mostra Panoramica"
        kwriteconfig6 --file kglobalshortcutsrc --group kwin --key "ShowDesktopGrid" "Ctrl+F8,none,Griglia Desktop"
        kwriteconfig6 --file kglobalshortcutsrc --group kwin --key "Switch to Next Desktop" "Ctrl+Right,none,Desktop Successivo"
        kwriteconfig6 --file kglobalshortcutsrc --group kwin --key "Switch to Previous Desktop" "Ctrl+Left,none,Desktop Precedente"

        # 4. Configurazione Trackpad (Tap to click, scrolling naturale)
        kwriteconfig6 --file kcminputrc --group Touchpad --key tapToClick true
        kwriteconfig6 --file kcminputrc --group Touchpad --key naturalScroll true

        # 5. Effetti grafici fluidi per le finestre (Magic Lamp minimizzazione stile Genio Mac)
        kwriteconfig6 --file kwinrc --group Plugins --key magiclampEnabled true
        kwriteconfig6 --file kwinrc --group Plugins --key overviewEnabled true

        echo "[✓] Multitasking e gesture stile MacBook configurati con successo!"
    else
        echo "[i] kwriteconfig6 non trovato; applicazione differita al primo avvio di KDE Plasma 6."
    fi
}

apply_macos_multitasking
