#!/usr/bin/env python3
# ==============================================================================
# OSify Bare-Metal ISO Builder (build/build-baremetal-iso.py)
# ==============================================================================
# Ingegnerizzato da Andrea Taliento (ANDRYXify) per OSify
# Assembla e genera l'immagine ISO autonoma bare-metal OSify-A.1-BareMetal.iso
# pronta per essere scritta su pennetta USB e avviata sul silicio.
# Zero distribuzioni terze: OSify al 100% dal bootloader al desktop.
# ==============================================================================

import os
import sys
import struct
import shutil
import subprocess

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
KERNEL_DIR = os.path.join(REPO_ROOT, "sistema", "nucleo", "kernel")
BUILD_OUT  = os.path.join(REPO_ROOT, "build", "out")
ISO_OUTPUT = os.path.join(BUILD_OUT, "OSify-A.1-BareMetal.iso")
ISO_LABEL  = "OSIFY_A1"

def log(msg):
    print(f"[+] {msg}")

def ensure_dirs():
    os.makedirs(BUILD_OUT, exist_ok=True)

def build_kernel():
    log("Compilazione del Kernel Nativo ELF OSify bare-metal...")
    compile_cmd = (
        "clang -target i386-unknown-none-elf -c boot/boot.S -o boot/boot.elf.o && "
        "for f in core/osify_skin_core.c core/osify_memory.c core/osify_level0_security.c "
        "         core/osify_kstring.c core/osify_idt.c core/osify_main.c core/osify_syscall.c core/osify_synch.c "
        "         core/osify_hetero_dispatch.c "
        "         security/osify_anticheat_guard.c "
        "         drivers/osify_native_graphics.c drivers/osify_font.c drivers/osify_ps2_input.c "
        "         drivers/osify_storage.c drivers/osify_desktop_wm.c "
        "         drivers/osify_net.c drivers/osify_audio.c drivers/osify_installer.c "
        "         drivers/osify_capture_card.c "
        "         compat/osify_universal_bridge.c compat/osify_path_unifier.c "
        "         loaders/osify_binary_loader.c; do "
        "    clang -target i386-unknown-none-elf -ffreestanding -fno-pie -fno-stack-protector -mno-red-zone -mno-sse -mno-sse2 -mno-mmx -Wall -Wextra -O2 -Iinclude -c \"$f\" -o \"${f%.c}.elf.o\" || exit 1; "
        "done && "
        "/opt/homebrew/bin/i686-elf-ld -T boot/kernel.ld -m elf_i386 -nostdlib -static "
        "    boot/boot.elf.o "
        "    core/*.elf.o security/*.elf.o drivers/*.elf.o compat/*.elf.o loaders/*.elf.o "
        "    -o osify_kernel.elf"
    )
    res = subprocess.run(compile_cmd, shell=True, cwd=KERNEL_DIR, capture_output=True, text=True)
    if res.returncode != 0:
        print("Errore compilazione:", res.stderr)
        sys.exit(1)
    log("Kernel bare-metal compilato con successo (osify_kernel.elf pronto).")

def generate_baremetal_iso():
    log(f"Generazione immagine ISO Bare-Metal COMPLETA: {ISO_OUTPUT}...")
    iso_root = os.path.join(BUILD_OUT, "iso_baremetal_root")
    if os.path.exists(iso_root):
        shutil.rmtree(iso_root)
    os.makedirs(iso_root, exist_ok=True)
    
    boot_dir = os.path.join(iso_root, "boot")
    syslinux_dir = os.path.join(boot_dir, "syslinux")
    grub_dir = os.path.join(boot_dir, "grub")
    os.makedirs(boot_dir, exist_ok=True)
    os.makedirs(syslinux_dir, exist_ok=True)
    os.makedirs(grub_dir, exist_ok=True)

    # 1. Copia del Kernel Nativo ELF OSify Bare-Metal
    kernel_src = os.path.join(KERNEL_DIR, "osify_kernel.elf")
    kernel_dest = os.path.join(boot_dir, "osify-kernel.elf")
    shutil.copy2(kernel_src, kernel_dest)
    log(f"Kernel nativo installato in ISO: {kernel_dest}")

    # 2. Setup Bootloader Multiboot Syslinux (mboot.c32) per BIOS/Bare-Metal
    syslinux_src_dir = os.path.join(REPO_ROOT, "build", "syslinux_alpine")
    required_boot_files = [
        "isolinux.bin", "ldlinux.c32", "libcom32.c32", "libutil.c32",
        "mboot.c32", "isohdpfx.bin"
    ]
    for bf in required_boot_files:
        src_f = os.path.join(syslinux_src_dir, bf)
        if os.path.exists(src_f):
            shutil.copy2(src_f, os.path.join(syslinux_dir, bf))
    
    isolinux_cfg = (
        "DEFAULT osify\n"
        "PROMPT 0\n"
        "TIMEOUT 10\n"
        "LABEL osify\n"
        "    MENU LABEL OSify vA.1 Bare-Metal Nativo (100% Autonomo)\n"
        "    KERNEL mboot.c32\n"
        "    APPEND /boot/osify-kernel.elf\n"
    )
    with open(os.path.join(syslinux_dir, "isolinux.cfg"), "w") as f:
        f.write(isolinux_cfg)
    with open(os.path.join(syslinux_dir, "syslinux.cfg"), "w") as f:
        f.write(isolinux_cfg)

    # 3. Setup GRUB Multiboot config
    grub_cfg = (
        "set timeout=0\n"
        "set default=0\n\n"
        "menuentry 'OSify vA.1 Bare-Metal Nativo' {\n"
        "    multiboot /boot/osify-kernel.elf\n"
        "    boot\n"
        "}\n"
    )
    with open(os.path.join(grub_dir, "grub.cfg"), "w") as f:
        f.write(grub_cfg)

    # 4. Impacchettamento Completo di TUTTO l'albero di sistema e Userspace OSify
    log("Integrazione dell'intero userspace nativo OSify...")
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
            log(f"  -> Integrato comparto: {src_rel} => /{dst_rel}")

    # Creazione profilo utente predefinito
    utenti_dir = os.path.join(iso_root, "Utenti", "Compagno")
    for udir in ["Scrivania", "Documenti", "Scaricati", "Applicazioni", "Impostazioni"]:
        os.makedirs(os.path.join(utenti_dir, udir), exist_ok=True)

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
                # Copia anche in UEM radice per accesso diretto
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
        log("  -> Inclusi programmi reali: Windows (PuTTY, 7-Zip, Syslinux, WinCompat), Linux (server.elf), macOS (darwin_tool.macho)")

    # Identita e Manifesto Autonomo
    with open(os.path.join(iso_root, "OSify-Identity.txt"), "w") as f:
        f.write("OSify Versione A.1 (Naked-Skin Architecture)\n")
        f.write("Sistema Operativo Autonomo Universale al 100%\n")
        f.write("Ingegnerizzato con orgoglio da Andrea Taliento (ANDRYXify)\n")
        f.write("Stato: Indipendente, Completo, Zero Basi Terze.\n")

    manifesto_path = os.path.join(REPO_ROOT, "desktop", "manifesto.json")
    if os.path.exists(manifesto_path):
        shutil.copy2(manifesto_path, os.path.join(iso_root, "manifesto.json"))

    # 5. Generazione dell'immagine ISO con xorriso
    log("Masterizzazione ISO con xorriso...")
    xorriso_bin = "/opt/homebrew/bin/xorriso"
    if not os.path.exists(xorriso_bin):
        xorriso_bin = shutil.which("xorriso")
    if not xorriso_bin:
        raise RuntimeError("xorriso non trovato nel sistema!")

    mbr_bin = os.path.join(syslinux_dir, "isohdpfx.bin")
    boot_bin = "boot/syslinux/isolinux.bin"
    boot_cat = "boot/syslinux/boot.cat"

    cmd = [
        xorriso_bin,
        "-as", "mkisofs",
        "-r", "-J", "-joliet-long",
        "-V", ISO_LABEL,
        "-isohybrid-mbr", mbr_bin,
        "-partition_cyl_align", "on",
        "-partition_offset", "0",
        "-c", boot_cat,
        "-b", boot_bin,
        "-no-emul-boot",
        "-boot-load-size", "4",
        "-boot-info-table",
        "-o", ISO_OUTPUT,
        iso_root
    ]

    log(f"Esecuzione: {' '.join(cmd)}")
    res = subprocess.run(cmd, capture_output=True, text=True)
    if res.returncode != 0:
        log(f"ERRORE xorriso: {res.stderr}")
        sys.exit(1)

    iso_bytes = os.path.getsize(ISO_OUTPUT)
    iso_mb = iso_bytes / (1024 * 1024)
    log(f"ISO Bare-Metal generata con successo: {ISO_OUTPUT} ({iso_mb:.2f} MB, {iso_bytes} bytes).")

    # Copia anche in release
    release_dir = os.path.join(BUILD_OUT, "release")
    os.makedirs(release_dir, exist_ok=True)
    release_iso = os.path.join(release_dir, "OSify-A.1-BareMetal.iso")
    shutil.copy2(ISO_OUTPUT, release_iso)
    log(f"ISO Bare-Metal copiata in release: {release_iso}")
    return True

def main():
    log("=== Avvio Pipeline ISO Bare-Metal OSify A.1 COMPLETA ===")
    ensure_dirs()
    build_kernel()
    generate_baremetal_iso()
    log("=== Procedura completata: OSify e un OS a se stante al 100%! ===")

if __name__ == "__main__":
    main()

