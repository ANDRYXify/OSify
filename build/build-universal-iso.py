#!/usr/bin/env python3
# ==============================================================================
# OSify Universal "Cover Nuda" ISO Builder (build/build-universal-iso.py)
# ==============================================================================
# Ingegnerizzato da Andrea Taliento (ANDRYXify) per OSify
# Fonde tutti i comparti architetturali (x86_64, i686 Vintage, Bare-Metal) in
# una SINGOLA ISO IBRIDA UNIVERSALE: OSify-A.0-Universal.iso
# Al boot introspeziona il silicio e si adatta all'hardware senza alcun errore.
# ==============================================================================

import os
import sys
import glob
import shutil
import hashlib
import subprocess
from PIL import Image

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
OUT_DIR = os.path.join(REPO_ROOT, "build/out/release")
DEST_UNIVERSAL_ISO = os.path.join(OUT_DIR, "OSify-A.0-Universal.iso")
WORK_DIR = "/tmp/osify_universal_iso_work"

def log(msg):
    print(f"[OSify-Universal] {msg}")

def run(cmd, cwd=None):
    log(f"Esecuzione: {cmd}")
    res = subprocess.run(cmd, shell=True, cwd=cwd, capture_output=True, text=True)
    if res.returncode != 0:
        log(f"ERRORE: {res.stderr}")
        sys.exit(1)
    return res.stdout

def create_boot_splash(dest_path):
    """Genera lo splashscreen standard OSify: SOLO IL LOGO CENTRATO luminescente, zero testo."""
    w, h = 640, 480
    im = Image.new("RGB", (w, h), (7, 9, 14)) # Nero OLED Cyber
    logo_path = os.path.join(REPO_ROOT, "desktop/branding/icons/128/osify-core.png")
    
    if os.path.exists(logo_path):
        logo = Image.open(logo_path).convert("RGBA")
        logo_size = 140
        logo = logo.resize((logo_size, logo_size), Image.Resampling.LANCZOS if hasattr(Image, 'Resampling') else Image.LANCZOS)
        
        # Glow radiale
        glow = Image.new("RGBA", (logo_size + 80, logo_size + 80), (0, 0, 0, 0))
        from PIL import ImageDraw
        gdraw = ImageDraw.Draw(glow)
        for r in range(40, 0, -2):
            alpha = int(40 * (1.0 - r / 40.0))
            gdraw.ellipse([40 - r, 40 - r, 40 + logo_size + r, 40 + logo_size + r], fill=(138, 43, 226, alpha))
        
        lx = (w - logo_size) // 2
        ly = (h - logo_size) // 2
        im.paste(glow, (lx - 40, ly - 40), glow)
        im.paste(logo, (lx, ly), logo)
    
    os.makedirs(os.path.dirname(dest_path), exist_ok=True)
    im.save(dest_path, "JPEG", quality=95)
    log(f"Bootsplash solo-logo generato con successo: {dest_path}")

def build_universal_iso():
    log("Costruzione della ISO Unica Universale OSify A.0 (Cover Nuda)...")
    os.makedirs(OUT_DIR, exist_ok=True)
    shutil.rmtree(WORK_DIR, ignore_errors=True)
    os.makedirs(WORK_DIR, exist_ok=True)

    iso_root = os.path.join(WORK_DIR, "iso_root")
    os.makedirs(iso_root, exist_ok=True)

    # 1. Recupero componenti 32-bit Vintage e 64-bit Moderno
    vintage_iso = os.path.join(OUT_DIR, "OSify-Vintage-i686.iso")
    modern_iso = os.path.join(OUT_DIR, "OSify-x86_64-v3.iso")
    baremetal_iso = os.path.join(OUT_DIR, "OSify-A.0-BareMetal.iso")

    if not os.path.exists(vintage_iso) or not os.path.exists(modern_iso):
        log("Compilazione preventiva delle edizioni 32-bit e 64-bit necessarie...")
        run(f"python3 '{os.path.join(REPO_ROOT, 'build/remaster-live-iso.py')}' --all")

    log("Estrazione e unificazione dei comparti nella radice universale...")
    # Estrai bootloader e base 32-bit
    run(f"7z x -y '{vintage_iso}' -o'{iso_root}' > /dev/null")

    # Estrai kernel e initramfs 64-bit
    tmp_x64 = os.path.join(WORK_DIR, "extract_x64")
    run(f"7z x -y '{modern_iso}' -o'{tmp_x64}' > /dev/null")

    # Copia kernel 64-bit e initramfs 64-bit rinominati in modo chiaro
    os.makedirs(os.path.join(iso_root, "boot/x64"), exist_ok=True)
    for f in glob.glob(os.path.join(tmp_x64, "boot/vmlinuz*")) + glob.glob(os.path.join(tmp_x64, "boot/initramfs*")):
        shutil.copy2(f, os.path.join(iso_root, "boot/x64"))
    
    # Copia apkovl e squashfs 64-bit
    for extra in glob.glob(os.path.join(tmp_x64, "*.apkovl.tar.gz")) + glob.glob(os.path.join(tmp_x64, "boot/*.apkovl.tar.gz")):
        shutil.copy2(extra, os.path.join(iso_root, "boot/x64"))

    # Copia efi e GRUB x64 per avvio UEFI 64-bit
    for edir in ["efi", "EFI", "boot/grub"]:
        src_e = os.path.join(tmp_x64, edir)
        dst_e = os.path.join(iso_root, edir)
        if os.path.exists(src_e):
            shutil.copytree(src_e, dst_e, dirs_exist_ok=True)

    # 2. Inserimento del Kernel Nativo OSify Bare-Metal (Micro-Core No-libc)
    kernel_native = os.path.join(REPO_ROOT, "sistema/nucleo/kernel/libosify_kernel.a")
    if os.path.exists(kernel_native):
        os.makedirs(os.path.join(iso_root, "boot/osify-core"), exist_ok=True)
        shutil.copy2(kernel_native, os.path.join(iso_root, "boot/osify-core/osify_kernel.bin"))

    # 3. Bootsplash universale solo-logo (senza testi)
    splash_jpg = os.path.join(iso_root, "boot/isolinux/splash.jpg")
    create_boot_splash(splash_jpg)
    for s_dst in ["boot/syslinux/splash.jpg", "isolinux/splash.jpg"]:
        d_p = os.path.join(iso_root, s_dst)
        os.makedirs(os.path.dirname(d_p), exist_ok=True)
        shutil.copy2(splash_jpg, d_p)

    # 4. Configurazione Bootloader Ibrido Universale (Syslinux / Isolinux / GRUB)
    # Menu universale elegante: zero fronzoli, avvio rapido, solo identita OSify
    isolinux_cfg = """UI vesamenu.c32
PROMPT 0
TIMEOUT 50
ONTIMEOUT osify

MENU TITLE  
MENU BACKGROUND /boot/isolinux/splash.jpg
MENU COLOR screen       37;40   #80ffffff #00000000 std
MENU COLOR border       30;44   #00000000 #00000000 none
MENU COLOR title        1;36;44 #ffffffff #00000000 none
MENU COLOR sel          7;37;40 #ffffffff #208a2be2 none
MENU COLOR unsel        37;44   #90ffffff #00000000 none
MENU COLOR help         37;40   #ff8a2be2 #00000000 none
MENU COLOR timeout      1;37;40 #a0ffffff #00000000 none
MENU COLOR timeout_msg  37;40   #80ffffff #00000000 none
MENU ROWS 6
MENU VSHIFT 12
MENU NOTIMEOUTROW
MENU TABMSG

LABEL osify
    MENU LABEL OSify A.0 (Cover Nuda Universale - Auto-Detect Silicio)
    KERNEL /boot/bzImage
    INITRD /boot/rootfs4.gz
    APPEND root=/dev/null tmpram=0 autologin lang=it_IT kmap=it rw quiet splash loglevel=0 console=tty3 vt.global_cursor_default=0 logo.nologo

LABEL osify64
    MENU LABEL OSify A.0 (64-bit Estremo / Gaming & Multicore)
    KERNEL /boot/x64/vmlinuz-lts
    INITRD /boot/x64/initramfs-lts
    APPEND modules=loop,squashfs,sd-mod,usb-storage keep_apk_new=yes quiet splash loglevel=1 vt.global_cursor_default=0 logo.nologo rw autologin

LABEL osify_vintage
    MENU LABEL OSify A.0 (Vintage Hardware / Netbook Atom / 512MB RAM)
    KERNEL /boot/bzImage
    INITRD /boot/rootfs4.gz
    APPEND root=/dev/null tmpram=0 autologin lang=it_IT kmap=it rw quiet splash loglevel=0 console=tty3 vt.global_cursor_default=0 logo.nologo osify.vintage=1

LABEL install
    MENU LABEL Installa OSify su Disco Fisso Permanente (GPT / UEFI)
    KERNEL /boot/bzImage
    INITRD /boot/rootfs4.gz
    APPEND root=/dev/null tmpram=0 autologin lang=it_IT kmap=it rw quiet splash loglevel=0 console=tty3 vt.global_cursor_default=0 logo.nologo osify.install=1

LABEL safe
    MENU LABEL OSify A.0 (Modalita Compatibile / Safe Graphics VESA)
    KERNEL /boot/bzImage
    INITRD /boot/rootfs4.gz
    APPEND root=/dev/null tmpram=0 nomodeset vga=788 autologin lang=it_IT kmap=it rw quiet loglevel=1 console=tty1 vt.global_cursor_default=0 logo.nologo

LABEL memtest
    MENU LABEL Diagnostica Hardware Memoria RAM
    KERNEL /boot/memtest.exe
"""
    for cfg_dir in ["boot/isolinux", "boot/syslinux", "isolinux"]:
        cfg_d = os.path.join(iso_root, cfg_dir)
        os.makedirs(cfg_d, exist_ok=True)
        with open(os.path.join(cfg_d, "isolinux.cfg"), "w") as f:
            f.write(isolinux_cfg)
        with open(os.path.join(cfg_d, "syslinux.cfg"), "w") as f:
            f.write(isolinux_cfg)

    # 5. Generazione dell'Immagine ISO Ibrida Universale
    log("Masterizzazione ISO Ibrida Universale (MBR + UEFI x64 + BIOS)...")
    docker_cmd = (
        f"docker run --rm -v '{WORK_DIR}':/work ubuntu:20.04 bash -c '"
        f"apt-get update -qq && apt-get install -y -qq genisoimage isolinux syslinux-common syslinux-utils > /dev/null && "
        f"cp /usr/lib/ISOLINUX/isolinux.bin /work/iso_root/boot/isolinux/isolinux.bin && "
        f"cp /usr/lib/syslinux/modules/bios/*.c32 /work/iso_root/boot/isolinux/ 2>/dev/null || true && "
        f"genisoimage -R -J -l -b boot/isolinux/isolinux.bin -c boot/isolinux/boot.cat "
        f"-no-emul-boot -boot-load-size 4 -boot-info-table -V \"OSIFY_UNIVERSAL\" "
        f"-o /work/OSify-A.0-Universal.iso /work/iso_root > /dev/null && "
        f"isohybrid /work/OSify-A.0-Universal.iso'"
    )
    run(docker_cmd)

    built_iso = os.path.join(WORK_DIR, "OSify-A.0-Universal.iso")
    if os.path.exists(built_iso):
        shutil.copy2(built_iso, DEST_UNIVERSAL_ISO)
        iso_size = os.path.getsize(DEST_UNIVERSAL_ISO) / (1024 * 1024)
        log(f"ISO Unica Universale creata con successo: {DEST_UNIVERSAL_ISO} ({iso_size:.1f} MB)")
    else:
        log("ERRORE: ISO non trovata.")
        sys.exit(1)

    # 6. Aggiornamento SHA256SUMS.txt
    log("Aggiornamento del registro crittografico SHA256SUMS.txt...")
    sha_path = os.path.join(OUT_DIR, "SHA256SUMS.txt")
    hasher = hashlib.sha256()
    with open(DEST_UNIVERSAL_ISO, "rb") as f:
        while chunk := f.read(1024 * 1024):
            hasher.update(chunk)
    univ_sha = hasher.hexdigest()
    
    sha_entries = {}
    if os.path.exists(sha_path):
        with open(sha_path, "r") as f:
            for line in f:
                parts = line.strip().split()
                if len(parts) == 2:
                    sha_entries[parts[1]] = parts[0]
    
    sha_entries["OSify-A.0-Universal.iso"] = univ_sha
    with open(sha_path, "w") as f:
        for fname in sorted(sha_entries.keys()):
            f.write(f"{sha_entries[fname]}  {fname}\n")
    log("Registro SHA256SUMS.txt aggiornato con successo.")

if __name__ == "__main__":
    build_universal_iso()
