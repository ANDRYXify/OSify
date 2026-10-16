#!/usr/bin/env python3
"""
OSify Real VM Live Testbed & Screen Radiography Engine
=============================================================================
Ingegnerizzato da Andrea Taliento (ANDRYXify)
Avvia le macchine virtuali reali in ambiente isolato headless (QEMU + Monitor),
cattura schermate ad alta risoluzione (screendump) del bootloader, del desktop,
di Slim autologin e dei menu grafici, salvandole come artefatti PNG per l'analisi.
=============================================================================
"""

import os
import sys
import time
import socket
import subprocess
from PIL import Image

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
ARTIFACTS_DIR = "/Users/andryxify/.gemini/antigravity-ide/brain/8e1ce86a-d1cb-440c-9e32-b5f414d5f7a9"
SCREENSHOTS_DIR = os.path.join(ARTIFACTS_DIR, "vm_screenshots")
os.makedirs(SCREENSHOTS_DIR, exist_ok=True)

TELNET_PORT = 4445

def send_qemu_cmd(cmd, port=TELNET_PORT):
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(5.0)
        s.connect(("127.0.0.1", port))
        # Leggi banner iniziale
        time.sleep(0.2)
        try:
            s.recv(1024)
        except Exception:
            pass
        s.sendall((cmd + "\n").encode())
        time.sleep(0.5)
        resp = b""
        try:
            resp = s.recv(4096)
        except Exception:
            pass
        s.close()
        return resp.decode(errors="ignore")
    except Exception as e:
        return f"ERR: {e}"

def convert_ppm_to_png(ppm_path, png_path):
    if os.path.isfile(ppm_path) and os.path.getsize(ppm_path) > 0:
        try:
            img = Image.open(ppm_path)
            img.save(png_path, "PNG")
            os.remove(ppm_path)
            return True
        except Exception as e:
            print(f"[!] Errore conversione PPM: {e}")
    return False

def test_vm(edition="vintage", boot_seconds=40):
    print(f"\n=============================================================================")
    print(f"   COLLAUDO REALE MACCHINA VIRTUALE: {edition.upper()}                       ")
    print(f"=============================================================================")
    
    if edition == "vintage":
        iso = os.path.join(REPO_ROOT, "build/out/release/OSify-Vintage-i686.iso")
        qemu_bin = "/opt/homebrew/bin/qemu-system-i386"
        if not os.path.exists(qemu_bin):
            qemu_bin = "qemu-system-i386"
        mem = "1024M"
        vga = "std"
    else:
        iso = os.path.join(REPO_ROOT, "build/out/release/OSify-x86_64-v3.iso")
        qemu_bin = "/opt/homebrew/bin/qemu-system-x86_64"
        if not os.path.exists(qemu_bin):
            qemu_bin = "qemu-system-x86_64"
        mem = "2048M"
        vga = "virtio"

    assert os.path.isfile(iso), f"File ISO non trovato: {iso}"

    # Termina eventuali QEMU residui
    subprocess.run("pkill -9 -f qemu-system || true", shell=True)
    time.sleep(1)

    cmd = [
        qemu_bin,
        "-name", f"OSify-{edition}-Testbed",
        "-m", mem,
        "-cdrom", iso,
        "-boot", "d",
        "-vga", vga,
        "-display", "none",
        "-monitor", f"tcp:127.0.0.1:{TELNET_PORT},server,nowait",
        "-serial", "stdio"
    ]

    print(f"[+] Avvio QEMU headless per {edition} su porta monitor {TELNET_PORT}...")
    log_file = open(f"/tmp/qemu_{edition}_test.log", "w")
    proc = subprocess.Popen(cmd, stdout=log_file, stderr=subprocess.STDOUT)

    try:
        # 1. Attesa bootloader (5 secondi)
        time.sleep(5)
        ppm1 = f"/tmp/{edition}_bootloader.ppm"
        png1 = os.path.join(SCREENSHOTS_DIR, f"{edition}_01_bootloader.png")
        send_qemu_cmd(f"screendump {ppm1}")
        time.sleep(1)
        if convert_ppm_to_png(ppm1, png1):
            print(f"[✓ SCREENSHOT 1] Bootloader catturato: {png1} ({os.path.getsize(png1)} bytes)")

        # Invia invio per avviare il boot predefinito da isolinux/syslinux
        print("[+] Invio tasto ENTER al bootloader...")
        send_qemu_cmd("sendkey ret")

        # 2. Attesa caricamento kernel e avvio interfaccia grafica
        print(f"[+] Attesa boot live e avvio desktop ({boot_seconds}s)...")
        step = 10
        elapsed = 0
        while elapsed < boot_seconds:
            time.sleep(step)
            elapsed += step
            ppm_step = f"/tmp/{edition}_step_{elapsed}s.ppm"
            png_step = os.path.join(SCREENSHOTS_DIR, f"{edition}_progress_{elapsed}s.png")
            send_qemu_cmd(f"screendump {ppm_step}")
            time.sleep(0.5)
            convert_ppm_to_png(ppm_step, png_step)
            print(f"  ... {elapsed}s / {boot_seconds}s completati")

        # 3. Screenshot finale del desktop caricato
        ppm_final = f"/tmp/{edition}_desktop.ppm"
        png_final = os.path.join(SCREENSHOTS_DIR, f"{edition}_02_desktop.png")
        send_qemu_cmd(f"screendump {ppm_final}")
        time.sleep(1)
        if convert_ppm_to_png(ppm_final, png_final):
            print(f"[✓ SCREENSHOT 2] Desktop finale catturato: {png_final} ({os.path.getsize(png_final)} bytes)")

        # 4. Invia tasto Super/Windows (W-space o W-a) per aprire l'App Drawer o Start menu
        print("[+] Invia shortcut Super (W-space) per testare l'apertura del menu...")
        send_qemu_cmd("sendkey meta_l-spc")
        time.sleep(3)
        ppm_menu = f"/tmp/{edition}_menu.ppm"
        png_menu = os.path.join(SCREENSHOTS_DIR, f"{edition}_03_menu_aperto.png")
        send_qemu_cmd(f"screendump {ppm_menu}")
        time.sleep(1)
        if convert_ppm_to_png(ppm_menu, png_menu):
            print(f"[✓ SCREENSHOT 3] Menu Start/Drawer catturato: {png_menu} ({os.path.getsize(png_menu)} bytes)")

        return {
            "bootloader": png1,
            "desktop": png_final,
            "menu": png_menu
        }

    finally:
        print("[+] Chiusura processo QEMU...")
        try:
            send_qemu_cmd("quit")
        except Exception:
            pass
        time.sleep(1)
        proc.terminate()
        log_file.close()

if __name__ == "__main__":
    target = sys.argv[1] if len(sys.argv) > 1 else "vintage"
    test_vm(target, boot_seconds=45)
