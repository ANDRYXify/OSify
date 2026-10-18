#!/usr/bin/env python3
# ==============================================================================
# OSify Interactive QEMU Real-User Test Session
# ==============================================================================
# Ingegnerizzato per collaudare il sistema operativo dal vivo come un utente reale:
# - Avvio e Desktop Cyberpunk 2050 con Streamer Privacy Mode
# - Toggle Privacy Rete (IP protetto Quad9 vs IP reale)
# - Silicon Benchmark Sovrano 2050 (ALU, SIMD, RAM Throughput, Blitter 2D)
# - Cyber Arcade 2050 (Breakout nativo, paddle neon, mattoni cibernetici)
# - Calcolatrice Scientifica multi-operatore (SQRT, +/-, ^2, MOD)
# - Esplora File OSifyFS con breadcrumb e scorciatoie cartelle
# ==============================================================================

import socket
import subprocess
import time
import os
from PIL import Image

def test_qemu():
    sock_path = "/tmp/qemu-monitor.sock"
    if os.path.exists(sock_path):
        os.remove(sock_path)

    qemu_cmd = [
        "qemu-system-x86_64",
        "-cdrom", "build/out/OSify-A.1-BareMetal.iso",
        "-m", "2048",
        "-vga", "std",
        "-monitor", f"unix:{sock_path},server,nowait",
        "-serial", "stdio",
        "-display", "none",
        "-no-reboot"
    ]

    print("[+] Avvio QEMU con ISO Bare-Metal e socket monitor...")
    proc = subprocess.Popen(qemu_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    for _ in range(50):
        if os.path.exists(sock_path):
            break
        time.sleep(0.1)

    time.sleep(3.0) # Attendi bootstrap del kernel OSify e rendering desktop a 1024x768

    client = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    client.connect(sock_path)
    time.sleep(0.5)
    try:
        _ = client.recv(4096)
    except:
        pass

    def send_mon(cmd):
        client.sendall((cmd + "\n").encode())
        time.sleep(0.2)
        try:
            return client.recv(4096).decode()
        except:
            return ""

    def type_word(word):
        for ch in word:
            if ch == ' ':
                send_mon("sendkey spc")
            elif ch == '-':
                send_mon("sendkey minus")
            elif ch == '_':
                send_mon("sendkey shift-minus")
            elif ch == '/':
                send_mon("sendkey slash")
            else:
                send_mon(f"sendkey {ch}")
            time.sleep(0.04)
        send_mon("sendkey ret")
        time.sleep(0.4)

    print("[+] 1. Cattura screendump QEMU Desktop Boot (Privacy Streamer + Icona Arcade)...")
    send_mon("screendump /tmp/qemu_desktop_boot.ppm")

    print("[+] 2. Apertura Benchmark Silicio Sovrano 2050 ('benchgui')...")
    type_word("benchgui")
    time.sleep(0.8)
    print("[+] Cattura screendump QEMU con Benchmark GUI aperto...")
    send_mon("screendump /tmp/qemu_desktop_bench.ppm")

    print("[+] 3. Chiusura Benchmark e apertura Cyber Arcade 2050 ('arcade')...")
    # Premiamo ESC o digitiamo 'arcade' nel terminale
    type_word("arcade")
    time.sleep(0.8)
    print("[+] Simulazione input giocatore arcade: muovi paddle a destra e a sinistra...")
    send_mon("sendkey d")
    time.sleep(0.1)
    send_mon("sendkey d")
    time.sleep(0.1)
    send_mon("sendkey a")
    time.sleep(0.1)
    print("[+] Cattura screendump QEMU Cyber Arcade 2050...")
    send_mon("screendump /tmp/qemu_desktop_arcade.ppm")

    print("[+] 4. Apertura Calcolatrice Scientifica ('calc')...")
    type_word("calc")
    time.sleep(0.6)
    print("[+] Cattura screendump QEMU Calcolatrice Scientifica...")
    send_mon("screendump /tmp/qemu_desktop_calc.ppm")

    print("[+] 5. Apertura Esplora File OSifyFS ('files')...")
    type_word("files")
    time.sleep(0.6)
    print("[+] Cattura screendump QEMU Esplora File OSifyFS...")
    send_mon("screendump /tmp/qemu_desktop_files.ppm")

    print("[+] 6. Test Streamer Privacy Toggle ('privacy')...")
    type_word("privacy")
    time.sleep(0.5)
    print("[+] Cattura screendump QEMU Privacy Toggle (IP mostrato)...")
    send_mon("screendump /tmp/qemu_desktop_privacy.ppm")

    print("[+] 7. Apertura Centro Personalizzazione & Temi 2050 ('personalizza')...")
    type_word("personalizza")
    time.sleep(0.8)
    print("[+] Cattura screendump QEMU Centro Personalizzazione...")
    send_mon("screendump /tmp/qemu_desktop_personalizza.ppm")

    print("[+] 8. Applicazione a caldo Tema Matrix Hacker ('tema matrix')...")
    type_word("tema matrix")
    time.sleep(0.6)
    print("[+] Cattura screendump QEMU Tema Matrix Hacker...")
    send_mon("screendump /tmp/qemu_desktop_matrix.ppm")

    print("[+] 9. Applicazione a caldo Tema Tokyo Synthwave & Campo Stellare ('tema synth', 'sfondo stars')...")
    type_word("tema synth")
    time.sleep(0.4)
    type_word("sfondo stars")
    time.sleep(0.6)
    print("[+] Cattura screendump QEMU Tema Tokyo Synthwave...")
    send_mon("screendump /tmp/qemu_desktop_synthwave.ppm")

    send_mon("quit")
    client.close()
    proc.terminate()
    proc.wait()

    os.makedirs("build/out/screendumps", exist_ok=True)
    dumps = [
        ("qemu_desktop_boot", "build/out/screendumps/01_desktop_boot.png"),
        ("qemu_desktop_bench", "build/out/screendumps/02_silicon_benchmark.png"),
        ("qemu_desktop_arcade", "build/out/screendumps/03_cyber_arcade.png"),
        ("qemu_desktop_calc", "build/out/screendumps/04_scientific_calc.png"),
        ("qemu_desktop_files", "build/out/screendumps/05_file_explorer.png"),
        ("qemu_desktop_privacy", "build/out/screendumps/06_privacy_toggle.png"),
        ("qemu_desktop_personalizza", "build/out/screendumps/07_personalizzazione_temi.png"),
        ("qemu_desktop_matrix", "build/out/screendumps/08_tema_matrix_live.png"),
        ("qemu_desktop_synthwave", "build/out/screendumps/09_tema_synthwave_stars.png")
    ]

    for src_name, dest_png in dumps:
        ppm_path = f"/tmp/{src_name}.ppm"
        if os.path.exists(ppm_path):
            img = Image.open(ppm_path)
            img.save(dest_png)
            print(f"[+] Screendump salvato: {dest_png} ({img.size[0]}x{img.size[1]})")

if __name__ == "__main__":
    test_qemu()

