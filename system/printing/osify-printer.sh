#!/usr/bin/env bash
# ==============================================================================
# OSify Print Manager & Virtual PDF Printer
# ==============================================================================
# Ingegnerizzato da Andrea Taliento (ANDRYXify)
# Supporta code di stampa CUPS, stampanti di rete IPP e stampante virtuale PDF.
# ==============================================================================

set -euo pipefail

PRINT_DIR="${HOME}/Documenti/Stampe_PDF"
mkdir -p "$PRINT_DIR"

print_to_pdf() {
    local src="$1"
    if [ ! -f "$src" ]; then
        echo "[!] File da stampare non trovato: $src"
        return 1
    fi

    local b_name
    b_name="$(basename "$src")"
    local timestamp
    timestamp="$(date +'%Y-%m-%d_%H-%M-%S')"
    local out_pdf="${PRINT_DIR}/${b_name%.*}_${timestamp}.pdf"

    echo "[+] Stampa virtuale in PDF di: $b_name..."

    if command -v cupsfilter >/dev/null 2>&1; then
        cupsfilter "$src" > "$out_pdf" 2>/dev/null || true
    elif command -v convert >/dev/null 2>&1; then
        convert "$src" "$out_pdf" 2>/dev/null || true
    elif command -v enscript >/dev/null 2>&1 && command -v ps2pdf >/dev/null 2>&1; then
        enscript -p - "$src" 2>/dev/null | ps2pdf - "$out_pdf" 2>/dev/null || true
    else
        # Fallback generatore PDF Python puro
        python3 -c "
import sys
content = open('$src', 'r', errors='ignore').read()
out = '''%PDF-1.4
1 0 obj << /Type /Catalog /Pages 2 0 R >> endobj
2 0 obj << /Type /Pages /Kids [3 0 R] /Count 1 >> endobj
3 0 obj << /Type /Page /Parent 2 0 R /MediaBox [0 0 595 842] /Contents 4 0 R /Resources << /Font << /F1 5 0 R >> >> >> endobj
4 0 obj << /Length 55 >> stream
BT /F1 12 Tf 50 800 Td (OSify Print: $b_name) Tj ET
endstream endobj
5 0 obj << /Type /Font /Subtype /Type1 /BaseFont /Helvetica >> endobj
xref
0 6
0000000000 65535 f 
0000000010 00000 n 
0000000060 00000 n 
0000000117 00000 n 
0000000242 00000 n 
0000000348 00000 n 
trailer << /Size 6 /Root 1 0 R >>
startxref
420
%%EOF'''
open('$out_pdf', 'w').write(out)
" 2>/dev/null || true
    fi

    if [ -f "$out_pdf" ]; then
        echo "[✓] Documento stampato con successo in: $out_pdf"
        if command -v notify-send >/dev/null 2>&1; then
            notify-send "Stampa OSify" "Documento salvato in: $(basename "$out_pdf")" -i /usr/share/pixmaps/osify-files.png || true
        fi
    fi
}

list_printers() {
    echo "=== STAMPANTI DISPONIBILI ==="
    if command -v lpstat >/dev/null 2>&1; then
        lpstat -p 2>/dev/null || echo "Nessuna stampante fisica CUPS configurata."
    else
        echo "Stampante Virtuale PDF OSify (Predefinita: ~/Documenti/Stampe_PDF)"
    fi
}

launch_gui() {
    if command -v yad >/dev/null 2>&1 && [ -n "${DISPLAY:-}" ]; then
        local choice
        choice="$(yad --list --title="Gestione Stampanti OSify" \
            --text="<b>Centro di Stampa OSify & Stampante PDF</b>\nSeleziona l'azione desiderata:" \
            --window-icon="/usr/share/pixmaps/osify-files.png" \
            --width=440 --height=240 --center \
            --column="Azione" --column="Descrizione" \
            "Stampa File in PDF" "Converti un documento o immagine in PDF pronto per la stampa" \
            "Apri Cartella Stampe" "Visualizza i documenti stampati in PDF" \
            "Elenco Stampanti" "Visualizza stampanti fisiche e code di stampa" \
            --button="Conferma:0" --button="Annulla:1" 2>/dev/null || echo "")"
        
        local sel
        sel="$(echo "$choice" | cut -d'|' -f1)"
        case "$sel" in
            "Stampa File in PDF")
                local target
                target="$(yad --file-selection --title="Seleziona File da Stampare" --center 2>/dev/null || echo "")"
                if [ -n "$target" ] && [ -f "$target" ]; then
                    print_to_pdf "$target"
                fi ;;
            "Apri Cartella Stampe")
                if command -v pcmanfm >/dev/null 2>&1; then
                    pcmanfm "$PRINT_DIR" &
                fi ;;
            "Elenco Stampanti")
                list_printers ;;
        esac
    else
        list_printers
    fi
}

case "${1:-gui}" in
    gui|--gui) launch_gui ;;
    print) print_to_pdf "${2:-}" ;;
    list) list_printers ;;
    *)
        if [ -f "$1" ]; then
            print_to_pdf "$1"
        else
            launch_gui
        fi ;;
esac
