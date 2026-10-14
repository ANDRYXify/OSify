#!/usr/bin/env bash
# ==============================================================================
# OSify Binary Inspector — Deep Architectural & ABI Radiography
# ==============================================================================
# Esegue un'analisi approfondita su qualsiasi file per determinare:
# - Formato contenitore (ELF, PE, Mach-O, WASM, JVM, ZIP/APK, DOS MZ, Script)
# - Architettura target (x86_64, i686, ARM, AArch64, RISC-V, Bytecode)
# - Sottosistema grafico / ABI richiesta (Win32, POSIX, WASI, ART, JVM)
# - Compatibilita' con l'hardware host e strategia di esecuzione pianificata da OSify
# ==============================================================================

set -euo pipefail

TARGET="${1:-}"

if [[ -z "$TARGET" || (! -f "$TARGET" && ! -d "$TARGET") ]]; then
    echo "Uso: osify-inspect <file-o-bundle>"
    exit 1
fi

echo "========================================================="
echo "       OSify Universal Binary Radiography                "
echo "========================================================="
echo "File Target        : $(basename "$TARGET")"
echo "Percorso Completo  : $(cd "$(dirname "$TARGET")" && pwd)/$(basename "$TARGET")"
echo "Dimensione         : $(du -h "$TARGET" 2>/dev/null | awk '{print $1}')"

HOST_ARCH="$(uname -m)"
echo "Architettura Host  : $HOST_ARCH"
echo "---------------------------------------------------------"

FORMAT="Sconosciuto"
TARGET_ISA="N/A"
EXEC_STRATEGY="Esecuzione standard di sistema"
RUNNER_USED="Nativo"

# Lettura Magic Bytes
HEX_MAGIC=""
if command -v od >/dev/null 2>&1; then
    HEX_MAGIC=$(od -An -N 4 -t x1 "$TARGET" 2>/dev/null | tr -d ' \n' || echo "")
fi

if [[ "$HEX_MAGIC" =~ ^4d5a ]]; then
    PE_OFFSET=$(od -An -j 60 -N 4 -t u4 "$TARGET" 2>/dev/null | tr -d ' ' || echo "0")
    if [[ "$PE_OFFSET" =~ ^[0-9]+$ ]] && [[ "$PE_OFFSET" -ge 64 ]]; then
        SIG=$(dd if="$TARGET" bs=1 skip="$PE_OFFSET" count=2 2>/dev/null || echo "")
        if [[ "$SIG" == "PE" ]]; then
            # Lettura Machine Type PE all'offset PE_OFFSET + 4
            PE_MACHINE=$(od -An -j "$((PE_OFFSET + 4))" -N 2 -t x2 "$TARGET" 2>/dev/null | tr -d ' ' || echo "")
            if [[ "$PE_MACHINE" == "8664" ]]; then
                FORMAT="Windows Portable Executable 64-bit (PE32+)"
                TARGET_ISA="x86_64"
            elif [[ "$PE_MACHINE" == "014c" ]]; then
                FORMAT="Windows Portable Executable 32-bit (PE32)"
                TARGET_ISA="i386 / i686"
            else
                FORMAT="Windows Portable Executable (PE)"
                TARGET_ISA="x86 Compatibile"
            fi
            EXEC_STRATEGY="Wine 32/64 + WineD3D (Vintage) oppure Proton-GE + DXVK + Fsync (Modern)"
            RUNNER_USED="uem/runners/osify-pe-runner.sh"
        fi
    fi
    if [[ "$FORMAT" == "Sconosciuto" ]]; then
        FORMAT="MS-DOS Executable a 16-bit (Real Mode MZ)"
        TARGET_ISA="x86 16-bit (Real Mode / 8086)"
        EXEC_STRATEGY="Emulazione trasparente hardware DOS (dosbox-staging / dosemu2)"
        RUNNER_USED="uem/runners/osify-dos-runner.sh"
    fi
elif [[ "$HEX_MAGIC" =~ ^7f454c46 ]]; then
    ELF_CLASS=$(od -An -j 4 -N 1 -t u1 "$TARGET" 2>/dev/null | tr -d ' ' || echo "0")
    ELF_MACHINE=$(od -An -j 18 -N 2 -t x2 "$TARGET" 2>/dev/null | tr -d ' ' || echo "")
    
    case "$ELF_MACHINE" in
        "003e") TARGET_ISA="x86_64" ;;
        "0003") TARGET_ISA="i386 / i686" ;;
        "00b7") TARGET_ISA="AArch64 (ARM64)" ;;
        "0028") TARGET_ISA="ARM 32-bit (armv7l)" ;;
        "00f3") TARGET_ISA="RISC-V 64-bit" ;;
        "0014"|"0015") TARGET_ISA="PowerPC (PPC32/PPC64)" ;;
        "0008") TARGET_ISA="MIPS" ;;
        *) TARGET_ISA="ELF Machine ID $ELF_MACHINE" ;;
    esac

    if [[ "$ELF_CLASS" -eq 2 ]]; then
        FORMAT="Linux Executable & Linkable Format 64-bit (ELF64)"
    else
        FORMAT="Linux Executable & Linkable Format 32-bit (ELF32)"
    fi

    if [[ "$HOST_ARCH" == "x86_64" && "$TARGET_ISA" == "x86_64" ]] || \
       [[ "$HOST_ARCH" =~ ^(i686|i386)$ && "$TARGET_ISA" =~ i386 ]] || \
       [[ "$HOST_ARCH" =~ ^(aarch64|arm64)$ && "$TARGET_ISA" =~ AArch64 ]]; then
        EXEC_STRATEGY="Esecuzione Nativa Immediata a Zero Overhead"
        RUNNER_USED="Kernel Nativo (ELF Loader)"
    else
        EXEC_STRATEGY="Dynamic Binary Recompilation (Box64/Box86 JIT) con forwarding librerie o QEMU-Static"
        RUNNER_USED="uem/runners/osify-cross-runner.sh"
    fi
elif [[ "$HEX_MAGIC" =~ ^(feedface|feedfacf|cffaedfe|cefaedfe) ]]; then
    FORMAT="Apple Darwin / macOS Mach-O Executable"
    TARGET_ISA="Mach-O (Darwin ABI)"
    EXEC_STRATEGY="Translation Layer Darwin / Mach Kernel (Darling)"
    RUNNER_USED="uem/runners/osify-macho-runner.sh"
elif [[ "$HEX_MAGIC" =~ ^cafebabe ]]; then
    VER_BYTE=$(od -An -j 4 -N 4 -t x1 "$TARGET" 2>/dev/null | tr -d ' ' || echo "")
    if [[ "$VER_BYTE" =~ ^0000 ]]; then
        FORMAT="Java Virtual Machine Compiled Bytecode (.class)"
        TARGET_ISA="JVM Bytecode"
        EXEC_STRATEGY="OpenJDK JVM JIT Compiler (HotSpot)"
        RUNNER_USED="uem/runners/osify-java-runner.sh"
    else
        FORMAT="Apple macOS Mach-O Fat / Universal Binary"
        TARGET_ISA="Multi-Arch (x86_64 + ARM64)"
        EXEC_STRATEGY="Translation Layer Darwin / Mach Kernel (Darling)"
        RUNNER_USED="uem/runners/osify-macho-runner.sh"
    fi
elif [[ "$HEX_MAGIC" =~ ^0061736d ]]; then
    FORMAT="WebAssembly Standalone Binary (WASM)"
    TARGET_ISA="Wasm Bytecode"
    EXEC_STRATEGY="WebAssembly System Interface (Wasmtime / Wasmer / Node WASI)"
    RUNNER_USED="uem/runners/osify-wasm-runner.sh"
elif [[ "$HEX_MAGIC" =~ ^504b0304 ]]; then
    if [[ "$TARGET" =~ \.apk$ ]] || (command -v unzip >/dev/null 2>&1 && unzip -l "$TARGET" 2>/dev/null | grep -q "AndroidManifest.xml"); then
        FORMAT="Android Application Package (APK)"
        TARGET_ISA="DEX Bytecode + NDK Native Libs"
        EXEC_STRATEGY="Waydroid Container LXC isolato con DRI3 GPU Hardware Acceleration"
        RUNNER_USED="uem/runners/osify-apk-runner.sh"
    elif [[ "$TARGET" =~ \.ipa$ ]] || (command -v unzip >/dev/null 2>&1 && unzip -l "$TARGET" 2>/dev/null | grep -qE "Payload/[^/]+\.app"); then
        FORMAT="Apple iOS Application Package (IPA)"
        TARGET_ISA="Mach-O (ARM64 / ARMv7 / x86_64 Simulator)"
        EXEC_STRATEGY="Analisi FairPlay DRM -> touchHLE (iOS 32-bit legacy) / Darling Bridge (Simulator) / Fallback guidato APK Android"
        RUNNER_USED="uem/runners/osify-ipa-runner.sh"
    elif [[ "$TARGET" =~ \.jar$ ]] || (command -v unzip >/dev/null 2>&1 && unzip -l "$TARGET" 2>/dev/null | grep -q "META-INF/MANIFEST.MF"); then
        FORMAT="Java Executable Archive (JAR)"
        TARGET_ISA="JVM Bytecode Package"
        EXEC_STRATEGY="OpenJDK Runtime Environment"
        RUNNER_USED="uem/runners/osify-java-runner.sh"
    fi
fi

echo "Formato Rilevato   : $FORMAT"
echo "ISA Architettura   : $TARGET_ISA"
echo "Runner Invocato    : $RUNNER_USED"
echo "Strategia Runtime  : $EXEC_STRATEGY"
echo "========================================================="
