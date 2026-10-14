#!/usr/bin/env bash
# ==============================================================================
# OSify Universal PDF Viewer Wrapper
# ==============================================================================
# Ingegnerizzato da Andrea Taliento (ANDRYXify)
# ==============================================================================

set -euo pipefail

PDF_FILE="${1:-}"

if [ -z "$PDF_FILE" ] || [ ! -f "$PDF_FILE" ]; then
    echo "Uso: $0 <percorso_file.pdf>"
    exit 0
fi

# 1. Lettore PDF dedicato se installato
for v in epdfview mupdf xpdf evince atril qpdfview; do
    if command -v "$v" >/dev/null 2>&1 && [ -n "${DISPLAY:-}" ]; then
        exec "$v" "$PDF_FILE"
    fi
done

# 2. Rendering tramite Dillo o Browser se disponibile
if command -v dillo >/dev/null 2>&1 && [ -n "${DISPLAY:-}" ]; then
    ABS_PDF="$(readlink -f "$PDF_FILE" 2>/dev/null || echo "$PDF_FILE")"
    exec dillo "file://${ABS_PDF}"
fi

# 3. Estrazione testo su terminale con pdftotext se disponibile
if command -v pdftotext >/dev/null 2>&1; then
    TMP_TXT="/tmp/osify_pdf_$$.txt"
    pdftotext "$PDF_FILE" "$TMP_TXT"
    if [ -x /usr/bin/osify-notepad ]; then
        exec /usr/bin/osify-notepad "$TMP_TXT"
    else
        exec less "$TMP_TXT"
    fi
fi

echo "[!] Nessun lettore PDF grafico disponibile. Installa epdfview o dillo."
