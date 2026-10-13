#!/usr/bin/env bash
# ==============================================================================
# OSify Universal Polyglot Dispatcher — The Architecture-Breaking Execution Core
# ==============================================================================
# Analizza qualsiasi file binario o script tramite Magic Number Sniffing e
# instrada deterministica l'esecuzione al runner specializzato:
# - Windows PE (32/64-bit) -> osify-pe-runner.sh
# - MS-DOS 16-bit (MZ/COM) -> osify-dos-runner.sh
# - Apple Darwin Mach-O    -> osify-macho-runner.sh
# - Android APK / AAB      -> osify-apk-runner.sh
# - WebAssembly (WASI)     -> osify-wasm-runner.sh
# - Java Bytecode / JAR    -> osify-java-runner.sh
# - Cross-ISA ELF          -> osify-cross-runner.sh
# - Script polyglot        -> Interprete di sistema associato
# ==============================================================================

set -euo pipefail

TARGET="${1:-}"

if [[ -z "$TARGET" || (! -f "$TARGET" && ! -d "$TARGET") ]]; then
    echo "========================================================="
    echo "       OSify Universal Polyglot Dispatcher               "
    echo "========================================================="
    echo "Uso: osify-exec <qualsiasi-file-o-programma> [argomenti...]"
    echo ""
    echo "Esempi:"
    echo "  osify-exec setup.exe           (Esegue con Wine / Proton / DXVK)"
    echo "  osify-exec app.apk             (Esegue in Waydroid LXC)"
    echo "  osify-exec binary_arm64        (Esegue con Box64 / QEMU-Static)"
    echo "  osify-exec turbo_pascal.exe    (Esegue in ambiente MS-DOS reale)"
    echo "  osify-exec module.wasm         (Esegue via WASI engine)"
    echo "  osify-exec app.jar             (Esegue via OpenJDK)"
    exit 1
fi

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Se e' una cartella .app di macOS
if [[ -d "$TARGET" && "$TARGET" =~ \.app/?$ ]]; then
    exec "$SCRIPT_DIR/osify-macho-runner.sh" "$TARGET" "${@:2}"
fi

# Lettura primi 4 byte esadecimali
HEX_MAGIC=""
if command -v od >/dev/null 2>&1; then
    HEX_MAGIC=$(od -An -N 4 -t x1 "$TARGET" 2>/dev/null | tr -d ' \n' || echo "")
fi

# 1. Riconoscimento MS-DOS / Windows PE (Magic: 4d5a = "MZ")
if [[ "$HEX_MAGIC" =~ ^4d5a ]]; then
    PE_OFFSET=0
    if command -v od >/dev/null 2>&1; then
        PE_OFFSET=$(od -An -j 60 -N 4 -t u4 "$TARGET" 2>/dev/null | tr -d ' ' || echo "0")
    fi
    if [[ "$PE_OFFSET" =~ ^[0-9]+$ ]] && [[ "$PE_OFFSET" -ge 64 ]]; then
        SIG=$(dd if="$TARGET" bs=1 skip="$PE_OFFSET" count=2 2>/dev/null || echo "")
        if [[ "$SIG" == "PE" ]]; then
            exec "$SCRIPT_DIR/osify-pe-runner.sh" "$TARGET" "${@:2}"
        fi
    fi
    # Se non c'e' header PE, e' un binario MS-DOS a 16-bit
    exec "$SCRIPT_DIR/osify-dos-runner.sh" "$TARGET" "${@:2}"
fi

# 2. Riconoscimento WebAssembly (Magic: 0061736d = "\x00asm")
if [[ "$HEX_MAGIC" =~ ^0061736d ]]; then
    exec "$SCRIPT_DIR/osify-wasm-runner.sh" "$TARGET" "${@:2}"
fi

# 3. Riconoscimento Java / Mach-O Fat Binary (Magic: cafebabe)
if [[ "$HEX_MAGIC" =~ ^cafebabe ]]; then
    # Distinzione tra Java .class e Mach-O Fat Binary
    # In Java class i byte 4-7 contengono minor e major version (es. 00000034)
    VER_BYTE=$(od -An -j 4 -N 4 -t x1 "$TARGET" 2>/dev/null | tr -d ' ' || echo "")
    if [[ "$VER_BYTE" =~ ^0000 ]]; then
        exec "$SCRIPT_DIR/osify-java-runner.sh" "$TARGET" "${@:2}"
    else
        exec "$SCRIPT_DIR/osify-macho-runner.sh" "$TARGET" "${@:2}"
    fi
fi

# 4. Riconoscimento Mach-O Darwin (Magic: feedface, feedfacf, cffaedfe, cefaedfe)
if [[ "$HEX_MAGIC" =~ ^(feedface|feedfacf|cffaedfe|cefaedfe) ]]; then
    exec "$SCRIPT_DIR/osify-macho-runner.sh" "$TARGET" "${@:2}"
fi

# 5. Riconoscimento Archivi PKZIP (Magic: 504b0304 = "PK\x03\x04")
if [[ "$HEX_MAGIC" =~ ^504b0304 ]]; then
    if [[ "$TARGET" =~ \.apk$ ]] || (command -v unzip >/dev/null 2>&1 && unzip -l "$TARGET" 2>/dev/null | grep -q "AndroidManifest.xml"); then
        exec "$SCRIPT_DIR/osify-apk-runner.sh" "$TARGET" "${@:2}"
    elif [[ "$TARGET" =~ \.jar$ ]] || (command -v unzip >/dev/null 2>&1 && unzip -l "$TARGET" 2>/dev/null | grep -q "META-INF/MANIFEST.MF"); then
        exec "$SCRIPT_DIR/osify-java-runner.sh" "$TARGET" "${@:2}"
    fi
fi

# 6. Riconoscimento ELF Linux (Magic: 7f454c46 = "\x7fELF")
if [[ "$HEX_MAGIC" =~ ^7f454c46 ]]; then
    # Rilevamento architettura target del binario ELF
    TARGET_MACHINE=$(od -An -j 18 -N 2 -t x2 "$TARGET" 2>/dev/null | tr -d ' ' || echo "")
    HOST_ARCH="$(uname -m)"
    
    # 0003 = x86 (i386/i686), 003e = x86_64, 0028 = ARM, 00b7 = AArch64, 00f3 = RISC-V 64
    IS_NATIVE=0
    if [[ "$HOST_ARCH" == "x86_64" && "$TARGET_MACHINE" == "003e" ]]; then IS_NATIVE=1; fi
    if [[ "$HOST_ARCH" =~ ^(i686|i386)$ && "$TARGET_MACHINE" == "0003" ]]; then IS_NATIVE=1; fi
    if [[ "$HOST_ARCH" =~ ^(aarch64|arm64)$ && "$TARGET_MACHINE" == "00b7" ]]; then IS_NATIVE=1; fi

    if [[ "$IS_NATIVE" -eq 1 ]]; then
        chmod +x "$TARGET" 2>/dev/null || true
        exec "$TARGET" "${@:2}"
    else
        exec "$SCRIPT_DIR/osify-cross-runner.sh" "$TARGET" "${@:2}"
    fi
fi

# 7. Script interpretati con Shebang o estensioni note
FIRST_TWO=$(dd if="$TARGET" bs=1 count=2 2>/dev/null || echo "")
if [[ "$FIRST_TWO" == "#!" ]]; then
    chmod +x "$TARGET" 2>/dev/null || true
    exec "$TARGET" "${@:2}"
fi

case "$TARGET" in
    *.py)   exec python3 "$TARGET" "${@:2}" ;;
    *.js|*.mjs) exec node "$TARGET" "${@:2}" ;;
    *.sh|*.bash) exec bash "$TARGET" "${@:2}" ;;
    *.zsh)  exec zsh "$TARGET" "${@:2}" ;;
    *.lua)  exec lua "$TARGET" "${@:2}" ;;
    *.pl)   exec perl "$TARGET" "${@:2}" ;;
    *.rb)   exec ruby "$TARGET" "${@:2}" ;;
    *.com)  exec "$SCRIPT_DIR/osify-dos-runner.sh" "$TARGET" "${@:2}" ;;
esac

# Fallback finale: tentativo di esecuzione diretta
chmod +x "$TARGET" 2>/dev/null || true
exec "$TARGET" "${@:2}"
