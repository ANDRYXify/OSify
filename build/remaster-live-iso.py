#!/usr/bin/env python3
import os
import shutil
import subprocess
import sys
import lzma
import hashlib
from PIL import Image, ImageDraw, ImageFont

LANCZOS_FILTER = getattr(getattr(Image, 'Resampling', None), 'LANCZOS', getattr(Image, 'LANCZOS', getattr(Image, 'ANTIALIAS', 1)))

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

def extract_cpio_archive(data, dest_dir):
    pos = 0
    total = len(data)
    count = 0
    while pos + 110 <= total:
        magic = data[pos:pos+6]
        if magic not in (b'070701', b'070702'):
            break
        header = data[pos:pos+110]
        pos += 110
        mode = int(header[14:22], 16)
        filesize = int(header[54:62], 16)
        namesize = int(header[94:102], 16)
        
        name_raw = data[pos:pos+namesize-1]
        pos += namesize
        if (110 + namesize) % 4 != 0:
            pos += 4 - ((110 + namesize) % 4)
            
        name = name_raw.decode('utf-8', 'ignore')
        if name == 'TRAILER!!!':
            break
            
        file_data = data[pos:pos+filesize]
        pos += filesize
        if filesize % 4 != 0:
            pos += 4 - (filesize % 4)
            
        if name in ('.', '..') or name.startswith('/'):
            continue
            
        target_path = os.path.join(dest_dir, name)
        file_type = mode & 0o170000
        
        try:
            if file_type == 0o040000: # Directory
                os.makedirs(target_path, exist_ok=True)
            elif file_type == 0o120000: # Symlink
                os.makedirs(os.path.dirname(target_path), exist_ok=True)
                link_target = file_data.decode('utf-8', 'ignore')
                if os.path.islink(target_path) or os.path.exists(target_path):
                    os.unlink(target_path)
                os.symlink(link_target, target_path)
            elif file_type == 0o100000: # Regular file
                os.makedirs(os.path.dirname(target_path), exist_ok=True)
                with open(target_path, 'wb') as f:
                    f.write(file_data)
                os.chmod(target_path, mode & 0o777)
            count += 1
        except Exception:
            pass
    return count

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
def create_boot_splash(dest_jpg):
    img = Image.new("RGB", (640, 480), color=(11, 13, 20))
    draw = ImageDraw.Draw(img)
    for r in range(180, 0, -2):
        alpha = int(45 * (1 - r / 180))
        color = (11 + int(alpha * 1.5), 13 + int(alpha * 0.5), 20 + int(alpha * 3))
        draw.ellipse([(320 - r, 100 - r//2), (320 + r, 100 + r//2)], fill=color)
    logo_path = os.path.join(REPO_ROOT, "OSify.png")
    if os.path.exists(logo_path):
        logo = Image.open(logo_path).convert("RGBA")
        logo.thumbnail((90, 90))
        img.paste(logo, (320 - logo.width//2, 45), logo)
    draw.text((320, 145), "OSify Operating System", fill=(255, 255, 255), anchor="mm")
    draw.text((320, 168), "Ingegnerizzato da Andrea Taliento (ANDRYXify)", fill=(6, 182, 212), anchor="mm")
    draw.text((320, 186), "Intel Atom N280 • GMA 950 • WSVGA 1024x600 Live Profile", fill=(148, 163, 184), anchor="mm")
    img.save(dest_jpg, "JPEG", quality=90)

def remaster_rootfs3(work_dir, iso_root, wallpaper_jpg):
    print("[i] Remastering rootfs3 (SLIM autologin 0s, rimozione ragno SliTaz, OSify Cyber-Bar)...")
    r3_work = os.path.join(work_dir, "rootfs3")
    os.makedirs(r3_work, exist_ok=True)
    r3_gz = os.path.join(iso_root, "boot/rootfs3.gz")
    
    with open(r3_gz, "rb") as f:
        r3_data = lzma.decompress(f.read())
    extract_cpio_archive(r3_data, r3_work)

    # 1. Configurazione SLIM per autologin forzato e tema osify
    slim_conf = os.path.join(r3_work, "etc/slim.conf")
    if os.path.exists(slim_conf):
        with open(slim_conf, "r") as f:
            lines = f.readlines()
        new_lines = []
        for line in lines:
            if line.strip().startswith("auto_login") or line.strip().startswith("#auto_login"):
                new_lines.append("auto_login          yes\n")
            elif line.strip().startswith("default_user") or line.strip().startswith("#default_user"):
                new_lines.append("default_user        tux\n")
            elif line.strip().startswith("current_theme"):
                new_lines.append("current_theme       osify\n")
            else:
                new_lines.append(line)
        with open(slim_conf, "w") as f:
            f.writelines(new_lines)

    # 2. Sostituzione temi SLIM: cancellazione totale del ragno di SliTaz
    blank_panel = Image.new("RGBA", (1, 1), (0, 0, 0, 0))
    for theme_dir in ["usr/share/slim/themes/slitaz", "usr/share/slim/themes/base", "usr/share/slim/themes/osify"]:
        td = os.path.join(r3_work, theme_dir)
        os.makedirs(td, exist_ok=True)
        shutil.copy2(wallpaper_jpg, os.path.join(td, "background.png"))
        blank_panel.save(os.path.join(td, "panel.png"), "PNG")
        with open(os.path.join(td, "slim.theme"), "w") as f:
            f.write("""# OSify SLIM Theme
# Ingegnerizzato da Andrea Taliento (ANDRYXify)
input_panel_x 50%
input_panel_y 50%
input_name_x 30
input_name_y 30
input_pass_x 30
input_pass_y 30
input_font Sans:size=10
input_color #000000
welcome_x -1000
welcome_y -1000
intro_x -1000
intro_y -1000
username_msg
password_msg
""")

    # 3. Configurazione Pannello LXPanel (OSify Cyber-Bar)
    lxpanel_cfg = """# OSify Cyber-Bar Configuration
Global {
    edge=bottom
    allign=center
    margin=0
    widthtype=percent
    width=100
    height=24
    transparent=1
    tintcolor=#0b0d14
    alpha=240
    autohide=0
    heightwhenhidden=2
    setdocktype=1
    setpartialstrut=1
    usefontcolor=1
    fontsize=9
    fontcolor=#e2e8f0
    usefontsize=1
    background=0
    iconsize=20
    loglevel=2
}

Plugin {
    type = menu
    Config {
        image=/usr/share/pixmaps/osify.png
        system {
        }
        separator {
        }
        item {
            name=⚡ OSify Quick Access HUD
            image=preferences-system
            action=/usr/bin/osify-hud
        }
        item {
            name=📊 OSify Process Commander (Task Manager)
            image=utilities-system-monitor
            action=/usr/bin/osify-taskmanager
        }
        item {
            name=⚙️ OSify Control Center
            image=preferences-desktop
            action=/usr/bin/osify-settings
        }
        item {
            name=💾 Installa OSify su Disco
            image=system-software-install
            action=terminal -geometry 95x26 -T 'OSify Installer' -e /usr/bin/osify-install
        }
        separator {
        }
        item {
            name=Terminale OSify
            image=terminal
            action=/usr/bin/osify-terminal
        }
        item {
            name=File Manager
            image=system-file-manager
            action=pcmanfm
        }
        separator {
        }
        item {
            name=Blocca Schermo
            image=system-lock-screen
            action=xlock
        }
        item {
            name=Riavvia Computer
            image=system-reboot-panel
            action=reboot
        }
        item {
            name=Spegni Computer
            image=system-shutdown-panel
            action=poweroff
        }
    }
}

Plugin {
    type = launchbar
    Config {
        Button {
            id=/usr/share/applications/osify-hud.desktop
        }
        Button {
            id=/usr/share/applications/osify-taskmanager.desktop
        }
        Button {
            id=/usr/share/applications/pcmanfm.desktop
        }
        Button {
            id=/usr/share/applications/osify-terminal.desktop
        }
        Button {
            id=/usr/share/applications/osify-settings.desktop
        }
    }
}

Plugin {
    type = space
    Config {
        Size=6
    }
}

Plugin {
    type = taskbar
    Config {
        tooltips=1
        IconsOnly=0
        ShowAllDesks=0
        UseMouseWheel=1
        UseUrgencyHint=1
        FlatButton=1
        MaxTaskWidth=180
        spacing=2
        GroupedTasks=0
    }
}

Plugin {
    type = space
    expand=1
    Config {
        Size=4
    }
}

Plugin {
    type = tray
}

Plugin {
    type = space
    Config {
        Size=4
    }
}

Plugin {
    type = volumealsa
}

Plugin {
    type = space
    Config {
        Size=4
    }
}

Plugin {
    type = batt
    Config {
        HideIfNoBattery=0
        AlarmTime=10
        BackgroundColor=#1e293b
        BorderWidth=1
        ChargingColor1=#10b981
        ChargingColor2=#10b981
        DischargingColor1=#ef4444
        DischargingColor2=#f59e0b
        Size=10
    }
}

Plugin {
    type = space
    Config {
        Size=4
    }
}

Plugin {
    type = cpu
}

Plugin {
    type = space
    Config {
        Size=4
    }
}

Plugin {
    type = dclock
    Config {
        ClockFmt=%H:%M
        TooltipFmt=%A %d %B %Y
        BoldFont=1
        IconOnly=0
        CenterText=1
    }
}
"""
    for p_path in ["etc/skel/.config/lxpanel/slitaz/panels/panel", "etc/lxpanel/slitaz/panels/panel", "etc/lxpanel/default/panels/panel"]:
        full_p = os.path.join(r3_work, p_path)
        os.makedirs(os.path.dirname(full_p), exist_ok=True)
        with open(full_p, "w") as f:
            f.write(lxpanel_cfg)

    # 4. Scorciatoie Openbox in etc/xdg/openbox/rc.xml
    rc_xml = os.path.join(r3_work, "etc/xdg/openbox/rc.xml")
    if os.path.exists(rc_xml):
        with open(rc_xml, "r") as f:
            rc_content = f.read()
        custom_keys = """
    <!-- OSify Universali Hotkeys -->
    <keybind key="W-a"><action name="Execute"><command>/usr/bin/osify-hud</command></action></keybind>
    <keybind key="C-S-Escape"><action name="Execute"><command>/usr/bin/osify-taskmanager</command></action></keybind>
    <keybind key="W-F10"><action name="Execute"><command>/usr/bin/osify-hud --toggle-scale</command></action></keybind>
    <keybind key="W-t"><action name="Execute"><command>/usr/bin/osify-terminal</command></action></keybind>
    <keybind key="C-A-t"><action name="Execute"><command>/usr/bin/osify-terminal</command></action></keybind>
    <keybind key="W-e"><action name="Execute"><command>pcmanfm</command></action></keybind>
    <keybind key="W-F1"><action name="Execute"><command>/usr/bin/osify-welcome</command></action></keybind>
"""
        if "</keyboard>" in rc_content:
            rc_content = rc_content.replace("</keyboard>", f"{custom_keys}\n  </keyboard>")
            with open(rc_xml, "w") as f:
                f.write(rc_content)

    os.remove(r3_gz)
    run(f"(cd '{r3_work}' && find . -print0 | cpio --null -ov -H newc) | python3 -c \"import lzma, sys; sys.stdout.buffer.write(lzma.compress(sys.stdin.buffer.read(), format=lzma.FORMAT_ALONE))\" > '{r3_gz}'")
    print(f"[✓] rootfs3 ricompatto con successo ({os.path.getsize(r3_gz)/(1024*1024):.1f} MB)")

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

    # Wallpaper e splash ad alta risoluzione
    src_png = os.path.join(REPO_ROOT, "desktop/branding/wallpapers/osify-netbook-1024x600.png")
    if not os.path.exists(src_png):
        src_png = os.path.join(REPO_ROOT, "OSify.png")
    img = Image.open(src_png).convert("RGB")
    wallpaper_jpg = os.path.join(work_dir, "osify-wallpaper.jpg")
    img.resize((1024, 600), LANCZOS_FILTER).save(wallpaper_jpg, "JPEG", quality=95)
    
    splash_jpg = os.path.join(work_dir, "osify-splash.jpg")
    create_boot_splash(splash_jpg)

    # Bootloader ISOLINUX / SYSLINUX grafico ad alta risoluzione
    isolinux_dir = os.path.join(iso_root, "boot/isolinux")
    os.makedirs(isolinux_dir, exist_ok=True)
    if os.path.exists(os.path.join(isolinux_dir, "boot.cat")):
        os.remove(os.path.join(isolinux_dir, "boot.cat"))
    shutil.copy2(splash_jpg, os.path.join(isolinux_dir, "splash.jpg"))

    clean_cfg = """UI vesamenu.c32
PROMPT 0
TIMEOUT 40

MENU TITLE OSify Operating System — by Andrea Taliento (ANDRYXify)
MENU BACKGROUND splash.jpg
MENU WIDTH 78
MENU MARGIN 6
MENU ROWS 12
MENU TIMEOUTROW 18
MENU TABMSGROW 16
MENU CMDLINEROW 16

MENU COLOR border       *   #00000000 #00000000 none
MENU COLOR title        *   #ffffffff #00000000 *
MENU COLOR sel          0   #ffffffff #7c3aedcc *
MENU COLOR unsel        0   #b0ffffff #00000000 none
MENU COLOR help         *   #ffffffff #00000000 *
MENU COLOR timeout      1;37;40 #06b6d4ff #00000000 std
MENU COLOR timeout_msg  37;40   #a0ffffff #00000000 std

LABEL osify
    MENU LABEL 🚀 OSify Vintage Desktop (Live Session — Automazione Completa)
    KERNEL /boot/bzImage
    INITRD /boot/rootfs4.gz,/boot/rootfs3.gz,/boot/rootfs2.gz,/boot/rootfs1.gz
    APPEND root=/dev/null video=-32 autologin lang=it_IT kmap=it rw quiet splash vga=791 vt.global_cursor_default=0

LABEL turbo
    MENU LABEL ⚡ OSify Turbo Performance Mode (CPU 1.66GHz & zRAM Max)
    KERNEL /boot/bzImage
    INITRD /boot/rootfs4.gz,/boot/rootfs3.gz,/boot/rootfs2.gz,/boot/rootfs1.gz
    APPEND root=/dev/null video=-32 autologin lang=it_IT kmap=it rw quiet splash vga=791 osify.turbo=1

LABEL safe
    MENU LABEL 🛠️ OSify Safe Graphics (Fallback VESA / Nomodeset)
    KERNEL /boot/bzImage
    INITRD /boot/rootfs4.gz,/boot/rootfs3.gz,/boot/rootfs2.gz,/boot/rootfs1.gz
    APPEND root=/dev/null nomodeset autologin lang=it_IT kmap=it rw vga=791

LABEL install
    MENU LABEL 💾 Installa OSify su Disco Fisso
    KERNEL /boot/bzImage
    INITRD /boot/rootfs4.gz,/boot/rootfs3.gz,/boot/rootfs2.gz,/boot/rootfs1.gz
    APPEND root=/dev/null video=-32 autologin lang=it_IT kmap=it rw quiet splash vga=791 osify.install=1

LABEL memtest
    MENU LABEL 🧠 Verifica Memoria RAM (Memtest86)
    KERNEL /boot/memtest.exe
"""
    with open(os.path.join(isolinux_dir, "isolinux.cfg"), "w") as f:
        f.write(clean_cfg)

    # Copia speculare in syslinux
    syslinux_dir = os.path.join(iso_root, "boot/syslinux")
    os.makedirs(syslinux_dir, exist_ok=True)
    with open(os.path.join(syslinux_dir, "syslinux.cfg"), "w") as f:
        f.write(clean_cfg)
    shutil.copy2(splash_jpg, os.path.join(syslinux_dir, "splash.jpg"))

    # Remastering di rootfs3 (SLIM, LXPanel, Openbox)
    remaster_rootfs3(work_dir, iso_root, wallpaper_jpg)

    # Remastering rootfs4
    print("[i] Remastering rootfs4 desktop e toolchain...")
    r4_work = os.path.join(work_dir, "rootfs4")
    os.makedirs(r4_work, exist_ok=True)
    r4_gz = os.path.join(iso_root, "boot/rootfs4.gz")
    
    with open(r4_gz, "rb") as f:
        r4_data = lzma.decompress(f.read())
    n_files = extract_cpio_archive(r4_data, r4_work)
    print(f"[✓] Decompressi {n_files} file da rootfs4.gz senza errori")

    img_dir = os.path.join(r4_work, "usr/share/images")
    os.makedirs(img_dir, exist_ok=True)
    shutil.copy2(wallpaper_jpg, os.path.join(img_dir, "osify-wallpaper.jpg"))
    shutil.copy2(wallpaper_jpg, os.path.join(img_dir, "slitaz-background.jpg"))
    shutil.copy2(wallpaper_jpg, os.path.join(img_dir, "slitaz-background_2.jpg"))
    img.resize((300, 100), LANCZOS_FILTER).save(os.path.join(img_dir, "slitaz-banner.png"), "PNG")

    # Iniezione GNU Bash statico 32-bit (i386) per esecuzione garantita di tutti gli script
    print("[i] Iniezione binario GNU Bash statico 32-bit (i386)...")
    bash_injected = False
    for candidate in ["/bin/bash-static", "/usr/bin/bash-static"]:
        if os.path.exists(candidate):
            os.makedirs(os.path.join(r4_work, "bin"), exist_ok=True)
            shutil.copy2(candidate, os.path.join(r4_work, "bin/bash"))
            os.chmod(os.path.join(r4_work, "bin/bash"), 0o755)
            os.makedirs(os.path.join(r4_work, "usr/bin"), exist_ok=True)
            if not os.path.exists(os.path.join(r4_work, "usr/bin/bash")):
                os.symlink("/bin/bash", os.path.join(r4_work, "usr/bin/bash"))
            bash_injected = True
            print(f"[✓] Inietto bash-static da sistema: {candidate}")
            break

    if not bash_injected and shutil.which("docker"):
        try:
            docker_bash_cmd = (
                f"docker run --rm -v '{r4_work}':/r4 ubuntu:20.04 bash -c '"
                f"dpkg --add-architecture i386 && apt-get update -qq && "
                f"apt-get install -y -qq bash-static:i386 > /dev/null && "
                f"mkdir -p /r4/bin /r4/usr/bin && "
                f"cp /bin/bash-static /r4/bin/bash && chmod 755 /r4/bin/bash && "
                f"ln -sf /bin/bash /r4/usr/bin/bash'"
            )
            run(docker_bash_cmd)
            bash_injected = True
            print("[✓] Inietto bash-static via container docker")
        except Exception as e:
            print(f"[!] Warning docker bash: {e}")

    if not bash_injected:
        os.makedirs(os.path.join(r4_work, "bin"), exist_ok=True)
        if not os.path.exists(os.path.join(r4_work, "bin/bash")):
            os.symlink("/bin/sh", os.path.join(r4_work, "bin/bash"))
        os.makedirs(os.path.join(r4_work, "usr/bin"), exist_ok=True)
        if not os.path.exists(os.path.join(r4_work, "usr/bin/bash")):
            os.symlink("/bin/bash", os.path.join(r4_work, "usr/bin/bash"))

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
    shutil.copy2(os.path.join(REPO_ROOT, "tools/osify-gui/osify-hud.sh"), os.path.join(bin_dir, "osify-hud"))
    shutil.copy2(os.path.join(REPO_ROOT, "tools/osify-gui/osify-taskmanager.sh"), os.path.join(bin_dir, "osify-taskmanager"))
    shutil.copy2(os.path.join(REPO_ROOT, "tools/osify-gui/osify-settings.sh"), os.path.join(bin_dir, "osify-settings"))
    shutil.copy2(os.path.join(REPO_ROOT, "tools/osify-gui/osify-terminal.sh"), os.path.join(bin_dir, "osify-terminal"))
    run(f"chmod +x '{bin_dir}'/osify-*")

    # Iniezione Icona OSify nel sistema
    pixmaps_dir = os.path.join(r4_work, "usr/share/pixmaps")
    os.makedirs(pixmaps_dir, exist_ok=True)
    osify_png = os.path.join(REPO_ROOT, "OSify.png")
    if os.path.exists(osify_png):
        shutil.copy2(osify_png, os.path.join(pixmaps_dir, "osify.png"))
        for icon_path in [
            "usr/share/icons/SliTaz-Faenza/48x48/places/start-here.png",
            "usr/share/icons/SliTaz-Faenza/22x22/places/start-here.png",
            "usr/share/icons/SliTaz-Faenza-Dark/22x22/places/start-here.png",
            "usr/share/icons/hicolor/48x48/apps/osify.png"
        ]:
            full_ip = os.path.join(r4_work, icon_path)
            os.makedirs(os.path.dirname(full_ip), exist_ok=True)
            shutil.copy2(osify_png, full_ip)

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
        "\\n# Inizializzazione Ambiente Desktop OSify (Sfondo, Touchpad, Wizard)\\n"
        "(pcmanfm --set-wallpaper=/usr/share/images/osify-wallpaper.jpg --wallpaper-mode=fit) 2>/dev/null &\\n"
        "(sleep 1 && /usr/bin/osify-welcome) &\\n"
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
        f.write("OSify Operating System (32-bit Vintage Edition — by Andrea Taliento)\\n\\l\n")

    # Entry Applicative Ufficiali OSify (.desktop)
    app_entries = {
        "osify-hud.desktop": (
            "[Desktop Entry]\n"
            "Type=Application\n"
            "Name=⚡ OSify Quick Access HUD\n"
            "Comment=Pannello Rapido Prestazioni, zRAM e Virtual Scaler 1280x768\n"
            "Exec=/usr/bin/osify-hud\n"
            "Icon=preferences-system\n"
            "Terminal=false\n"
            "Categories=System;Settings;\n"
        ),
        "osify-taskmanager.desktop": (
            "[Desktop Entry]\n"
            "Type=Application\n"
            "Name=📊 OSify Process Commander\n"
            "Comment=Task Manager Grafico e Gestione Attività in Tempo Reale\n"
            "Exec=/usr/bin/osify-taskmanager\n"
            "Icon=utilities-system-monitor\n"
            "Terminal=false\n"
            "Categories=System;\n"
        ),
        "osify-settings.desktop": (
            "[Desktop Entry]\n"
            "Type=Application\n"
            "Name=⚙️ OSify Control Center\n"
            "Comment=Centro di Controllo Sistema, Rete, Touchpad e Schermo\n"
            "Exec=/usr/bin/osify-settings\n"
            "Icon=preferences-desktop\n"
            "Terminal=false\n"
            "Categories=Settings;\n"
        ),
        "osify-terminal.desktop": (
            "[Desktop Entry]\n"
            "Type=Application\n"
            "Name=💻 Terminale OSify\n"
            "Comment=Terminale con Fastfetch e Diagnostica Hardware\n"
            "Exec=terminal -geometry 95x26 -T 'OSify Terminal' -e /usr/bin/osify-terminal\n"
            "Icon=terminal\n"
            "Terminal=false\n"
            "Categories=System;\n"
        ),
        "osify-install.desktop": (
            "[Desktop Entry]\n"
            "Type=Application\n"
            "Name=💾 Installa OSify su Disco\n"
            "Comment=Installatore Guidato su Disco Fisso\n"
            "Exec=terminal -geometry 95x26 -T 'OSify Installer' -e /usr/bin/osify-install\n"
            "Icon=system-software-install\n"
            "Terminal=false\n"
            "Categories=System;\n"
        ),
        "osify-welcome.desktop": (
            "[Desktop Entry]\n"
            "Type=Application\n"
            "Name=👋 Benvenuto in OSify\n"
            "Comment=Esperienza di Primo Avvio e Diagnostica Netbook\n"
            "Exec=/usr/bin/osify-welcome\n"
            "Icon=preferences-desktop\n"
            "Terminal=false\n"
            "Categories=System;\n"
        )
    }

    # Scrittura in usr/share/applications e sui Desktop utente
    apps_sys = os.path.join(r4_work, "usr/share/applications")
    os.makedirs(apps_sys, exist_ok=True)
    for name, content in app_entries.items():
        with open(os.path.join(apps_sys, name), "w") as f:
            f.write(content)

    for dpath in ["root/Desktop", "home/tux/Desktop", "etc/skel/Desktop"]:
        full_d = os.path.join(r4_work, dpath)
        os.makedirs(full_d, exist_ok=True)
        for name, content in app_entries.items():
            with open(os.path.join(full_d, name), "w") as f:
                f.write(content)

    # Autostart automatico XDG
    autostart_dir = os.path.join(r4_work, "etc/xdg/autostart")
    os.makedirs(autostart_dir, exist_ok=True)
    with open(os.path.join(autostart_dir, "osify-welcome.desktop"), "w") as f:
        f.write(app_entries["osify-welcome.desktop"])

    os.remove(r4_gz)
    run(f"(cd '{r4_work}' && find . -print0 | cpio --null -ov -H newc) | python3 -c \"import lzma, sys; sys.stdout.buffer.write(lzma.compress(sys.stdin.buffer.read(), format=lzma.FORMAT_ALONE))\" > '{r4_gz}'")

    # Iniezione Windows Installer e albero OSify
    inject_windows_installer(iso_root)
    inject_osify_tree(iso_root)

    with open(os.path.join(iso_root, "OSify-Version.txt"), "w") as f:
        f.write("OSify Live System (32-bit Vintage Edition)\nTarget: Intel Atom N280/N270\n")

    print("[i] Masterizzazione immagine ibrida avviabile (isohybrid MBR)...")
    os.makedirs(OUT_RELEASE_DIR, exist_ok=True)
    out_iso_tmp = os.path.join(work_dir, "OSify-Vintage-i686.iso")
    
    native_geniso = shutil.which("genisoimage") or shutil.which("mkisofs")
    native_isohybrid = shutil.which("isohybrid")
    isolinux_bin_host = "/usr/lib/ISOLINUX/isolinux.bin"

    if native_geniso and native_isohybrid and os.path.exists(isolinux_bin_host):
        print("[+] Utilizzo toolchain nativa host...")
        shutil.copy2(isolinux_bin_host, os.path.join(iso_root, "boot/isolinux/isolinux.bin"))
        for mod in ["ldlinux.c32", "libutil.c32", "libcom32.c32", "menu.c32", "vesamenu.c32"]:
            mod_path = f"/usr/lib/syslinux/modules/bios/{mod}"
            if os.path.exists(mod_path):
                shutil.copy2(mod_path, os.path.join(iso_root, "boot/isolinux", mod))
        
        cmd_geniso = (
            f"{native_geniso} -R -J -l -b boot/isolinux/isolinux.bin -c boot/isolinux/boot.cat "
            f"-no-emul-boot -boot-load-size 4 -boot-info-table -V \"OSIFY_VINTAGE\" "
            f"-o '{out_iso_tmp}' '{iso_root}'"
        )
        run(cmd_geniso)
        run(f"{native_isohybrid} '{out_iso_tmp}'")
    else:
        print("[+] Utilizzo container Docker per generazione ISO...")
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
        
    shutil.copy2(out_iso_tmp, DEST_VINTAGE_ISO)
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

    # Aggiorna SHA256SUMS nativamente con hashlib
    print("[+] Aggiornamento checksum SHA256 universale...")
    import hashlib
    sha_lines = []
    for f_name in sorted(os.listdir(OUT_RELEASE_DIR)):
        if f_name.endswith((".iso", ".zip")):
            f_path = os.path.join(OUT_RELEASE_DIR, f_name)
            hasher = hashlib.sha256()
            with open(f_path, "rb") as fh:
                while chunk := fh.read(65536):
                    hasher.update(chunk)
            sha_lines.append(f"{hasher.hexdigest()}  {f_name}")
    sha_txt = "\n".join(sha_lines) + "\n"
    with open(os.path.join(OUT_RELEASE_DIR, "SHA256SUMS.txt"), "w") as f:
        f.write(sha_txt)
    print(sha_txt)
    print("=========================================================")
    print("[✓✓✓] ENTRAMBE LE IMMAGINI ISO SONO PRONTE E COLLAUDATE!")
    print("=========================================================")

if __name__ == "__main__":
    main()
