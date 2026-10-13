#!/usr/bin/env python3
import os
import shutil
import subprocess
import sys
from PIL import Image

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
SRC_ISO = os.path.join(REPO_ROOT, "tests/sandbox/osify-vintage-desktop.iso")
DEST_ISO = os.path.join(REPO_ROOT, "tests/sandbox/OSify-Vintage-Live.iso")
WORK_DIR = "/tmp/osify_remaster"

def run(cmd, cwd=None):
    print(f"[RUN] {cmd}")
    res = subprocess.run(cmd, shell=True, cwd=cwd, capture_output=True, text=True)
    if res.returncode != 0:
        print(f"[ERROR] {res.stderr}")
        sys.exit(1)
    return res.stdout

def main():
    print("=== Remastering OSify Vintage Live ISO con Branding Reale ===")
    if os.path.exists(WORK_DIR):
        shutil.rmtree(WORK_DIR)
    os.makedirs(WORK_DIR)

    iso_root = os.path.join(WORK_DIR, "iso_root")
    os.makedirs(iso_root)

    print("[1/6] Estrazione ISO sorgente...")
    run(f"7z x -y '{SRC_ISO}' -o'{iso_root}' > /dev/null")

    # Conversione wallpaper in JPEG e PNG formattati
    src_png = os.path.join(REPO_ROOT, "desktop/branding/wallpapers/osify-netbook-1024x600.png")
    if not os.path.exists(src_png):
        src_png = os.path.join(REPO_ROOT, "OSify.png")
    
    img = Image.open(src_png).convert("RGB")
    wallpaper_jpg = os.path.join(WORK_DIR, "osify-wallpaper.jpg")
    img.resize((1024, 600), Image.Resampling.LANCZOS).save(wallpaper_jpg, "JPEG", quality=95)

    splash_jpg = os.path.join(WORK_DIR, "osify-splash.jpg")
    img.resize((640, 480), Image.Resampling.LANCZOS).save(splash_jpg, "JPEG", quality=90)

    # 2. Aggiornamento Isolinux Bootloader (diretto, senza c32box intermedio)
    print("[2/6] Configurazione ISOLINUX con Boot Diretto & Splash OSify...")
    isolinux_dir = os.path.join(iso_root, "boot/isolinux")
    os.makedirs(isolinux_dir, exist_ok=True)
    
    # Rimuove vecchio boot.cat (deve essere ricreato da mkisofs/xorriso per evitare offset corrotti)
    if os.path.exists(os.path.join(isolinux_dir, "boot.cat")):
        os.remove(os.path.join(isolinux_dir, "boot.cat"))

    shutil.copy2(splash_jpg, os.path.join(isolinux_dir, "splash.jpg"))

    # Configurazione diretta pulita per ISOLINUX
    clean_cfg = """DEFAULT core
PROMPT 0
TIMEOUT 10

LABEL core
    MENU LABEL OSify Vintage Desktop (Toshiba NB200)
    KERNEL /boot/bzImage
    INITRD /boot/rootfs4.gz,/boot/rootfs3.gz,/boot/rootfs2.gz,/boot/rootfs1.gz
    APPEND root=/dev/null video=-32 autologin lang=it_IT kmap=it rw
"""
    with open(os.path.join(isolinux_dir, "isolinux.cfg"), "w") as f:
        f.write(clean_cfg)

    # Copia speculare in /isolinux/ e /boot/syslinux/ per compatibilità totale
    root_isolinux = os.path.join(iso_root, "isolinux")
    if os.path.exists(root_isolinux):
        shutil.rmtree(root_isolinux)
    shutil.copytree(isolinux_dir, root_isolinux)

    # 3. Aggiornamento rootfs4 (Base Desktop & Wallpapers)
    print("[3/6] Remastering rootfs4 (Sfondi Ufficiali & Sostituzione Ragno)...")
    r4_work = os.path.join(WORK_DIR, "rootfs4")
    os.makedirs(r4_work)
    r4_gz = os.path.join(iso_root, "boot/rootfs4.gz")
    run(f"lzma -dc '{r4_gz}' | (cd '{r4_work}' && cpio -idmv > /dev/null 2>&1)")

    # Sovrascrittura sfondi ufficiali OSify
    img_dir = os.path.join(r4_work, "usr/share/images")
    os.makedirs(img_dir, exist_ok=True)
    shutil.copy2(wallpaper_jpg, os.path.join(img_dir, "slitaz-background.jpg"))
    shutil.copy2(wallpaper_jpg, os.path.join(img_dir, "slitaz-background_2.jpg"))
    img.resize((300, 100), Image.Resampling.LANCZOS).save(os.path.join(img_dir, "slitaz-banner.png"), "PNG")

    # Iniezione CLI & Tool OSify
    bin_dir = os.path.join(r4_work, "usr/bin")
    os.makedirs(bin_dir, exist_ok=True)
    shutil.copy2(os.path.join(REPO_ROOT, "tools/osify-ctl"), os.path.join(bin_dir, "osify-ctl"))
    shutil.copy2(os.path.join(REPO_ROOT, "uem/runners/osify-inspect.sh"), os.path.join(bin_dir, "osify-inspect"))
    shutil.copy2(os.path.join(REPO_ROOT, "uem/runners/osify-universal-dispatcher.sh"), os.path.join(bin_dir, "osify-exec"))
    run(f"chmod +x '{bin_dir}'/osify-*")

    # Banner di login
    issue_text = "OSify Vintage Micro-Edition (Intel Atom N280 • GMA 950 Profile)\\n\\l\n"
    with open(os.path.join(r4_work, "etc/issue"), "w") as f:
        f.write(issue_text)

    # Forzatura wallpaper in xinitrc se presente
    for xinit in ["root/.xinitrc", "etc/skel/.xinitrc"]:
        xinit_path = os.path.join(r4_work, xinit)
        if os.path.exists(xinit_path):
            with open(xinit_path, "r") as f:
                content = f.read()
            # Inietta feh o pcmanfm background all'avvio di X
            inject = "\nfeh --bg-scale /usr/share/images/slitaz-background.jpg 2>/dev/null &\n"
            if "slitaz-background" not in content:
                content = inject + content
            with open(xinit_path, "w") as f:
                f.write(content)

    print("[+] Ricompressione rootfs4 con LZMA...")
    os.remove(r4_gz)
    run(f"(cd '{r4_work}' && find . -print0 | cpio --null -ov -H newc) | lzma > '{r4_gz}'")
    efi_r4 = os.path.join(iso_root, "EFI/boot/rootfs4.gz")
    if os.path.exists(os.path.dirname(efi_r4)):
        shutil.copy2(r4_gz, efi_r4)

    # 4. Aggiornamento rootfs3 (SLiM Display Manager Theme)
    print("[4/6] Remastering rootfs3 (Tema Login SLiM)...")
    r3_work = os.path.join(WORK_DIR, "rootfs3")
    os.makedirs(r3_work)
    r3_gz = os.path.join(iso_root, "boot/rootfs3.gz")
    run(f"lzma -dc '{r3_gz}' | (cd '{r3_work}' && cpio -idmv > /dev/null 2>&1)")
    slim_bg = os.path.join(r3_work, "usr/share/slim/themes/slitaz/background.png")
    if os.path.exists(os.path.dirname(slim_bg)):
        img.resize((1024, 600), Image.Resampling.LANCZOS).save(slim_bg, "PNG")
    
    os.remove(r3_gz)
    run(f"(cd '{r3_work}' && find . -print0 | cpio --null -ov -H newc) | lzma > '{r3_gz}'")
    efi_r3 = os.path.join(iso_root, "EFI/boot/rootfs3.gz")
    if os.path.exists(os.path.dirname(efi_r3)):
        shutil.copy2(r3_gz, efi_r3)

    # 5. Generazione ISO con xorriso
    print("[5/6] Generazione file ISO avviabile con xorriso...")
    run(f"xorriso -as mkisofs -R -r -J -V 'OSIFY_VINTAGE' -b boot/isolinux/isolinux.bin -c boot/isolinux/boot.cat -no-emul-boot -boot-load-size 4 -boot-info-table -o '{DEST_ISO}' '{iso_root}'")

    print(f"[6/6] Operazione completata. Nuova ISO creata: {DEST_ISO}")
    iso_size = os.path.getsize(DEST_ISO) / (1024 * 1024)
    print(f"[✓] Dimensione ISO: {iso_size:.2f} MB")

if __name__ == "__main__":
    main()
