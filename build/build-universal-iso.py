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
    log(f"Costruzione della ISO Unica Universale OSify {OSIFY_VERSION} (Cover Nuda)...")
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

    # 2. Inserimento del Kernel Nativo OSify Bare-Metal (osify_kernel.elf)
    kernel_src = os.path.join(REPO_ROOT, "sistema/nucleo/kernel/osify_kernel.elf")
    if not os.path.exists(kernel_src):
        log("Compilazione preventiva del Kernel Nativo Bare-Metal...")
        run("python3 build/build-baremetal-iso.py", cwd=REPO_ROOT)
    
    if os.path.exists(kernel_src):
        shutil.copy2(kernel_src, os.path.join(iso_root, "boot/osify-kernel.elf"))
        os.makedirs(os.path.join(iso_root, "boot/osify-core"), exist_ok=True)
        shutil.copy2(kernel_src, os.path.join(iso_root, "boot/osify-core/osify_kernel.elf"))
        log("  -> Kernel nativo bare-metal integrato in /boot/osify-kernel.elf")

    # 3. Integrazione dell'intero userspace nativo OSify (/Sistema, /Applicazioni, /UEM, /Desktop, /Strumenti)
    log("Integrazione dell'albero userspace completo e binari UEM...")
    dirs_to_package = [
        ("sistema", "Sistema"),
        ("system", "System"),
        ("applicazioni", "Applicazioni"),
        ("uem", "UEM"),
        ("desktop", "Desktop"),
        ("tools", "Strumenti"),
        ("security", "Sicurezza"),
        ("network", "Rete"),
        ("docs", "Documenti"),
        ("services", "Servizi"),
        ("audio", "Audio"),
        ("emulation", "Emulazione"),
        ("blocks", "Blocchi"),
        ("streaming", "Streaming")
    ]

    def ignore_patterns(path, names):
        ignored = []
        for n in names:
            if n.endswith(".o") and not n.endswith(".elf.o"):
                ignored.append(n)
            elif n in [".git", ".DS_Store", "__pycache__", ".pytest_cache"]:
                ignored.append(n)
        return set(ignored)

    for src_rel, dst_rel in dirs_to_package:
        src_path = os.path.join(REPO_ROOT, src_rel)
        dst_path = os.path.join(iso_root, dst_rel)
        if os.path.exists(src_path):
            shutil.copytree(src_path, dst_path, ignore=ignore_patterns, dirs_exist_ok=True)

    # Inclusione Programmi Reali Multi-Piattaforma (Windows PE, Linux ELF, macOS Mach-O)
    real_bin_dir = os.path.join(REPO_ROOT, "uem", "binari_reali")
    if os.path.exists(real_bin_dir):
        win_dir = os.path.join(iso_root, "UEM", "Windows")
        linux_dir = os.path.join(iso_root, "UEM", "Linux")
        mac_dir = os.path.join(iso_root, "UEM", "macOS")
        os.makedirs(win_dir, exist_ok=True)
        os.makedirs(linux_dir, exist_ok=True)
        os.makedirs(mac_dir, exist_ok=True)
        for f in ["compat_win.exe", "compat_win64.exe", "putty.exe", "7z.exe", "syslinux.exe"]:
            src = os.path.join(real_bin_dir, f)
            if os.path.exists(src):
                shutil.copy2(src, os.path.join(win_dir, f))
                if f == "compat_win.exe":
                    shutil.copy2(src, os.path.join(iso_root, "UEM", f))
        for f in ["server.elf"]:
            src = os.path.join(real_bin_dir, f)
            if os.path.exists(src):
                shutil.copy2(src, os.path.join(linux_dir, f))
                shutil.copy2(src, os.path.join(iso_root, "UEM", f))
        for f in ["darwin_tool.macho"]:
            src = os.path.join(real_bin_dir, f)
            if os.path.exists(src):
                shutil.copy2(src, os.path.join(mac_dir, f))
                shutil.copy2(src, os.path.join(iso_root, "UEM", f))

    # Identita e Manifesto Autonomo
    with open(os.path.join(iso_root, "OSify-Identity.txt"), "w") as f:
        f.write("OSify Versione A.1 Universal Cover Nuda\n")
        f.write("Sistema Operativo Universale per Qualsiasi Architettura e Firmware\n")
        f.write("Ingegnerizzato con orgoglio da Andrea Taliento (ANDRYXify)\n")
        f.write("Supporto Ibrido: UEFI x86_64, BIOS Legacy, Vintage 32-bit, Bare-Metal Multiboot.\n")

    manifesto_path = os.path.join(REPO_ROOT, "desktop", "manifesto.json")
    if os.path.exists(manifesto_path):
        shutil.copy2(manifesto_path, os.path.join(iso_root, "manifesto.json"))

    # 4. Bootsplash universale solo-logo (senza testi)
    splash_src = os.path.join(tmp_vintage, "boot/isolinux/splash.jpg")
    for s_dst in ["boot/syslinux/splash.jpg", "boot/isolinux/splash.jpg", "isolinux/splash.jpg", "splash.jpg"]:
        d_p = os.path.join(iso_root, s_dst)
        os.makedirs(os.path.dirname(d_p), exist_ok=True)
        if os.path.exists(splash_src):
            shutil.copy2(splash_src, d_p)
        else:
            create_boot_splash(d_p)

    # 5. Moduli Syslinux di auto-rilevamento silicio da toolchain coerente (build/syslinux_alpine)
    syslinux_alpine_dir = os.path.join(REPO_ROOT, "build/syslinux_alpine")
    syslinux_dst_dir = os.path.join(iso_root, "boot/syslinux")
    os.makedirs(syslinux_dst_dir, exist_ok=True)
    for mod in ["isolinux.bin", "isohdpfx.bin", "ldlinux.c32", "libcom32.c32", "libutil.c32", "vesamenu.c32", "menu.c32", "ifcpu64.c32", "mboot.c32"]:
        mod_src = os.path.join(syslinux_alpine_dir, mod)
        if os.path.exists(mod_src):
            shutil.copy2(mod_src, os.path.join(syslinux_dst_dir, mod))

    # 6. Configurazione Syslinux / Isolinux per BIOS Legacy con Auto-Detect CPU
    isolinux_cfg = """DEFAULT autodetect
UI vesamenu.c32
PROMPT 0
TIMEOUT 40
ONTIMEOUT autodetect

MENU TITLE OSify vA.1 Universal Sovrano (Cover Nuda)
MENU BACKGROUND splash.jpg
MENU WIDTH 78
MENU MARGIN 6
MENU ROWS 8
MENU VSHIFT 12
MENU TABMSG Premi TAB per modificare i parametri di avvio

LABEL autodetect
    MENU LABEL OSify vA.1 (Auto-Rilevamento Silicio 32/64-bit) [PREDEFINITO]
    COM32 ifcpu64.c32
    APPEND osify64 -- osify32

LABEL osify64
    MENU LABEL OSify vA.1 (Live Desktop & Gaming x86_64)
    KERNEL /boot/vmlinuz-lts
    INITRD /boot/initramfs-lts
    APPEND modules=loop,squashfs,sd-mod,usb-storage keep_apk_new=yes quiet splash loglevel=0 console=tty3 vt.global_cursor_default=0 logo.nologo rw autologin

LABEL osify32
    MENU LABEL OSify vA.1 (Vintage 32-bit / Netbook & Macchine Storiche)
    KERNEL /boot/bzImage
    INITRD /boot/rootfs4.gz
    APPEND root=/dev/null video=-32 tmpram=0 autologin lang=it_IT kmap=it rw quiet splash loglevel=0 console=tty3 vt.global_cursor_default=0 logo.nologo

LABEL install
    MENU LABEL Installa OSify su Disco Fisso Permanente (GPT / UEFI / BIOS)
    KERNEL /boot/vmlinuz-lts
    INITRD /boot/initramfs-lts
    APPEND modules=loop,squashfs,sd-mod,usb-storage keep_apk_new=yes osify.install=1 quiet splash loglevel=0 console=tty3 vt.global_cursor_default=0 logo.nologo rw autologin

LABEL baremetal
    MENU LABEL OSify vA.1 (Kernel Nativo Bare-Metal / Micro-Core No-libc)
    KERNEL mboot.c32
    APPEND /boot/osify-kernel.elf

LABEL safe
    MENU LABEL OSify vA.1 (Modalita Compatibile / Safe Graphics VESA)
    KERNEL /boot/vmlinuz-lts
    INITRD /boot/initramfs-lts
    APPEND modules=loop,squashfs,sd-mod,usb-storage keep_apk_new=yes nomodeset vga=788 quiet loglevel=1 vt.global_cursor_default=0 logo.nologo console=tty1 rw autologin

LABEL memtest
    MENU LABEL Diagnostica Hardware Memoria RAM (Memtest86+)
    KERNEL /boot/memtest.exe
"""
    with open(os.path.join(syslinux_dst_dir, "isolinux.cfg"), "w") as f:
        f.write(isolinux_cfg)
    with open(os.path.join(syslinux_dst_dir, "syslinux.cfg"), "w") as f:
        f.write(isolinux_cfg)

    # 7. Configurazione GRUB per UEFI 64-bit
    grub_cfg = """set timeout=5
set default=0

menuentry "OSify vA.1 Universal Live (Desktop & Gaming 64-bit)" {
    linux /boot/vmlinuz-lts modules=loop,squashfs,sd-mod,usb-storage keep_apk_new=yes quiet splash loglevel=0 console=tty1 console=ttyS0 vt.global_cursor_default=0 logo.nologo rd.systemd.show_status=false rd.udev.log_priority=0 udev.log_priority=0 rw autologin
    initrd /boot/initramfs-lts
}

menuentry "OSify vA.1 Installa su Disco Fisso Permanente (GPT / UEFI)" {
    linux /boot/vmlinuz-lts modules=loop,squashfs,sd-mod,usb-storage keep_apk_new=yes osify.install=1 quiet splash loglevel=0 console=tty1 console=ttyS0 vt.global_cursor_default=0 logo.nologo rw autologin
    initrd /boot/initramfs-lts
}

menuentry "OSify vA.1 Modalita Compatibile (Safe Graphics VESA / nomodeset)" {
    linux /boot/vmlinuz-lts modules=loop,squashfs,sd-mod,usb-storage keep_apk_new=yes nomodeset vga=788 quiet loglevel=1 vt.global_cursor_default=0 logo.nologo console=tty1 rw autologin
    initrd /boot/initramfs-lts
}

menuentry "OSify vA.1 Bare-Metal Nativo (Micro-Core Diretto Multiboot)" {
    multiboot /boot/osify-kernel.elf
    boot
}
"""
    for g_dir in ["boot/grub", "efi/boot", "EFI/BOOT"]:
        gd = os.path.join(iso_root, g_dir)
        os.makedirs(gd, exist_ok=True)
        with open(os.path.join(gd, "grub.cfg"), "w") as f:
            f.write(grub_cfg)

    # 8. Script di avvio automatico EDK II / UEFI Shell (startup.nsh)
    startup_nsh = """@echo -off
cls
echo Avvio OSify vA.1 Universal in corso...
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
        f.write("OSify vA.1 Universal Cover Nuda (Single Hybrid ISO: UEFI x86_64, BIOS Legacy, Vintage 32-bit, Bare-Metal)\n")

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
        out_root_iso = os.path.join(REPO_ROOT, "build/out", f"OSify-{OSIFY_VERSION}-Universal.iso")
        shutil.copy2(built_iso, out_root_iso)
        iso_size = os.path.getsize(DEST_UNIVERSAL_ISO) / (1024 * 1024)
        log(f"ISO Unica Universale creata con successo: {DEST_UNIVERSAL_ISO} ({iso_size:.1f} MB)")
        log(f"Copia parallela creata in: {out_root_iso}")
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
