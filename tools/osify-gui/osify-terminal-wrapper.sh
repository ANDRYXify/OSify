#!/bin/sh
# ==============================================================================
# OSify Universal Terminal Dispatcher & Emulator Wrapper
# ==============================================================================
# Ingegnerizzato da Andrea Taliento (ANDRYXify)
# Risolve in modo deterministico e universale qualsiasi chiamata a 'terminal'
# da file .desktop, scorciatoie da tastiera, dock e script di sistema.
# Supporta: Sakura, Xterm, LXTerminal, URXVT, RXVT, ST e fallback console.
# ==============================================================================

# Parsing parametri standard (-geometry, -T, -title, -e)
TITLE="OSify Terminal"
GEOMETRY=""
COMMAND=""
USE_EXEC=0

while [ $# -gt 0 ]; do
    case "$1" in
        -T|-title|--title)
            TITLE="$2"
            shift 2
            ;;
        -geometry|--geometry)
            GEOMETRY="$2"
            shift 2
            ;;
        -e|--execute|-x)
            shift
            USE_EXEC=1
            COMMAND="$*"
            break
            ;;
        *)
            # Altri argomenti o comando diretto
            if [ $USE_EXEC -eq 0 ]; then
                USE_EXEC=1
                COMMAND="$*"
                break
            fi
            shift
            ;;
    esac
done

# Se nessun comando è specificato, esegui il terminale cyber con Fastfetch
if [ -z "$COMMAND" ]; then
    if [ -x /usr/bin/osify-terminal ]; then
        COMMAND="/usr/bin/osify-terminal"
    else
        COMMAND="/bin/sh -l"
    fi
fi

# 1. Rilevamento SAKURA (preinstallato nativo in SliTaz e ultraleggero VTE)
if command -v sakura >/dev/null 2>&1; then
    # Calcola righe e colonne da geometria tipo 95x28 o 75x20
    COLS=""
    ROWS=""
    if [ -n "$GEOMETRY" ]; then
        COLS=$(echo "$GEOMETRY" | sed -E 's/([0-9]+)x([0-9]+).*/\1/')
        ROWS=$(echo "$GEOMETRY" | sed -E 's/([0-9]+)x([0-9]+).*/\2/')
    fi
    SAKURA_ARGS="-t \"$TITLE\""
    [ -n "$COLS" ] && SAKURA_ARGS="$SAKURA_ARGS -c $COLS"
    [ -n "$ROWS" ] && SAKURA_ARGS="$SAKURA_ARGS -r $ROWS"
    
    exec /bin/sh -c "sakura $SAKURA_ARGS -x \"$COMMAND\""
fi

# 2. Rilevamento XTERM (garantito nativo in OSify)
if command -v xterm >/dev/null 2>&1; then
    XTERM_GEOM="${GEOMETRY:-80x24}"
    exec xterm \
        -title "$TITLE" \
        -geometry "$XTERM_GEOM" \
        -bg "#0b0d14" \
        -fg "#38bdf8" \
        -cr "#10b981" \
        +sb \
        -e /bin/sh -c "$COMMAND"
fi

# 3. Rilevamento LXTERMINAL
if command -v lxterminal >/dev/null 2>&1; then
    exec lxterminal --title="$TITLE" --geometry="${GEOMETRY:-80x24}" -e /bin/sh -c "$COMMAND"
fi

# 4. Rilevamento URXVT / RXVT
if command -v urxvt >/dev/null 2>&1; then
    exec urxvt -title "$TITLE" -geometry "${GEOMETRY:-80x24}" -bg "#0b0d14" -fg "#38bdf8" -e /bin/sh -c "$COMMAND"
elif command -v rxvt >/dev/null 2>&1; then
    exec rxvt -title "$TITLE" -geometry "${GEOMETRY:-80x24}" -bg "#0b0d14" -fg "#38bdf8" -e /bin/sh -c "$COMMAND"
fi

# Fallback headless / TTY diretto
exec /bin/sh -c "$COMMAND"
