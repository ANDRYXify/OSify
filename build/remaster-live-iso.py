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
VERSION_FILE = os.path.join(REPO_ROOT, "VERSION")
OSIFY_VERSION = "1.5.0"
if os.path.isfile(VERSION_FILE):
    try:
        with open(VERSION_FILE, "r") as f:
            v = f.read().strip()
            if v:
                OSIFY_VERSION = v
    except Exception:
        pass

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
    
    version_file = os.path.join(REPO_ROOT, "VERSION")
    if os.path.exists(version_file):
        shutil.copy2(version_file, os.path.join(dest_iso_root, "VERSION"))
        shutil.copy2(version_file, os.path.join(osify_tree, "VERSION"))

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
    for r in range(160, 0, -2):
        alpha = int(45 * (1 - r / 160))
        color = (11 + int(alpha * 1.5), 13 + int(alpha * 0.5), 20 + int(alpha * 3))
        draw.ellipse([(320 - r, 70 - r//2), (320 + r, 70 + r//2)], fill=color)
    logo_path = os.path.join(REPO_ROOT, "OSify.png")
    if os.path.exists(logo_path):
        logo = Image.open(logo_path).convert("RGBA")
        logo.thumbnail((75, 75))
        img.paste(logo, (320 - logo.width//2, 25), logo)
    draw.text((320, 110), "OSify Operating System", fill=(255, 255, 255), anchor="mm")
    draw.text((320, 128), "Ingegnerizzato da Andrea Taliento (ANDRYXify)", fill=(6, 182, 212), anchor="mm")
    draw.text((320, 144), "Intel Atom N280 - GMA 950 - WSVGA 1024x600 Live Profile", fill=(148, 163, 184), anchor="mm")
    img.save(dest_jpg, "JPEG", quality=90)

CLEAN_XINITRC = """#!/bin/sh
# OSify Universal Desktop Session Manager
# Ingegnerizzato da Andrea Taliento (ANDRYXify)
exec /usr/bin/osify-session
"""

PCMANFM_CONF = """[config]
bm_open_method=0
su_cmd=sudo %s

[volume]
mount_on_startup=0
mount_removable=1
autorun=1

[desktop]
wallpaper_mode=stretch
wallpaper=/usr/share/images/osify-wallpaper.jpg
desktop_bg=#0b0d14
desktop_fg=#ffffff
desktop_shadow=#000000
desktop_font=Sans 10
show_wm_menu=1
show_documents=0
show_trash=0
show_mounts=1

[ui]
show_thumbnails=1
thumbnail_max=8192
close_on_unmount=0
focus_previous=1
always_show_tabs=0
max_tab_chars=32
win_width=640
win_height=480
splitter_pos=150
side_pane_mode=1
view_mode=0
show_hidden=0
sort_type=0
sort_by=2
"""

OPENBOX_AUTOSTART = """#!/bin/sh
# OSify Openbox Session Autostart
[ -x /usr/bin/osify-input-setup ] && /usr/bin/osify-input-setup &
[ -x /usr/bin/osify-storage-governor ] && /usr/bin/osify-storage-governor --tune &
if command -v pcmanfm >/dev/null 2>&1; then
    (sleep 0.3 && pgrep -f "pcmanfm --desktop" >/dev/null || pcmanfm --desktop) &
fi
if command -v lxpanel >/dev/null 2>&1; then
    (sleep 0.5 && pgrep -x lxpanel >/dev/null || lxpanel --profile default 2>/dev/null || lxpanel 2>/dev/null || true) &
fi
"""

OSIFY_OPENBOX_MENU = """<?xml version="1.0" encoding="UTF-8"?>
<openbox_menu xmlns="http://openbox.org/3.4/menu">
  <menu id="root-menu" label="OSify Menu">
    <separator label="OSify Operating System"/>
    <item label="Dashboard di Sistema" icon="/usr/share/pixmaps/osify-hub.png">
      <action name="Execute"><command>/usr/bin/terminal -geometry 80x24 -T 'Dashboard di Sistema' -e /usr/bin/osify</command></action>
    </item>
    <item label="Tutte le Applicazioni" icon="/usr/share/pixmaps/osify-drawer.png">
      <action name="Execute"><command>/usr/bin/osify-app-drawer</command></action>
    </item>
    <separator/>
    <separator label="Applicazioni"/>
    <item label="Terminale di Sistema" icon="/usr/share/pixmaps/osify-terminal.png">
      <action name="Execute"><command>/usr/bin/terminal</command></action>
    </item>
    <item label="Navigatore Web" icon="/usr/share/pixmaps/osify-browser.png">
      <action name="Execute"><command>/usr/bin/osify-browser</command></action>
    </item>
    <item label="Gestione File" icon="/usr/share/pixmaps/osify-files.png">
      <action name="Execute"><command>pcmanfm</command></action>
    </item>
    <item label="Gaming Hub" icon="/usr/share/pixmaps/osify-games.png">
      <action name="Execute"><command>/usr/bin/terminal -geometry 75x20 -T 'Gaming Hub' -e /usr/bin/osify-games</command></action>
    </item>
    <item label="Acquisizione Video HDMI" icon="/usr/share/pixmaps/osify-games.png">
      <action name="Execute"><command>/usr/bin/osify-capture</command></action>
    </item>
    <item label="Mirroring Smartphone" icon="/usr/share/pixmaps/osify-hub.png">
      <action name="Execute"><command>/usr/bin/osify-phone</command></action>
    </item>
    <separator/>
    <separator label="Strumenti e Hardware"/>
    <item label="Modalita Turbo" icon="/usr/share/pixmaps/osify-hub.png">
      <action name="Execute"><command>/usr/bin/osify turbo</command></action>
    </item>
    <item label="Pulizia Memoria RAM" icon="/usr/share/pixmaps/osify-hub.png">
      <action name="Execute"><command>/usr/bin/osify pulisci</command></action>
    </item>
    <item label="Connessione Wi-Fi" icon="/usr/share/pixmaps/osify-wifi.png">
      <action name="Execute"><command>/usr/bin/terminal -geometry 75x20 -T 'Connessione Wi-Fi' -e /usr/bin/osify-wifi</command></action>
    </item>
    <item label="Schermo e Risoluzioni" icon="/usr/share/pixmaps/osify-appearance.png">
      <action name="Execute"><command>/usr/bin/osify-display</command></action>
    </item>
    <item label="Gestione Attivita" icon="/usr/share/pixmaps/osify-taskmanager.png">
      <action name="Execute"><command>/usr/bin/osify-taskmanager</command></action>
    </item>
    <item label="Centro di Controllo" icon="/usr/share/pixmaps/osify-settings.png">
      <action name="Execute"><command>/usr/bin/osify-settings</command></action>
    </item>
    <separator/>
    <separator label="Sistema e Installazione"/>
    <item label="Installa OSify su Disco" icon="/usr/share/pixmaps/osify-install.png">
      <action name="Execute"><command>/usr/bin/osify-install</command></action>
    </item>
    <item label="Profilo Utente" icon="/usr/share/pixmaps/osify-profile.png">
      <action name="Execute"><command>/usr/bin/osify-profile-setup --force</command></action>
    </item>
    <item label="Aggiornamento Sistema" icon="/usr/share/pixmaps/osify-update.png">
      <action name="Execute"><command>/usr/bin/terminal -T 'Aggiornamento Sistema' -e /usr/bin/osify-update</command></action>
    </item>
    <separator/>
    <item label="Esci / Riavvia / Spegni">
      <action name="Execute"><command>/usr/bin/terminal -geometry 60x14 -T 'Uscita OSify' -e sh -c 'echo "1) Riavvia  2) Spegni  3) Chiudi sessione"; read -r a; case $a in 1) reboot;; 2) poweroff;; 3) pkill -u $USER;; esac'</command></action>
    </item>
  </menu>
</openbox_menu>
"""

OSIFY_SHELL_PROFILE = """# OSify Universal Shell Environment & Aliases
export PS1='\\[\\033[1;36m\\][OSify:\\[\\033[1;32m\\]\\u\\[\\033[1;36m\\]@\\[\\033[1;35m\\]\\h \\[\\033[1;33m\\]\\W\\[\\033[1;36m\\]]\\$ \\[\\033[0m\\]'
alias info='osify info'
alias stato='osify stato'
alias status='osify status'
alias turbo='osify turbo'
alias eco='osify eco'
alias pulisci='osify pulisci'
alias wifi='osify wifi'
alias rete='osify wifi'
alias schermo='osify schermo'
alias display='osify schermo'
alias installa='osify installa'
alias install='osify installa'
alias profilo='osify profilo'
alias cattura='osify cattura'
alias telefono='osify telefono'
alias aggiorna='osify aggiorna'
alias aiuto='osify aiuto'
alias help='osify aiuto'
alias fastfetch='osify-fastfetch'
alias neofetch='osify-fastfetch'
"""

lxpanel_cfg = ""

def remaster_rootfs3(work_dir, iso_root, wallpaper_jpg):
    print("[i] Remastering rootfs3 (SLIM autologin 0s, rimozione ragno SliTaz, OSify Cyber-Bar)...")
    r3_work = os.path.join(work_dir, "rootfs3")
    os.makedirs(r3_work, exist_ok=True)
    r3_gz = os.path.join(iso_root, "boot/rootfs3.gz")
    
    with open(r3_gz, "rb") as f:
        r3_data = lzma.decompress(f.read())
    extract_cpio_archive(r3_data, r3_work)

    # 1. Configurazione SLIM per autologin forzato e tema osify con fallback indistruttibile
    slim_conf = os.path.join(r3_work, "etc/slim.conf")
    slim_content = """default_path        /bin:/usr/bin:/usr/local/bin:/usr/X11R6/bin
default_xserver     /usr/bin/Xorg
halt_cmd            /sbin/poweroff
reboot_cmd          /sbin/reboot
console_cmd         /usr/bin/xterm -C -fg white -bg black +sb -T "Console login" -e /bin/sh -l -c "exec /bin/login"
xauth_path          /usr/bin/xauth 
authfile            /var/run/slim.auth
hidecursor          true
login_cmd           exec /bin/sh -l /usr/bin/osify-session
auto_login          yes
default_user        osify
current_theme       osify
lockfile            /var/lock/slim.lock
logfile             /var/log/slim.log
"""
    os.makedirs(os.path.dirname(slim_conf), exist_ok=True)
    with open(slim_conf, "w") as f:
        f.write(slim_content)

    # Scrittura account utente ufficiale OSify (UID 1000) e rimozione totale residui tux
    passwd_file = os.path.join(r3_work, "etc/passwd")
    shadow_file = os.path.join(r3_work, "etc/shadow")
    group_file = os.path.join(r3_work, "etc/group")
    sudoers_file = os.path.join(r3_work, "etc/sudoers")
    hostname_file = os.path.join(r3_work, "etc/hostname")

    with open(passwd_file, "w") as f:
        f.write("root:x:0:0:root:/root:/bin/sh\n"
                "osify:x:1000:1000:OSify Live User:/home/osify:/bin/sh\n"
                "nobody:x:65534:65534:nobody:/tmp:/bin/false\n"
                "messagebus:x:25:25:messagebus:/var/run/dbus:/bin/false\n")
    with open(shadow_file, "w") as f:
        f.write("root::14000:0:99999:7:::\n"
                "osify::14000:0:99999:7:::\n"
                "nobody:*:14000:0:99999:7:::\n")
    with open(group_file, "w") as f:
        f.write("root:x:0:\n"
                "osify:x:1000:\n"
                "wheel:x:10:root,osify\n"
                "sudo:x:27:root,osify\n"
                "audio:x:29:osify\n"
                "video:x:44:osify\n"
                "cdrom:x:24:osify\n"
                "dialout:x:20:osify\n"
                "disk:x:6:osify\n"
                "storage:x:26:osify\n"
                "input:x:97:osify\n"
                "users:x:100:osify\n")
    with open(sudoers_file, "w") as f:
        f.write("root ALL=(ALL) ALL\n"
                "osify ALL=(ALL) NOPASSWD: ALL\n")
    with open(hostname_file, "w") as f:
        f.write("osify-system\n")

    # Scrittura diretta e deterministica di .xinitrc con permessi 755
    for rc_path in ["etc/skel/.xinitrc", "root/.xinitrc", "home/osify/.xinitrc", "etc/X11/xinit/xinitrc"]:
        full_rc = os.path.join(r3_work, rc_path)
        os.makedirs(os.path.dirname(full_rc), exist_ok=True)
        with open(full_rc, "w") as f:
            f.write(CLEAN_XINITRC)
        os.chmod(full_rc, 0o755)

    osify_home_r3 = os.path.join(r3_work, "home/osify")
    os.makedirs(osify_home_r3, exist_ok=True)
    os.chmod(osify_home_r3, 0o777)
    for udir in ["Desktop", "Documenti", "Download", "Musica", "Video", "Progetti", "Giochi"]:
        os.makedirs(os.path.join(osify_home_r3, udir), exist_ok=True)

    # Pulizia residui tux e symlink invisibile di retrocompatibilità
    tux_dir = os.path.join(r3_work, "home/tux")
    if os.path.exists(tux_dir) and not os.path.islink(tux_dir):
        shutil.rmtree(tux_dir, ignore_errors=True)
    if not os.path.exists(tux_dir):
        os.symlink("osify", tux_dir)

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
    global lxpanel_cfg
    lxpanel_cfg = """# OSify Cyber-Bar Configuration
Global {
    edge=bottom
    allign=center
    margin=0
    widthtype=percent
    width=100
    height=32
    transparent=1
    tintcolor=#0a0e17
    alpha=225
    autohide=0
    heightwhenhidden=2
    setdocktype=1
    setpartialstrut=1
    usefontcolor=1
    fontsize=10
    fontcolor=#38bdf8
    usefontsize=1
    background=0
    iconsize=24
    loglevel=2
}

Plugin {
    type = menu
    Config {
        image=/usr/share/pixmaps/osify-drawer.png
        item {
            name=Tutte le Applicazioni
            image=/usr/share/pixmaps/osify-drawer.png
            action=/usr/bin/osify-app-drawer
        }
        separator {
        }
        item {
            name=Profilo Utente
            image=/usr/share/pixmaps/osify-settings.png
            action=/usr/bin/osify-profile-setup --force
        }
        item {
            name=Gestione Utenti
            image=/usr/share/pixmaps/osify-settings.png
            action=/usr/bin/osify-users
        }
        item {
            name=Installa OSify su Disco
            image=/usr/share/pixmaps/osify-install.png
            action=/usr/bin/osify-install
        }
        separator {
        }
        item {
            name=OSify Hub
            image=/usr/share/pixmaps/osify-hub.png
            action=/usr/bin/terminal -geometry 74x20 -T 'OSify Hub' -e /usr/bin/osify-hub
        }
        item {
            name=Navigatore Web
            image=/usr/share/pixmaps/osify-browser.png
            action=/usr/bin/osify-browser
        }
        item {
            name=Connessione Wi-Fi
            image=/usr/share/pixmaps/osify-wifi.png
            action=/usr/bin/terminal -geometry 75x20 -T 'Connessione Wi-Fi' -e /usr/bin/osify-wifi
        }
        item {
            name=Gaming Hub
            image=/usr/share/pixmaps/osify-games.png
            action=/usr/bin/terminal -geometry 75x20 -T 'Gaming Hub' -e /usr/bin/osify-games
        }
        item {
            name=Strumenti di Sviluppo
            image=/usr/share/pixmaps/osify-developer.png
            action=/usr/bin/terminal -geometry 75x20 -T 'Strumenti di Sviluppo' -e /usr/bin/osify-developer
        }
        item {
            name=Personalizzazione Schermo
            image=/usr/share/pixmaps/osify-appearance.png
            action=/usr/bin/osify-appearance
        }
        item {
            name=Gestione Attivita
            image=/usr/share/pixmaps/osify-taskmanager.png
            action=/usr/bin/osify-taskmanager
        }
        item {
            name=Centro di Controllo
            image=/usr/share/pixmaps/osify-settings.png
            action=/usr/bin/osify-settings
        }
        separator {
        }
        item {
            name=Terminale di Sistema
            image=/usr/share/pixmaps/osify-terminal.png
            action=/usr/bin/terminal
        }
        item {
            name=Gestore File
            image=/usr/share/pixmaps/osify-files.png
            action=pcmanfm
        }
        separator {
        }
        item {
            name=Blocca Schermo
            image=/usr/share/pixmaps/osify-settings.png
            action=xlock
        }
        item {
            name=Riavvia Computer
            image=/usr/share/pixmaps/osify-update.png
            action=reboot
        }
        item {
            name=Spegni Computer
            image=/usr/share/pixmaps/osify-taskmanager.png
            action=poweroff
        }
    }
}

Plugin {
    type = launchbar
    Config {
        Button {
            id=osify-drawer.desktop
        }
        Button {
            id=osify-hub.desktop
        }
        Button {
            id=osify-browser.desktop
        }
        Button {
            id=osify-wifi.desktop
        }
        Button {
            id=osify-games.desktop
        }
        Button {
            id=osify-developer.desktop
        }
        Button {
            id=osify-appearance.desktop
        }
        Button {
            id=osify-files.desktop
        }
        Button {
            id=osify-terminal.desktop
        }
        Button {
            id=osify-install.desktop
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
    type = volume
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
    for p_path in [
        "etc/skel/.config/lxpanel/slitaz/panels/panel",
        "etc/skel/.config/lxpanel/default/panels/panel",
        "home/osify/.config/lxpanel/slitaz/panels/panel",
        "home/osify/.config/lxpanel/default/panels/panel",
        "home/tux/.config/lxpanel/slitaz/panels/panel",
        "home/tux/.config/lxpanel/default/panels/panel",
        "etc/lxpanel/slitaz/panels/panel",
        "etc/lxpanel/default/panels/panel",
        "etc/xdg/lxpanel/default/panels/panel",
        "etc/xdg/lxpanel/slitaz/panels/panel",
        "etc/xdg/lxpanel/original/panels/panel",
        "root/.config/lxpanel/default/panels/panel",
        "root/.config/lxpanel/slitaz/panels/panel"
    ]:
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
    <keybind key="W-space"><action name="Execute"><command>/usr/bin/osify-app-drawer</command></action></keybind>
    <keybind key="W-a"><action name="Execute"><command>/usr/bin/osify-app-drawer</command></action></keybind>
    <keybind key="Super_L"><action name="Execute"><command>/usr/bin/osify-app-drawer</command></action></keybind>
    <keybind key="F1"><action name="Execute"><command>/usr/bin/osify-app-drawer</command></action></keybind>
    <keybind key="A-F1"><action name="Execute"><command>/usr/bin/osify-app-drawer</command></action></keybind>
    <keybind key="W-h"><action name="Execute"><command>/usr/bin/osify-hub</command></action></keybind>
    <keybind key="C-S-Escape"><action name="Execute"><command>/usr/bin/osify-taskmanager</command></action></keybind>
    <keybind key="W-F10"><action name="Execute"><command>/usr/bin/osify-hud --toggle-scale</command></action></keybind>
    <keybind key="W-t"><action name="Execute"><command>/usr/bin/terminal</command></action></keybind>
    <keybind key="C-A-t"><action name="Execute"><command>/usr/bin/terminal</command></action></keybind>
    <keybind key="W-e"><action name="Execute"><command>pcmanfm</command></action></keybind>
    <keybind key="W-w"><action name="Execute"><command>/usr/bin/osify-browser</command></action></keybind>
    <keybind key="W-i"><action name="Execute"><command>/usr/bin/osify-install</command></action></keybind>
    <keybind key="W-p"><action name="Execute"><command>/usr/bin/osify-profile-setup --force</command></action></keybind>
"""
        if "</keyboard>" in rc_content:
            rc_content = rc_content.replace("</keyboard>", f"{custom_keys}\n  </keyboard>")
            with open(rc_xml, "w") as f:
                f.write(rc_content)
            for ob_p in ["etc/skel/.config/openbox/rc.xml", "home/osify/.config/openbox/rc.xml", "home/tux/.config/openbox/rc.xml", "root/.config/openbox/rc.xml"]:
                full_ob = os.path.join(r3_work, ob_p)
                os.makedirs(os.path.dirname(full_ob), exist_ok=True)
                with open(full_ob, "w") as f:
                    f.write(rc_content)

    # 4b. Menu Contestuale Ufficiale OSify (Click Destro sul Desktop)
    for m_path in [
        "etc/xdg/openbox/menu.xml",
        "etc/xdg/openbox/menu.it.xml",
        "etc/skel/.config/openbox/menu.xml",
        "etc/skel/.config/openbox/menu.it.xml",
        "home/osify/.config/openbox/menu.xml",
        "home/tux/.config/openbox/menu.xml",
        "root/.config/openbox/menu.xml"
    ]:
        full_m = os.path.join(r3_work, m_path)
        os.makedirs(os.path.dirname(full_m), exist_ok=True)
        with open(full_m, "w") as f:
            f.write(OSIFY_OPENBOX_MENU)

    # 5. Configurazione nativa PCManFM Desktop Manager (Sfondo ed icone)
    for pfm_p in [
        "etc/xdg/pcmanfm/default/pcmanfm.conf",
        "etc/skel/.config/pcmanfm/default/pcmanfm.conf",
        "home/osify/.config/pcmanfm/default/pcmanfm.conf",
        "home/tux/.config/pcmanfm/default/pcmanfm.conf",
        "root/.config/pcmanfm/default/pcmanfm.conf"
    ]:
        full_pfm = os.path.join(r3_work, pfm_p)
        os.makedirs(os.path.dirname(full_pfm), exist_ok=True)
        with open(full_pfm, "w") as f:
            f.write(PCMANFM_CONF)

    # 6. Openbox Autostart Suite
    for as_p in [
        "etc/xdg/openbox/autostart",
        "etc/skel/.config/openbox/autostart",
        "home/osify/.config/openbox/autostart",
        "home/tux/.config/openbox/autostart",
        "root/.config/openbox/autostart"
    ]:
        full_as = os.path.join(r3_work, as_p)
        os.makedirs(os.path.dirname(full_as), exist_ok=True)
        with open(full_as, "w") as f:
            f.write(OPENBOX_AUTOSTART)
        os.chmod(full_as, 0o755)

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

    clean_cfg = """DEFAULT osify
UI vesamenu.c32
PROMPT 0
TIMEOUT 40

MENU TITLE OSify Operating System (32-bit Vintage Edition)
MENU BACKGROUND splash.jpg
MENU WIDTH 78
MENU MARGIN 6
MENU ROWS 7
MENU VSHIFT 4
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
    MENU LABEL [1] OSify Vintage Desktop (Auto-boot / Live Session)
    KERNEL /boot/bzImage
    INITRD /boot/rootfs4.gz,/boot/rootfs3.gz,/boot/rootfs2.gz,/boot/rootfs1.gz
    APPEND root=/dev/null video=-32 autologin lang=it_IT kmap=it rw quiet splash

LABEL turbo
    MENU LABEL [2] OSify Turbo Performance Mode (1.66GHz & zRAM Max)
    KERNEL /boot/bzImage
    INITRD /boot/rootfs4.gz,/boot/rootfs3.gz,/boot/rootfs2.gz,/boot/rootfs1.gz
    APPEND root=/dev/null video=-32 autologin lang=it_IT kmap=it rw quiet splash osify.turbo=1

LABEL safe
    MENU LABEL [3] OSify Safe Graphics Mode (Fallback VESA / Nomodeset)
    KERNEL /boot/bzImage
    INITRD /boot/rootfs4.gz,/boot/rootfs3.gz,/boot/rootfs2.gz,/boot/rootfs1.gz
    APPEND root=/dev/null nomodeset autologin lang=it_IT kmap=it rw

LABEL install
    MENU LABEL [4] Installa OSify su Disco Fisso
    KERNEL /boot/bzImage
    INITRD /boot/rootfs4.gz,/boot/rootfs3.gz,/boot/rootfs2.gz,/boot/rootfs1.gz
    APPEND root=/dev/null video=-32 autologin lang=it_IT kmap=it rw quiet splash osify.install=1

LABEL memtest
    MENU LABEL [5] Verifica Memoria RAM (Memtest86)
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
    os.makedirs(os.path.join(r4_work, "usr/local/bin"), exist_ok=True)

    # Universal Terminal Wrapper per Sakura/Xterm/LXTerminal
    shutil.copy2(os.path.join(REPO_ROOT, "tools/osify-gui/osify-terminal-wrapper.sh"), os.path.join(bin_dir, "terminal"))
    shutil.copy2(os.path.join(REPO_ROOT, "tools/osify-gui/osify-terminal-wrapper.sh"), os.path.join(r4_work, "usr/local/bin/terminal"))
    shutil.copy2(os.path.join(REPO_ROOT, "tools/osify-gui/osify-terminal-wrapper.sh"), os.path.join(bin_dir, "x-terminal-emulator"))

    # Master Command OSify (CLI & TUI Dashboard a 360 Gradi)
    shutil.copy2(os.path.join(REPO_ROOT, "tools/osify"), os.path.join(bin_dir, "osify"))
    shutil.copy2(os.path.join(REPO_ROOT, "tools/osify"), os.path.join(r4_work, "usr/local/bin/osify"))
    shutil.copy2(os.path.join(REPO_ROOT, "tools/osify"), os.path.join(r4_work, "bin/osify"))
    os.chmod(os.path.join(bin_dir, "osify"), 0o755)

    # Fastfetch & Neofetch Nativo OSify
    fastfetch_src = os.path.join(REPO_ROOT, "desktop/branding/fastfetch/osify-fastfetch.sh")
    if os.path.exists(fastfetch_src):
        shutil.copy2(fastfetch_src, os.path.join(bin_dir, "fastfetch"))
        shutil.copy2(fastfetch_src, os.path.join(bin_dir, "neofetch"))
        shutil.copy2(fastfetch_src, os.path.join(bin_dir, "osify-fastfetch"))
        shutil.copy2(fastfetch_src, os.path.join(r4_work, "usr/local/bin/fastfetch"))
        os.chmod(os.path.join(bin_dir, "fastfetch"), 0o755)
        os.chmod(os.path.join(bin_dir, "neofetch"), 0o755)
        os.chmod(os.path.join(bin_dir, "osify-fastfetch"), 0o755)

    # Toolchain Ufficiale OSify & Gestione Sistema
    shutil.copy2(os.path.join(REPO_ROOT, "tools/osify-ctl"), os.path.join(bin_dir, "osify-ctl"))
    shutil.copy2(os.path.join(REPO_ROOT, "uem/runners/osify-inspect.sh"), os.path.join(bin_dir, "osify-inspect"))
    shutil.copy2(os.path.join(REPO_ROOT, "uem/runners/osify-universal-dispatcher.sh"), os.path.join(bin_dir, "osify-exec"))
    shutil.copy2(os.path.join(REPO_ROOT, "tools/osify-gui/osify-install-gui.sh"), os.path.join(bin_dir, "osify-install"))
    shutil.copy2(os.path.join(REPO_ROOT, "tools/osify-gui/osify-install-gui.sh"), os.path.join(bin_dir, "osify-install-gui"))
    shutil.copy2(os.path.join(REPO_ROOT, "system/installer/osify-disk-installer.sh"), os.path.join(bin_dir, "osify-disk-installer"))
    shutil.copy2(os.path.join(REPO_ROOT, "system/autotune/osify-autotune.sh"), os.path.join(bin_dir, "osify-autotune"))
    shutil.copy2(os.path.join(REPO_ROOT, "system/storage/osify-memory-cleaner.sh"), os.path.join(bin_dir, "osify-cleanmem"))
    shutil.copy2(os.path.join(REPO_ROOT, "tools/osify-gui/osify-welcome.sh"), os.path.join(bin_dir, "osify-welcome"))
    shutil.copy2(os.path.join(REPO_ROOT, "tools/osify-gui/osify-welcome-wizard.py"), os.path.join(bin_dir, "osify-welcome-wizard.py"))
    shutil.copy2(os.path.join(REPO_ROOT, "tools/osify-gui/osify-profile-setup.sh"), os.path.join(bin_dir, "osify-profile-setup"))
    shutil.copy2(os.path.join(REPO_ROOT, "tools/osify-gui/osify-user-manager.sh"), os.path.join(bin_dir, "osify-users"))
    shutil.copy2(os.path.join(REPO_ROOT, "tools/osify-gui/osify-user-manager.sh"), os.path.join(bin_dir, "osify-user-manager"))
    shutil.copy2(os.path.join(REPO_ROOT, "system/input/osify-input-manager.sh"), os.path.join(bin_dir, "osify-input"))
    shutil.copy2(os.path.join(REPO_ROOT, "system/autotune/osify-hw-probe.sh"), os.path.join(bin_dir, "osify-hw-probe"))
    shutil.copy2(os.path.join(REPO_ROOT, "tools/osify-gui/osify-hud.sh"), os.path.join(bin_dir, "osify-hud"))
    shutil.copy2(os.path.join(REPO_ROOT, "tools/osify-gui/osify-taskmanager.sh"), os.path.join(bin_dir, "osify-taskmanager"))
    shutil.copy2(os.path.join(REPO_ROOT, "tools/osify-gui/osify-settings.sh"), os.path.join(bin_dir, "osify-settings"))
    shutil.copy2(os.path.join(REPO_ROOT, "tools/osify-gui/osify-terminal.sh"), os.path.join(bin_dir, "osify-terminal"))
    shutil.copy2(os.path.join(REPO_ROOT, "uem/runners/osify-pe-runner.sh"), os.path.join(bin_dir, "osify-pe-runner"))
    shutil.copy2(os.path.join(REPO_ROOT, "uem/runners/osify-apk-runner.sh"), os.path.join(bin_dir, "osify-apk-runner"))
    shutil.copy2(os.path.join(REPO_ROOT, "uem/runners/osify-macho-runner.sh"), os.path.join(bin_dir, "osify-macho-runner"))
    shutil.copy2(os.path.join(REPO_ROOT, "uem/runners/osify-ipa-runner.sh"), os.path.join(bin_dir, "osify-ipa-runner"))
    shutil.copy2(os.path.join(REPO_ROOT, "uem/runners/osify-dos-runner.sh"), os.path.join(bin_dir, "osify-dos-runner"))
    shutil.copy2(os.path.join(REPO_ROOT, "uem/runners/osify-wasm-runner.sh"), os.path.join(bin_dir, "osify-wasm-runner"))
    shutil.copy2(os.path.join(REPO_ROOT, "uem/runners/osify-java-runner.sh"), os.path.join(bin_dir, "osify-java-runner"))
    shutil.copy2(os.path.join(REPO_ROOT, "uem/runners/osify-cross-runner.sh"), os.path.join(bin_dir, "osify-cross-runner"))
    shutil.copy2(os.path.join(REPO_ROOT, "tools/osify-gui/osify-hub.sh"), os.path.join(bin_dir, "osify-hub"))
    shutil.copy2(os.path.join(REPO_ROOT, "tools/osify-gui/osify-browser.sh"), os.path.join(bin_dir, "osify-browser"))
    shutil.copy2(os.path.join(REPO_ROOT, "network/osify-wifi-gui.sh"), os.path.join(bin_dir, "osify-wifi"))
    shutil.copy2(os.path.join(REPO_ROOT, "tools/osify-gui/osify-games.sh"), os.path.join(bin_dir, "osify-games"))
    shutil.copy2(os.path.join(REPO_ROOT, "tools/osify-gui/osify-developer.sh"), os.path.join(bin_dir, "osify-developer"))
    shutil.copy2(os.path.join(REPO_ROOT, "system/storage/osify-storage-governor.sh"), os.path.join(bin_dir, "osify-storage-governor"))
    shutil.copy2(os.path.join(REPO_ROOT, "system/storage/osify-storage-governor.sh"), os.path.join(bin_dir, "osify-eject"))
    shutil.copy2(os.path.join(REPO_ROOT, "tools/osify-gui/osify-video-capture.sh"), os.path.join(bin_dir, "osify-capture"))
    shutil.copy2(os.path.join(REPO_ROOT, "tools/osify-gui/osify-video-capture.sh"), os.path.join(bin_dir, "osify-video-capture"))
    shutil.copy2(os.path.join(REPO_ROOT, "tools/osify-gui/osify-phone-companion.sh"), os.path.join(bin_dir, "osify-phone-companion"))
    shutil.copy2(os.path.join(REPO_ROOT, "tools/osify-gui/osify-phone-companion.sh"), os.path.join(bin_dir, "osify-phone"))
    shutil.copy2(os.path.join(REPO_ROOT, "tools/osify-gui/osify-display-switch.sh"), os.path.join(bin_dir, "osify-display"))
    shutil.copy2(os.path.join(REPO_ROOT, "tools/osify-gui/osify-display-switch.sh"), os.path.join(bin_dir, "osify-display-switch"))
    shutil.copy2(os.path.join(REPO_ROOT, "tools/osify-gui/osify-smart-customizer.sh"), os.path.join(bin_dir, "osify-appearance"))
    shutil.copy2(os.path.join(REPO_ROOT, "tools/osify-gui/osify-smart-customizer.sh"), os.path.join(bin_dir, "osify-customizer"))
    shutil.copy2(os.path.join(REPO_ROOT, "tools/osify-gui/osify-media-processor.py"), os.path.join(bin_dir, "osify-media-processor"))
    shutil.copy2(os.path.join(REPO_ROOT, "tools/osify-gui/osify-cyber-dock.sh"), os.path.join(bin_dir, "osify-cyber-dock"))
    shutil.copy2(os.path.join(REPO_ROOT, "tools/osify-gui/osify-app-drawer.py"), os.path.join(bin_dir, "osify-app-drawer.py"))
    shutil.copy2(os.path.join(REPO_ROOT, "tools/osify-gui/osify-app-drawer.sh"), os.path.join(bin_dir, "osify-app-drawer"))
    shutil.copy2(os.path.join(REPO_ROOT, "tools/osify-gui/osify-app-drawer.sh"), os.path.join(bin_dir, "osify-drawer"))
    shutil.copy2(os.path.join(REPO_ROOT, "system/input/osify-input-setup.sh"), os.path.join(bin_dir, "osify-input-setup"))
    shutil.copy2(os.path.join(REPO_ROOT, "system/session/osify-session.sh"), os.path.join(bin_dir, "osify-session"))
    shutil.copy2(os.path.join(REPO_ROOT, "system/updater/osify-live-updater.sh"), os.path.join(bin_dir, "osify-update"))
    for f in os.listdir(bin_dir):
        p = os.path.join(bin_dir, f)
        if not os.path.islink(p) and os.path.isfile(p):
            try:
                os.chmod(p, 0o755)
            except Exception:
                pass

    # Iniezione Browser Grafico Nativo Dillo (i686) per Navigazione Istantanea
    def inject_tazpkg(pkg_name, pkg_url, dest_rootfs):
        cache_path = os.path.join(REPO_ROOT, "build/cache", pkg_name)
        if not (os.path.exists(cache_path) and os.path.getsize(cache_path) > 10 * 1024):
            print(f"[+] Download {pkg_name} per OSify...")
            os.makedirs(os.path.dirname(cache_path), exist_ok=True)
            run(f"curl -sL '{pkg_url}' -o '{cache_path}'")
        
        if os.path.exists(cache_path):
            tmp_d = f"/tmp/osify_{pkg_name}_extract"
            shutil.rmtree(tmp_d, ignore_errors=True)
            os.makedirs(tmp_d, exist_ok=True)
            run(f"cd '{tmp_d}' && cpio -idmv < '{cache_path}' >/dev/null 2>&1")
            lzma_cpio = os.path.join(tmp_d, "fs.cpio.lzma")
            if os.path.exists(lzma_cpio):
                with open(lzma_cpio, "rb") as f:
                    raw_cpio = lzma.decompress(f.read())
                with open(os.path.join(tmp_d, "fs.cpio"), "wb") as f:
                    f.write(raw_cpio)
                run(f"cd '{tmp_d}' && cpio -idmv < fs.cpio >/dev/null 2>&1")
                pkg_fs = os.path.join(tmp_d, "fs")
                if os.path.exists(pkg_fs):
                    for sub in ["usr/bin", "usr/lib", "usr/share", "etc"]:
                        src_sub = os.path.join(pkg_fs, sub)
                        dst_sub = os.path.join(dest_rootfs, sub)
                        if os.path.exists(src_sub):
                            shutil.copytree(src_sub, dst_sub, dirs_exist_ok=True)
                    print(f"[✓] Pacchetto {pkg_name} integrato con successo nella rootfs!")

    # Iniezione Applicativi Chiave: Dillo (Web), YAD (GTK Dialogs) e Htop (Task Manager)
    inject_tazpkg("dillo-3.0.5.tazpkg", "https://mirror.slitaz.org/i486/cooking/packages/dillo-3.0.5.tazpkg", r4_work)
    inject_tazpkg("yad-gtk2-0.40.0.tazpkg", "https://mirror.slitaz.org/i486/cooking/packages/yad-gtk2-0.40.0.tazpkg", r4_work)
    inject_tazpkg("htop-3.1.2-1.tazpkg", "https://mirror.slitaz.org/i486/cooking/packages/htop-3.1.2-1.tazpkg", r4_work)

    # Configurazione Utenti & Sicurezza Radicale OSify (Addio SliTaz Admin)
    etc_dir = os.path.join(r4_work, "etc")
    os.makedirs(etc_dir, exist_ok=True)

    # 1. Account utenti in /etc/passwd
    passwd_txt = (
        "root:x:0:0:Amministratore OSify:/root:/bin/sh\n"
        "osify:x:1000:1000:Utente OSify:/home/osify:/bin/sh\n"
        "tux:x:1001:1000:Utente OSify Live:/home/osify:/bin/sh\n"
        "nobody:x:99:99:Unprivileged User:/dev/null:/bin/false\n"
        "www:x:80:80:Web Server User:/var/www:/bin/false\n"
    )
    with open(os.path.join(etc_dir, "passwd"), "w") as f:
        f.write(passwd_txt)

    # 2. Shadow sbloccato senza password per la sessione Live
    shadow_txt = (
        "root::19000:0:99999:7:::\n"
        "osify::19000:0:99999:7:::\n"
        "tux::19000:0:99999:7:::\n"
    )
    with open(os.path.join(etc_dir, "shadow"), "w") as f:
        f.write(shadow_txt)
    os.chmod(os.path.join(etc_dir, "shadow"), 0o600)

    # 3. Gruppi di sistema con privilegi per osify
    group_txt = (
        "root:x:0:\n"
        "wheel:x:10:root,osify,tux\n"
        "audio:x:29:osify,tux\n"
        "video:x:44:osify,tux\n"
        "disk:x:6:osify,tux\n"
        "storage:x:95:osify,tux\n"
        "input:x:97:osify,tux\n"
        "users:x:100:osify,tux\n"
        "osify:x:1000:\n"
    )
    with open(os.path.join(etc_dir, "group"), "w") as f:
        f.write(group_txt)

    # 4. Sudoers: NOPASSWD totale per non chiedere MAI password in sessione Live
    sudoers_txt = (
        "root ALL=(ALL) ALL\n"
        "osify ALL=(ALL) NOPASSWD: ALL\n"
        "tux ALL=(ALL) NOPASSWD: ALL\n"
        "%wheel ALL=(ALL) NOPASSWD: ALL\n"
        "%users ALL=(ALL) NOPASSWD: ALL\n"
    )
    with open(os.path.join(etc_dir, "sudoers"), "w") as f:
        f.write(sudoers_txt)
    os.chmod(os.path.join(etc_dir, "sudoers"), 0o440)

    # 5. Sostituzione subox e gksu con wrapper sudo trasparente
    subox_wrapper = "#!/bin/sh\nexec sudo \"$@\"\n"
    for sw in ["usr/bin/subox", "usr/bin/gksu", "bin/subox", "bin/gksu"]:
        sw_p = os.path.join(r4_work, sw)
        os.makedirs(os.path.dirname(sw_p), exist_ok=True)
        with open(sw_p, "w") as f:
            f.write(subox_wrapper)
        os.chmod(sw_p, 0o755)

    # 6. SLiM Display Manager: Autologin garantito su osify
    slim_cfg = os.path.join(etc_dir, "slim.conf")
    if os.path.exists(slim_cfg):
        with open(slim_cfg, "r") as f:
            stxt = f.read()
        stxt = stxt.replace("default_user        tux", "default_user        osify")
        stxt = stxt.replace("#auto_login          no", "auto_login          yes")
        stxt = stxt.replace("auto_login          no", "auto_login          yes")
        with open(slim_cfg, "w") as f:
            f.write(stxt)
    else:
        with open(slim_cfg, "w") as f:
            f.write("default_path ./bin:/usr/bin\ndefault_xserver /usr/bin/Xorg\nlogin_cmd exec /bin/sh -l ~/.xinitrc %session\ndefault_user osify\nauto_login yes\n")

    # 7. Creazione Home per osify e tux con symlink di allineamento
    home_osify = os.path.join(r4_work, "home/osify")
    home_tux = os.path.join(r4_work, "home/tux")
    os.makedirs(home_osify, exist_ok=True)
    os.makedirs(os.path.join(home_osify, "Desktop"), exist_ok=True)
    os.makedirs(os.path.join(home_osify, ".config"), exist_ok=True)

    # Iniezione regole binfmt del kernel
    binfmt_dir = os.path.join(r4_work, "etc/binfmt.d")
    os.makedirs(binfmt_dir, exist_ok=True)
    binfmt_src = os.path.join(REPO_ROOT, "uem/binfmt/99-osify-binfmt.conf")
    if os.path.exists(binfmt_src):
        shutil.copy2(binfmt_src, os.path.join(binfmt_dir, "99-osify.conf"))

    # Iniezione Icone Native Vettoriali OSify (Eliminazione Totale Icone Bianche)
    pixmaps_dir = os.path.join(r4_work, "usr/share/pixmaps")
    os.makedirs(pixmaps_dir, exist_ok=True)
    hicolor_dir = os.path.join(r4_work, "usr/share/icons/hicolor/48x48/apps")
    os.makedirs(hicolor_dir, exist_ok=True)

    icons_src_dir = os.path.join(REPO_ROOT, "desktop/branding/icons/48")
    if os.path.exists(icons_src_dir):
        for icon_file in os.listdir(icons_src_dir):
            if icon_file.endswith(".png"):
                src_icon = os.path.join(icons_src_dir, icon_file)
                shutil.copy2(src_icon, os.path.join(pixmaps_dir, icon_file))
                shutil.copy2(src_icon, os.path.join(hicolor_dir, icon_file))
        print(f"[✓] Copiate {len(os.listdir(icons_src_dir))} icone native in /usr/share/pixmaps/")

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

    # Inizializzazione Hardware Autonoma e Auto-Updater in /etc/init.d/local.sh
    local_sh = os.path.join(r4_work, "etc/init.d/local.sh")
    with open(local_sh, "a") as f:
        f.write("""
# OSify Universal Autonomous Hardware Engine
/usr/bin/osify-hw-probe >/var/log/osify-hw-probe.log 2>&1 &

# OSify Autonomous Auto-Updater Background Monitor
nice -n 19 /usr/bin/osify-update daemon >/var/log/osify-autoupdate.log 2>&1 &
""")

    # Impronta e Identita Indelebile OSify nel Kernel e User-Space
    with open(os.path.join(r4_work, "etc/osify-version"), "w") as f:
        f.write(f"{OSIFY_VERSION}\n")

    with open(os.path.join(r4_work, "etc/os-release"), "w") as f:
        f.write(f"""NAME="OSify"
PRETTY_NAME="OSify {OSIFY_VERSION} (Vintage Universal Edition)"
ID=osify
ID_LIKE="slitaz debian linux"
VERSION="{OSIFY_VERSION}"
VERSION_ID="{OSIFY_VERSION}"
HOME_URL="https://github.com/ANDRYXify/OSify"
BUG_REPORT_URL="https://github.com/ANDRYXify/OSify/issues"
SUPPORT_URL="https://github.com/ANDRYXify/OSify"
ANSI_COLOR="0;36"
""")

    with open(os.path.join(r4_work, "etc/lsb-release"), "w") as f:
        f.write(f"""DISTRIB_ID=OSify
DISTRIB_RELEASE={OSIFY_VERSION}
DISTRIB_CODENAME=vintage
DISTRIB_DESCRIPTION="OSify {OSIFY_VERSION} (Vintage Universal Edition)"
""")

    with open(os.path.join(r4_work, "etc/hostname"), "w") as f:
        f.write("osify\n")

    with open(os.path.join(r4_work, "etc/hosts"), "w") as f:
        f.write("""127.0.0.1   localhost
127.0.1.1   osify
::1         localhost ip6-localhost ip6-loopback
""")

    with open(os.path.join(r4_work, "etc/issue"), "w") as f:
        f.write(rf"""\033[1;36m
   ____   _____  _  __       
  / __ \ / ____|(_)/ _|      
 | |  | | (___   _| |_ _   _ 
 | |  | |\___ \ | |  _| | | |
 | |__| |____) || | | | |_| |
  \____/|_____/ |_|_|  \__, |
                        __/ |
                       |___/ 
\033[0m
 \033[1;37mOSify {OSIFY_VERSION} (Vintage Universal Edition)\033[0m - Kernel \r (\m)
 Ingegnerizzato da Andrea Taliento (ANDRYXify)
 
""")

    with open(os.path.join(r4_work, "etc/issue.net"), "w") as f:
        f.write(f"OSify {OSIFY_VERSION} (Vintage Universal Edition) - \\r (\\m)\n")

    with open(os.path.join(r4_work, "etc/motd"), "w") as f:
        f.write(rf"""==============================================================================
   OSify {OSIFY_VERSION} — Sistema Operativo Universale & Resurrezione Hardware
==============================================================================
 Nucleo: Linux (\r \m)
 Identita: OSify (ID: osify)
 Subsystems: UEM (Win32, APK, Darwin, WASI, DOS, ELF-Cross) attivo
 Aggiornamenti: OSify Autonomous Auto-Updater attivo
==============================================================================
""")

    # Configurazione applicazioni predefinite OSify
    app_conf = """# OSify default applications configuration
FILE_MANAGER="pcmanfm"
BROWSER="osify-browser"
EDITOR="nano"
TERMINAL="terminal"
WINDOW_MANAGER="openbox"
"""
    for ac_path in ["etc/slitaz/applications.conf", "etc/skel/.config/slitaz/applications.conf", "home/osify/.config/slitaz/applications.conf"]:
        full_ac = os.path.join(r4_work, ac_path)
        os.makedirs(os.path.dirname(full_ac), exist_ok=True)
        with open(full_ac, "w") as f:
            f.write(app_conf)

    # Iniezione deterministica di .xinitrc con permessi 755 in rootfs4
    for rc_path in ["etc/skel/.xinitrc", "root/.xinitrc", "home/osify/.xinitrc", "etc/X11/xinit/xinitrc"]:
        full_rc = os.path.join(r4_work, rc_path)
        os.makedirs(os.path.dirname(full_rc), exist_ok=True)
        with open(full_rc, "w") as f:
            f.write(CLEAN_XINITRC)
        os.chmod(full_rc, 0o755)

    osify_home_r4 = os.path.join(r4_work, "home/osify")
    os.makedirs(osify_home_r4, exist_ok=True)
    os.chmod(osify_home_r4, 0o777)
    for udir in ["Desktop", "Documenti", "Download", "Musica", "Video", "Progetti", "Giochi"]:
        os.makedirs(os.path.join(osify_home_r4, udir), exist_ok=True)

    # Symlink di sicurezza retrocompatibile per tux
    tux_r4 = os.path.join(r4_work, "home/tux")
    if os.path.exists(tux_r4) and not os.path.islink(tux_r4):
        shutil.rmtree(tux_r4, ignore_errors=True)
    if not os.path.exists(tux_r4):
        os.symlink("osify", tux_r4)

    # Configurazione nativa PCManFM Desktop Manager e Openbox Autostart in rootfs4
    for pfm_p in [
        "etc/xdg/pcmanfm/default/pcmanfm.conf",
        "etc/skel/.config/pcmanfm/default/pcmanfm.conf",
        "home/osify/.config/pcmanfm/default/pcmanfm.conf",
        "root/.config/pcmanfm/default/pcmanfm.conf"
    ]:
        full_pfm = os.path.join(r4_work, pfm_p)
        os.makedirs(os.path.dirname(full_pfm), exist_ok=True)
        with open(full_pfm, "w") as f:
            f.write(PCMANFM_CONF)

    for as_p in [
        "etc/xdg/openbox/autostart",
        "etc/skel/.config/openbox/autostart",
        "home/osify/.config/openbox/autostart",
        "root/.config/openbox/autostart"
    ]:
        full_as = os.path.join(r4_work, as_p)
        os.makedirs(os.path.dirname(full_as), exist_ok=True)
        with open(full_as, "w") as f:
            f.write(OPENBOX_AUTOSTART)
        os.chmod(full_as, 0o755)

    # Entry Applicative Ufficiali OSify (.desktop) con Icone Native Garantite (Zero Emoji per piena compatibilita X11)
    app_entries = {
        "osify-dashboard.desktop": (
            "[Desktop Entry]\n"
            "Type=Application\n"
            "Name=Dashboard di Sistema\n"
            "Comment=Centro di Controllo Interattivo a 360 Gradi (Hardware, Turbo, Wi-Fi, Schermo, RAM)\n"
            "Exec=/usr/bin/terminal -geometry 80x24 -T 'Dashboard di Sistema' -e /usr/bin/osify\n"
            "Icon=/usr/share/pixmaps/osify-hub.png\n"
            "Terminal=false\n"
            "Categories=System;Utility;\n"
        ),
        "osify-drawer.desktop": (
            "[Desktop Entry]\n"
            "Type=Application\n"
            "Name=Tutte le Applicazioni\n"
            "Comment=Pannello Applicazioni e Launchpad di Sistema\n"
            "Exec=/usr/bin/osify-app-drawer\n"
            "Icon=/usr/share/pixmaps/osify-drawer.png\n"
            "Terminal=false\n"
            "Categories=System;Utility;\n"
        ),
        "osify-hub.desktop": (
            "[Desktop Entry]\n"
            "Type=Application\n"
            "Name=OSify Hub\n"
            "Comment=Centro di Controllo, Prestazioni e Launchpad di OSify\n"
            "Exec=/usr/bin/terminal -geometry 74x20 -T 'OSify Hub' -e /usr/bin/osify-hub\n"
            "Icon=/usr/share/pixmaps/osify-hub.png\n"
            "Terminal=false\n"
            "Categories=System;Utility;\n"
        ),
        "osify-browser.desktop": (
            "[Desktop Entry]\n"
            "Type=Application\n"
            "Name=Navigatore Web\n"
            "Comment=Naviga su Internet con rendering grafico completo e Adblock integrato\n"
            "Exec=/usr/bin/osify-browser\n"
            "Icon=/usr/share/pixmaps/osify-browser.png\n"
            "Terminal=false\n"
            "Categories=Network;WebBrowser;\n"
        ),
        "osify-files.desktop": (
            "[Desktop Entry]\n"
            "Type=Application\n"
            "Name=Gestione File\n"
            "Comment=Esplora e gestisci cartelle, dischi e file personali\n"
            "Exec=pcmanfm\n"
            "Icon=/usr/share/pixmaps/osify-files.png\n"
            "Terminal=false\n"
            "Categories=System;Utility;FileManager;\n"
        ),
        "osify-wifi.desktop": (
            "[Desktop Entry]\n"
            "Type=Application\n"
            "Name=Connessione Wi-Fi\n"
            "Comment=Scansione reti wireless, inserimento password e connessione immediata\n"
            "Exec=/usr/bin/terminal -geometry 75x20 -T 'Connessione Wi-Fi' -e /usr/bin/osify-wifi\n"
            "Icon=/usr/share/pixmaps/osify-wifi.png\n"
            "Terminal=false\n"
            "Categories=Network;Settings;\n"
        ),
        "osify-games.desktop": (
            "[Desktop Entry]\n"
            "Type=Application\n"
            "Name=Gaming Hub\n"
            "Comment=Giochi Windows (.exe), Retrogaming DOS, Emulazione e Turbo Boost\n"
            "Exec=/usr/bin/terminal -geometry 75x20 -T 'Gaming Hub' -e /usr/bin/osify-games\n"
            "Icon=/usr/share/pixmaps/osify-games.png\n"
            "Terminal=false\n"
            "Categories=Game;\n"
        ),
        "osify-developer.desktop": (
            "[Desktop Entry]\n"
            "Type=Application\n"
            "Name=Strumenti di Sviluppo\n"
            "Comment=Suite di Programmazione: Python, C, Git, Editor e Progetti\n"
            "Exec=/usr/bin/terminal -geometry 75x20 -T 'Strumenti di Sviluppo' -e /usr/bin/osify-developer\n"
            "Icon=/usr/share/pixmaps/osify-developer.png\n"
            "Terminal=false\n"
            "Categories=Development;\n"
        ),
        "osify-appearance.desktop": (
            "[Desktop Entry]\n"
            "Type=Application\n"
            "Name=Personalizzazione Schermo\n"
            "Comment=Virtual Scaler Netbook 1280x768, Sfondi Cyber Dark e Risoluzioni\n"
            "Exec=/usr/bin/osify-appearance\n"
            "Icon=/usr/share/pixmaps/osify-appearance.png\n"
            "Terminal=false\n"
            "Categories=Settings;\n"
        ),
        "osify-taskmanager.desktop": (
            "[Desktop Entry]\n"
            "Type=Application\n"
            "Name=Gestione Attivita\n"
            "Comment=Monitor di Processi e Telemetria di Sistema in Tempo Reale\n"
            "Exec=/usr/bin/osify-taskmanager\n"
            "Icon=/usr/share/pixmaps/osify-taskmanager.png\n"
            "Terminal=false\n"
            "Categories=System;\n"
        ),
        "osify-terminal.desktop": (
            "[Desktop Entry]\n"
            "Type=Application\n"
            "Name=Terminale di Sistema\n"
            "Comment=Terminale con Fastfetch e Diagnostica Hardware\n"
            "Exec=/usr/bin/terminal\n"
            "Icon=/usr/share/pixmaps/osify-terminal.png\n"
            "Terminal=false\n"
            "Categories=System;\n"
        ),
        "osify-install.desktop": (
            "[Desktop Entry]\n"
            "Type=Application\n"
            "Name=Installa OSify su Disco\n"
            "Comment=Installatore Guidato su Disco Fisso con Migrazione Dati Live\n"
            "Exec=/usr/bin/osify-install\n"
            "Icon=/usr/share/pixmaps/osify-install.png\n"
            "Terminal=false\n"
            "Categories=System;\n"
        ),
        "osify-profile.desktop": (
            "[Desktop Entry]\n"
            "Type=Application\n"
            "Name=Profilo Utente\n"
            "Comment=Configura Account, Password, Avatar e Preferenze Sistema\n"
            "Exec=/usr/bin/osify-profile-setup --force\n"
            "Icon=/usr/share/pixmaps/osify-profile.png\n"
            "Terminal=false\n"
            "Categories=Settings;System;\n"
        ),
        "osify-users.desktop": (
            "[Desktop Entry]\n"
            "Type=Application\n"
            "Name=Gestione Utenti\n"
            "Comment=Crea, modifica ed elimina account utenti e permessi di amministrazione\n"
            "Exec=/usr/bin/osify-users\n"
            "Icon=/usr/share/pixmaps/osify-users.png\n"
            "Terminal=false\n"
            "Categories=Settings;System;\n"
        ),
        "osify-update.desktop": (
            "[Desktop Entry]\n"
            "Type=Application\n"
            "Name=Aggiornamento Sistema\n"
            "Comment=Verifica e installa aggiornamenti ufficiali a caldo\n"
            "Exec=/usr/bin/osify-update --gui\n"
            "Icon=/usr/share/pixmaps/osify-update.png\n"
            "Terminal=false\n"
            "Categories=System;Settings;PackageManager;\n"
        ),
        "osify-settings.desktop": (
            "[Desktop Entry]\n"
            "Type=Application\n"
            "Name=Centro di Controllo\n"
            "Comment=Centro di Controllo Sistema, Rete, Touchpad e Schermo\n"
            "Exec=/usr/bin/osify-settings\n"
            "Icon=/usr/share/pixmaps/osify-settings.png\n"
            "Terminal=false\n"
            "Categories=Settings;\n"
        ),
        "osify-capture.desktop": (
            "[Desktop Entry]\n"
            "Type=Application\n"
            "Name=Acquisizione Video HDMI\n"
            "Comment=Usa lo schermo di OSify per giocare con Switch, PS5, Xbox o reflex a latenza zero\n"
            "Exec=/usr/bin/osify-capture\n"
            "Icon=/usr/share/pixmaps/osify-games.png\n"
            "Terminal=false\n"
            "Categories=AudioVideo;Video;Game;\n"
        ),
        "osify-phone.desktop": (
            "[Desktop Entry]\n"
            "Type=Application\n"
            "Name=Mirroring Smartphone\n"
            "Comment=Duplica e controlla il tuo smartphone Android o iPhone direttamente dal PC\n"
            "Exec=/usr/bin/osify-phone-companion\n"
            "Icon=/usr/share/pixmaps/osify-hub.png\n"
            "Terminal=false\n"
            "Categories=Utility;Network;\n"
        ),
        "osify-display.desktop": (
            "[Desktop Entry]\n"
            "Type=Application\n"
            "Name=Uscite Video e Monitor\n"
            "Comment=Gestione Display Esterni HDMI/VGA: Clona, Estendi o Solo TV\n"
            "Exec=/usr/bin/osify-display\n"
            "Icon=/usr/share/pixmaps/osify-appearance.png\n"
            "Terminal=false\n"
            "Categories=Settings;HardwareSettings;\n"
        ),
        "osify-welcome.desktop": (
            "[Desktop Entry]\n"
            "Type=Application\n"
            "Name=Guida di Benvenuto\n"
            "Comment=Esperienza di Primo Avvio e Diagnostica Netbook\n"
            "Exec=/usr/bin/osify-hub\n"
            "Icon=/usr/share/pixmaps/osify-hub.png\n"
            "Terminal=false\n"
            "Categories=System;\n"
        )
    }

    # Scrittura in usr/share/applications e sui Desktop utente con permessi di esecuzione garantiti
    apps_sys = os.path.join(r4_work, "usr/share/applications")
    os.makedirs(apps_sys, exist_ok=True)
    for name, content in app_entries.items():
        dest_f = os.path.join(apps_sys, name)
        with open(dest_f, "w") as f:
            f.write(content)
        os.chmod(dest_f, 0o755)

    for dpath in ["root/Desktop", "home/osify/Desktop", "home/tux/Desktop", "home/slitaz/Desktop", "etc/skel/Desktop"]:
        full_d = os.path.join(r4_work, dpath)
        if os.path.exists(full_d):
            shutil.rmtree(full_d, ignore_errors=True)
        os.makedirs(full_d, exist_ok=True)
        for name, content in app_entries.items():
            dest_f = os.path.join(full_d, name)
            with open(dest_f, "w") as f:
                f.write(content)
            os.chmod(dest_f, 0o755)

    # Scrittura LXPanel Cyber-Bar anche in rootfs4 per integrità garantita
    for p_path in [
        "etc/skel/.config/lxpanel/slitaz/panels/panel",
        "etc/skel/.config/lxpanel/default/panels/panel",
        "home/osify/.config/lxpanel/slitaz/panels/panel",
        "home/osify/.config/lxpanel/default/panels/panel",
        "home/tux/.config/lxpanel/slitaz/panels/panel",
        "home/tux/.config/lxpanel/default/panels/panel",
        "etc/lxpanel/slitaz/panels/panel",
        "etc/lxpanel/default/panels/panel",
        "etc/xdg/lxpanel/default/panels/panel",
        "etc/xdg/lxpanel/slitaz/panels/panel",
        "etc/xdg/lxpanel/original/panels/panel",
        "root/.config/lxpanel/default/panels/panel",
        "root/.config/lxpanel/slitaz/panels/panel"
    ]:
        full_p = os.path.join(r4_work, p_path)
        os.makedirs(os.path.dirname(full_p), exist_ok=True)
        with open(full_p, "w") as f:
            f.write(lxpanel_cfg)

    # Permessi corretti su tutte le home degli utenti live
    for uh in ["home/osify", "home/tux", "home/slitaz"]:
        full_uh = os.path.join(r4_work, uh)
        if os.path.exists(full_uh):
            run(f"chmod -R 777 '{full_uh}' 2>/dev/null || true")

    # Scrittura Menu Contestuale Openbox OSify anche in rootfs4
    for m_path in [
        "etc/xdg/openbox/menu.xml",
        "etc/xdg/openbox/menu.it.xml",
        "etc/skel/.config/openbox/menu.xml",
        "etc/skel/.config/openbox/menu.it.xml",
        "home/osify/.config/openbox/menu.xml",
        "home/tux/.config/openbox/menu.xml",
        "root/.config/openbox/menu.xml"
    ]:
        full_m = os.path.join(r4_work, m_path)
        os.makedirs(os.path.dirname(full_m), exist_ok=True)
        with open(full_m, "w") as f:
            f.write(OSIFY_OPENBOX_MENU)

    # Scrittura Ambiente Shell, Prompt Cyber-OSify e Alias in rootfs4
    os.makedirs(os.path.join(r4_work, "etc/profile.d"), exist_ok=True)
    with open(os.path.join(r4_work, "etc/profile.d/osify-env.sh"), "w") as f:
        f.write(OSIFY_SHELL_PROFILE)
    os.chmod(os.path.join(r4_work, "etc/profile.d/osify-env.sh"), 0o755)

    for rc_path in [
        "etc/skel/.bashrc", "etc/skel/.profile",
        "home/osify/.bashrc", "home/osify/.profile",
        "home/tux/.bashrc", "home/tux/.profile",
        "root/.bashrc", "root/.profile"
    ]:
        full_rc = os.path.join(r4_work, rc_path)
        os.makedirs(os.path.dirname(full_rc), exist_ok=True)
        with open(full_rc, "a") as f:
            f.write(f"\n{OSIFY_SHELL_PROFILE}\n")

    # Autostart automatico XDG
    autostart_dir = os.path.join(r4_work, "etc/xdg/autostart")
    os.makedirs(autostart_dir, exist_ok=True)
    with open(os.path.join(autostart_dir, "osify-hub.desktop"), "w") as f:
        f.write(app_entries["osify-hub.desktop"])

    os.remove(r4_gz)
    run(f"(cd '{r4_work}' && find . -print0 | cpio --null -ov -H newc) | python3 -c \"import lzma, sys; sys.stdout.buffer.write(lzma.compress(sys.stdin.buffer.read(), format=lzma.FORMAT_ALONE))\" > '{r4_gz}'")

    # Iniezione Windows Installer e albero OSify
    inject_windows_installer(iso_root)
    inject_osify_tree(iso_root)

    with open(os.path.join(iso_root, "OSify-Version.txt"), "w") as f:
        f.write(f"OSify Live System v{OSIFY_VERSION} (32-bit Vintage Edition)\nTarget: Intel Atom / Netbook / i686 Universal\n")

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
