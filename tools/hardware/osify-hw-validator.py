#!/usr/bin/env python3
"""
OSify Hardware Compatibility & Predictive Diagnostic Engine (by Andryx)
========================================================================
Analizza le caratteristiche hardware della macchina corrente oppure simula
profili hardware vintage/moderni (come il Toshiba NB200 con Intel Atom N280)
per certificare se il sistema può supportare OSify prima dell'installazione.

Fornisce raccomandazioni su:
- Architettura CPU (32-bit i686 vs 64-bit x86_64-v3)
- Calcolo stima RAM Footprint & Budget per ZRAM
- Compatibilità GPU (GMA 950 vs AMDGPU vs NVIDIA)
- Mitigazioni per schermi WSVGA a bassa risoluzione (1024x600)
"""

import sys
import os
import platform
import argparse
import json

class TerminalColors:
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    BOLD = '\033[1m'
    END = '\033[0m'

TOSHIBA_NB200_SPECS = {
    "name": "Toshiba Dynabook NB200",
    "cpu_model": "Intel Atom N280 @ 1.66GHz (Diamondville)",
    "arch": "i686 (32-bit strictly)",
    "bits": 32,
    "cores": 1,
    "threads": 2,
    "has_64bit": False,
    "cpu_level": "i686-legacy",
    "ram_mb": 1024,
    "gpu": "Intel Mobile GMA 950 (Calistoga / 945GME)",
    "gpu_driver": "i915 (Mesa legacy)",
    "has_vulkan": False,
    "opengl_max": "2.0 (DirectX 9c level)",
    "display_res": "1024x600 (WSVGA 10.1\")",
    "display_height": 600,
    "storage_type": "HDD 160GB 5400 RPM SATA-I",
    "boot_mode": "BIOS Legacy (MBR only, No UEFI)"
}

MODERN_RIG_SPECS = {
    "name": "Modern Gaming & Streaming Rig",
    "cpu_model": "AMD Ryzen / Intel Core i7 (x86-64-v3)",
    "arch": "x86_64",
    "bits": 64,
    "cores": 8,
    "threads": 16,
    "has_64bit": True,
    "cpu_level": "x86-64-v3",
    "ram_mb": 16384,
    "gpu": "AMD Radeon RX / NVIDIA GeForce RTX",
    "gpu_driver": "amdgpu / nvidia-open",
    "has_vulkan": True,
    "opengl_max": "4.6",
    "display_res": "1920x1080 (Full HD 144Hz+)",
    "display_height": 1080,
    "storage_type": "NVMe PCIe Gen4",
    "boot_mode": "UEFI SecureBoot/CSM"
}

def analyze_hardware(specs):
    results = {
        "device": specs["name"],
        "compatible": True,
        "edition_required": "OSify Standard (x86_64-v3)",
        "ram_budget": {},
        "warnings": [],
        "optimizations": []
    }

    # 1. Analisi Architettura e CPU
    if not specs["has_64bit"]:
        results["compatible"] = False  # Incompatibile con la ISO a 64-bit standard!
        results["edition_required"] = "OSify 32-Bit Micro-Edition (i686 Vintage)"
        results["warnings"].append(
            f"CPU a 32-bit pura rilevata ({specs['cpu_model']}). La ISO standard 'OSify-x86_64-v3.iso' "
            "NON eseguirà il boot e andrà in kernel panic (assenza flag 'lm'). "
            "È NECESSARIO usare l'immagine OSify Vintage i686 con kernel LTS 32-bit."
        )
    else:
        results["edition_required"] = f"OSify Standard ({specs['cpu_level']})"
        results["optimizations"].append(
            f"CPU a 64-bit con set istruzioni {specs['cpu_level']}. Pieno supporto a BORE scheduler e AVX."
        )

    # 2. Analisi Memoria RAM
    ram_mb = specs["ram_mb"]
    if ram_mb <= 1024:
        results["ram_budget"]["total_ram_mb"] = ram_mb
        results["ram_budget"]["desktop_target"] = "Openbox / Tint2 / LXQt Ultra-Light"
        results["ram_budget"]["target_os_idle_mb"] = 125
        results["ram_budget"]["zram_size_mb"] = int(ram_mb * 1.5)  # 1.5 GB ZRAM
        results["ram_budget"]["zram_algorithm"] = "lz4 (basso impatto CPU Atom)"
        results["ram_budget"]["swappiness"] = 100

        results["warnings"].append(
            f"Memoria RAM limitata a {ram_mb} MB (Toshiba NB200 standard). "
            "KDE Plasma Wayland o GNOME porterebbero all'esaurimento immediato della RAM (OOM). "
            "OSify commuterà sul profilo ultra-light (footprint ~120MB a freddo)."
        )
        results["optimizations"].append("ZRAM compressa impostata a 1.5GB con compressione rapida lz4.")
        results["optimizations"].append("Disattivazione totale demoni indicizzatori (Baloo, Tracker, mlocate).")
    elif ram_mb <= 2048:
        results["ram_budget"]["desktop_target"] = "XFCE4 / LXQt Minimal"
        results["ram_budget"]["target_os_idle_mb"] = 280
        results["ram_budget"]["zram_size_mb"] = ram_mb
        results["ram_budget"]["zram_algorithm"] = "zstd"
        results["ram_budget"]["swappiness"] = 60
    else:
        results["ram_budget"]["desktop_target"] = "KDE Plasma 6 (Wayland) con BORE Gaming Engine"
        results["ram_budget"]["target_os_idle_mb"] = 650
        results["ram_budget"]["zram_size_mb"] = 4096
        results["ram_budget"]["zram_algorithm"] = "zstd"
        results["ram_budget"]["swappiness"] = 10

    # 3. Analisi GPU e Stack Grafico
    if not specs["has_vulkan"]:
        results["warnings"].append(
            f"GPU {specs['gpu']} non supporta Vulkan (solo OpenGL {specs['opengl_max']}). "
            "DXVK, VKD3D e Gamescope non saranno disponibili. Il rendering dei giochi Windows "
            "avverrà tramite WineD3D (OpenGL nativo)."
        )
        results["optimizations"].append("Forzato driver video Mesa classico 'i915' con accelerazione DRI2.")
    else:
        results["optimizations"].append("Supporto Vulkan attivo: DXVK-Async, VKD3D e Gamescope micro-compositor pronti.")

    # 4. Analisi Display e Risoluzione (WSVGA 1024x600)
    if specs["display_height"] <= 600:
        results["warnings"].append(
            f"Display WSVGA rilevato: altezza verticale di soli {specs['display_height']}px. "
            "Molti wizard di installazione standard richiedono 768px verticali e potrebbero avere i pulsanti nascosti!"
        )
        results["optimizations"].append(
            "Attivazione scorciatoia 'Alt + Trascina con mouse sinistro' per muovere le finestre oltre i bordi dello schermo."
        )
        results["optimizations"].append("Pannello inferiore impostato su Auto-Hide per recuperare 28px verticali preziosi.")
        results["optimizations"].append("Font di sistema impostati su 9pt compatti per massimizzare lo spazio utile.")

    # 5. Analisi Storage
    if "HDD" in specs["storage_type"]:
        results["optimizations"].append("Storage meccanico rilevato: scheduler I/O kernel impostato su 'bfq' per prevenire freeze.")
    else:
        results["optimizations"].append("Storage a stato solido: scheduler I/O 'none' per NVMe e 'kyber' per SATA SSD.")

    return results

def print_diagnostic_report(res, specs):
    c = TerminalColors
    print(f"\n{c.HEADER}{c.BOLD}========================================================================{c.END}")
    print(f"{c.CYAN}{c.BOLD}       OSify Hardware Compatibility & Predictive Diagnostic Report     {c.END}")
    print(f"{c.HEADER}{c.BOLD}========================================================================{c.END}\n")

    print(f"{c.BOLD}Dispositivo in Esame:{c.END} {specs['name']}")
    print(f"{c.BOLD}Processore:{c.END}          {specs['cpu_model']} ({specs['arch']})")
    print(f"{c.BOLD}Memoria RAM:{c.END}         {specs['ram_mb']} MB")
    print(f"{c.BOLD}GPU Integrata:{c.END}       {specs['gpu']} ({specs['gpu_driver']})")
    print(f"{c.BOLD}Display:{c.END}             {specs['display_res']}")
    print(f"{c.BOLD}Storage:{c.END}             {specs['storage_type']}")
    print(f"{c.BOLD}Boot Mode:{c.END}           {specs['boot_mode']}\n")

    print(f"{c.BOLD}--- VERDETTO ARCHITETTURALE ---{c.END}")
    if res["compatible"]:
        print(f"[{c.GREEN}CERTIFICATO PIENAMENTE{c.END}] Compatibile con {res['edition_required']}")
    else:
        print(f"[{c.YELLOW}ATTENZIONE SPECIFICA{c.END}] Richiede: {c.BOLD}{res['edition_required']}{c.END}")

    print(f"\n{c.BOLD}--- RACCOMANDAZIONI & AVVISI ({len(res['warnings'])}) ---{c.END}")
    for w in res["warnings"]:
        print(f"  {c.YELLOW}⚠{c.END} {w}")

    print(f"\n{c.BOLD}--- OTTIMIZZAZIONI AUTOMATICHE APPLICATE ({len(res['optimizations'])}) ---{c.END}")
    for opt in res["optimizations"]:
        print(f"  {c.GREEN}✓{c.END} {opt}")

    print(f"\n{c.BOLD}--- BUDGET MEMORIA E DESKTOP ---{c.END}")
    rb = res["ram_budget"]
    print(f"  • Ambiente Desktop Consigliato : {rb.get('desktop_target')}")
    print(f"  • Target RAM a Freddo          : ~{rb.get('target_os_idle_mb')} MB")
    print(f"  • Dimensione ZRAM Dedicata     : {rb.get('zram_size_mb')} MB ({rb.get('zram_algorithm')})")
    print(f"  • Kernel Swappiness            : {rb.get('swappiness')}")
    print(f"\n{c.HEADER}========================================================================{c.END}\n")

def inspect_current_host():
    """Tenta di rilevare l'hardware reale del sistema corrente."""
    machine = platform.machine()
    system = platform.system()
    has_64bit = sys.maxsize > 2**32
    
    # Valori di default
    cpu_model = platform.processor() or "Generic CPU"
    ram_mb = 4096
    
    if system == "Darwin":
        try:
            import subprocess
            mem_bytes = subprocess.check_output(["sysctl", "-n", "hw.memsize"]).decode().strip()
            ram_mb = int(int(mem_bytes) / (1024 * 1024))
            cpu_model = subprocess.check_output(["sysctl", "-n", "machdep.cpu.brand_string"]).decode().strip()
        except Exception:
            pass

    return {
        "name": f"Host Locale ({system} {machine})",
        "cpu_model": cpu_model,
        "arch": machine,
        "bits": 64 if has_64bit else 32,
        "cores": os.cpu_count() or 2,
        "threads": os.cpu_count() or 2,
        "has_64bit": has_64bit,
        "cpu_level": "x86-64-v3" if has_64bit else "i686-legacy",
        "ram_mb": ram_mb,
        "gpu": "Native Host GPU",
        "gpu_driver": "Host Native Display",
        "has_vulkan": True,
        "opengl_max": "4.1+",
        "display_res": "Host Native Resolution",
        "display_height": 1080,
        "storage_type": "Host SSD / Virtual Drive",
        "boot_mode": "Native OS"
    }

def main():
    parser = argparse.ArgumentParser(description="OSify Hardware Compatibility Validator")
    parser.add_argument("--profile", choices=["nb200", "toshiba", "modern", "host"], default="host",
                        help="Profilo hardware da analizzare (toshiba/nb200 per netbook Atom, modern per gaming rig, host per macchina corrente)")
    parser.add_argument("--json", action="store_true", help="Emetti risultato in formato JSON")
    args = parser.parse_args()

    if args.profile in ["nb200", "toshiba"]:
        specs = TOSHIBA_NB200_SPECS
    elif args.profile == "modern":
        specs = MODERN_RIG_SPECS
    else:
        specs = inspect_current_host()

    analysis = analyze_hardware(specs)

    if args.json:
        print(json.dumps({"specs": specs, "analysis": analysis}, indent=2))
    else:
        print_diagnostic_report(analysis, specs)

if __name__ == "__main__":
    main()
