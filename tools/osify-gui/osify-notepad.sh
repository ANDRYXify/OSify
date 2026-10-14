#!/usr/bin/env bash
# ==============================================================================
# OSify Notepad — Editor di Testo Grafico Leggero & Veloce
# ==============================================================================
# Ingegnerizzato da Andrea Taliento (ANDRYXify)
# ==============================================================================

set -euo pipefail

TARGET_FILE="${1:-}"

# 1. Se esiste un editor GTK nativo installato, usalo direttamente
for ed in leafpad mousepad featherpad geany beaver nano-gui; do
    if command -v "$ed" >/dev/null 2>&1 && [ -n "${DISPLAY:-}" ]; then
        exec "$ed" "$TARGET_FILE"
    fi
done

# 2. Editor grafico integrato con YAD
if command -v yad >/dev/null 2>&1 && [ -n "${DISPLAY:-}" ]; then
    TMP_F="/tmp/osify_note_$$.txt"
    if [ -n "$TARGET_FILE" ] && [ -f "$TARGET_FILE" ]; then
        cp "$TARGET_FILE" "$TMP_F"
        WIN_TITLE="OSify Note — $(basename "$TARGET_FILE")"
    else
        touch "$TMP_F"
        WIN_TITLE="OSify Note — Nuovo Documento"
    fi

    yad --text-info --title="$WIN_TITLE" \
        --filename="$TMP_F" --editable \
        --window-icon="/usr/share/pixmaps/osify-developer.png" \
        --width=640 --height=440 --center \
        --button="Salva:0" --button="Chiudi:1" >/dev/null 2>&1 || true

    if [ -n "$TARGET_FILE" ]; then
        if [ -w "$TARGET_FILE" ] || [ ! -e "$TARGET_FILE" ]; then
            cp "$TMP_F" "$TARGET_FILE" 2>/dev/null || sudo cp "$TMP_F" "$TARGET_FILE" 2>/dev/null || true
        fi
    fi
    rm -f "$TMP_F"
    exit 0
fi

# 3. Fallback su terminale e nano
if [ -n "${DISPLAY:-}" ]; then
    if command -v terminal >/dev/null 2>&1; then
        exec terminal -geometry 80x24 -T "Editor Testo" -e nano "$TARGET_FILE"
    elif command -v xterm >/dev/null 2>&1; then
        exec xterm -geometry 80x24 -T "Editor Testo" -e nano "$TARGET_FILE"
    fi
fi

exec nano "$TARGET_FILE"
