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
VERSION_FILE = os.path.join(REPO_ROOT, "VERSION")
OSIFY_VERSION = "A.1"
if os.path.isfile(VERSION_FILE):
    try:
        with open(VERSION_FILE, "r") as f:
            v = f.read().strip()
            if v:
                OSIFY_VERSION = v
    except Exception:
        pass

OUT_DIR = os.path.join(REPO_ROOT, "build/out/release")
DEST_UNIVERSAL_ISO = os.path.join(OUT_DIR, f"OSify-{OSIFY_VERSION}-Universal.iso")
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

    # 1. Recupero componenti
    vintage_iso = os.path.join(OUT_DIR, "OSify-Vintage-i686.iso")
    modern_iso = os.path.join(OUT_DIR, "OSify-x86_64-v3.iso")
    baremetal_iso = os.path.join(OUT_DIR, f"OSify-{OSIFY_VERSION}-BareMetal.iso")

    if not os.path.exists(vintage_iso) or not os.path.exists(modern_iso):
        log("Compilazione preventiva delle edizioni 32-bit e 64-bit necessarie...")
        run(f"python3 '{os.path.join(REPO_ROOT, 'build/remaster-live-iso.py')}' --all")

    log("Estrazione della base moderna 64-bit UEFI come fondamenta universale...")
    # Estraiamo modern_iso (che include UEFI, GRUB EFI, efi.img, apks, vmlinuz-lts, initramfs-lts)
    run(f"7z x -y '{modern_iso}' -o'{iso_root}' > /dev/null")

    log("Integrazione del comparto Vintage 32-bit (Cover Nuda per netbook e macchine storiche)...")
    tmp_vintage = os.path.join(WORK_DIR, "extract_vintage")
    run(f"7z x -y '{vintage_iso}' -o'{tmp_vintage}' > /dev/null")

    # Copia kernel 32-bit e rootfs4.gz
    for item in ["bzImage", "rootfs4.gz", "memtest.exe"]:
        src_item = os.path.join(tmp_vintage, "boot", item)
        if os.path.exists(src_item):
            shutil.copy2(src_item, os.path.join(iso_root, "boot", item))

    # 2. Inserimento del Kernel Nativo OSify Bare-Metal (Micro-Core No-libc)
    kernel_native = os.path.join(REPO_ROOT, "sistema/nucleo/kernel/libosify_kernel.a")
    if os.path.exists(kernel_native):
        os.makedirs(os.path.join(iso_root, "boot/osify-core"), exist_ok=True)
        shutil.copy2(kernel_native, os.path.join(iso_root, "boot/osify-core/osify_kernel.bin"))

    # 3. Bootsplash universale solo-logo (senza testi)
    splash_src = os.path.join(tmp_vintage, "boot/isolinux/splash.jpg")
    for s_dst in ["boot/syslinux/splash.jpg", "boot/isolinux/splash.jpg", "isolinux/splash.jpg", "splash.jpg"]:
        d_p = os.path.join(iso_root, s_dst)
        os.makedirs(os.path.dirname(d_p), exist_ok=True)
        if os.path.exists(splash_src):
            shutil.copy2(splash_src, d_p)
        else:
            create_boot_splash(d_p)

    # 4. Moduli Syslinux di auto-rilevamento silicio da toolchain coerente (build/syslinux_alpine)
    syslinux_alpine_dir = os.path.join(REPO_ROOT, "build/syslinux_alpine")
    syslinux_dst_dir = os.path.join(iso_root, "boot/syslinux")
    os.makedirs(syslinux_dst_dir, exist_ok=True)
    for mod in ["isolinux.bin", "isohdpfx.bin", "ldlinux.c32", "libcom32.c32", "libutil.c32", "vesamenu.c32", "menu.c32", "ifcpu64.c32", "mboot.c32"]:
        mod_src = os.path.join(syslinux_alpine_dir, mod)
        if os.path.exists(mod_src):
            shutil.copy2(mod_src, os.path.join(syslinux_dst_dir, mod))

    # 5. Configurazione Syslinux / Isolinux per BIOS Legacy con Auto-Detect CPU
    isolinux_cfg = """DEFAULT autodetect
UI vesamenu.c32
PROMPT 0
TIMEOUT 20
ONTIMEOUT autodetect
MENU HIDDEN

MENU TITLE
MENU BACKGROUND splash.jpg
MENU WIDTH 78
MENU MARGIN 6
MENU ROWS 0
MENU VSHIFT 0
MENU NOTIMEOUTROW
MENU TABMSG

MENU COLOR border       *   #00000000 #00000000 none
MENU COLOR title        *   #00000000 #00000000 none
MENU COLOR sel          0   #00000000 #00000000 none
MENU COLOR unsel        0   #00000000 #00000000 none
MENU COLOR help         *   #00000000 #00000000 none
MENU COLOR timeout      *   #00000000 #00000000 none
MENU COLOR timeout_msg  *   #00000000 #00000000 none

LABEL autodetect
    MENU LABEL OSify A.0 (Cover Nuda - Auto-Rilevamento Silicio)
    COM32 ifcpu64.c32
    APPEND osify64 -- osify32

LABEL osify64
    MENU LABEL OSify A.0 (64-bit Estremo / Gaming & Desktop)
    KERNEL /boot/vmlinuz-lts
    INITRD /boot/initramfs-lts
    APPEND modules=loop,squashfs,sd-mod,usb-storage keep_apk_new=yes quiet splash loglevel=0 console=tty3 vt.global_cursor_default=0 logo.nologo rw autologin

LABEL osify32
    MENU LABEL OSify A.0 (Vintage 32-bit / Netbook & Leggeri)
    KERNEL /boot/bzImage
    INITRD /boot/rootfs4.gz
    APPEND root=/dev/null video=-32 tmpram=0 autologin lang=it_IT kmap=it rw quiet splash loglevel=0 console=tty3 vt.global_cursor_default=0 logo.nologo

LABEL install
    MENU LABEL Installa OSify su Disco Fisso Permanente (GPT / UEFI)
    KERNEL /boot/vmlinuz-lts
    INITRD /boot/initramfs-lts
    APPEND modules=loop,squashfs,sd-mod,usb-storage keep_apk_new=yes osify.install=1 quiet splash loglevel=0 console=tty3 vt.global_cursor_default=0 logo.nologo rw autologin

LABEL safe
    MENU LABEL OSify A.0 (Modalita Compatibile / Safe Graphics VESA)
    KERNEL /boot/vmlinuz-lts
    INITRD /boot/initramfs-lts
    APPEND modules=loop,squashfs,sd-mod,usb-storage keep_apk_new=yes nomodeset vga=788 quiet loglevel=1 vt.global_cursor_default=0 logo.nologo console=tty1 rw autologin

LABEL memtest
    MENU LABEL Diagnostica Hardware Memoria RAM
    KERNEL /boot/memtest.exe
"""
    with open(os.path.join(syslinux_dst_dir, "isolinux.cfg"), "w") as f:
        f.write(isolinux_cfg)
    with open(os.path.join(syslinux_dst_dir, "syslinux.cfg"), "w") as f:
        f.write(isolinux_cfg)

    # 6. Configurazione GRUB per UEFI 64-bit
    grub_cfg = """set timeout=0
set default=0

menuentry "OSify A.0 Universal (64-bit Cover Nuda)" {
    linux /boot/vmlinuz-lts modules=loop,squashfs,sd-mod,usb-storage keep_apk_new=yes quiet splash loglevel=0 console=tty1 console=ttyS0 vt.global_cursor_default=0 logo.nologo rd.systemd.show_status=false rd.udev.log_priority=0 udev.log_priority=0 rw autologin
    initrd /boot/initramfs-lts
}

menuentry "OSify A.0 Modalita Compatibile (Safe Graphics VESA)" {
    linux /boot/vmlinuz-lts modules=loop,squashfs,sd-mod,usb-storage keep_apk_new=yes nomodeset vga=788 quiet loglevel=1 vt.global_cursor_default=0 logo.nologo console=tty1 rw autologin
    initrd /boot/initramfs-lts
}

menuentry "OSify A.0 Installa su Disco Fisso" {
    linux /boot/vmlinuz-lts modules=loop,squashfs,sd-mod,usb-storage keep_apk_new=yes osify.install=1 quiet splash loglevel=0 console=tty1 console=ttyS0 vt.global_cursor_default=0 logo.nologo rw autologin
    initrd /boot/initramfs-lts
}
"""
    for g_dir in ["boot/grub", "efi/boot", "EFI/BOOT"]:
        gd = os.path.join(iso_root, g_dir)
        os.makedirs(gd, exist_ok=True)
        with open(os.path.join(gd, "grub.cfg"), "w") as f:
            f.write(grub_cfg)

    # 7. Script di avvio automatico EDK II / UEFI Shell (startup.nsh)
    startup_nsh = """@echo -off
cls
echo Avvio OSify A.0 Universal in corso...
fs0:
if exist \\EFI\\BOOT\\BOOTX64.EFI then
    \\EFI\\BOOT\\BOOTX64.EFI
endif
if exist \\efi\\boot\\bootx64.efi then
    \\efi\\boot\\bootx64.efi
endif
fs1:
if exist \\EFI\\BOOT\\BOOTX64.EFI then
    \\EFI\\BOOT\\BOOTX64.EFI
endif
if exist \\efi\\boot\\bootx64.efi then
    \\efi\\boot\\bootx64.efi
endif
fs2:
if exist \\EFI\\BOOT\\BOOTX64.EFI then
    \\EFI\\BOOT\\BOOTX64.EFI
endif
if exist \\efi\\boot\\bootx64.efi then
    \\efi\\boot\\bootx64.efi
endif
"""
    for nsh_name in ["startup.nsh", "STARTUP.NSH"]:
        with open(os.path.join(iso_root, nsh_name), "w") as f:
            f.write(startup_nsh)

    with open(os.path.join(iso_root, "OSify-Version.txt"), "w") as f:
        f.write("OSify A.0 Universal Cover Nuda (Single Hybrid ISO: UEFI x86_64, BIOS Legacy, Vintage 32-bit)\n")

    # Pulizia preventiva del vecchio catalogo e di cartelle o file spuri
    for spuria in [
        os.path.join(iso_root, "boot/syslinux/boot.cat"),
        os.path.join(iso_root, "[BOOT]"),
        os.path.join(iso_root, "boot/isolinux"),
        os.path.join(iso_root, "isolinux"),
        os.path.join(iso_root, "isolinux.cfg")
    ]:
        if os.path.isdir(spuria):
            shutil.rmtree(spuria)
        elif os.path.isfile(spuria):
            os.remove(spuria)

    # 8. Masterizzazione con xorriso per supporto Ibrido Universale (MBR + GPT + El Torito EFI + BIOS)
    log("Masterizzazione ISO Ibrida Universale con xorriso (MBR + GPT basdat + El Torito EFI)...")
    built_iso = os.path.join(WORK_DIR, f"OSify-{OSIFY_VERSION}-Universal.iso")

    mbr_bin = os.path.join(iso_root, "boot/syslinux/isohdpfx.bin")
    efi_img = os.path.join(iso_root, "boot/grub/efi.img")

    cmd_xorriso = (
        f"xorriso -as mkisofs -r -J "
        f"-V 'OSify-2050-Gaming-x86_64' "
        f"-isohybrid-mbr '{mbr_bin}' "
        f"-partition_cyl_align on -partition_offset 0 "
        f"-partition_hd_cyl 64 -partition_sec_hd 32 --mbr-force-bootable "
        f"-iso_mbr_part_type 0x00 "
        f"-c boot/syslinux/boot.cat "
        f"-b boot/syslinux/isolinux.bin -no-emul-boot -boot-load-size 4 -boot-info-table "
        f"-eltorito-alt-boot -e boot/grub/efi.img -no-emul-boot -isohybrid-gpt-basdat "
        f"-o '{built_iso}' '{iso_root}'"
    )
    run(cmd_xorriso)

    if os.path.exists(built_iso):
        shutil.copy2(built_iso, DEST_UNIVERSAL_ISO)
        iso_size = os.path.getsize(DEST_UNIVERSAL_ISO) / (1024 * 1024)
        log(f"ISO Unica Universale creata con successo: {DEST_UNIVERSAL_ISO} ({iso_size:.1f} MB)")
    else:
        log("ERRORE: ISO non trovata.")
        sys.exit(1)

    # 9. Aggiornamento SHA256SUMS.txt
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
    
    sha_entries[f"OSify-{OSIFY_VERSION}-Universal.iso"] = univ_sha
    with open(sha_path, "w") as f:
        for fname in sorted(sha_entries.keys()):
            f.write(f"{sha_entries[fname]}  {fname}\n")
    log("Registro SHA256SUMS.txt aggiornato con successo.")

if __name__ == "__main__":
    build_universal_iso()
