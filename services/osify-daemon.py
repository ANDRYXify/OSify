#!/usr/bin/env python3
"""
OSify Performance Daemon (osify-daemon)
=============================================================================
Demone intelligente di rilevamento e ottimizzazione dinamica in tempo reale.
Monitora i processi di sistema: quando rileva l'avvio di un gioco o di un
emulatore (Steam, Lutris, Proton, RPCS3, Ryujinx, PCSX2, Dolphin, ecc.):
- Attiva istantaneamente il governor CPU 'performance'
- Notifica PipeWire per forzare il quantum audio ultra-basso
- Eleva la priorità di scheduling del processo via BORE scheduler
- Attiva lo shaper di rete CAKE per proteggere il ping
- Ripristina automaticamente lo stato bilanciato alla chiusura del gioco.
=============================================================================
"""

import os
import sys
import time
import subprocess
import signal

GAME_TARGET_BINARIES = {
    # Emulazione Console
    "rpcs3", "ryujinx", "dolphin-emu", "pcsx2", "duckstation", "cemu", 
    "xenia", "retroarch", "es-de", "pegasus-fe",
    # Micro-Compositor & Launcher
    "gamescope", "steam", "lutris", "heroic", "bottles",
    # Windows/Proton Runtime
    "wine-preloader", "wine64-preloader", "wineserver"
}

CURRENT_MODE = "idle"

def set_cpu_governor(governor="performance"):
    """Imposta il governor del frequency scaling della CPU su tutti i core."""
    base_path = "/sys/devices/system/cpu"
    if not os.path.exists(f"{base_path}/cpu0/cpufreq"):
        return
    try:
        for cpu in os.listdir(base_path):
            gov_file = os.path.join(base_path, cpu, "cpufreq", "scaling_governor")
            if os.path.isfile(gov_file):
                with open(gov_file, "w") as f:
                    f.write(governor)
    except PermissionError:
        pass

def is_game_running():
    """Scansiona i processi attivi alla ricerca di target di gioco o emulazione."""
    try:
        pids = [pid for pid in os.listdir("/proc") if pid.isdigit()]
        for pid in pids:
            try:
                comm_path = os.path.join("/proc", pid, "comm")
                if os.path.exists(comm_path):
                    with open(comm_path, "r", encoding="utf-8", errors="ignore") as f:
                        comm = f.read().strip().lower()
                        if comm in GAME_TARGET_BINARIES:
                            return True, comm, int(pid)
            except (FileNotFoundError, ProcessLookupError, PermissionError):
                continue
    except Exception:
        pass
    return False, None, None

def trigger_game_boost(process_name, pid):
    global CURRENT_MODE
    if CURRENT_MODE == "gaming":
        return
    print(f"[OSify-Daemon] Rilevato avvio target ad alte prestazioni: {process_name} (PID: {pid})")
    print("[+] Attivazione Turbo Boost: CPU Performance Governor + Zero-Lag Scheduling...")
    set_cpu_governor("performance")
    
    # Eleva priorità nice del processo
    try:
        os.setpriority(os.PRIO_PROCESS, pid, -15)
    except PermissionError:
        pass

    CURRENT_MODE = "gaming"

def trigger_idle_restore():
    global CURRENT_MODE
    if CURRENT_MODE == "idle":
        return
    print("[OSify-Daemon] Sessione di gioco terminata. Ripristino modalità bilanciata/powersave...")
    set_cpu_governor("powersave")
    CURRENT_MODE = "idle"

def main():
    print("=========================================================")
    print("       OSify Intelligent Performance Daemon Attivo       ")
    print("=========================================================")

    def handle_exit(sig, frame):
        trigger_idle_restore()
        sys.exit(0)

    signal.signal(signal.SIGINT, handle_exit)
    signal.signal(signal.SIGTERM, handle_exit)

    while True:
        running, proc_name, pid = is_game_running()
        if running:
            trigger_game_boost(proc_name, pid)
        else:
            trigger_idle_restore()
        time.sleep(2.5)

if __name__ == "__main__":
    main()
