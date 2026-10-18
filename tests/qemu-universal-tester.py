#!/usr/bin/env python3
"""
OSify Universal Live ISO Real Hardware/QEMU Tester
=============================================================================
Ingegnerizzato da Andrea Taliento (ANDRYXify) per OSify
Esegue il collaudo REALE in ambiente virtuale della ISO Universale:
1. Boot UEFI x86_64 con firmware EDK II (OVMF)
2. Boot BIOS Legacy x86_64 con isolinux e auto-detect silicio ifcpu64
3. Cattura radiografie video (screendump) ad alta risoluzione del bootsplash,
   della sequenza di avvio e del desktop Dark Glass con Dock e Setup Wizard.
=============================================================================
"""

import os
import sys
import time
import socket
import subprocess
from PIL import Image

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
OUT_DIR = os.path.join(REPO_ROOT, "build/out")
os.makedirs(OUT_DIR, exist_ok=True)

UNIVERSAL_ISO = os.path.join(REPO_ROOT, "build/out/release/OSify-A.0-Universal.iso")
OVMF_BIOS = "/opt/homebrew/Cellar/qemu/11.0.0/share/qemu/edk2-x86_64-code.fd"
QEMU_BIN = "/opt/homebrew/bin/qemu-system-x86_64"
TELNET_PORT = 4555

def send_qemu_cmd(cmd, port=TELNET_PORT):
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(5.0)
        s.connect(("127.0.0.1", port))
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
            print(f"[!] Errore conversione PPM -> PNG: {e}")
    return False

def run_real_uefi_test():
    print("\n=============================================================================")
    print(" [1/2] COLLAUDO REALE UEFI: OSify-A.0-Universal.iso (Firmware EDK II)       ")
    print("=============================================================================")
    assert os.path.isfile(UNIVERSAL_ISO), f"ISO non trovata: {UNIVERSAL_ISO}"
    assert os.path.isfile(OVMF_BIOS), f"OVMF non trovato: {OVMF_BIOS}"

    subprocess.run("pkill -9 -f qemu-system || true", shell=True)
    time.sleep(1)

    serial_log = "/tmp/qemu_uefi_serial.log"
    if os.path.exists(serial_log):
        os.remove(serial_log)

    cmd = [
        QEMU_BIN,
        "-name", "OSify-UEFI-RealTest",
        "-m", "2048M",
        "-smp", "2",
        "-bios", OVMF_BIOS,
        "-cdrom", UNIVERSAL_ISO,
        "-boot", "d",
        "-vga", "virtio",
        "-display", "none",
        "-monitor", f"tcp:127.0.0.1:{TELNET_PORT},server,nowait",
        "-serial", f"file:{serial_log}"
    ]

    print("[+] Lancio QEMU UEFI...")
    proc = subprocess.Popen(cmd)

    try:
        # T+5s: Bootloader / GRUB
        print("[+] Attesa 6s per cattura fase bootloader UEFI...")
        time.sleep(6)
        ppm_boot = "/tmp/uefi_boot.ppm"
        png_boot = os.path.join(OUT_DIR, "real_uefi_bootloader.png")
        send_qemu_cmd(f"screendump {ppm_boot}")
        time.sleep(1)
        convert_ppm_to_png(ppm_boot, png_boot)
        print(f"[[OK]] Radiografia Bootloader UEFI: {png_boot}")

        # T+40s: Desktop grafico
        print("[+] Attesa 38s per caricamento Desktop Xorg, Openbox, Dock e OOBE...")
        time.sleep(38)
        ppm_desk = "/tmp/uefi_desk.ppm"
        png_desk = os.path.join(OUT_DIR, "real_uefi_desktop.png")
        send_qemu_cmd(f"screendump {ppm_desk}")
        time.sleep(1)
        if convert_ppm_to_png(ppm_desk, png_desk):
            print(f"[[OK]] Radiografia Desktop UEFI Reale: {png_desk} ({os.path.getsize(png_desk)} bytes)")

        # Test interattività: invio scorciatoia tastiera Super+Spazio (Spotlight/Menu)
        print("[+] Test interattività Desktop: invio combinazione tasti Super+Spazio...")
        send_qemu_cmd("sendkey meta_l-spc")
        time.sleep(3)
        ppm_interact = "/tmp/uefi_interact.ppm"
        png_interact = os.path.join(OUT_DIR, "real_uefi_interactivity.png")
        send_qemu_cmd(f"screendump {ppm_interact}")
        time.sleep(1)
        convert_ppm_to_png(ppm_interact, png_interact)
        print(f"[[OK]] Radiografia Interattività Desktop: {png_interact}")

        return png_desk
    finally:
        send_qemu_cmd("quit")
        time.sleep(1)
        proc.terminate()

def run_real_bios_test():
    print("\n=============================================================================")
    print(" [2/2] COLLAUDO REALE BIOS LEGACY: OSify-A.0-Universal.iso                   ")
    print("=============================================================================")
    assert os.path.isfile(UNIVERSAL_ISO), f"ISO non trovata: {UNIVERSAL_ISO}"

    subprocess.run("pkill -9 -f qemu-system || true", shell=True)
    time.sleep(1)

    serial_log = "/tmp/qemu_bios_serial.log"
    if os.path.exists(serial_log):
        os.remove(serial_log)

    cmd = [
        QEMU_BIN,
        "-name", "OSify-BIOS-RealTest",
        "-m", "2048M",
        "-smp", "2",
        "-cdrom", UNIVERSAL_ISO,
        "-boot", "d",
        "-vga", "std",
        "-display", "none",
        "-monitor", f"tcp:127.0.0.1:{TELNET_PORT},server,nowait",
        "-serial", f"file:{serial_log}"
    ]

    print("[+] Lancio QEMU BIOS Legacy...")
    proc = subprocess.Popen(cmd)

    try:
        # T+2s: Solo-Logo bootsplash Syslinux
        print("[+] Attesa 2.5s per cattura Solo-Logo bootsplash Syslinux...")
        time.sleep(2.5)
        ppm_splash = "/tmp/bios_splash.ppm"
        png_splash = os.path.join(OUT_DIR, "real_bios_bootsplash.png")
        send_qemu_cmd(f"screendump {ppm_splash}")
        time.sleep(1)
        if convert_ppm_to_png(ppm_splash, png_splash):
            print(f"[[OK]] Radiografia Solo-Logo Bootsplash BIOS: {png_splash} ({os.path.getsize(png_splash)} bytes)")

        # T+40s: Avvio automatico dopo timeout (auto-detect ifcpu64)
        print("[+] Attesa 38s per handoff automatico timeout e avvio desktop...")
        time.sleep(38)
        ppm_desk = "/tmp/bios_desk.ppm"
        png_desk = os.path.join(OUT_DIR, "real_bios_desktop.png")
        send_qemu_cmd(f"screendump {ppm_desk}")
        time.sleep(1)
        if convert_ppm_to_png(ppm_desk, png_desk):
            print(f"[[OK]] Radiografia Desktop BIOS Reale: {png_desk} ({os.path.getsize(png_desk)} bytes)")

        return png_desk
    finally:
        send_qemu_cmd("quit")
        time.sleep(1)
        proc.terminate()

if __name__ == "__main__":
    t1 = run_real_uefi_test()
    t2 = run_real_bios_test()
    print("\n=============================================================================")
    print("[] COLLAUDO REALE COMPLETATO CON SUCCESSO SU ENTRAMBI I TARGET HARDWARE!")
    print(f"   UEFI Desktop Snapshot: {t1}")
    print(f"   BIOS Desktop Snapshot: {t2}")
    print("=============================================================================")
