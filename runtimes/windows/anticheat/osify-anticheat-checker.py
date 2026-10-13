#!/usr/bin/env python3
"""
OSify Anti-Cheat Intelligence & Compatibility Engine
=============================================================================
Analizza lo stato di compatibilità dei giochi Windows con sistemi anti-cheat.
Distingue tra:
1. Anti-Cheat supportati nativamente su Linux/Proton (EAC, BattlEye con modulo Proton).
2. Anti-Cheat Ring-0 proprietari a livello kernel (Riot Vanguard, Ricochet, EA AC, FACEIT)
   che bloccano Wine/Proton e richiedono contromisure avanzate:
   - VFIO KVM Cloaked (Macchina virtuale con mascheramento dell'hypervisor e passthrough GPU)
   - Reboot istantaneo one-time su partizione Windows nativa via UEFI BootNext.
=============================================================================
"""

import sys
import json
import urllib.request
import urllib.error

# Database locale pre-compilato dei giochi più diffusi e del loro livello di Anti-Cheat
KNOWN_ANTICHEAT_DB = {
    "valorant": {
        "title": "VALORANT",
        "anticheat": "Riot Vanguard (Ring-0 Boot-Start Kernel Driver)",
        "status": "BLOCKED_RING0",
        "proton_compatible": False,
        "notes": "Richiede driver vgk.sys all'avvio del kernel NT + TPM 2.0 + Secure Boot. Impossibile su Wine. Richiede VM KVM Stealth o Dual-Boot."
    },
    "league of legends": {
        "title": "League of Legends",
        "anticheat": "Riot Vanguard (Ring-0)",
        "status": "BLOCKED_RING0",
        "proton_compatible": False,
        "notes": "Vanguard implementato a livello kernel. Richiede VM KVM Stealth o Windows nativo."
    },
    "call of duty": {
        "title": "Call of Duty: Warzone / Modern Warfare",
        "anticheat": "Ricochet (Kernel-Level Driver)",
        "status": "BLOCKED_RING0",
        "proton_compatible": False,
        "notes": "Ricochet blocca esplicitamente ambienti non-Windows NT a livello driver."
    },
    "fortnite": {
        "title": "Fortnite",
        "anticheat": "Easy Anti-Cheat / BattlEye (Client-Locked)",
        "status": "BLOCKED_BY_DEVELOPER",
        "proton_compatible": False,
        "notes": "Epic Games ha disabilitato volontariamente il modulo Linux/Proton per Fortnite."
    },
    "rainbow six siege": {
        "title": "Tom Clancy's Rainbow Six Siege",
        "anticheat": "BattlEye",
        "status": "BLOCKED_BY_DEVELOPER",
        "proton_compatible": False,
        "notes": "BattlEye supporta Proton, ma Ubisoft non ha attivato il flag per la build principale."
    },
    "apex legends": {
        "title": "Apex Legends",
        "anticheat": "Easy Anti-Cheat (EAC Proton Bridge)",
        "status": "RESTRICTED",
        "proton_compatible": False,
        "notes": "EA ha recentemente limitato l'accesso Linux per policy interne anti-cheat."
    },
    "elden ring": {
        "title": "Elden Ring",
        "anticheat": "Easy Anti-Cheat (Proton Native Bridge)",
        "status": "SUPPORTED",
        "proton_compatible": True,
        "notes": "Perfettamente funzionante out-of-the-box tramite Proton EAC Runtime di Valve."
    },
    "war thunder": {
        "title": "War Thunder",
        "anticheat": "Easy Anti-Cheat",
        "status": "SUPPORTED",
        "proton_compatible": True,
        "notes": "Supporto completo nativo Linux / Proton."
    },
    "helldivers 2": {
        "title": "HELLDIVERS 2",
        "anticheat": "nProtect GameGuard",
        "status": "SUPPORTED_WINE",
        "proton_compatible": True,
        "notes": "GameGuard è stato patchato per funzionare all'interno di Proton-GE."
    },
    "counter-strike 2": {
        "title": "Counter-Strike 2",
        "anticheat": "Valve Anti-Cheat (VAC / VACNet)",
        "status": "NATIVE",
        "proton_compatible": True,
        "notes": "Gioco ed engine 100% nativi Linux via Vulkan."
    },
    "dota 2": {
        "title": "Dota 2",
        "anticheat": "Valve Anti-Cheat (VAC)",
        "status": "NATIVE",
        "proton_compatible": True,
        "notes": "Nativo Linux con Vulkan e latenza zero."
    }
}

def query_anticheat_status(game_query):
    query_clean = game_query.strip().lower()
    
    # 1. Ricerca nel database locale istantaneo
    for key, data in KNOWN_ANTICHEAT_DB.items():
        if query_clean in key or key in query_clean:
            return data

    # 2. Se non presente, tenta la query online alle API di AreWeAntiCheatYet
    try:
        url = "https://areweanticheatyet.com/api/games"
        req = urllib.request.Request(url, headers={"User-Agent": "OSify-AntiCheat-Engine/1.0"})
        with urllib.request.urlopen(req, timeout=3) as resp:
            games = json.loads(resp.read().decode())
            for g in games:
                if query_clean in g.get("name", "").lower():
                    return {
                        "title": g.get("name"),
                        "anticheat": g.get("anticheats", ["Sconosciuto"])[0] if g.get("anticheats") else "Sconosciuto",
                        "status": g.get("status", "UNKNOWN").upper(),
                        "proton_compatible": g.get("status") == "Supported",
                        "notes": g.get("notes", "Nessuna nota specifica disponibile.")
                    }
    except Exception:
        pass

    return {
        "title": game_query,
        "anticheat": "Verifica manuale richiesta",
        "status": "UNKNOWN",
        "proton_compatible": False,
        "notes": "Titolo non censito o server offline. Verificare se utilizza driver .sys Ring-0."
    }

def print_report(data):
    print("=========================================================")
    print(f"       OSify Anti-Cheat Report: {data['title']}")
    print("=========================================================")
    print(f"[Anti-Cheat Rilevato]  : {data['anticheat']}")
    print(f"[Stato Compatibilità]  : {data['status']}")
    print(f"[Supporto Proton/Wine] : {'SI (Nativo/Bridge)' if data['proton_compatible'] else 'NO (Bloccato a livello kernel)'}")
    print(f"[Dettagli Tecnici]     : {data['notes']}")
    print("---------------------------------------------------------")
    
    if not data['proton_compatible']:
        print("💡 SOLUZIONI INGEGNERISTICHE OSIFY DISPONIBILI:")
        print(" 1. Avvia in VM KVM Stealth con GPU Passthrough (Hypervisor Cloaked):")
        print("    -> osify-ctl anticheat run-stealth-vm")
        print(" 2. Riavvio immediato su Windows con ritorno automatico a OSify:")
        print("    -> osify-ctl anticheat boot-windows")
    else:
        print("✓ Questo titolo gira con prestazioni native su OSify tramite Proton-GE.")
    print("=========================================================")

def main():
    if len(sys.argv) < 2:
        print("Uso: osify-anticheat-checker <nome-gioco>")
        print("Esempio: osify-anticheat-checker 'Valorant'")
        sys.exit(1)

    game = " ".join(sys.argv[1:])
    data = query_anticheat_status(game)
    print_report(data)

if __name__ == "__main__":
    main()
