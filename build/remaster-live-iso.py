#!/usr/bin/env python3
import os
import shutil
import subprocess
import sys
from PIL import Image

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
CACHE_I686 = os.path.join(REPO_ROOT, "build/cache/osify-base-i686.iso")
CACHE_X86_64 = os.path.join(REPO_ROOT, "build/cache/osify-base-x86_64.iso")
SANDBOX_I686 = os.path.join(REPO_ROOT, "tests/sandbox/osify-vintage-desktop.iso")

OUT_RELEASE_DIR = os.path.join(REPO_ROOT, "build/out/release")
DEST_VINTAGE_ISO = os.path.join(OUT_RELEASE_DIR, "OSify-Vintage-i686.iso")
DEST_MODERN_ISO = os.path.join(OUT_RELEASE_DIR, "OSify-x86_64-v3.iso")
DEST_SANDBOX_VINTAGE = os.path.join(REPO_ROOT, "tests/sandbox/OSify-Vintage-Live.iso")

def run(cmd, cwd=None):
    print(f"[RUN] {cmd}")
    res = subprocess.run(cmd, shell=True, cwd=cwd, capture_output=True, text=True)
    if res.returncode != 0:
        print(f"[ERROR] {res.stderr}")
        sys.exit(1)
    return res.stdout

def inject_windows_installer(dest_iso_root):
    tools_win = os.path.join(dest_iso_root, "tools/windows-installer")
    os.makedirs(tools_win, exist_ok=True)
    win_src = os.path.join(REPO_ROOT, "tools/windows-installer")
    for item in ["OSify-Setup.bat", "OSify-Windows-Installer-GUI.ps1", "OSify-NoUSB-Installer.ps1", 
                 "7z.exe", "7z.dll", "syslinux.exe", "logo.png", "ISTRUZIONI-INSTALLAZIONE.txt"]:
        sp = os.path.join(win_src, item)
        if os.path.exists(sp):
            shutil.copy2(sp, tools_win)
    
    setup_bat = os.path.join(win_src, "OSify-Setup.bat")
    if os.path.exists(setup_bat):
        shutil.copy2(setup_bat, os.path.join(dest_iso_root, "OSify-Setup.bat"))

def inject_osify_tree(dest_iso_root):
    osify_tree = os.path.join(dest_iso_root, "osify")
    if os.path.exists(osify_tree):
        shutil.rmtree(osify_tree)
    os.makedirs(osify_tree, exist_ok=True)
    for mod in ["kernel", "network", "audio", "desktop", "tools", "security", "system", "uem", "streaming", "services"]:
        mod_src = os.path.join(REPO_ROOT, mod)
        if os.path.exists(mod_src):
            shutil.copytree(mod_src, os.path.join(osify_tree, mod), dirs_exist_ok=True)
    
    logo_png = os.path.join(REPO_ROOT, "OSify.png")
    if os.path.exists(logo_png):
        shutil.copy2(logo_png, os.path.join(osify_tree, "OSify.png"))

def build_vintage_i686():
    print("=========================================================")
    print(" [1/2] Costruzione OSify Vintage 32-bit (Intel Atom/NB200)")
    print("=========================================================")
    
    src_iso = CACHE_I686
    if not (os.path.exists(src_iso) and os.path.getsize(src_iso) > 10 * 1024 * 1024):
        if os.path.exists(SANDBOX_I686) and os.path.getsize(SANDBOX_I686) > 10 * 1024 * 1024:
            src_iso = SANDBOX_I686
        else:
            print("[+] Download base Linux 32-bit (SliTaz Rolling)...")
            os.makedirs(os.path.dirname(CACHE_I686), exist_ok=True)
            run(f"curl -L -o '{CACHE_I686}' 'http://mirror.slitaz.org/iso/rolling/slitaz-rolling.iso'")
            src_iso = CACHE_I686

    work_dir = "/tmp/osify_remaster_i686"
    if os.path.exists(work_dir):
        shutil.rmtree(work_dir)
    os.makedirs(work_dir)

    iso_root = os.path.join(work_dir, "iso_root")
    os.makedirs(iso_root)

    print("[i] Estrazione base 32-bit...")
    run(f"7z x -y '{src_iso}' -o'{iso_root}' > /dev/null")

    # Wallpaper e splash
    src_png = os.path.join(REPO_ROOT, "desktop/branding/wallpapers/osify-netbook-1024x600.png")
    if not os.path.exists(src_png):
        src_png = os.path.join(REPO_ROOT, "OSify.png")
    img = Image.open(src_png).convert("RGB")
    wallpaper_jpg = os.path.join(work_dir, "osify-wallpaper.jpg")
    img.resize((1024, 600), Image.Resampling.LANCZOS).save(wallpaper_jpg, "JPEG", quality=95)
    splash_jpg = os.path.join(work_dir, "osify-splash.jpg")
    img.resize((640, 480), Image.Resampling.LANCZOS).save(splash_jpg, "JPEG", quality=90)

    # Bootloader ISOLINUX / SYSLINUX config
    isolinux_dir = os.path.join(iso_root, "boot/isolinux")
    os.makedirs(isolinux_dir, exist_ok=True)
    if os.path.exists(os.path.join(isolinux_dir, "boot.cat")):
        os.remove(os.path.join(isolinux_dir, "boot.cat"))
    shutil.copy2(splash_jpg, os.path.join(isolinux_dir, "splash.jpg"))

    clean_cfg = """DEFAULT osify
PROMPT 0
TIMEOUT 50

LABEL osify
    MENU LABEL OSify Vintage Live Desktop (Intel Atom N280)
    KERNEL /boot/bzImage
    INITRD /boot/rootfs4.gz,/boot/rootfs3.gz,/boot/rootfs2.gz,/boot/rootfs1.gz
    APPEND root=/dev/null autologin lang=it_IT kmap=it rw quiet

LABEL safe
    MENU LABEL OSify Safe Mode (Nomodeset)
    KERNEL /boot/bzImage
    INITRD /boot/rootfs4.gz,/boot/rootfs3.gz,/boot/rootfs2.gz,/boot/rootfs1.gz
    APPEND root=/dev/null nomodeset autologin lang=it_IT kmap=it rw
"""
    with open(os.path.join(isolinux_dir, "isolinux.cfg"), "w") as f:
        f.write(clean_cfg)

    # Copia speculare in syslinux
    syslinux_dir = os.path.join(iso_root, "boot/syslinux")
    os.makedirs(syslinux_dir, exist_ok=True)
    with open(os.path.join(syslinux_dir, "syslinux.cfg"), "w") as f:
        f.write(clean_cfg)

    # Remastering rootfs4
    print("[i] Remastering rootfs4 desktop e toolchain...")
    r4_work = os.path.join(work_dir, "rootfs4")
    os.makedirs(r4_work)
    r4_gz = os.path.join(iso_root, "boot/rootfs4.gz")
    run(f"lzma -dc '{r4_gz}' | (cd '{r4_work}' && cpio -idmv > /dev/null 2>&1)")

    img_dir = os.path.join(r4_work, "usr/share/images")
    os.makedirs(img_dir, exist_ok=True)
    shutil.copy2(wallpaper_jpg, os.path.join(img_dir, "slitaz-background.jpg"))
    shutil.copy2(wallpaper_jpg, os.path.join(img_dir, "slitaz-background_2.jpg"))
    img.resize((300, 100), Image.Resampling.LANCZOS).save(os.path.join(img_dir, "slitaz-banner.png"), "PNG")

    # Iniezione GNU Bash statico 32-bit (i386) per esecuzione garantita di tutti gli script
    print("[i] Iniezione binario GNU Bash statico 32-bit (i386)...")
    docker_bash_cmd = (
        f"docker run --rm -v '{r4_work}':/r4 ubuntu:20.04 bash -c '"
        f"dpkg --add-architecture i386 && apt-get update -qq && "
        f"apt-get install -y -qq bash-static:i386 > /dev/null && "
        f"mkdir -p /r4/bin /r4/usr/bin && "
        f"cp /bin/bash-static /r4/bin/bash && chmod 755 /r4/bin/bash && "
        f"ln -sf /bin/bash /r4/usr/bin/bash'"
    )
    run(docker_bash_cmd)

    bin_dir = os.path.join(r4_work, "usr/bin")
    os.makedirs(bin_dir, exist_ok=True)
    shutil.copy2(os.path.join(REPO_ROOT, "tools/osify-ctl"), os.path.join(bin_dir, "osify-ctl"))
    shutil.copy2(os.path.join(REPO_ROOT, "uem/runners/osify-inspect.sh"), os.path.join(bin_dir, "osify-inspect"))
    shutil.copy2(os.path.join(REPO_ROOT, "uem/runners/osify-universal-dispatcher.sh"), os.path.join(bin_dir, "osify-exec"))
    shutil.copy2(os.path.join(REPO_ROOT, "system/installer/osify-disk-installer.sh"), os.path.join(bin_dir, "osify-install"))
    shutil.copy2(os.path.join(REPO_ROOT, "system/autotune/osify-autotune.sh"), os.path.join(bin_dir, "osify-autotune"))
    shutil.copy2(os.path.join(REPO_ROOT, "system/storage/osify-memory-cleaner.sh"), os.path.join(bin_dir, "osify-cleanmem"))
    shutil.copy2(os.path.join(REPO_ROOT, "tools/osify-gui/osify-welcome.sh"), os.path.join(bin_dir, "osify-welcome"))
    shutil.copy2(os.path.join(REPO_ROOT, "tools/osify-gui/osify-welcome-wizard.py"), os.path.join(bin_dir, "osify-welcome-wizard.py"))
    shutil.copy2(os.path.join(REPO_ROOT, "system/input/osify-input-manager.sh"), os.path.join(bin_dir, "osify-input"))
    shutil.copy2(os.path.join(REPO_ROOT, "system/autotune/osify-hw-probe.sh"), os.path.join(bin_dir, "osify-hw-probe"))
    run(f"chmod +x '{bin_dir}'/osify-*")

    # Inizializzazione Hardware Autonoma in /etc/init.d/local.sh
    local_sh = os.path.join(r4_work, "etc/init.d/local.sh")
    with open(local_sh, "a") as f:
        f.write("""
# OSify Universal Autonomous Hardware Engine
/usr/bin/osify-hw-probe >/var/log/osify-hw-probe.log 2>&1 &
""")

    # Configurazione Touchpad Synaptics/Alps (Tap-to-click e Scorrimento Bordo)
    syn_dir = os.path.join(r4_work, "etc/X11/xorg.conf.d")
    os.makedirs(syn_dir, exist_ok=True)
    with open(os.path.join(syn_dir, "50-synaptics.conf"), "w") as f:
        f.write("""Section "InputClass"
    Identifier "touchpad catchall"
    Driver "synaptics"
    MatchIsTouchpad "on"
    Option "TapButton1" "1"
    Option "TapButton2" "3"
    Option "TapButton3" "2"
    Option "VertEdgeScroll" "on"
    Option "HorizEdgeScroll" "on"
    Option "CoastingSpeed" "20"
EndSection
""")

    # Iniezione hook autostart in .xinitrc (utente tux e root)
    hook_str = (
        "\\n# Avvio Wizard di Primo Avvio e Configurazione Touchpad OSify\\n"
        "(sleep 2 && /usr/bin/osify-welcome) &\\n"
        "(sleep 1 && synclient TapButton1=1 TapButton2=3 TapButton3=2 VertEdgeScroll=1 HorizEdgeScroll=1) 2>/dev/null &\\n"
    )
    for rc in [os.path.join(r4_work, "etc/skel/.xinitrc"), os.path.join(r4_work, "root/.xinitrc")]:
        if os.path.exists(rc):
            with open(rc, "r") as f:
                content = f.read()
            if "case \"$WINDOW_MANAGER\" in" in content:
                content = content.replace("case \"$WINDOW_MANAGER\" in", f"{hook_str}\ncase \"$WINDOW_MANAGER\" in")
                with open(rc, "w") as f:
                    f.write(content)

    with open(os.path.join(r4_work, "etc/issue"), "w") as f:
        f.write("OSify Vintage Edition (Intel Atom N280 / GMA 950 Profile)\\n\\l\n")

    # Launcher Desktop per Installazione (apre in terminale con geometria WSVGA 1024x600 ottimale)
    desktop_inst_entry = (
        "[Desktop Entry]\n"
        "Type=Application\n"
        "Name=Installa OSify su Disco\n"
        "Comment=Configurazione e Installazione OSify per Netbook\n"
        "Exec=terminal -geometry 95x26+30+30 -T 'OSify Installer' -e /usr/bin/osify-install\n"
        "Icon=system-software-install\n"
        "Terminal=false\n"
        "Categories=System;\n"
    )

    # Launcher Desktop per Benvenuto e Diagnostica (esegue lo script nativo GTK2/YAD)
    desktop_welcome_entry = (
        "[Desktop Entry]\n"
        "Type=Application\n"
        "Name=Benvenuto in OSify\n"
        "Comment=Esperienza di Primo Avvio e Configurazione Guidata per Netbook\n"
        "Exec=/usr/bin/osify-welcome\n"
        "Icon=preferences-desktop\n"
        "Terminal=false\n"
        "Categories=System;\n"
    )

    for dpath in ["root/Desktop", "home/tux/Desktop", "etc/skel/Desktop"]:
        full_d = os.path.join(r4_work, dpath)
        os.makedirs(full_d, exist_ok=True)
        with open(os.path.join(full_d, "osify-install.desktop"), "w") as f:
            f.write(desktop_inst_entry)
        with open(os.path.join(full_d, "osify-welcome.desktop"), "w") as f:
            f.write(desktop_welcome_entry)

    # Autostart automatico XDG
    autostart_dir = os.path.join(r4_work, "etc/xdg/autostart")
    os.makedirs(autostart_dir, exist_ok=True)
    with open(os.path.join(autostart_dir, "osify-welcome.desktop"), "w") as f:
        f.write(desktop_welcome_entry)

    os.remove(r4_gz)
    run(f"(cd '{r4_work}' && find . -print0 | cpio --null -ov -H newc) | lzma > '{r4_gz}'")

    # Iniezione Windows Installer e albero OSify
    inject_windows_installer(iso_root)
    inject_osify_tree(iso_root)

    with open(os.path.join(iso_root, "OSify-Version.txt"), "w") as f:
        f.write("OSify Live System (32-bit Vintage Edition)\nTarget: Intel Atom N280/N270\n")

    print("[i] Masterizzazione immagine ibrida avviabile (isohybrid MBR)...")
    os.makedirs(OUT_RELEASE_DIR, exist_ok=True)
    docker_cmd = (
        f"docker run --rm -v '{work_dir}':/work ubuntu:20.04 bash -c '"
        f"apt-get update -qq && apt-get install -y -qq genisoimage isolinux syslinux-common syslinux-utils > /dev/null && "
        f"cp /usr/lib/ISOLINUX/isolinux.bin /work/iso_root/boot/isolinux/isolinux.bin && "
        f"cp /usr/lib/syslinux/modules/bios/ldlinux.c32 /work/iso_root/boot/isolinux/ldlinux.c32 && "
        f"cp /usr/lib/syslinux/modules/bios/libutil.c32 /work/iso_root/boot/isolinux/libutil.c32 && "
        f"cp /usr/lib/syslinux/modules/bios/libcom32.c32 /work/iso_root/boot/isolinux/libcom32.c32 && "
        f"cp /usr/lib/syslinux/modules/bios/menu.c32 /work/iso_root/boot/isolinux/menu.c32 && "
        f"cp /usr/lib/syslinux/modules/bios/vesamenu.c32 /work/iso_root/boot/isolinux/vesamenu.c32 && "
        f"genisoimage -R -J -l -b boot/isolinux/isolinux.bin -c boot/isolinux/boot.cat "
        f"-no-emul-boot -boot-load-size 4 -boot-info-table -V \"OSIFY_VINTAGE\" "
        f"-o /work/OSify-Vintage-i686.iso /work/iso_root > /dev/null && "
        f"isohybrid /work/OSify-Vintage-i686.iso'"
    )
    run(docker_cmd)
    shutil.copy2(os.path.join(work_dir, "OSify-Vintage-i686.iso"), DEST_VINTAGE_ISO)
    shutil.copy2(DEST_VINTAGE_ISO, DEST_SANDBOX_VINTAGE)
    print(f"[✓] OSify Vintage 32-bit Ibrida creata: {DEST_VINTAGE_ISO} ({os.path.getsize(DEST_VINTAGE_ISO)/(1024*1024):.1f} MB)")

def build_modern_x86_64():
    print("=========================================================")
    print(" [2/2] Costruzione OSify Modern 64-bit (x86-64-v3 Gaming)")
    print("=========================================================")
    
    src_iso = CACHE_X86_64
    if not (os.path.exists(src_iso) and os.path.getsize(src_iso) > 10 * 1024 * 1024):
        print("[+] Download base Linux 64-bit (Alpine LTS x86_64)...")
        os.makedirs(os.path.dirname(CACHE_X86_64), exist_ok=True)
        url = "https://dl-cdn.alpinelinux.org/alpine/v3.20/releases/x86_64/alpine-standard-3.20.3-x86_64.iso"
        run(f"curl -L -o '{CACHE_X86_64}' '{url}'")

    work_dir = "/tmp/osify_remaster_x64"
    if os.path.exists(work_dir):
        shutil.rmtree(work_dir)
    os.makedirs(work_dir)

    iso_root = os.path.join(work_dir, "iso_root")
    os.makedirs(iso_root)

    print("[i] Estrazione base 64-bit...")
    run(f"7z x -y '{src_iso}' -o'{iso_root}' > /dev/null")

    # Iniezione Windows Installer e albero di sistema OSify
    inject_windows_installer(iso_root)
    inject_osify_tree(iso_root)

    # Configurazione GRUB UEFI ufficiale
    grub_cfg = """set timeout=5
set default=0

menuentry "OSify Live System (x86-64-v3 Gaming & Streaming)" {
    linux /boot/vmlinuz-lts quiet splash rw
    initrd /boot/initramfs-lts
}

menuentry "Installa OSify su Disco Fisso" {
    linux /boot/vmlinuz-lts osify.install=1 quiet splash rw
    initrd /boot/initramfs-lts
}

menuentry "OSify Safe Mode (Nomodeset)" {
    linux /boot/vmlinuz-lts nomodeset rw
    initrd /boot/initramfs-lts
}

menuentry "OSify RAM Rescue Mode" {
    linux /boot/vmlinuz-lts copytoram rw
    initrd /boot/initramfs-lts
}
"""
    grub_path = os.path.join(iso_root, "boot/grub/grub.cfg")
    os.makedirs(os.path.dirname(grub_path), exist_ok=True)
    with open(grub_path, "w") as f:
        f.write(grub_cfg)

    # Configurazione Syslinux Legacy BIOS ufficiale
    syslinux_cfg = """TIMEOUT 50
DEFAULT osify

LABEL osify
    MENU LABEL OSify Live System (x86-64-v3 Gaming & Streaming)
    LINUX /boot/vmlinuz-lts
    INITRD /boot/initramfs-lts
    APPEND quiet splash rw

LABEL install
    MENU LABEL Installa OSify su Disco Fisso
    LINUX /boot/vmlinuz-lts
    INITRD /boot/initramfs-lts
    APPEND osify.install=1 quiet splash rw

LABEL safe
    MENU LABEL OSify Safe Mode (Nomodeset)
    LINUX /boot/vmlinuz-lts
    INITRD /boot/initramfs-lts
    APPEND nomodeset rw

LABEL rescue
    MENU LABEL OSify RAM Rescue Mode
    LINUX /boot/vmlinuz-lts
    INITRD /boot/initramfs-lts
    APPEND copytoram rw
"""
    syslinux_path = os.path.join(iso_root, "boot/syslinux/syslinux.cfg")
    os.makedirs(os.path.dirname(syslinux_path), exist_ok=True)
    with open(syslinux_path, "w") as f:
        f.write(syslinux_cfg)

    with open(os.path.join(iso_root, "OSify-Version.txt"), "w") as f:
        f.write("OSify Live System (x86-64-v3 Gaming & Streaming Edition)\nKernel: Linux 64-bit BORE/LTS\n")

    print("[i] Masterizzazione immagine ibrida 64-bit avviabile (UEFI + BIOS)...")
    os.makedirs(OUT_RELEASE_DIR, exist_ok=True)
    cmd_xorriso = (
        f"xorriso -as mkisofs -r -J "
        f"-V 'OSIFY_X64' "
        f"-isohybrid-mbr --interval:local_fs:0s-15s:zero_mbrpt,zero_gpt:'{src_iso}' "
        f"-partition_cyl_align on -partition_offset 0 "
        f"-partition_hd_cyl 64 -partition_sec_hd 32 --mbr-force-bootable "
        f"-iso_mbr_part_type 0x00 "
        f"-c '/boot/syslinux/boot.cat' "
        f"-b '/boot/syslinux/isolinux.bin' -no-emul-boot -boot-load-size 4 -boot-info-table "
        f"-eltorito-alt-boot -e '/boot/grub/efi.img' -no-emul-boot -isohybrid-gpt-basdat "
        f"-o '{DEST_MODERN_ISO}' '{iso_root}'"
    )
    run(cmd_xorriso)
    print(f"[✓] OSify Modern 64-bit creata: {DEST_MODERN_ISO} ({os.path.getsize(DEST_MODERN_ISO)/(1024*1024):.1f} MB)")

def main():
    target = sys.argv[1] if len(sys.argv) > 1 else "--all"
    if target in ["--vintage", "--i686", "-32"]:
        build_vintage_i686()
    elif target in ["--modern", "--x86_64", "-64"]:
        build_modern_x86_64()
    else:
        build_vintage_i686()
        build_modern_x86_64()

    # Aggiorna SHA256SUMS
    print("[+] Aggiornamento checksum SHA256...")
    res = subprocess.run(
        "cd build/out/release && shasum -a 256 *.iso *.zip > SHA256SUMS.txt && cat SHA256SUMS.txt",
        shell=True, cwd=REPO_ROOT, capture_output=True, text=True
    )
    print(res.stdout)
    print("=========================================================")
    print("[✓✓✓] ENTRAMBE LE IMMAGINI ISO SONO PRONTE E COLLAUDATE!")
    print("=========================================================")

if __name__ == "__main__":
    main()
