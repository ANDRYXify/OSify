#!/usr/bin/env python3
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

    # Attendi avvio socket
    for _ in range(50):
        if os.path.exists(sock_path):
            break
        time.sleep(0.1)

    time.sleep(3.0) # Attendi bootstrap del kernel OSify e rendering desktop a 1024x768

    client = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    client.connect(sock_path)
    time.sleep(0.5)
    _ = client.recv(4096)

    def send_mon(cmd):
        client.sendall((cmd + "\n").encode())
        time.sleep(0.3)
        try:
            return client.recv(4096).decode()
        except:
            return ""

    print("[+] Cattura screendump QEMU Desktop Boot...")
    send_mon("screendump /tmp/qemu_desktop_boot.ppm")

    print("[+] Iniezione comandi utente reale: digitazione 'info'...")
    for ch in "info":
        send_mon(f"sendkey {ch}")
        time.sleep(0.05)
    send_mon("sendkey ret")
    time.sleep(0.5)

    print("[+] Iniezione comandi utente reale: digitazione 'calc'...")
    for ch in "calc":
        send_mon(f"sendkey {ch}")
        time.sleep(0.05)
    send_mon("sendkey ret")
    time.sleep(0.8)

    print("[+] Cattura screendump QEMU con Calcolatrice aperta...")
    send_mon("screendump /tmp/qemu_desktop_calc.ppm")

    send_mon("quit")
    client.close()
    proc.terminate()
    proc.wait()

    # Converti PPM in PNG
    if os.path.exists("/tmp/qemu_desktop_boot.ppm"):
        Image.open("/tmp/qemu_desktop_boot.ppm").save("build/out/osify_qemu_desktop_boot.png")
        print("[+] Immagine generata: build/out/osify_qemu_desktop_boot.png")

    if os.path.exists("/tmp/qemu_desktop_calc.ppm"):
        Image.open("/tmp/qemu_desktop_calc.ppm").save("build/out/osify_qemu_desktop_calc.png")
        print("[+] Immagine generata: build/out/osify_qemu_desktop_calc.png")

if __name__ == "__main__":
    test_qemu()
