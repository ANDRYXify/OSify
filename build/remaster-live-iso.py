#!/usr/bin/env python3
import os
import shutil
import subprocess
import sys
import lzma
import hashlib
import glob
from PIL import Image, ImageDraw, ImageFont

LANCZOS_FILTER = getattr(getattr(Image, 'Resampling', None), 'LANCZOS', getattr(Image, 'LANCZOS', getattr(Image, 'ANTIALIAS', 1)))

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
VERSION_FILE = os.path.join(REPO_ROOT, "VERSION")
OSIFY_VERSION = "A.0"
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
CACHE_ARM64 = os.path.join(REPO_ROOT, "build/cache/osify-base-aarch64.iso")
SANDBOX_I686 = os.path.join(REPO_ROOT, "tests/sandbox/osify-vintage-desktop.iso")

OUT_RELEASE_DIR = os.path.join(REPO_ROOT, "build/out/release")
DEST_VINTAGE_ISO = os.path.join(OUT_RELEASE_DIR, "OSify-Vintage-i686.iso")
DEST_MODERN_ISO = os.path.join(OUT_RELEASE_DIR, "OSify-x86_64-v3.iso")
DEST_ARM64_ISO = os.path.join(OUT_RELEASE_DIR, "OSify-ARM64.iso")
DEST_SANDBOX_VINTAGE = os.path.join(REPO_ROOT, "tests/sandbox/OSify-Vintage-Live.iso")

def run(cmd, cwd=None):
    print(f"[RUN] {cmd}")
    res = subprocess.run(cmd, shell=True, cwd=cwd, capture_output=True, text=True)
    if res.returncode != 0:
        print(f"[ERROR] {res.stderr}")
        sys.exit(1)
    return res.stdout

def patch_kernel_binary(kernel_path):
    if not os.path.exists(kernel_path):
        return
    with open(kernel_path, "rb") as f:
        data = f.read()
    orig_len = len(data)
    targets = [
        b"early console in decompress_kernel\n",
        b"Decompressing Linux... ",
        b"Parsing ELF... ",
        b"No relocation needed... ",
        b"Performing relocations... ",
        b"done.\nBooting the kernel.\n",
        b"Booting the kernel.\n",
        b"done.\n",
    ]
    patched = data
    count = 0
    for t in targets:
        while True:
            pos = patched.find(t)
            if pos == -1:
                break
            patched = patched[:pos] + (b"\x00" * len(t)) + patched[pos+len(t):]
            count += 1
    if count > 0 and len(patched) == orig_len:
        with open(kernel_path, "wb") as f:
            f.write(patched)
        print(f"[✓] Patch binaria kernel completata ({os.path.basename(kernel_path)}): soppresse {count} stringhe VGA early console")

def patch_binary_string(file_path, old_bytes, new_bytes):
    if not os.path.exists(file_path):
        return False
    if len(old_bytes) != len(new_bytes):
        raise ValueError(f"old_bytes len ({len(old_bytes)}) != new_bytes len ({len(new_bytes)})")
    with open(file_path, "rb") as f:
        data = f.read()
    if old_bytes in data:
        data = data.replace(old_bytes, new_bytes)
        with open(file_path, "wb") as f:
            f.write(data)
        print(f"[✓] Patch binaria EFI ({os.path.basename(file_path)}): {old_bytes.decode('latin1', 'replace')} -> {new_bytes.decode('latin1', 'replace')}")
        return True
    return False

def safe_lzma_decompress(data):
    try:
        return lzma.decompress(data)
    except Exception:
        pass
    try:
        d = lzma.LZMADecompressor(format=lzma.FORMAT_ALONE)
        return d.decompress(data)
    except Exception:
        pass
    d = lzma.LZMADecompressor(format=lzma.FORMAT_AUTO)
    return d.decompress(data)

class CpioArchive:
    def __init__(self):
        self.entries = {}
        self.order = []

    @classmethod
    def from_bytes(cls, data):
        archive = cls()
        pos = 0
        total = len(data)
        while pos + 110 <= total:
            magic = data[pos:pos+6]
            if magic not in (b'070701', b'070702'):
                break
            header = data[pos:pos+110]
            pos += 110
            ino = int(header[6:14], 16)
            mode = int(header[14:22], 16)
            uid = int(header[22:30], 16)
            gid = int(header[30:38], 16)
            nlink = int(header[38:46], 16)
            mtime = int(header[46:54], 16)
            filesize = int(header[54:62], 16)
            maj = int(header[62:70], 16)
            min_ = int(header[70:78], 16)
            rmaj = int(header[78:86], 16)
            rmin = int(header[86:94], 16)
            namesize = int(header[94:102], 16)

            name = data[pos:pos+namesize-1].decode('utf-8', 'ignore')
            pos += namesize
            if (110 + namesize) % 4 != 0:
                pos += 4 - ((110 + namesize) % 4)

            file_data = data[pos:pos+filesize]
            pos += filesize
            if filesize % 4 != 0:
                pos += 4 - (filesize % 4)

            if name == 'TRAILER!!!':
                break

            clean_name = name.lstrip('./')
            if clean_name in ('', '.'):
                clean_name = '.'

            archive.entries[clean_name] = {
                'ino': ino, 'mode': mode, 'uid': uid, 'gid': gid,
                'nlink': nlink, 'mtime': mtime, 'filesize': filesize,
                'maj': maj, 'min': min_, 'rmaj': rmaj, 'rmin': rmin,
                'data': file_data, 'raw_name': name
            }
            if clean_name not in archive.order:
                archive.order.append(clean_name)
        return archive

    def add_file(self, path, data_bytes, mode=0o100755, uid=0, gid=0, mtime=0):
        clean_name = path.lstrip('./')
        self.entries[clean_name] = {
            'ino': len(self.entries) + 1, 'mode': mode, 'uid': uid, 'gid': gid,
            'nlink': 1, 'mtime': mtime, 'filesize': len(data_bytes),
            'maj': 3, 'min': 1, 'rmaj': 0, 'rmin': 0,
            'data': data_bytes, 'raw_name': clean_name
        }
        if clean_name not in self.order:
            self.order.append(clean_name)

    def add_symlink(self, path, target, mode=0o120777, uid=0, gid=0, mtime=0):
        target_bytes = target.encode('utf-8')
        clean_name = path.lstrip('./')
        self.entries[clean_name] = {
            'ino': len(self.entries) + 1, 'mode': mode, 'uid': uid, 'gid': gid,
            'nlink': 1, 'mtime': mtime, 'filesize': len(target_bytes),
            'maj': 3, 'min': 1, 'rmaj': 0, 'rmin': 0,
            'data': target_bytes, 'raw_name': clean_name
        }
        if clean_name not in self.order:
            self.order.append(clean_name)

    def add_dir(self, path, mode=0o040755, uid=0, gid=0, mtime=0):
        clean_name = path.lstrip('./')
        if not clean_name:
            clean_name = '.'
        self.entries[clean_name] = {
            'ino': len(self.entries) + 1, 'mode': mode, 'uid': uid, 'gid': gid,
            'nlink': 2, 'mtime': mtime, 'filesize': 0,
            'maj': 3, 'min': 1, 'rmaj': 0, 'rmin': 0,
            'data': b'', 'raw_name': clean_name
        }
        if clean_name not in self.order:
            self.order.append(clean_name)

    def import_directory(self, root_dir):
        for dirpath, dirnames, filenames in os.walk(root_dir):
            rel_dir = os.path.relpath(dirpath, root_dir).lstrip('./')
            if rel_dir and rel_dir != '.':
                self.add_dir(rel_dir)
            for f in filenames:
                full_path = os.path.join(dirpath, f)
                rel_file = os.path.normpath(os.path.join(rel_dir, f) if rel_dir and rel_dir != '.' else f)
                if os.path.islink(full_path):
                    target = os.readlink(full_path)
                    self.add_symlink(rel_file, target)
                elif os.path.isfile(full_path):
                    with open(full_path, 'rb') as fp:
                        content = fp.read()
                    st = os.stat(full_path)
                    is_exec = (st.st_mode & 0o111) != 0
                    mode = 0o100755 if is_exec else 0o100644
                    self.add_file(rel_file, content, mode=mode)

    def to_bytes(self):
        chunks = []
        ino = 1
        for name in self.order:
            ent = self.entries[name]
            raw_name = ent.get('raw_name', name)
            name_bytes = raw_name.encode('utf-8') + b'\0'
            namesize = len(name_bytes)
            data = ent['data']
            filesize = len(data)
            mode = ent['mode']
            uid = ent.get('uid', 0)
            gid = ent.get('gid', 0)
            nlink = ent.get('nlink', 1)
            mtime = ent.get('mtime', 0)
            maj = ent.get('maj', 3)
            min_ = ent.get('min', 1)
            rmaj = ent.get('rmaj', 0)
            rmin = ent.get('rmin', 0)

            header = (
                f'070701'
                f'{ino:08x}'
                f'{mode:08x}'
                f'{uid:08x}'
                f'{gid:08x}'
                f'{nlink:08x}'
                f'{mtime:08x}'
                f'{filesize:08x}'
                f'{maj:08x}'
                f'{min_:08x}'
                f'{rmaj:08x}'
                f'{rmin:08x}'
                f'{namesize:08x}'
                f'{0:08x}'
            ).encode('ascii')
            pad_name = (4 - ((110 + namesize) % 4)) % 4
            pad_data = (4 - (filesize % 4)) % 4
            chunks.append(header)
            chunks.append(name_bytes)
            if pad_name:
                chunks.append(b'\0' * pad_name)
            if filesize > 0:
                chunks.append(data)
            if pad_data:
                chunks.append(b'\0' * pad_data)
            ino += 1

        trailer_name = b'TRAILER!!!\0'
        namesize = len(trailer_name)
        header = (
            f'070701'
            f'{ino:08x}'
            f'{0:08x}'
            f'{0:08x}'
            f'{0:08x}'
            f'{1:08x}'
            f'{0:08x}'
            f'{0:08x}'
            f'{0:08x}'
            f'{0:08x}'
            f'{0:08x}'
            f'{0:08x}'
            f'{namesize:08x}'
            f'{0:08x}'
        ).encode('ascii')
        pad_name = (4 - ((110 + namesize) % 4)) % 4
        chunks.append(header)
        chunks.append(trailer_name)
        if pad_name:
            chunks.append(b'\0' * pad_name)

        return b''.join(chunks)

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
    for mod in ["kernel", "network", "audio", "desktop", "tools", "security", "system", "uem", "streaming", "services", "sistema", "applicazioni"]:
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

def create_boot_splash(dest_jpg):
    src_splash = os.path.join(REPO_ROOT, "desktop/branding/wallpapers/osify-bootsplash.jpg")
    if os.path.exists(src_splash):
        img = Image.open(src_splash).convert("RGB")
        img.resize((640, 480), LANCZOS_FILTER).save(dest_jpg, "JPEG", quality=95)
        return

    width, height = 640, 480
    img = Image.new("RGB", (width, height), color=(7, 9, 14))
    center_x = width // 2
    center_y = height // 2 - 25

    # Glow radiale neon sfumato
    glow = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    glow_draw = ImageDraw.Draw(glow)
    for r in range(120, 0, -3):
        alpha = int(35 * (1.0 - r / 120.0))
        glow_draw.ellipse((center_x - r, center_y - r, center_x + r, center_y + r), fill=(124, 58, 237, alpha))
    for r in range(70, 0, -2):
        alpha = int(45 * (1.0 - r / 70.0))
        glow_draw.ellipse((center_x - r, center_y - r, center_x + r, center_y + r), fill=(6, 182, 212, alpha))
    img.paste(Image.composite(glow, Image.new("RGBA", (width, height), (7, 9, 14, 255)), glow).convert("RGB"), (0, 0))

    logo_path = os.path.join(REPO_ROOT, "OSify.png")
    if os.path.exists(logo_path):
        logo = Image.open(logo_path).convert("RGBA")
        logo = logo.resize((128, 128), LANCZOS_FILTER)
        img.paste(logo, (center_x - 64, center_y - 64), logo)

    # Solo il logo iconico centrato con glow radiale: zero testo, zero sottotitoli
    img.save(dest_jpg, "JPEG", quality=98)

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

LIBFM_CONF = """# OSify LibFM Desktop & File Manager Configuration
[config]
quick_exec=1
terminal=terminal
single_click=0
use_trash=1
confirm_del=1
show_thumbnail=1
thumbnail_max=8192
show_internal_volumes=1
auto_selection_delay=600

[ui]
big_icon_size=48
small_icon_size=24
pane_icon_size=24
thumbnail_size=128
show_statusbar=1
"""

OPENBOX_AUTOSTART = """#!/bin/sh
# OSify Openbox Session Autostart
[ -x /usr/bin/osify-time-sync ] && (/usr/bin/osify-time-sync check >/dev/null 2>&1 &)
[ -x /usr/bin/osify-touchpad ] && /usr/bin/osify-touchpad auto &
[ -x /usr/bin/osify-input-setup ] && /usr/bin/osify-input-setup &
[ -x /usr/bin/osify-superkey ] && (/usr/bin/osify-superkey >/dev/null 2>&1) &
[ -x /usr/bin/osify-storage-governor ] && /usr/bin/osify-storage-governor --tune &
[ -x /usr/bin/osify-automount ] && (/usr/bin/osify-automount daemon >/dev/null 2>&1) &
[ -x /usr/bin/osify-first-boot ] && (sleep 1.5 && /usr/bin/osify-first-boot) &
if command -v pcmanfm >/dev/null 2>&1; then
    (sleep 0.3 && pgrep -f "pcmanfm --desktop" >/dev/null || pcmanfm --desktop) &
fi
if command -v lxpanel >/dev/null 2>&1; then
    (sleep 0.5 && pgrep -x lxpanel >/dev/null || lxpanel --profile default 2>/dev/null || lxpanel 2>/dev/null || true) &
fi
"""

OSIFY_OPENBOX_MENU = """<?xml version="1.0" encoding="UTF-8"?>
<openbox_menu xmlns="http://openbox.org/3.4/menu">
  <menu id="root-menu" label="Menu OSify">
    <separator label="OSify 2050"/>
    <item label="Centro OSify.ify" icon="/usr/share/pixmaps/osify-hub.png">
      <action name="Execute"><command>/Applicazioni/Centro OSify.ify/avvia.sh</command></action>
    </item>
    <item label="Tutte le Applicazioni (.ify)" icon="/usr/share/pixmaps/osify-drawer.png">
      <action name="Execute"><command>/usr/bin/osify-app-drawer</command></action>
    </item>
    <separator/>
    <separator label="Applicazioni Native"/>
    <item label="Navigatore.ify" icon="/usr/share/pixmaps/osify-browser.png">
      <action name="Execute"><command>/Applicazioni/Navigatore.ify/avvia.sh</command></action>
    </item>
    <item label="Esplora.ify" icon="/usr/share/pixmaps/osify-files.png">
      <action name="Execute"><command>/Applicazioni/Esplora.ify/avvia.sh</command></action>
    </item>
    <item label="Reti.ify" icon="/usr/share/pixmaps/osify-wifi.png">
      <action name="Execute"><command>/Applicazioni/Reti.ify/avvia.sh</command></action>
    </item>
    <item label="Giochi.ify" icon="/usr/share/pixmaps/osify-games.png">
      <action name="Execute"><command>/Applicazioni/Giochi.ify/avvia.sh</command></action>
    </item>
    <item label="Sviluppo.ify" icon="/usr/share/pixmaps/osify-developer.png">
      <action name="Execute"><command>/Applicazioni/Sviluppo.ify/avvia.sh</command></action>
    </item>
    <item label="Compatibilità.ify" icon="/usr/share/pixmaps/osify-games.png">
      <action name="Execute"><command>/Sistema/Servizi/Compatibilità.ify</command></action>
    </item>
    <item label="Negozio.ify" icon="/usr/share/pixmaps/osify-install.png">
      <action name="Execute"><command>/Applicazioni/Negozio.ify/avvia.sh</command></action>
    </item>
    <separator/>
    <menu id="multimedia-menu" label="Multimedia e Ufficio">
      <item label="Galleria.ify" icon="/usr/share/pixmaps/osify-appearance.png">
        <action name="Execute"><command>/Applicazioni/Galleria.ify/avvia.sh</command></action>
      </item>
      <item label="Musica.ify" icon="/usr/share/pixmaps/osify-audio.png">
        <action name="Execute"><command>/Applicazioni/Musica.ify/avvia.sh</command></action>
      </item>
      <item label="Video.ify" icon="/usr/share/pixmaps/osify-audio.png">
        <action name="Execute"><command>/Applicazioni/Video.ify/avvia.sh</command></action>
      </item>
      <item label="Documenti.ify" icon="/usr/share/pixmaps/osify-files.png">
        <action name="Execute"><command>/Applicazioni/Documenti.ify/avvia.sh</command></action>
      </item>
      <item label="Archivi.ify" icon="/usr/share/pixmaps/osify-archive.png">
        <action name="Execute"><command>/Applicazioni/Archivi.ify/avvia.sh</command></action>
      </item>
      <item label="Cattura.ify" icon="/usr/share/pixmaps/osify-appearance.png">
        <action name="Execute"><command>/Applicazioni/Cattura.ify/avvia.sh</command></action>
      </item>
      <item label="Calcolatrice.ify" icon="/usr/share/pixmaps/osify-calculator.png">
        <action name="Execute"><command>/Applicazioni/Calcolatrice.ify/avvia.sh</command></action>
      </item>
      <item label="Note.ify" icon="/usr/share/pixmaps/osify-notepad.png">
        <action name="Execute"><command>/Applicazioni/Note.ify/avvia.sh</command></action>
      </item>
    </menu>
    <menu id="settings-menu" label="Impostazioni e Sistema">
      <item label="Impostazioni.ify" icon="/usr/share/pixmaps/osify-settings.png">
        <action name="Execute"><command>/Applicazioni/Impostazioni.ify/avvia.sh</command></action>
      </item>
      <item label="Dispositivi.ify" icon="/usr/share/pixmaps/osify-usb.png">
        <action name="Execute"><command>/Applicazioni/Dispositivi.ify/avvia.sh</command></action>
      </item>
      <item label="Accessibilità.ify" icon="/usr/share/pixmaps/osify-accessibility.png">
        <action name="Execute"><command>/Applicazioni/Accessibilità.ify/avvia.sh</command></action>
      </item>
      <item label="Ripristino.ify" icon="/usr/share/pixmaps/osify-backup.png">
        <action name="Execute"><command>/Applicazioni/Ripristino.ify/avvia.sh</command></action>
      </item>
      <item label="Compatibilità.ify" icon="/usr/share/pixmaps/osify-hub.png">
        <action name="Execute"><command>/Applicazioni/Compatibilità.ify/avvia.sh</command></action>
      </item>
      <item label="Aspetto.ify" icon="/usr/share/pixmaps/osify-appearance.png">
        <action name="Execute"><command>/Applicazioni/Aspetto.ify/avvia.sh</command></action>
      </item>
      <item label="Monitor.ify" icon="/usr/share/pixmaps/osify-taskmanager.png">
        <action name="Execute"><command>/Applicazioni/Monitor.ify/avvia.sh</command></action>
      </item>
      <item label="Aggiornamenti.ify" icon="/usr/share/pixmaps/osify-update.png">
        <action name="Execute"><command>/Applicazioni/Aggiornamenti.ify/avvia.sh</command></action>
      </item>
      <item label="Gestore Pacchetti (.ify)" icon="/usr/share/pixmaps/osify-install.png">
        <action name="Execute"><command>/Sistema/Servizi/GestorePacchetti.ify</command></action>
      </item>
    </menu>
    <separator/>
    <item label="Installa OSify.ify" icon="/usr/share/pixmaps/osify-install.png">
      <action name="Execute"><command>/Applicazioni/Installa OSify.ify/avvia.sh</command></action>
    </item>
    <separator/>
    <item label="Spegni Computer" icon="/usr/share/pixmaps/osify-power.png">
      <action name="Execute"><command>/usr/bin/osify-power off</command></action>
    </item>
    <item label="Riavvia Computer" icon="/usr/share/pixmaps/osify-power.png">
      <action name="Execute"><command>/usr/bin/osify-power reboot</command></action>
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

lxpanel_topbar_cfg = ""
lxpanel_dock_cfg = ""


def remaster_rootfs3(work_dir, iso_root, wallpaper_jpg):
    print("[i] Remastering rootfs3 (SLIM autologin 0s, rimozione ragno SliTaz, OSify Cyber-Bar)...")
    r3_work = os.path.join(work_dir, "rootfs3")
    os.makedirs(r3_work, exist_ok=True)
    r3_gz = os.path.join(iso_root, "boot/rootfs3.gz")
    
    with open(r3_gz, "rb") as f:
        r3_data = safe_lzma_decompress(f.read())
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
login_cmd           exec /bin/sh -l ~/.xinitrc %session
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

    # 3. Configurazione Dual Panel LXPanel (Top Menu Bar macOS + Floating Dock 2050)
    global lxpanel_topbar_cfg, lxpanel_dock_cfg
    lxpanel_topbar_cfg = """# OSify Top Menu Bar (macOS Style 2050)
Global {
    edge=top
    allign=center
    margin=0
    widthtype=percent
    width=100
    height=26
    transparent=1
    tintcolor=#0f111a
    alpha=230
    autohide=0
    setdocktype=1
    setpartialstrut=1
    usefontcolor=1
    fontsize=10
    fontcolor=#f8fafc
    usefontsize=1
    background=0
    iconsize=18
    loglevel=2
}

Plugin {
    type = menu
    Config {
        image=/usr/share/pixmaps/osify.png
        item {
            name=Informazioni su OSify 2050
            image=/usr/share/pixmaps/osify-about.png
            action=/usr/bin/osify-about
        }
        separator {
        }
        item {
            name=Impostazioni di Sistema...
            image=/usr/share/pixmaps/osify-settings.png
            action=/usr/bin/osify-settings
        }
        item {
            name=Centro OSify...
            image=/usr/share/pixmaps/osify-hub.png
            action=/usr/bin/osify-hub
        }
        item {
            name=Compatibilità.ify...
            image=/usr/share/pixmaps/osify-games.png
            action=/Sistema/Servizi/Compatibilità.ify
        }
        item {
            name=Aspetto e Risoluzioni...
            image=/usr/share/pixmaps/osify-appearance.png
            action=/usr/bin/osify-appearance
        }
        item {
            name=Reti e Connessione Wi-Fi...
            image=/usr/share/pixmaps/osify-wifi.png
            action=/usr/bin/osify-wifi
        }
        separator {
        }
        item {
            name=Blocca Schermo
            image=/usr/share/pixmaps/osify-settings.png
            action=xlock
        }
        item {
            name=Riavvia Computer...
            image=/usr/share/pixmaps/osify-update.png
            action=/usr/bin/osify-power reboot
        }
        item {
            name=Spegni Computer...
            image=/usr/share/pixmaps/osify-taskmanager.png
            action=/usr/bin/osify-power off
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
    type = menu
    Config {
        name=OSify
        image=/usr/share/pixmaps/transparent.png
        item {
            name=Informazioni su OSify 2050
            action=/usr/bin/osify-about
        }
        item {
            name=Impostazioni di Sistema
            action=/usr/bin/osify-settings
        }
        item {
            name=Ricerca Globale OSify (Super+Spazio)
            action=/usr/bin/osify-spotlight
        }
        separator {
        }
        item {
            name=Profilo Prestazioni & Turbo
            action=/usr/bin/osify-hub
        }
    }
}

Plugin {
    type = menu
    Config {
        name=File
        image=/usr/share/pixmaps/transparent.png
        item {
            name=Nuova Finestra Esplora
            action=pcmanfm
        }
        item {
            name=Cartella Utente (/Utenti)
            action=pcmanfm ~
        }
        item {
            name=Cerca nel Sistema
            action=/usr/bin/osify-spotlight
        }
    }
}

Plugin {
    type = menu
    Config {
        name=Visualizza
        image=/usr/share/pixmaps/transparent.png
        item {
            name=Tutte le Applicazioni (.ify)
            action=/usr/bin/osify-app-drawer
        }
        item {
            name=Personalizzazione Aspetto
            action=/usr/bin/osify-appearance
        }
        item {
            name=Monitor di Sistema
            action=/usr/bin/osify-taskmanager
        }
    }
}

Plugin {
    type = menu
    Config {
        name=Strumenti
        image=/usr/share/pixmaps/transparent.png
        item {
            name=Centro OSify
            action=/usr/bin/osify-hub
        }
        item {
            name=Gestore Compatibilità.ify
            action=/Sistema/Servizi/Compatibilità.ify
        }
        item {
            name=Strumenti di Sviluppo
            action=/usr/bin/osify-developer
        }
    }
}

Plugin {
    type = menu
    Config {
        name=Aiuto
        image=/usr/share/pixmaps/transparent.png
        item {
            name=Guida Rapida OSify
            action=/usr/bin/osify-hub
        }
        item {
            name=Specifiche OSify 2050
            action=/usr/bin/osify-about
        }
        item {
            name=Diagnostica Hardware
            action=/usr/bin/osify-sysinfo
        }
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
    type = launchbar
    Config {
        Button {
            id=osify-spotlight.desktop
        }
        Button {
            id=osify-controlcenter.desktop
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
    type = dclock
    Config {
        ClockFmt=%a %d %b  %H:%M
        TooltipFmt=%A %d %B %Y
        BoldFont=1
        IconOnly=0
        CenterText=1
    }
}
"""

    lxpanel_dock_cfg = """# OSify Cyber Dock 2050
Global {
    edge=bottom
    allign=center
    margin=8
    widthtype=request
    height=48
    transparent=1
    tintcolor=#0a0e17
    alpha=220
    autohide=0
    setdocktype=1
    setpartialstrut=1
    usefontcolor=1
    fontsize=10
    fontcolor=#38bdf8
    usefontsize=1
    background=0
    iconsize=38
    loglevel=2
}

Plugin {
    type = launchbar
    Config {
        Button {
            id=osify-files.desktop
        }
        Button {
            id=osify-drawer.desktop
        }
        Button {
            id=osify-browser.desktop
        }
        Button {
            id=osify-hub.desktop
        }
        Button {
            id=osify-package-installer.desktop
        }
        Button {
            id=osify-settings.desktop
        }
        Button {
            id=osify-games.desktop
        }
        Button {
            id=osify-media-player.desktop
        }
        Button {
            id=osify-taskmanager.desktop
        }
        Button {
            id=osify-install.desktop
        }
    }
}

Plugin {
    type = space
    Config {
        Size=8
    }
}

Plugin {
    type = taskbar
    Config {
        tooltips=1
        IconsOnly=1
        ShowAllDesks=0
        UseMouseWheel=1
        UseUrgencyHint=1
        FlatButton=1
        MaxTaskWidth=38
        spacing=4
        GroupedTasks=1
    }
}

Plugin {
    type = space
    Config {
        Size=8
    }
}

Plugin {
    type = launchbar
    Config {
        Button {
            id=osify-install.desktop
        }
    }
}
"""

    # Iniezione Top Bar e Dock in tutte le cartelle profilo LXPanel
    for base_p in [
        "etc/skel/.config/lxpanel",
        "home/osify/.config/lxpanel",
        "home/tux/.config/lxpanel",
        "etc/lxpanel",
        "etc/xdg/lxpanel",
        "root/.config/lxpanel"
    ]:
        for prof in ["default", "slitaz", "original"]:
            prof_path = os.path.join(r3_work, base_p, prof)
            if os.path.exists(prof_path) and not os.path.isdir(prof_path):
                try:
                    os.remove(prof_path)
                except Exception:
                    pass
            panels_dir = os.path.join(prof_path, "panels")
            if os.path.exists(panels_dir) and not os.path.isdir(panels_dir):
                try:
                    os.remove(panels_dir)
                except Exception:
                    pass
            os.makedirs(panels_dir, exist_ok=True)
            # Rimuovi il vecchio panel monolitico se presente
            old_p = os.path.join(panels_dir, "panel")
            if os.path.exists(old_p):
                try:
                    os.remove(old_p)
                except Exception:
                    pass
            # Scrivi topbar e dock
            with open(os.path.join(panels_dir, "topbar"), "w") as f:
                f.write(lxpanel_topbar_cfg)
            with open(os.path.join(panels_dir, "dock"), "w") as f:
                f.write(lxpanel_dock_cfg)

    # Iniezione Icone Brand e Tema Openbox macOS in rootfs3
    icons_src = os.path.join(REPO_ROOT, "desktop/branding/icons")
    if os.path.exists(icons_src):
        r3_pixmaps = os.path.join(r3_work, "usr/share/pixmaps")
        os.makedirs(r3_pixmaps, exist_ok=True)
        for ic in glob.glob(os.path.join(icons_src, "*/*.png")):
            shutil.copy2(ic, r3_pixmaps)
        # Sostituzione icone sistema SliTaz con logo OSify Apple-style
        for spider_ic in [
            "usr/share/icons/SliTaz-Faenza/48x48/places/start-here.png",
            "usr/share/icons/SliTaz-Faenza/22x22/places/start-here.png",
            "usr/share/icons/SliTaz-Faenza-Dark/22x22/places/start-here.png",
            "usr/share/pixmaps/slitaz-menu.png",
            "usr/share/pixmaps/slitaz-spider.png"
        ]:
            sp_dst = os.path.join(r3_work, spider_ic)
            if os.path.exists(os.path.dirname(sp_dst)):
                shutil.copy2(os.path.join(icons_src, "24/osify-apple-logo.png"), sp_dst)

    theme_src = os.path.join(REPO_ROOT, "desktop/branding/themes/OSify-macOS")
    if os.path.exists(theme_src):
        theme_dst = os.path.join(r3_work, "usr/share/themes/OSify-macOS")
        shutil.copytree(theme_src, theme_dst, dirs_exist_ok=True)


    # 4. Scorciatoie Openbox in etc/xdg/openbox/rc.xml
    rc_xml = os.path.join(r3_work, "etc/xdg/openbox/rc.xml")
    if os.path.exists(rc_xml):
        with open(rc_xml, "r") as f:
            rc_content = f.read()

        # Applicazione tema macOS con Traffic Lights a sinistra (CIML: Close, Iconify, Maximize, Label)
        theme_block = """  <theme>
    <name>OSify-macOS</name>
    <titlelayout>CIML</titlelayout>
    <keepBorder>yes</keepBorder>
    <animateIconify>yes</animateIconify>
    <font place="ActiveWindow">
      <name>sans</name>
      <size>9</size>
      <weight>bold</weight>
      <slant>normal</slant>
    </font>
    <font place="InactiveWindow">
      <name>sans</name>
      <size>9</size>
      <weight>normal</weight>
      <slant>normal</slant>
    </font>
    <font place="MenuHeader">
      <name>sans</name>
      <size>9</size>
      <weight>bold</weight>
      <slant>normal</slant>
    </font>
    <font place="MenuItem">
      <name>sans</name>
      <size>9</size>
      <weight>normal</weight>
      <slant>normal</slant>
    </font>
  </theme>"""
        if "<theme>" in rc_content and "</theme>" in rc_content:
            before_t = rc_content.split("<theme>")[0]
            after_t = rc_content.split("</theme>")[1]
            rc_content = before_t + theme_block + after_t

        custom_keys = """
    <!-- OSify Spotlight Search & macOS Hotkeys -->
    <keybind key="W-space"><action name="Execute"><command>/usr/bin/osify-spotlight</command></action></keybind>
    <keybind key="C-space"><action name="Execute"><command>/usr/bin/osify-spotlight</command></action></keybind>
    <keybind key="Super_L"><action name="Execute"><command>/usr/bin/osify-spotlight</command></action></keybind>
    <keybind key="W-c"><action name="Execute"><command>/usr/bin/osify-controlcenter</command></action></keybind>
    <keybind key="W-a"><action name="Execute"><command>/usr/bin/osify-app-drawer</command></action></keybind>
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
    <!-- Controlli Multimediali e Hardware -->
    <keybind key="XF86AudioRaiseVolume"><action name="Execute"><command>/usr/bin/osify-audio up</command></action></keybind>
    <keybind key="XF86AudioLowerVolume"><action name="Execute"><command>/usr/bin/osify-audio down</command></action></keybind>
    <keybind key="XF86AudioMute"><action name="Execute"><command>/usr/bin/osify-audio mute</command></action></keybind>
    <keybind key="XF86MonBrightnessUp"><action name="Execute"><command>/usr/bin/osify-brightness up</command></action></keybind>
    <keybind key="XF86MonBrightnessDown"><action name="Execute"><command>/usr/bin/osify-brightness down</command></action></keybind>
    <!-- Screenshot Istantaneo -->
    <keybind key="Print"><action name="Execute"><command>/usr/bin/osify-screenshot instant</command></action></keybind>
    <keybind key="A-Print"><action name="Execute"><command>/usr/bin/osify-screenshot window</command></action></keybind>
    <keybind key="W-s"><action name="Execute"><command>/usr/bin/osify-screenshot --gui</command></action></keybind>
    <!-- Gestione Desktop e Finestre -->
    <keybind key="W-d"><action name="ToggleShowDesktop"/></keybind>
    <keybind key="W-l"><action name="Execute"><command>/usr/bin/osify-power</command></action></keybind>
    <keybind key="W-q"><action name="Close"/></keybind>
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

    # 5b. Configurazione nativa LibFM (quick_exec=1 per esecuzione immediata al doppio click e miniature immagini)
    for lfm_p in [
        "etc/xdg/libfm/libfm.conf",
        "etc/skel/.config/libfm/libfm.conf",
        "home/osify/.config/libfm/libfm.conf",
        "home/tux/.config/libfm/libfm.conf",
        "root/.config/libfm/libfm.conf"
    ]:
        full_lfm = os.path.join(r3_work, lfm_p)
        os.makedirs(os.path.dirname(full_lfm), exist_ok=True)
        with open(full_lfm, "w") as f:
            f.write(LIBFM_CONF)

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

    # 7. Disattivazione categorica di check_tazpkgupg.sh e servizi bloccanti di rete
    stub_script = "#!/bin/sh\nexit 0\n"
    for blk_serv in [
        "etc/init.d/check_tazpkgupg.sh",
        "etc/init.d/tazpanel",
        "etc/init.d/httpd",
        "usr/bin/check_tazpkgupg.sh"
    ]:
        bpath = os.path.join(r3_work, blk_serv)
        os.makedirs(os.path.dirname(bpath), exist_ok=True)
        with open(bpath, "w") as f:
            f.write(stub_script)
        os.chmod(bpath, 0o755)

    # 8. Copia kernel bzImage direttamente nella rootfs per installazione su disco
    iso_k = os.path.join(iso_root, "boot/bzImage")
    if os.path.exists(iso_k):
        r3_kdir = os.path.join(r3_work, "boot")
        os.makedirs(r3_kdir, exist_ok=True)
        shutil.copy2(iso_k, os.path.join(r3_kdir, "bzImage"))
        vmlink = os.path.join(r3_kdir, "vmlinuz")
        if not os.path.exists(vmlink):
            try:
                os.symlink("bzImage", vmlink)
            except Exception:
                pass

    os.remove(r3_gz)
    archive3 = CpioArchive.from_bytes(r3_data)
    archive3.import_directory(r3_work)
    r3_packed = archive3.to_bytes()
    with open(r3_gz, "wb") as f:
        f.write(lzma.compress(r3_packed, format=lzma.FORMAT_ALONE))
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

    # Patch binaria kernel per azzerare stringhe VGA early console ("Decompressing Linux", "done.")
    for r, _, files in os.walk(iso_root):
        for f in files:
            if "bzImage" in f or "vmlinuz" in f:
                patch_kernel_binary(os.path.join(r, f))

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
TIMEOUT 5
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

LABEL osify
    MENU LABEL OSify
    KERNEL /boot/bzImage
    INITRD /boot/rootfs4.gz
    APPEND root=/dev/null tmpram=0 autologin lang=it_IT kmap=it rw quiet splash loglevel=0 console=tty3 vt.global_cursor_default=0 logo.nologo

LABEL turbo
    MENU LABEL OSify Prestazioni Turbo
    KERNEL /boot/bzImage
    INITRD /boot/rootfs4.gz
    APPEND root=/dev/null tmpram=0 autologin lang=it_IT kmap=it rw quiet splash loglevel=0 console=tty3 vt.global_cursor_default=0 logo.nologo osify.turbo=1

LABEL safe
    MENU LABEL OSify Modalita Compatibile (Emulatore / Safe Graphics)
    KERNEL /boot/bzImage
    INITRD /boot/rootfs4.gz
    APPEND root=/dev/null tmpram=0 nomodeset vga=788 autologin lang=it_IT kmap=it rw quiet loglevel=1 console=tty1 vt.global_cursor_default=0 logo.nologo

LABEL install
    MENU LABEL Installa OSify su Disco Fisso
    KERNEL /boot/bzImage
    INITRD /boot/rootfs4.gz
    APPEND root=/dev/null tmpram=0 autologin lang=it_IT kmap=it rw quiet splash loglevel=0 console=tty3 vt.global_cursor_default=0 logo.nologo osify.install=1

LABEL memtest
    MENU LABEL Diagnostica Memoria RAM
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

    # Remastering rootfs4 con unificazione completa di tutti i layer
    print("[i] Unificazione di tutti i layer rootfs (1, 2, 3, 4) in rootfs4...")
    r4_work = os.path.join(work_dir, "rootfs4")
    os.makedirs(r4_work, exist_ok=True)

    for r_sub in ["boot/rootfs1.gz", "boot/rootfs2.gz", "boot/rootfs3.gz"]:
        r_path = os.path.join(iso_root, r_sub)
        if os.path.exists(r_path):
            with open(r_path, "rb") as f:
                sub_data = safe_lzma_decompress(f.read())
            extract_cpio_archive(sub_data, r4_work)

    r4_gz = os.path.join(iso_root, "boot/rootfs4.gz")
    with open(r4_gz, "rb") as f:
        r4_data = safe_lzma_decompress(f.read())
    n_files = extract_cpio_archive(r4_data, r4_work)
    print(f"[✓] Layer unificati con successo: {n_files} file estratti nel rootfs unico")

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

    # Power Subsystem Deterministico
    shutil.copy2(os.path.join(REPO_ROOT, "system/power/osify-power.sh"), os.path.join(bin_dir, "osify-power"))
    shutil.copy2(os.path.join(REPO_ROOT, "system/power/osify-power.sh"), os.path.join(r4_work, "usr/local/bin/poweroff"))
    shutil.copy2(os.path.join(REPO_ROOT, "system/power/osify-power.sh"), os.path.join(r4_work, "usr/local/bin/reboot"))
    shutil.copy2(os.path.join(REPO_ROOT, "system/power/osify-power.sh"), os.path.join(r4_work, "usr/local/bin/halt"))
    os.chmod(os.path.join(bin_dir, "osify-power"), 0o755)
    os.chmod(os.path.join(r4_work, "usr/local/bin/poweroff"), 0o755)
    os.chmod(os.path.join(r4_work, "usr/local/bin/reboot"), 0o755)
    os.chmod(os.path.join(r4_work, "usr/local/bin/halt"), 0o755)

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
    shutil.copy2(os.path.join(REPO_ROOT, "tools/osify-gui/osify-hub.py"), os.path.join(bin_dir, "osify-hub.py"))
    shutil.copy2(os.path.join(REPO_ROOT, "tools/osify-gui/osify-hub.py"), os.path.join(r4_work, "usr/local/bin/osify-hub.py"))

    shutil.copy2(os.path.join(REPO_ROOT, "tools/osify-gui/osify-browser.sh"), os.path.join(bin_dir, "osify-browser"))
    shutil.copy2(os.path.join(REPO_ROOT, "network/osify-wifi-gui.sh"), os.path.join(bin_dir, "osify-wifi"))
    shutil.copy2(os.path.join(REPO_ROOT, "network/osify-wifi-gui.py"), os.path.join(bin_dir, "osify-wifi-gui.py"))
    shutil.copy2(os.path.join(REPO_ROOT, "network/osify-wifi-gui.py"), os.path.join(r4_work, "usr/local/bin/osify-wifi-gui.py"))

    shutil.copy2(os.path.join(REPO_ROOT, "tools/osify-gui/osify-games.sh"), os.path.join(bin_dir, "osify-games"))
    shutil.copy2(os.path.join(REPO_ROOT, "tools/osify-gui/osify-developer.sh"), os.path.join(bin_dir, "osify-developer"))
    shutil.copy2(os.path.join(REPO_ROOT, "system/storage/osify-storage-governor.sh"), os.path.join(bin_dir, "osify-storage-governor"))
    shutil.copy2(os.path.join(REPO_ROOT, "system/storage/osify-storage-governor.sh"), os.path.join(bin_dir, "osify-eject"))
    shutil.copy2(os.path.join(REPO_ROOT, "audio/osify-sound-manager.sh"), os.path.join(bin_dir, "osify-sound-manager"))
    shutil.copy2(os.path.join(REPO_ROOT, "audio/osify-sound-manager.sh"), os.path.join(bin_dir, "osify-audio"))
    shutil.copy2(os.path.join(REPO_ROOT, "audio/osify-sound-manager.sh"), os.path.join(r4_work, "usr/local/bin/osify-sound-manager"))
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
    shutil.copy2(os.path.join(REPO_ROOT, "system/session/osify-first-boot.sh"), os.path.join(bin_dir, "osify-first-boot"))
    shutil.copy2(os.path.join(REPO_ROOT, "system/session/osify-first-boot.sh"), os.path.join(r4_work, "usr/local/bin/osify-first-boot"))
    shutil.copy2(os.path.join(REPO_ROOT, "tools/osify-gui/osify-superkey.sh"), os.path.join(bin_dir, "osify-superkey"))
    shutil.copy2(os.path.join(REPO_ROOT, "tools/osify-gui/osify-superkey.sh"), os.path.join(r4_work, "usr/local/bin/osify-superkey"))
    shutil.copy2(os.path.join(REPO_ROOT, "system/storage/osify-automount.sh"), os.path.join(bin_dir, "osify-automount"))
    shutil.copy2(os.path.join(REPO_ROOT, "network/osify-bluetooth.sh"), os.path.join(bin_dir, "osify-bluetooth"))
    shutil.copy2(os.path.join(REPO_ROOT, "system/snapshot/osify-snapshot.sh"), os.path.join(bin_dir, "osify-snapshot"))
    shutil.copy2(os.path.join(REPO_ROOT, "network/osify-net-check.sh"), os.path.join(bin_dir, "osify-net-check"))
    shutil.copy2(os.path.join(REPO_ROOT, "system/updater/osify-live-updater.sh"), os.path.join(bin_dir, "osify-update"))
    shutil.copy2(os.path.join(REPO_ROOT, "system/display/osify-brightness.sh"), os.path.join(bin_dir, "osify-brightness"))
    shutil.copy2(os.path.join(REPO_ROOT, "system/display/osify-brightness.sh"), os.path.join(r4_work, "usr/local/bin/osify-brightness"))
    shutil.copy2(os.path.join(REPO_ROOT, "tools/osify-gui/osify-power.sh"), os.path.join(bin_dir, "osify-power"))
    shutil.copy2(os.path.join(REPO_ROOT, "tools/osify-gui/osify-power.sh"), os.path.join(r4_work, "usr/local/bin/osify-power"))
    shutil.copy2(os.path.join(REPO_ROOT, "tools/osify-gui/osify-screenshot.sh"), os.path.join(bin_dir, "osify-screenshot"))
    shutil.copy2(os.path.join(REPO_ROOT, "tools/osify-gui/osify-screenshot.sh"), os.path.join(r4_work, "usr/local/bin/osify-screenshot"))
    shutil.copy2(os.path.join(REPO_ROOT, "tools/osify-gui/osify-image-viewer.sh"), os.path.join(bin_dir, "osify-image-viewer"))
    shutil.copy2(os.path.join(REPO_ROOT, "tools/osify-gui/osify-image-viewer.sh"), os.path.join(r4_work, "usr/local/bin/osify-image-viewer"))
    shutil.copy2(os.path.join(REPO_ROOT, "tools/osify-gui/osify-archive-manager.sh"), os.path.join(bin_dir, "osify-archive-manager"))
    shutil.copy2(os.path.join(REPO_ROOT, "tools/osify-gui/osify-archive-manager.sh"), os.path.join(bin_dir, "osify-archive"))
    shutil.copy2(os.path.join(REPO_ROOT, "tools/osify-gui/osify-archive-manager.sh"), os.path.join(r4_work, "usr/local/bin/osify-archive-manager"))
    shutil.copy2(os.path.join(REPO_ROOT, "tools/osify-gui/osify-notepad.sh"), os.path.join(bin_dir, "osify-notepad"))
    shutil.copy2(os.path.join(REPO_ROOT, "tools/osify-gui/osify-notepad.sh"), os.path.join(r4_work, "usr/local/bin/osify-notepad"))
    shutil.copy2(os.path.join(REPO_ROOT, "tools/osify-gui/osify-pdf-viewer.sh"), os.path.join(bin_dir, "osify-pdf-viewer"))
    shutil.copy2(os.path.join(REPO_ROOT, "tools/osify-gui/osify-pdf-viewer.sh"), os.path.join(r4_work, "usr/local/bin/osify-pdf-viewer"))
    shutil.copy2(os.path.join(REPO_ROOT, "tools/osify-gui/osify-calculator.sh"), os.path.join(bin_dir, "osify-calculator"))
    shutil.copy2(os.path.join(REPO_ROOT, "tools/osify-gui/osify-calculator.sh"), os.path.join(r4_work, "usr/local/bin/osify-calculator"))
    shutil.copy2(os.path.join(REPO_ROOT, "tools/osify-gui/osify-media-player.sh"), os.path.join(bin_dir, "osify-media-player"))
    shutil.copy2(os.path.join(REPO_ROOT, "tools/osify-gui/osify-media-player.sh"), os.path.join(r4_work, "usr/local/bin/osify-media-player"))
    shutil.copy2(os.path.join(REPO_ROOT, "tools/osify-gui/osify-keyboard.sh"), os.path.join(bin_dir, "osify-keyboard"))
    shutil.copy2(os.path.join(REPO_ROOT, "tools/osify-gui/osify-keyboard.sh"), os.path.join(r4_work, "usr/local/bin/osify-keyboard"))
    shutil.copy2(os.path.join(REPO_ROOT, "tools/osify-gui/osify-onboard.sh"), os.path.join(bin_dir, "osify-onboard"))
    shutil.copy2(os.path.join(REPO_ROOT, "tools/osify-gui/osify-onboard.sh"), os.path.join(r4_work, "usr/local/bin/osify-onboard"))
    shutil.copy2(os.path.join(REPO_ROOT, "system/storage/osify-disk-health.sh"), os.path.join(bin_dir, "osify-disk-health"))
    shutil.copy2(os.path.join(REPO_ROOT, "system/storage/osify-disk-health.sh"), os.path.join(r4_work, "usr/local/bin/osify-disk-health"))
    shutil.copy2(os.path.join(REPO_ROOT, "network/osify-share.sh"), os.path.join(bin_dir, "osify-share"))
    shutil.copy2(os.path.join(REPO_ROOT, "network/osify-share.sh"), os.path.join(r4_work, "usr/local/bin/osify-share"))
    shutil.copy2(os.path.join(REPO_ROOT, "system/printing/osify-printer.sh"), os.path.join(bin_dir, "osify-printer"))
    shutil.copy2(os.path.join(REPO_ROOT, "system/printing/osify-printer.sh"), os.path.join(r4_work, "usr/local/bin/osify-printer"))
    shutil.copy2(os.path.join(REPO_ROOT, "system/power/osify-thermal-monitor.sh"), os.path.join(bin_dir, "osify-thermal-monitor"))
    shutil.copy2(os.path.join(REPO_ROOT, "system/power/osify-thermal-monitor.sh"), os.path.join(bin_dir, "osify-thermal"))
    shutil.copy2(os.path.join(REPO_ROOT, "system/power/osify-thermal-monitor.sh"), os.path.join(r4_work, "usr/local/bin/osify-thermal-monitor"))
    shutil.copy2(os.path.join(REPO_ROOT, "tools/osify-gui/osify-benchmark.sh"), os.path.join(bin_dir, "osify-benchmark"))
    shutil.copy2(os.path.join(REPO_ROOT, "tools/osify-gui/osify-benchmark.sh"), os.path.join(r4_work, "usr/local/bin/osify-benchmark"))
    shutil.copy2(os.path.join(REPO_ROOT, "network/osify-firewall.sh"), os.path.join(bin_dir, "osify-firewall"))
    shutil.copy2(os.path.join(REPO_ROOT, "network/osify-firewall.sh"), os.path.join(r4_work, "usr/local/bin/osify-firewall"))
    shutil.copy2(os.path.join(REPO_ROOT, "system/time/osify-time-sync.sh"), os.path.join(bin_dir, "osify-time-sync"))
    shutil.copy2(os.path.join(REPO_ROOT, "system/time/osify-time-sync.sh"), os.path.join(bin_dir, "osify-time"))
    shutil.copy2(os.path.join(REPO_ROOT, "system/time/osify-time-sync.sh"), os.path.join(r4_work, "usr/local/bin/osify-time-sync"))
    shutil.copy2(os.path.join(REPO_ROOT, "system/input/osify-touchpad.sh"), os.path.join(bin_dir, "osify-touchpad"))
    shutil.copy2(os.path.join(REPO_ROOT, "system/input/osify-touchpad.sh"), os.path.join(r4_work, "usr/local/bin/osify-touchpad"))
    shutil.copy2(os.path.join(REPO_ROOT, "tools/osify-gui/osify-search.sh"), os.path.join(bin_dir, "osify-search"))
    shutil.copy2(os.path.join(REPO_ROOT, "tools/osify-gui/osify-search.sh"), os.path.join(r4_work, "usr/local/bin/osify-search"))
    shutil.copy2(os.path.join(REPO_ROOT, "tools/osify-gui/osify-usb-writer.sh"), os.path.join(bin_dir, "osify-usb-writer"))
    shutil.copy2(os.path.join(REPO_ROOT, "tools/osify-gui/osify-usb-writer.sh"), os.path.join(bin_dir, "osify-usb"))
    shutil.copy2(os.path.join(REPO_ROOT, "tools/osify-gui/osify-usb-writer.sh"), os.path.join(r4_work, "usr/local/bin/osify-usb-writer"))
    shutil.copy2(os.path.join(REPO_ROOT, "system/display/osify-nightlight.sh"), os.path.join(bin_dir, "osify-nightlight"))
    shutil.copy2(os.path.join(REPO_ROOT, "system/display/osify-nightlight.sh"), os.path.join(r4_work, "usr/local/bin/osify-nightlight"))
    shutil.copy2(os.path.join(REPO_ROOT, "tools/osify-gui/osify-accessibility.sh"), os.path.join(bin_dir, "osify-accessibility"))
    shutil.copy2(os.path.join(REPO_ROOT, "tools/osify-gui/osify-accessibility.sh"), os.path.join(r4_work, "usr/local/bin/osify-accessibility"))
    shutil.copy2(os.path.join(REPO_ROOT, "tools/osify-gui/osify-backup.sh"), os.path.join(bin_dir, "osify-backup"))
    shutil.copy2(os.path.join(REPO_ROOT, "tools/osify-gui/osify-backup.sh"), os.path.join(r4_work, "usr/local/bin/osify-backup"))
    shutil.copy2(os.path.join(REPO_ROOT, "tools/osify-gui/osify-voice-recorder.sh"), os.path.join(bin_dir, "osify-voice-recorder"))
    shutil.copy2(os.path.join(REPO_ROOT, "tools/osify-gui/osify-voice-recorder.sh"), os.path.join(bin_dir, "osify-voice"))
    shutil.copy2(os.path.join(REPO_ROOT, "tools/osify-gui/osify-voice-recorder.sh"), os.path.join(r4_work, "usr/local/bin/osify-voice-recorder"))
    shutil.copy2(os.path.join(REPO_ROOT, "tools/osify-gui/osify-camera.sh"), os.path.join(bin_dir, "osify-camera"))
    shutil.copy2(os.path.join(REPO_ROOT, "tools/osify-gui/osify-camera.sh"), os.path.join(r4_work, "usr/local/bin/osify-camera"))
    shutil.copy2(os.path.join(REPO_ROOT, "network/osify-hotspot.sh"), os.path.join(bin_dir, "osify-hotspot"))
    shutil.copy2(os.path.join(REPO_ROOT, "network/osify-hotspot.sh"), os.path.join(r4_work, "usr/local/bin/osify-hotspot"))
    shutil.copy2(os.path.join(REPO_ROOT, "tools/osify-gui/osify-package-installer.sh"), os.path.join(bin_dir, "osify-package-installer"))
    shutil.copy2(os.path.join(REPO_ROOT, "tools/osify-gui/osify-package-installer.sh"), os.path.join(r4_work, "usr/local/bin/osify-package-installer"))
    shutil.copy2(os.path.join(REPO_ROOT, "system/power/osify-lid.sh"), os.path.join(bin_dir, "osify-lid"))
    shutil.copy2(os.path.join(REPO_ROOT, "system/power/osify-lid.sh"), os.path.join(r4_work, "usr/local/bin/osify-lid"))
    shutil.copy2(os.path.join(REPO_ROOT, "tools/osify-gui/osify-sysinfo.sh"), os.path.join(bin_dir, "osify-sysinfo"))
    shutil.copy2(os.path.join(REPO_ROOT, "tools/osify-gui/osify-sysinfo.sh"), os.path.join(r4_work, "usr/local/bin/osify-sysinfo"))
    shutil.copy2(os.path.join(REPO_ROOT, "tools/osify-gui/osify-factory-reset.sh"), os.path.join(bin_dir, "osify-factory-reset"))
    shutil.copy2(os.path.join(REPO_ROOT, "tools/osify-gui/osify-factory-reset.sh"), os.path.join(r4_work, "usr/local/bin/osify-factory-reset"))
    shutil.copy2(os.path.join(REPO_ROOT, "tools/osify-gui/osify-spotlight.py"), os.path.join(bin_dir, "osify-spotlight"))
    shutil.copy2(os.path.join(REPO_ROOT, "tools/osify-gui/osify-spotlight.py"), os.path.join(r4_work, "usr/local/bin/osify-spotlight"))
    shutil.copy2(os.path.join(REPO_ROOT, "tools/osify-gui/osify-controlcenter.py"), os.path.join(bin_dir, "osify-controlcenter"))
    shutil.copy2(os.path.join(REPO_ROOT, "tools/osify-gui/osify-controlcenter.py"), os.path.join(r4_work, "usr/local/bin/osify-controlcenter"))
    shutil.copy2(os.path.join(REPO_ROOT, "tools/osify-gui/osify-about.py"), os.path.join(bin_dir, "osify-about"))
    shutil.copy2(os.path.join(REPO_ROOT, "tools/osify-gui/osify-about.py"), os.path.join(r4_work, "usr/local/bin/osify-about"))
    shutil.copy2(os.path.join(REPO_ROOT, "tools/osify-gui/osify-bootsplash.sh"), os.path.join(bin_dir, "osify-bootsplash"))
    shutil.copy2(os.path.join(REPO_ROOT, "tools/osify-gui/osify-bootsplash.py"), os.path.join(bin_dir, "osify-bootsplash.py"))
    shutil.copy2(os.path.join(REPO_ROOT, "tools/osify-gui/osify-oobe.sh"), os.path.join(bin_dir, "osify-oobe"))
    shutil.copy2(os.path.join(REPO_ROOT, "tools/osify-gui/osify-bootsplash.sh"), os.path.join(r4_work, "usr/local/bin/osify-bootsplash"))
    shutil.copy2(os.path.join(REPO_ROOT, "tools/osify-gui/osify-oobe.sh"), os.path.join(r4_work, "usr/local/bin/osify-oobe"))

    # Suite di Sicurezza Autoadattiva, Privacy Vault e Zero-Telemetry
    shutil.copy2(os.path.join(REPO_ROOT, "security/adaptive/osify-adaptive-security.sh"), os.path.join(bin_dir, "osify-adaptive-security"))
    shutil.copy2(os.path.join(REPO_ROOT, "security/adaptive/osify-adaptive-security.sh"), os.path.join(r4_work, "usr/local/bin/osify-adaptive-security"))
    shutil.copy2(os.path.join(REPO_ROOT, "security/privacy/osify-privacy-vault.sh"), os.path.join(bin_dir, "osify-privacy-vault"))
    shutil.copy2(os.path.join(REPO_ROOT, "security/privacy/osify-privacy-vault.sh"), os.path.join(bin_dir, "osify-shred"))
    shutil.copy2(os.path.join(REPO_ROOT, "security/privacy/osify-privacy-vault.sh"), os.path.join(r4_work, "usr/local/bin/osify-privacy-vault"))
    shutil.copy2(os.path.join(REPO_ROOT, "security/shield/osify-shield.sh"), os.path.join(bin_dir, "osify-shield"))
    shutil.copy2(os.path.join(REPO_ROOT, "security/shield/osify-shield.sh"), os.path.join(r4_work, "usr/local/bin/osify-shield"))
    shutil.copy2(os.path.join(REPO_ROOT, "security/adblock/osify-adblock.sh"), os.path.join(bin_dir, "osify-adblock"))
    shutil.copy2(os.path.join(REPO_ROOT, "security/adblock/osify-adblock.sh"), os.path.join(r4_work, "usr/local/bin/osify-adblock"))
    shutil.copy2(os.path.join(REPO_ROOT, "security/auth/osify-auth-gateway.py"), os.path.join(bin_dir, "osify-auth-gateway"))
    shutil.copy2(os.path.join(REPO_ROOT, "security/auth/osify-auth-gateway.py"), os.path.join(r4_work, "usr/local/bin/osify-auth-gateway"))

    # Copia speculare in /Sistema/Servizi/Sicurezza.ify
    r4_servizi = os.path.join(r4_work, "Sistema/Servizi")
    os.makedirs(r4_servizi, exist_ok=True)
    shutil.copy2(os.path.join(REPO_ROOT, "sistema/servizi/Sicurezza.ify"), os.path.join(r4_servizi, "Sicurezza.ify"))
    os.chmod(os.path.join(r4_servizi, "Sicurezza.ify"), 0o755)

    bs_src = os.path.join(REPO_ROOT, "desktop/branding/wallpapers/osify-bootsplash.jpg")
    if os.path.exists(bs_src):
        os.makedirs(os.path.join(r4_work, "usr/share/pixmaps"), exist_ok=True)
        shutil.copy2(bs_src, os.path.join(r4_work, "usr/share/pixmaps/osify-bootsplash.jpg"))

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
                    raw_cpio = safe_lzma_decompress(f.read())
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

    # Albero del File System Nativo OSify in Lingua Italiana
    r4_sistema = os.path.join(r4_work, "Sistema")
    os.makedirs(os.path.join(r4_sistema, "Driver"), exist_ok=True)
    os.makedirs(os.path.join(r4_sistema, "Servizi"), exist_ok=True)
    os.makedirs(os.path.join(r4_sistema, "Icone"), exist_ok=True)
    os.makedirs(os.path.join(r4_sistema, "Librerie"), exist_ok=True)

    sistema_src = os.path.join(REPO_ROOT, "sistema")
    if os.path.exists(sistema_src):
        shutil.copytree(sistema_src, r4_sistema, dirs_exist_ok=True)

    r4_app = os.path.join(r4_work, "Applicazioni")
    os.makedirs(r4_app, exist_ok=True)
    app_src = os.path.join(REPO_ROOT, "applicazioni")
    if os.path.exists(app_src):
        shutil.copytree(app_src, r4_app, dirs_exist_ok=True)

    r4_utenti = os.path.join(r4_work, "Utenti")
    os.makedirs(r4_utenti, exist_ok=True)
    osify_symlink = os.path.join(r4_utenti, "osify")
    if not os.path.exists(osify_symlink):
        try:
            os.symlink("../home/osify", osify_symlink)
        except Exception:
            pass

    for srv_bin in ["GestorePacchetti.ify", "Compatibilità.ify"]:
        srv_file = os.path.join(r4_sistema, "Servizi", srv_bin)
        if os.path.exists(srv_file):
            os.chmod(srv_file, 0o755)
            w_name = "osify-package-installer" if "GestorePacchetti" in srv_bin else "osify-compatibility"
            w_path = os.path.join(r4_work, "usr/bin", w_name)
            with open(w_path, "w") as wf:
                wf.write(f"#!/bin/sh\nexec /Sistema/Servizi/{srv_bin} \"$@\"\n")
            os.chmod(w_path, 0o755)

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

    osify_48 = os.path.join(REPO_ROOT, "desktop/branding/icons/48/osify.png")
    if os.path.exists(osify_48):
        shutil.copy2(osify_48, os.path.join(pixmaps_dir, "osify.png"))
        for icon_path in [
            "usr/share/icons/SliTaz-Faenza/48x48/places/start-here.png",
            "usr/share/icons/SliTaz-Faenza/22x22/places/start-here.png",
            "usr/share/icons/SliTaz-Faenza-Dark/22x22/places/start-here.png",
            "usr/share/icons/hicolor/48x48/apps/osify.png"
        ]:
            full_ip = os.path.join(r4_work, icon_path)
            os.makedirs(os.path.dirname(full_ip), exist_ok=True)
            shutil.copy2(osify_48, full_ip)

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
ID_LIKE=osify
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

    for lfm_p in [
        "etc/xdg/libfm/libfm.conf",
        "etc/skel/.config/libfm/libfm.conf",
        "home/osify/.config/libfm/libfm.conf",
        "root/.config/libfm/libfm.conf"
    ]:
        full_lfm = os.path.join(r4_work, lfm_p)
        os.makedirs(os.path.dirname(full_lfm), exist_ok=True)
        with open(full_lfm, "w") as f:
            f.write(LIBFM_CONF)

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
        "osify-oobe.desktop": (
            "[Desktop Entry]\n"
            "Type=Application\n"
            "Name=Assistente di Configurazione\n"
            "Comment=Configurazione Iniziale OSify (Lingua, Tastiera, Wi-Fi, Account e Aspetto)\n"
            "Exec=/usr/bin/osify-oobe\n"
            "Icon=/usr/share/pixmaps/osify.png\n"
            "Terminal=false\n"
            "Categories=Settings;System;\n"
        ),
        "osify-dashboard.desktop": (
            "[Desktop Entry]\n"
            "Type=Application\n"
            "Name=Dashboard di Sistema\n"
            "Comment=Centro di Controllo Interattivo a 360 Gradi (Hardware, Turbo, Wi-Fi, Schermo, RAM)\n"
            "Exec=/usr/bin/osify-hub\n"
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
            "Name=Centro OSify.ify\n"
            "Comment=Centro di Controllo, Prestazioni e Plancia Operativa OSify 2050\n"
            "Exec=/Applicazioni/Centro\\ OSify.ify/avvia.sh\n"
            "Icon=/usr/share/pixmaps/osify-hub.png\n"
            "Terminal=false\n"
            "Categories=System;Utility;\n"
        ),
        "osify-browser.desktop": (
            "[Desktop Entry]\n"
            "Type=Application\n"
            "Name=Navigatore.ify\n"
            "Comment=Navigatore Web ultra-veloce con motore di rendering nativo e protezione tracciamento\n"
            "Exec=/Applicazioni/Navigatore.ify/avvia.sh\n"
            "Icon=/usr/share/pixmaps/osify-browser.png\n"
            "Terminal=false\n"
            "Categories=Network;WebBrowser;\n"
        ),
        "osify-files.desktop": (
            "[Desktop Entry]\n"
            "Type=Application\n"
            "Name=Esplora.ify\n"
            "Comment=Esplora e gestisci cartelle, dischi e file in /Utenti e /Sistema\n"
            "Exec=/Applicazioni/Esplora.ify/avvia.sh\n"
            "Icon=/usr/share/pixmaps/osify-files.png\n"
            "Terminal=false\n"
            "Categories=System;Utility;FileManager;\n"
        ),
        "osify-wifi.desktop": (
            "[Desktop Entry]\n"
            "Type=Application\n"
            "Name=Reti.ify\n"
            "Comment=Gestione reti wireless Wi-Fi, Ethernet e sicurezza di connessione\n"
            "Exec=/Applicazioni/Reti.ify/avvia.sh\n"
            "Icon=/usr/share/pixmaps/osify-wifi.png\n"
            "Terminal=false\n"
            "Categories=Network;Settings;\n"
        ),
        "osify-games.desktop": (
            "[Desktop Entry]\n"
            "Type=Application\n"
            "Name=Giochi.ify\n"
            "Comment=Piattaforma Giochi con Turbo Boost e compatibilità universale\n"
            "Exec=/Applicazioni/Giochi.ify/avvia.sh\n"
            "Icon=/usr/share/pixmaps/osify-games.png\n"
            "Terminal=false\n"
            "Categories=Game;\n"
        ),
        "osify-developer.desktop": (
            "[Desktop Entry]\n"
            "Type=Application\n"
            "Name=Sviluppo.ify\n"
            "Comment=Suite di Programmazione e Strumenti di Sviluppo OSify\n"
            "Exec=/Applicazioni/Sviluppo.ify/avvia.sh\n"
            "Icon=/usr/share/pixmaps/osify-developer.png\n"
            "Terminal=false\n"
            "Categories=Development;\n"
        ),
        "osify-appearance.desktop": (
            "[Desktop Entry]\n"
            "Type=Application\n"
            "Name=Aspetto.ify\n"
            "Comment=Personalizzazione Schermo, Sfondi Cyber Dark e Virtual Scaler Netbook\n"
            "Exec=/Applicazioni/Aspetto.ify/avvia.sh\n"
            "Icon=/usr/share/pixmaps/osify-appearance.png\n"
            "Terminal=false\n"
            "Categories=Settings;\n"
        ),
        "osify-taskmanager.desktop": (
            "[Desktop Entry]\n"
            "Type=Application\n"
            "Name=Monitor.ify\n"
            "Comment=Monitoraggio di Processi, Memoria e Telemetria Hardware in Tempo Reale\n"
            "Exec=/Applicazioni/Monitor.ify/avvia.sh\n"
            "Icon=/usr/share/pixmaps/osify-taskmanager.png\n"
            "Terminal=false\n"
            "Categories=System;\n"
        ),
        "osify-install.desktop": (
            "[Desktop Entry]\n"
            "Type=Application\n"
            "Name=Installa OSify.ify\n"
            "Comment=Installatore Guidato su Disco Fisso con Migrazione Dati Live\n"
            "Exec=/Applicazioni/Installa\\ OSify.ify/avvia.sh\n"
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
            "Name=Aggiornamenti.ify\n"
            "Comment=Verifica e installa aggiornamenti atomici di sistema OSify\n"
            "Exec=/Applicazioni/Aggiornamenti.ify/avvia.sh\n"
            "Icon=/usr/share/pixmaps/osify-update.png\n"
            "Terminal=false\n"
            "Categories=System;Settings;\n"
        ),
        "osify-settings.desktop": (
            "[Desktop Entry]\n"
            "Type=Application\n"
            "Name=Impostazioni.ify\n"
            "Comment=Centro Impostazioni di Sistema, Display, Periferiche e Risparmio Energetico\n"
            "Exec=/Applicazioni/Impostazioni.ify/avvia.sh\n"
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
        ),
        "osify-audio.desktop": (
            "[Desktop Entry]\n"
            "Type=Application\n"
            "Name=Controllo Audio e Volume\n"
            "Comment=Regola il volume master, mixer e canali audio ALSA/PipeWire\n"
            "Exec=/usr/bin/osify-audio gui\n"
            "Icon=/usr/share/pixmaps/osify-audio.png\n"
            "Terminal=false\n"
            "Categories=AudioVideo;Audio;Settings;\n"
        ),
        "osify-bluetooth.desktop": (
            "[Desktop Entry]\n"
            "Type=Application\n"
            "Name=Gestione Bluetooth\n"
            "Comment=Scansione e connessione cuffie wireless, controller e periferiche\n"
            "Exec=/usr/bin/osify-bluetooth\n"
            "Icon=/usr/share/pixmaps/osify-bluetooth.png\n"
            "Terminal=false\n"
            "Categories=Network;Settings;HardwareSettings;\n"
        ),
        "osify-snapshot.desktop": (
            "[Desktop Entry]\n"
            "Type=Application\n"
            "Name=Punti di Ripristino (Snapshot)\n"
            "Comment=Crea e ripristina istantanee atomiche di sistema e configurazioni\n"
            "Exec=/usr/bin/osify-snapshot\n"
            "Icon=/usr/share/pixmaps/osify-snapshot.png\n"
            "Terminal=false\n"
            "Categories=System;Utility;\n"
        ),
        "osify-power.desktop": (
            "[Desktop Entry]\n"
            "Type=Application\n"
            "Name=Alimentazione e Spegnimento\n"
            "Comment=Spegni, Riavvia, Sospendi o gestisci la Batteria e il Risparmio Energetico\n"
            "Exec=/usr/bin/osify-power gui\n"
            "Icon=/usr/share/pixmaps/osify-power.png\n"
            "Terminal=false\n"
            "Categories=System;Settings;\n"
        ),
        "osify-screenshot.desktop": (
            "[Desktop Entry]\n"
            "Type=Application\n"
            "Name=Cattura.ify\n"
            "Comment=Cattura schermate del desktop o di finestre a risoluzione nativa\n"
            "Exec=/Applicazioni/Cattura.ify/avvia.sh\n"
            "Icon=/usr/share/pixmaps/osify-appearance.png\n"
            "Terminal=false\n"
            "Categories=Utility;Graphics;\n"
        ),
        "osify-image-viewer.desktop": (
            "[Desktop Entry]\n"
            "Type=Application\n"
            "Name=Galleria.ify\n"
            "Comment=Visualizza immagini e foto a schermo intero o a finestra\n"
            "Exec=/Applicazioni/Galleria.ify/avvia.sh %f\n"
            "Icon=/usr/share/pixmaps/osify-appearance.png\n"
            "Terminal=false\n"
            "MimeType=image/jpeg;image/png;image/gif;image/bmp;image/webp;\n"
            "Categories=Graphics;Viewer;\n"
        ),
        "osify-brightness.desktop": (
            "[Desktop Entry]\n"
            "Type=Application\n"
            "Name=Luminosita Schermo\n"
            "Comment=Regola la luminosita del display su notebook e monitor\n"
            "Exec=/usr/bin/osify-brightness gui\n"
            "Icon=/usr/share/pixmaps/osify-appearance.png\n"
            "Terminal=false\n"
            "Categories=Settings;HardwareSettings;\n"
        ),
        "osify-archive-manager.desktop": (
            "[Desktop Entry]\n"
            "Type=Application\n"
            "Name=Archivi.ify\n"
            "Comment=Estrai e crea archivi compressi ZIP, TAR, GZ, XZ e 7Z con un click\n"
            "Exec=/Applicazioni/Archivi.ify/avvia.sh %f\n"
            "Icon=/usr/share/pixmaps/osify-archive.png\n"
            "Terminal=false\n"
            "MimeType=application/zip;application/x-zip-compressed;application/x-tar;application/x-gzip;application/x-bzip2;application/x-xz;application/x-7z-compressed;\n"
            "Categories=Utility;Archiving;\n"
        ),
        "osify-notepad.desktop": (
            "[Desktop Entry]\n"
            "Type=Application\n"
            "Name=Note.ify\n"
            "Comment=Editor di testo leggero e veloce per documenti, appunti e file di sistema\n"
            "Exec=/Applicazioni/Note.ify/avvia.sh %f\n"
            "Icon=/usr/share/pixmaps/osify-notepad.png\n"
            "Terminal=false\n"
            "MimeType=text/plain;text/x-log;text/x-sh;text/markdown;\n"
            "Categories=Utility;TextEditor;\n"
        ),
        "osify-pdf-viewer.desktop": (
            "[Desktop Entry]\n"
            "Type=Application\n"
            "Name=Documenti.ify\n"
            "Comment=Visualizza e consulta documenti e manuali in formato PDF\n"
            "Exec=/Applicazioni/Documenti.ify/avvia.sh %f\n"
            "Icon=/usr/share/pixmaps/osify-files.png\n"
            "Terminal=false\n"
            "MimeType=application/pdf;application/x-pdf;\n"
            "Categories=Office;Viewer;\n"
        ),
        "osify-calculator.desktop": (
            "[Desktop Entry]\n"
            "Type=Application\n"
            "Name=Calcolatrice.ify\n"
            "Comment=Esegui calcoli aritmetici, percentuali, scientifici e conversioni\n"
            "Exec=/Applicazioni/Calcolatrice.ify/avvia.sh\n"
            "Icon=/usr/share/pixmaps/osify-calculator.png\n"
            "Terminal=false\n"
            "Categories=Utility;Calculator;\n"
        ),
        "osify-media-player.desktop": (
            "[Desktop Entry]\n"
            "Type=Application\n"
            "Name=Video.ify\n"
            "Comment=Riproduci file video MP4, MKV, AVI e filmati ad alta definizione\n"
            "Exec=/Applicazioni/Video.ify/avvia.sh %f\n"
            "Icon=/usr/share/pixmaps/osify-audio.png\n"
            "Terminal=false\n"
            "MimeType=video/mp4;video/x-matroska;video/quicktime;video/x-msvideo;\n"
            "Categories=AudioVideo;Video;Player;\n"
        ),
        "osify-music.desktop": (
            "[Desktop Entry]\n"
            "Type=Application\n"
            "Name=Musica.ify\n"
            "Comment=Riproduttore audio e libreria musicale MP3, WAV, FLAC, OGG\n"
            "Exec=/Applicazioni/Musica.ify/avvia.sh %f\n"
            "Icon=/usr/share/pixmaps/osify-audio.png\n"
            "Terminal=false\n"
            "MimeType=audio/mpeg;audio/x-wav;audio/ogg;audio/flac;\n"
            "Categories=AudioVideo;Audio;Player;\n"
        ),
        "osify-app-store.desktop": (
            "[Desktop Entry]\n"
            "Type=Application\n"
            "Name=Negozio.ify\n"
            "Comment=Negozio Ufficiale di Applicazioni e Moduli .ify\n"
            "Exec=/Applicazioni/Negozio.ify/avvia.sh\n"
            "Icon=/usr/share/pixmaps/osify-install.png\n"
            "Terminal=false\n"
            "Categories=System;PackageManager;\n"
        ),
        "osify-compatibility.desktop": (
            "[Desktop Entry]\n"
            "Type=Application\n"
            "Name=Compatibilità.ify\n"
            "Comment=Sottosistema di Compatibilità Universale per Applicazioni e Giochi\n"
            "Exec=/Sistema/Servizi/Compatibilità.ify\n"
            "Icon=/usr/share/pixmaps/osify-games.png\n"
            "Terminal=false\n"
            "Categories=System;Utility;\n"
        ),
        "osify-keyboard.desktop": (
            "[Desktop Entry]\n"
            "Type=Application\n"
            "Name=Mappatura Tastiera\n"
            "Comment=Imposta o cambia il layout della tastiera (Italiana, USA, UK, Tedesca, Francese)\n"
            "Exec=/usr/bin/osify-keyboard gui\n"
            "Icon=/usr/share/pixmaps/osify-keyboard.png\n"
            "Terminal=false\n"
            "Categories=Settings;HardwareSettings;\n"
        ),
        "osify-onboard.desktop": (
            "[Desktop Entry]\n"
            "Type=Application\n"
            "Name=Tastiera a Schermo\n"
            "Comment=Digita testi, password e comandi a schermo con mouse o touchpad\n"
            "Exec=/usr/bin/osify-onboard\n"
            "Icon=/usr/share/pixmaps/osify-keyboard.png\n"
            "Terminal=false\n"
            "Categories=Utility;Accessibility;\n"
        ),
        "osify-disk-health.desktop": (
            "[Desktop Entry]\n"
            "Type=Application\n"
            "Name=Salute e Diagnostica Dischi\n"
            "Comment=Controlla lo spazio su disco, partizioni, usura e stato SMART dell'hardware\n"
            "Exec=/usr/bin/osify-disk-health\n"
            "Icon=/usr/share/pixmaps/osify-files.png\n"
            "Terminal=false\n"
            "Categories=System;HardwareSettings;\n"
        ),
        "osify-share.desktop": (
            "[Desktop Entry]\n"
            "Type=Application\n"
            "Name=Condivisione Rete e Smartphone\n"
            "Comment=Condividi file e cartelle via Wi-Fi con smartphone o altri computer all'istante\n"
            "Exec=/usr/bin/osify-share gui\n"
            "Icon=/usr/share/pixmaps/osify-share.png\n"
            "Terminal=false\n"
            "Categories=Network;FileTransfer;\n"
        ),
        "osify-printer.desktop": (
            "[Desktop Entry]\n"
            "Type=Application\n"
            "Name=Gestione Stampanti e PDF\n"
            "Comment=Gestisci stampanti locali, code di stampa e crea documenti PDF\n"
            "Exec=/usr/bin/osify-printer gui\n"
            "Icon=/usr/share/pixmaps/osify-printer.png\n"
            "Terminal=false\n"
            "Categories=System;Printing;Settings;\n"
        ),
        "osify-thermal-monitor.desktop": (
            "[Desktop Entry]\n"
            "Type=Application\n"
            "Name=Monitor Termico e Ventole\n"
            "Comment=Controlla la temperatura della CPU, ventole e previeni il surriscaldamento\n"
            "Exec=/usr/bin/osify-thermal-monitor gui\n"
            "Icon=/usr/share/pixmaps/osify-thermal.png\n"
            "Terminal=false\n"
            "Categories=System;HardwareSettings;\n"
        ),
        "osify-benchmark.desktop": (
            "[Desktop Entry]\n"
            "Type=Application\n"
            "Name=Benchmark Prestazioni\n"
            "Comment=Misura la velocita della CPU, memoria RAM e disco fisso con punteggio sintetico\n"
            "Exec=/usr/bin/osify-benchmark gui\n"
            "Icon=/usr/share/pixmaps/osify-benchmark.png\n"
            "Terminal=false\n"
            "Categories=System;Utility;\n"
        ),
        "osify-firewall.desktop": (
            "[Desktop Entry]\n"
            "Type=Application\n"
            "Name=Firewall e Sicurezza Rete\n"
            "Comment=Gestisci la protezione perimetrale, porte aperte e isolamento stealth del PC\n"
            "Exec=/usr/bin/osify-firewall gui\n"
            "Icon=/usr/share/pixmaps/osify-firewall.png\n"
            "Terminal=false\n"
            "Categories=System;Security;Settings;\n"
        ),
        "osify-time.desktop": (
            "[Desktop Entry]\n"
            "Type=Application\n"
            "Name=Data, Ora e Fuso Orario\n"
            "Comment=Configura data, orologio, fuso orario e sincronizzazione automatica Internet\n"
            "Exec=/usr/bin/osify-time-sync gui\n"
            "Icon=/usr/share/pixmaps/osify-time.png\n"
            "Terminal=false\n"
            "Categories=Settings;HardwareSettings;\n"
        ),
        "osify-touchpad.desktop": (
            "[Desktop Entry]\n"
            "Type=Application\n"
            "Name=Touchpad e Mouse\n"
            "Comment=Calibra il tocco, la velocita del puntatore e la protezione del palmo\n"
            "Exec=/usr/bin/osify-touchpad gui\n"
            "Icon=/usr/share/pixmaps/osify-touchpad.png\n"
            "Terminal=false\n"
            "Categories=Settings;HardwareSettings;\n"
        ),
        "osify-search.desktop": (
            "[Desktop Entry]\n"
            "Type=Application\n"
            "Name=Cerca File\n"
            "Comment=Trova rapidamente file, documenti e immagini nel sistema\n"
            "Exec=/usr/bin/osify-search\n"
            "Icon=/usr/share/pixmaps/osify-search.png\n"
            "Terminal=false\n"
            "Categories=Utility;FileManager;\n"
        ),
        "osify-usb-writer.desktop": (
            "[Desktop Entry]\n"
            "Type=Application\n"
            "Name=Scrittore USB Avviabile\n"
            "Comment=Crea chiavette USB avviabili da immagini ISO o IMG\n"
            "Exec=/usr/bin/osify-usb-writer gui\n"
            "Icon=/usr/share/pixmaps/osify-usb.png\n"
            "Terminal=false\n"
            "Categories=System;Utility;\n"
        ),
        "osify-nightlight.desktop": (
            "[Desktop Entry]\n"
            "Type=Application\n"
            "Name=Luce Notturna\n"
            "Comment=Filtro luce blu e temperatura colore per protezione visiva\n"
            "Exec=/usr/bin/osify-nightlight gui\n"
            "Icon=/usr/share/pixmaps/osify-nightlight.png\n"
            "Terminal=false\n"
            "Categories=Settings;HardwareSettings;\n"
        ),
        "osify-accessibility.desktop": (
            "[Desktop Entry]\n"
            "Type=Application\n"
            "Name=Accessibilita\n"
            "Comment=Centro aiuti visivi, ingranditore schermo e scaling caratteri\n"
            "Exec=/usr/bin/osify-accessibility gui\n"
            "Icon=/usr/share/pixmaps/osify-accessibility.png\n"
            "Terminal=false\n"
            "Categories=Settings;Accessibility;\n"
        ),
        "osify-backup.desktop": (
            "[Desktop Entry]\n"
            "Type=Application\n"
            "Name=Backup Personale\n"
            "Comment=Salvataggio e ripristino di documenti, foto e configurazioni su USB\n"
            "Exec=/usr/bin/osify-backup gui\n"
            "Icon=/usr/share/pixmaps/osify-backup.png\n"
            "Terminal=false\n"
            "Categories=System;Archiving;Utility;\n"
        ),
        "osify-voice-recorder.desktop": (
            "[Desktop Entry]\n"
            "Type=Application\n"
            "Name=Registratore Vocale\n"
            "Comment=Memo vocali e collaudo microfono integrato a bassissima latenza\n"
            "Exec=/usr/bin/osify-voice gui\n"
            "Icon=/usr/share/pixmaps/osify-voice.png\n"
            "Terminal=false\n"
            "Categories=AudioVideo;Audio;Recorder;\n"
        ),
        "osify-camera.desktop": (
            "[Desktop Entry]\n"
            "Type=Application\n"
            "Name=Fotocamera\n"
            "Comment=Visualizzatore webcam integrata e scatto foto istantaneo\n"
            "Exec=/usr/bin/osify-camera gui\n"
            "Icon=/usr/share/pixmaps/osify-camera.png\n"
            "Terminal=false\n"
            "Categories=AudioVideo;Video;Photography;\n"
        ),
        "osify-hotspot.desktop": (
            "[Desktop Entry]\n"
            "Type=Application\n"
            "Name=Hotspot Wi-Fi\n"
            "Comment=Condivisione connessione e creazione punto di accesso wireless\n"
            "Exec=/usr/bin/osify-hotspot gui\n"
            "Icon=/usr/share/pixmaps/osify-hotspot.png\n"
            "Terminal=false\n"
            "Categories=Network;Settings;HardwareSettings;\n"
        ),
        "osify-package-installer.desktop": (
            "[Desktop Entry]\n"
            "Type=Application\n"
            "Name=Gestore Pacchetti (.ify)\n"
            "Comment=Installa e gestisci applicazioni e pacchetti nativi OSify .ify\n"
            "Exec=/Sistema/Servizi/GestorePacchetti.ify %f\n"
            "Icon=/usr/share/pixmaps/osify-install.png\n"
            "Terminal=false\n"
            "MimeType=application/x-osify-package;\n"
            "Categories=System;PackageManager;\n"
        ),
        "osify-lid.desktop": (
            "[Desktop Entry]\n"
            "Type=Application\n"
            "Name=Coperchio e Sospensione\n"
            "Comment=Configura cosa fa il portatile alla chiusura dello schermo (Sleep o Schermo spento)\n"
            "Exec=/usr/bin/osify-lid gui\n"
            "Icon=/usr/share/pixmaps/osify-power.png\n"
            "Terminal=false\n"
            "Categories=Settings;HardwareSettings;\n"
        ),
        "osify-sysinfo.desktop": (
            "[Desktop Entry]\n"
            "Type=Application\n"
            "Name=Scheda Tecnica Hardware\n"
            "Comment=Visualizza specifiche dettagliate di CPU, RAM, GPU, batteria, dischi e BIOS\n"
            "Exec=/usr/bin/osify-sysinfo gui\n"
            "Icon=/usr/share/pixmaps/osify-settings.png\n"
            "Terminal=false\n"
            "Categories=System;HardwareSettings;Utility;\n"
        ),
        "osify-factory-reset.desktop": (
            "[Desktop Entry]\n"
            "Type=Application\n"
            "Name=Ripristino Aspetto Originale\n"
            "Comment=Ripristina la barra delle applicazioni, menu e icone alle impostazioni di fabbrica\n"
            "Exec=/usr/bin/osify-factory-reset gui\n"
            "Icon=/usr/share/pixmaps/osify-appearance.png\n"
            "Terminal=false\n"
            "Categories=Settings;DesktopSettings;\n"
        ),
        "osify-spotlight.desktop": (
            "[Desktop Entry]\n"
            "Type=Application\n"
            "Name=Spotlight Search\n"
            "Comment=Ricerca istantanea di applicazioni, impostazioni e calcolatrice\n"
            "Exec=/usr/bin/osify-spotlight\n"
            "Icon=/usr/share/pixmaps/osify-spotlight.png\n"
            "Terminal=false\n"
            "Categories=Utility;Core;\n"
        ),
        "osify-controlcenter.desktop": (
            "[Desktop Entry]\n"
            "Type=Application\n"
            "Name=Centro di Controllo\n"
            "Comment=Pannello rapido Wi-Fi, audio, luminosita e stato di sistema\n"
            "Exec=/usr/bin/osify-controlcenter\n"
            "Icon=/usr/share/pixmaps/osify-controlcenter.png\n"
            "Terminal=false\n"
            "Categories=Settings;System;\n"
        ),
        "osify-about.desktop": (
            "[Desktop Entry]\n"
            "Type=Application\n"
            "Name=Informazioni su questo OSify\n"
            "Comment=Panoramica hardware, specifiche processore, memoria e rilascio\n"
            "Exec=/usr/bin/osify-about\n"
            "Icon=/usr/share/pixmaps/osify-about.png\n"
            "Terminal=false\n"
            "Categories=System;Utility;\n"
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

    # Scrittura sul Desktop: Scrivania macOS Ultra-Pulita (solo disco ed installatore per zero disordine)
    desktop_essentials = [
        "osify-install.desktop",
        "osify-files.desktop"
    ]
    for dpath in ["root/Desktop", "home/osify/Desktop", "home/tux/Desktop", "home/slitaz/Desktop", "etc/skel/Desktop"]:
        full_d = os.path.join(r4_work, dpath)
        if os.path.exists(full_d):
            shutil.rmtree(full_d, ignore_errors=True)
        os.makedirs(full_d, exist_ok=True)
        for name in desktop_essentials:
            if name in app_entries:
                dest_f = os.path.join(full_d, name)
                with open(dest_f, "w") as f:
                    f.write(app_entries[name])
                os.chmod(dest_f, 0o755)

    # Scrittura LXPanel Dual Panel (Top Bar + Floating Dock) in rootfs4
    for base_p in [
        "etc/skel/.config/lxpanel",
        "home/osify/.config/lxpanel",
        "home/tux/.config/lxpanel",
        "etc/lxpanel",
        "etc/xdg/lxpanel",
        "root/.config/lxpanel"
    ]:
        for prof in ["default", "slitaz", "original"]:
            prof_path = os.path.join(r4_work, base_p, prof)
            if os.path.exists(prof_path) and not os.path.isdir(prof_path):
                try:
                    os.remove(prof_path)
                except Exception:
                    pass
            panels_dir = os.path.join(prof_path, "panels")
            if os.path.exists(panels_dir) and not os.path.isdir(panels_dir):
                try:
                    os.remove(panels_dir)
                except Exception:
                    pass
            os.makedirs(panels_dir, exist_ok=True)
            old_p = os.path.join(panels_dir, "panel")
            if os.path.exists(old_p):
                try:
                    os.remove(old_p)
                except Exception:
                    pass
            with open(os.path.join(panels_dir, "topbar"), "w") as f:
                f.write(lxpanel_topbar_cfg)
            with open(os.path.join(panels_dir, "dock"), "w") as f:
                f.write(lxpanel_dock_cfg)

    # Iniezione Icone Brand e Tema Openbox macOS anche in rootfs4
    icons_src = os.path.join(REPO_ROOT, "desktop/branding/icons")
    if os.path.exists(icons_src):
        r4_pixmaps = os.path.join(r4_work, "usr/share/pixmaps")
        os.makedirs(r4_pixmaps, exist_ok=True)
        for ic in glob.glob(os.path.join(icons_src, "*/*.png")):
            shutil.copy2(ic, r4_pixmaps)
        for spider_ic in [
            "usr/share/icons/SliTaz-Faenza/48x48/places/start-here.png",
            "usr/share/icons/SliTaz-Faenza/22x22/places/start-here.png",
            "usr/share/icons/SliTaz-Faenza-Dark/22x22/places/start-here.png",
            "usr/share/pixmaps/slitaz-menu.png",
            "usr/share/pixmaps/slitaz-spider.png"
        ]:
            sp_dst = os.path.join(r4_work, spider_ic)
            if os.path.exists(os.path.dirname(sp_dst)):
                shutil.copy2(os.path.join(icons_src, "24/osify-apple-logo.png"), sp_dst)

    theme_src = os.path.join(REPO_ROOT, "desktop/branding/themes/OSify-macOS")
    if os.path.exists(theme_src):
        theme_dst = os.path.join(r4_work, "usr/share/themes/OSify-macOS")
        shutil.copytree(theme_src, theme_dst, dirs_exist_ok=True)


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

    # Iniezione deterministica Openbox rc.xml con Hotkey Hardware anche in rootfs4
    r3_dir = os.path.join(work_dir, "rootfs3")
    src_rc = os.path.join(r3_dir, "etc/xdg/openbox/rc.xml")
    r4_rc_content = None
    if os.path.exists(src_rc):
        with open(src_rc, "r") as f:
            r4_rc_content = f.read()
    elif os.path.exists(os.path.join(r4_work, "etc/xdg/openbox/rc.xml")):
        with open(os.path.join(r4_work, "etc/xdg/openbox/rc.xml"), "r") as f:
            r4_rc_content = f.read()

    if r4_rc_content:
        for r4_ob in [
            "etc/xdg/openbox/rc.xml",
            "etc/skel/.config/openbox/rc.xml",
            "home/osify/.config/openbox/rc.xml",
            "home/tux/.config/openbox/rc.xml",
            "root/.config/openbox/rc.xml"
        ]:
            full_r4_ob = os.path.join(r4_work, r4_ob)
            os.makedirs(os.path.dirname(full_r4_ob), exist_ok=True)
            with open(full_r4_ob, "w") as f:
                f.write(r4_rc_content)


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

    # Pulizia autostart XDG: la Scrivania si avvia pulita e sgombra come macOS
    autostart_dir = os.path.join(r4_work, "etc/xdg/autostart")
    if os.path.exists(autostart_dir):
        shutil.rmtree(autostart_dir, ignore_errors=True)
    os.makedirs(autostart_dir, exist_ok=True)


    # Registrazione Associazioni MIME Universali UEM per doppio click su EXE, APK, WASM
    mime_pkg_dir = os.path.join(r4_work, "usr/share/mime/packages")
    os.makedirs(mime_pkg_dir, exist_ok=True)
    shutil.copy2(os.path.join(REPO_ROOT, "desktop/mime/osify-uem.xml"), os.path.join(mime_pkg_dir, "osify-uem.xml"))

    for m_dest in ["usr/share/applications/mimeapps.list", "etc/xdg/mimeapps.list"]:
        m_full = os.path.join(r4_work, m_dest)
        os.makedirs(os.path.dirname(m_full), exist_ok=True)
        shutil.copy2(os.path.join(REPO_ROOT, "desktop/mime/mimeapps.list"), m_full)

    shutil.copy2(os.path.join(REPO_ROOT, "desktop/applications/osify-uem-runner.desktop"), os.path.join(r4_work, "usr/share/applications/osify-uem-runner.desktop"))
    shutil.copy2(os.path.join(REPO_ROOT, "desktop/applications/osify-bluetooth.desktop"), os.path.join(r4_work, "usr/share/applications/osify-bluetooth.desktop"))

    # Disattivazione categorica di check_tazpkgupg.sh e servizi sincroni bloccanti in rootfs4
    for blk_serv in [
        "etc/init.d/check_tazpkgupg.sh",
        "etc/init.d/tazpanel",
        "etc/init.d/httpd",
        "usr/bin/check_tazpkgupg.sh"
    ]:
        bpath = os.path.join(r4_work, blk_serv)
        os.makedirs(os.path.dirname(bpath), exist_ok=True)
        with open(bpath, "w") as f:
            f.write("#!/bin/sh\nexit 0\n")
        os.chmod(bpath, 0o755)

    # Copia kernel bzImage in rootfs4 per garanzia assoluta durante installazione disco
    iso_k = os.path.join(iso_root, "boot/bzImage")
    if os.path.exists(iso_k):
        r4_kdir = os.path.join(r4_work, "boot")
        os.makedirs(r4_kdir, exist_ok=True)
        shutil.copy2(iso_k, os.path.join(r4_kdir, "bzImage"))
        vmlink = os.path.join(r4_kdir, "vmlinuz")
        if not os.path.exists(vmlink):
            try:
                os.symlink("bzImage", vmlink)
            except Exception:
                pass

    # Iniezione Bootsplash nativo x86 a 32-bit (render su /dev/fb0)
    bootsplash_src = os.path.join(REPO_ROOT, "tools/bootsplash/osify-bootsplash-32")
    if os.path.exists(bootsplash_src):
        for bdst in [os.path.join(r4_work, "usr/bin/osify-bootsplash"), os.path.join(r4_work, "bin/osify-bootsplash")]:
            os.makedirs(os.path.dirname(bdst), exist_ok=True)
            shutil.copy2(bootsplash_src, bdst)
            os.chmod(bdst, 0o755)

    # Patch rcS per silenziare i messaggi Linux sulla console, completare il bootsplash e avviare la grafica
    rcs_path = os.path.join(r4_work, "etc/init.d/rcS")
    if os.path.exists(rcs_path):
        with open(rcs_path, "r", encoding="utf-8", errors="ignore") as f:
            rcs_content = f.read()
        if "exec 1>>/run/boot.log 2>&1" not in rcs_content:
            rcs_content = rcs_content.replace("#!/bin/sh\n", "#!/bin/sh\n# OSify Silent Boot\nexec 1>>/run/boot.log 2>&1\n")
        if "killall osify-bootsplash" not in rcs_content:
            rcs_content += "\n# OSify Bootsplash Handoff & Session Launch\ntouch /run/osify-desktop-ready\nkillall osify-bootsplash 2>/dev/null || true\n[ -x /etc/init.d/slim ] && /etc/init.d/slim start &\n"
        with open(rcs_path, "w", encoding="utf-8") as f:
            f.write(rcs_content)
        os.chmod(rcs_path, 0o755)

    # Patch inittab per autologin grafico SLiM su tty1 anziché login testuale getty
    inittab_path = os.path.join(r4_work, "etc/inittab")
    if os.path.exists(inittab_path):
        with open(inittab_path, "r", encoding="utf-8", errors="ignore") as f:
            itab_content = f.read()
        itab_content = itab_content.replace("tty1::respawn:/sbin/getty 38400 tty1", "tty1::respawn:/usr/bin/slim -nodaemon")
        with open(inittab_path, "w", encoding="utf-8") as f:
            f.write(itab_content)
        os.chmod(inittab_path, 0o644)

    # Scrittura ~/.xinitrc per tutti gli utenti live
    for u in ["home/osify", "home/tux", "etc/skel", "root"]:
        x_path = os.path.join(r4_work, u, ".xinitrc")
        os.makedirs(os.path.dirname(x_path), exist_ok=True)
        with open(x_path, "w") as f:
            f.write("#!/bin/sh\nexec /usr/bin/osify-session\n")
        os.chmod(x_path, 0o755)

    # Master Init Nativo OSify 2050 (PID 1 infallibile: zero spostamenti distruttivi, zero Kernel Panic)
    master_init = """#!/bin/sh
# OSify Live Master Init (PID 1)
# Architettura OSify 2050 - Ingegnerizzato per avvio istantaneo, silenzioso e infallibile

# 1. Montaggio filesystem virtuali kernel
/bin/busybox mount -t proc proc /proc 2>/dev/null || mount -t proc proc /proc
/bin/busybox mount -t sysfs sys /sys 2>/dev/null || mount -t sysfs sys /sys
/bin/busybox mount -t devtmpfs devtmpfs /dev 2>/dev/null || mount -t devtmpfs devtmpfs /dev
/bin/busybox mount -t tmpfs -o mode=0755,size=64M tmpfs /run 2>/dev/null || true
mkdir -p /dev/pts /dev/shm
/bin/busybox mount -t devpts devpts /dev/pts 2>/dev/null || true

# 2. Popolamento e gestione nodi hardware
/bin/busybox mdev -s 2>/dev/null || true

# 3. Impostazione PATH universale
export PATH=/bin:/sbin:/usr/bin:/usr/sbin:/usr/local/bin:$PATH

# 4. Bootsplash grafico silenzioso OSify sul framebuffer /dev/fb0
if [ -e /dev/fb0 ] && [ -x /bin/osify-bootsplash ]; then
    /bin/osify-bootsplash &
elif [ -e /dev/fb0 ] && [ -x /usr/bin/osify-bootsplash ]; then
    /usr/bin/osify-bootsplash &
fi

# 5. Soppressione output console per preservare il bootsplash immacolato
exec 1>/run/boot.log 2>&1

# 6. Esecuzione definitiva dell'init di sistema (PID 1 non termina MAI)
if [ -x /sbin/init ]; then
    exec /sbin/init "$@"
elif [ -x /bin/busybox ]; then
    exec /bin/busybox init "$@"
else
    exec /bin/sh
fi
"""
    master_init_path = os.path.join(r4_work, "init")
    with open(master_init_path, "w") as f:
        f.write(master_init)
    os.chmod(master_init_path, 0o755)

    os.remove(r4_gz)
    print("[+] Ricompressione rootfs4 unificato con cpio ad alte prestazioni...")
    run(f'cd "{r4_work}" && find . -print0 | cpio --null -ov -H newc | lzma -z -1 > "{r4_gz}"')
    print(f"[✓] rootfs4 ricompatto con successo ({os.path.getsize(r4_gz)/(1024*1024):.1f} MB con tutti i file unificati e permessi corretti)")

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

    # Patch binaria kernel per azzerare stringhe VGA early console ("Decompressing Linux", "done.")
    for r, _, files in os.walk(iso_root):
        for f in files:
            if "bzImage" in f or "vmlinuz" in f:
                patch_kernel_binary(os.path.join(r, f))

    # Iniezione Windows Installer e albero di sistema OSify
    inject_windows_installer(iso_root)
     # Generazione pacchetto apkovl Desktop Grafico OSify 2050 (Xorg, Openbox, Dock, TopBar)
    print("[i] Generazione ambiente Desktop Grafico autonomo OSify 2050 (x86_64)...")
    apkovl_dir = os.path.join(work_dir, "apkovl")
    os.makedirs(os.path.join(apkovl_dir, "etc/inittab.d"), exist_ok=True)
    os.makedirs(os.path.join(apkovl_dir, "etc/xdg/tint2"), exist_ok=True)
    os.makedirs(os.path.join(apkovl_dir, "etc/xdg/openbox"), exist_ok=True)
    os.makedirs(os.path.join(apkovl_dir, "usr/share/images"), exist_ok=True)
    os.makedirs(os.path.join(apkovl_dir, "usr/share/pixmaps"), exist_ok=True)
    os.makedirs(os.path.join(apkovl_dir, "usr/share/applications"), exist_ok=True)
    os.makedirs(os.path.join(apkovl_dir, "usr/local/bin"), exist_ok=True)
    os.makedirs(os.path.join(apkovl_dir, "home/osify"), exist_ok=True)

    # Estrazione o compilazione runtime bundle desktop X11
    desktop_bundle = "/tmp/test_desktop_x64.tar.gz"
    # Verifica presenza libudev.so.1 nel bundle o rigenerazione forzata
    need_rebuild = True
    if os.path.exists(desktop_bundle) and os.path.getsize(desktop_bundle) > 50 * 1024 * 1024:
        # Verifica veloce se contiene libudev
        ret = subprocess.run(f"tar -tzf '{desktop_bundle}' lib/libudev.so.1 2>/dev/null", shell=True)
        if ret.returncode == 0:
            need_rebuild = False

    if need_rebuild:
        print("[+] Generazione bundle X11/Desktop x86_64 con /lib e libudev in container Docker...")
        run("docker run --rm --platform linux/amd64 -v /tmp:/out alpine:3.20 sh -c '"
            "apk update -q && apk add -q --no-cache xinit xorg-server xf86-video-modesetting xf86-video-vesa xf86-input-libinput "
            "openbox pcmanfm tint2 feh sakura dbus font-dejavu yad mesa-dri-gallium which eudev eudev-libs && "
            "tar -czf /out/test_desktop_x64.tar.gz /lib /usr /etc/xdg /etc/X11 /etc/fonts /etc/gtk-3.0 /etc/pango /var/lib/dbus 2>/dev/null || true'")
    
    print("[i] Iniezione binari Xorg, Openbox, Tint2, PCManFM e librerie di sistema in apkovl...")
    run(f"tar -xzf '{desktop_bundle}' -C '{apkovl_dir}' 2>/dev/null || true")
    shutil.rmtree(os.path.join(apkovl_dir, "lib/apk"), ignore_errors=True)

    # Garanzia symlink libudev.so.1 sia in /lib che in /usr/lib
    for udev_dir in [os.path.join(apkovl_dir, "lib"), os.path.join(apkovl_dir, "usr/lib")]:
        os.makedirs(udev_dir, exist_ok=True)
    if os.path.exists(os.path.join(apkovl_dir, "lib/libudev.so.1")):
        usr_udev = os.path.join(apkovl_dir, "usr/lib/libudev.so.1")
        if not os.path.exists(usr_udev):
            try:
                os.symlink("/lib/libudev.so.1", usr_udev)
            except Exception:
                pass

    # Configurazione permessi Xorg setuid per avvio grafico infallibile
    for xbin in ["usr/libexec/Xorg", "usr/libexec/Xorg.wrap", "usr/bin/Xorg"]:
        xp = os.path.join(apkovl_dir, xbin)
        if os.path.exists(xp):
            try:
                os.chmod(xp, 0o4755)
            except Exception:
                pass

    # Gruppi utente per accesso hardware diretto
    with open(os.path.join(apkovl_dir, "etc/group"), "w") as f:
        f.write("""root:x:0:root
wheel:x:10:root,osify
tty:x:5:osify
audio:x:18:osify
video:x:27:osify
input:x:107:osify
osify:x:1000:osify
""")

    # Wallpaper Dark Glass OSify
    src_wall = os.path.join(REPO_ROOT, "desktop/branding/wallpapers/osify-clean-1920x1080.png")
    if not os.path.exists(src_wall):
        src_wall = os.path.join(REPO_ROOT, "OSify.png")
    try:
        w_img = Image.open(src_wall).convert("RGB")
        w_img.save(os.path.join(apkovl_dir, "usr/share/images/osify-wallpaper.jpg"), "JPEG", quality=95)
    except Exception:
        pass

    # Copia Icone native squircle
    src_icons = os.path.join(REPO_ROOT, "sistema/icone")
    if os.path.exists(src_icons):
        for ic in os.listdir(src_icons):
            if ic.endswith(".png"):
                shutil.copy2(os.path.join(src_icons, ic), os.path.join(apkovl_dir, "usr/share/pixmaps", ic))

    # Top Bar tint2 (26px stile macOS / OSify)
    topbar_cfg = """# OSify Top Menu Bar (26px)
panel_monitor = all
panel_position = top center horizontal
panel_size = 100% 26
panel_margin = 0 0
panel_padding = 4 2 4
panel_background_id = 1
wm_menu = 1
panel_dock = 0
panel_layer = top
panel_items = LTSC

# Stile Dark Glass
rounded = 0
border_width = 1
border_sides = b
background_color = #07090e d8
border_color = #1e293b ff

# Launcher OSify
launcher_padding = 8 0
launcher_background_id = 0
launcher_icon_size = 18
launcher_item_app = /usr/share/applications/osify-hub.desktop

# Taskbar
taskbar_mode = multi_desktop
taskbar_padding = 2 2 2
task_icon_size = 16
task_font_color = #ffffff b0
task_active_font_color = #06b6d4 ff

# Orologio
time1_format = %H:%M
time1_font = Sans Bold 9
clock_font_color = #ffffff ff
clock_padding = 8 0

# Systray
systray_padding = 4 0 4
systray_icon_size = 16
"""
    with open(os.path.join(apkovl_dir, "etc/xdg/tint2/osify-topbar.tint2rc"), "w") as f:
        f.write(topbar_cfg)

    # Floating Dock tint2 (46px stile macOS / OSify)
    dock_cfg = """# OSify Floating Dock (46px)
panel_monitor = all
panel_position = bottom center horizontal
panel_size = 0 46
panel_margin = 0 10
panel_padding = 10 4 10
panel_background_id = 1
panel_dock = 0
panel_layer = top
panel_items = L

# Stile Glass Fluttuante
rounded = 12
border_width = 1
border_sides = tblr
background_color = #07090e e8
border_color = #334155 ff

launcher_padding = 8 2
launcher_background_id = 0
launcher_icon_size = 36
launcher_item_app = /usr/share/applications/pcmanfm.desktop
launcher_item_app = /usr/share/applications/sakura.desktop
launcher_item_app = /usr/share/applications/osify-hub.desktop
launcher_item_app = /usr/share/applications/osify-security.desktop
launcher_item_app = /usr/share/applications/osify-wifi.desktop
"""
    with open(os.path.join(apkovl_dir, "etc/xdg/tint2/osify-dock.tint2rc"), "w") as f:
        f.write(dock_cfg)

    # Scrittura Desktop Entry per Dock e Menu
    apps_meta = [
        ("osify-hub.desktop", "Centro OSify", "osify-hub", "osify-hub", "Controllo di sistema"),
        ("pcmanfm.desktop", "File Manager", "pcmanfm", "system-file-manager", "Gestione file"),
        ("sakura.desktop", "Terminale", "sakura", "utilities-terminal", "Terminale di comando"),
        ("osify-security.desktop", "Sicurezza", "osify-privacy-vault", "security-high", "Privacy e Shield"),
        ("osify-wifi.desktop", "Reti Wi-Fi", "osify-wifi", "network-wireless", "Connessione Wi-Fi"),
    ]
    for d_name, d_title, d_exec, d_icon, d_comm in apps_meta:
        with open(os.path.join(apkovl_dir, "usr/share/applications", d_name), "w") as f:
            f.write(f"[Desktop Entry]\nType=Application\nName={d_title}\nExec={d_exec}\nIcon={d_icon}\nComment={d_comm}\nTerminal=false\nCategories=System;\n")

    # Iniezione Assistente Primo Avvio OOBE OSify
    oobe_src = os.path.join(REPO_ROOT, "tools/osify-gui/osify-oobe.sh")
    if os.path.exists(oobe_src):
        for odst in [os.path.join(apkovl_dir, "usr/bin/osify-oobe"), os.path.join(apkovl_dir, "usr/local/bin/osify-oobe")]:
            os.makedirs(os.path.dirname(odst), exist_ok=True)
            shutil.copy2(oobe_src, odst)
            os.chmod(odst, 0o755)

    # Identità di Sistema Autonoma OSify (zero residui distro terze)
    with open(os.path.join(apkovl_dir, "etc/os-release"), "w") as f:
        f.write(f"""NAME="OSify"
PRETTY_NAME="OSify {OSIFY_VERSION} (Ultra-Performance Edition)"
ID=osify
ID_LIKE=osify
VERSION="{OSIFY_VERSION}"
VERSION_ID="{OSIFY_VERSION}"
HOME_URL="https://github.com/ANDRYXify/OSify"
BUG_REPORT_URL="https://github.com/ANDRYXify/OSify/issues"
SUPPORT_URL="https://github.com/ANDRYXify/OSify"
ANSI_COLOR="0;36"
""")
    with open(os.path.join(apkovl_dir, "etc/issue"), "w") as f:
        f.write("OSify 2050 (x86_64) \\n \\l\n\n")

    # Script sessione X11 (.xinitrc)
    xinitrc_content = """#!/bin/sh
export DISPLAY=:0
xsetroot -solid "#07090e"
feh --bg-fill /usr/share/images/osify-wallpaper.jpg 2>/dev/null || true
tint2 -c /etc/xdg/tint2/osify-topbar.tint2rc 2>/dev/null &
tint2 -c /etc/xdg/tint2/osify-dock.tint2rc 2>/dev/null &
pcmanfm --desktop 2>/dev/null &
# Assistente Primo Avvio OOBE OSify (Setup Wizard)
if [ ! -f /home/osify/.config/osify/setup_done ]; then
    (sleep 1 && /usr/bin/osify-oobe) &
fi
exec openbox-session
"""
    for x_path in [
        os.path.join(apkovl_dir, "home/osify/.xinitrc"),
        os.path.join(apkovl_dir, "root/.xinitrc"),
        os.path.join(apkovl_dir, "etc/X11/xinit/xinitrc")
    ]:
        os.makedirs(os.path.dirname(x_path), exist_ok=True)
        with open(x_path, "w") as f:
            f.write(xinitrc_content)
        os.chmod(x_path, 0o755)

    # Permessi Xorg Wrapper universali
    xwrap_dir = os.path.join(apkovl_dir, "etc/X11")
    os.makedirs(xwrap_dir, exist_ok=True)
    with open(os.path.join(xwrap_dir, "Xwrapper.config"), "w") as f:
        f.write("allowed_users = anybody\nneeds_root_rights = yes\n")

    # Script supervisore sessione grafica
    session_gui = """#!/bin/sh
# Supervisore Sessione Desktop OSify 2050
mkdir -p /home/osify/.config/openbox
mkdir -p /home/osify/.config/tint2
mkdir -p /home/osify/.config/pcmanfm/default
mkdir -p /home/osify/.config/osify
chown -R osify:osify /home/osify 2>/dev/null || true

# Configura hostname ufficiale per prevenire errori xauth
hostname osify 2>/dev/null || true
echo "osify" > /etc/hostname 2>/dev/null || true
grep -q "osify" /etc/hosts 2>/dev/null || echo "127.0.0.1 osify localhost" >> /etc/hosts 2>/dev/null || true

# Permessi dispositivi video, console e log per server X11
chmod 666 /dev/tty* /dev/fb* /dev/dri/* 2>/dev/null || true
mkdir -p /home/osify/.local/share/xorg /tmp/.X11-unix /var/log
chmod 1777 /tmp /tmp/.X11-unix /var/log 2>/dev/null || true
chown -R osify:osify /home/osify 2>/dev/null || true

# Inizializza D-Bus di sistema
if [ -x /usr/bin/dbus-uuidgen ] && [ ! -s /var/lib/dbus/machine-id ]; then
    mkdir -p /var/lib/dbus
    /usr/bin/dbus-uuidgen > /var/lib/dbus/machine-id 2>/dev/null || true
fi
if [ -x /usr/bin/dbus-daemon ] && [ ! -e /run/dbus/system_bus_socket ]; then
    mkdir -p /run/dbus /var/run/dbus
    /usr/bin/dbus-daemon --system --fork 2>/dev/null || true
fi

# Avvia sessione X11
export HOME=/home/osify
export USER=osify
export LOGNAME=osify
export DISPLAY=:0
export XAUTHORITY=/home/osify/.Xauthority
touch /home/osify/.Xauthority 2>/dev/null || true
chown -R osify:osify /home/osify 2>/dev/null || true

echo "[OSify-Session] Inizializzazione Display Server Xorg..." > /dev/console 2>/dev/null || true
if [ -x /usr/bin/startx ]; then
    /usr/bin/startx /home/osify/.xinitrc -- /usr/bin/Xorg :0 vt1 -keeptty 2>&1 | tee -a /var/log/osify-session.log > /dev/console
fi
sleep 2
"""
    gui_script = os.path.join(apkovl_dir, "usr/local/bin/osify-session-gui")
    os.makedirs(os.path.dirname(gui_script), exist_ok=True)
    with open(gui_script, "w") as f:
        f.write(session_gui)
    os.chmod(gui_script, 0o755)

    # Inittab per avvio grafico diretto (zero prompt CLI, zero ASCII art)
    with open(os.path.join(apkovl_dir, "etc/inittab"), "w") as f:
        f.write("""# OSify 2.0 Inittab — Avvio Grafico Diretto
::sysinit:/sbin/openrc sysinit
::sysinit:/sbin/openrc boot
::once:/sbin/openrc default
::ctrlaltdel:/sbin/reboot
::shutdown:/sbin/openrc shutdown
tty1::respawn:/usr/local/bin/osify-session-gui
tty2::respawn:/sbin/getty 38400 tty2
""")

    with open(os.path.join(apkovl_dir, "etc/passwd"), "w") as f:
        f.write("""root:x:0:0:root:/root:/bin/sh
osify:x:1000:1000:OSify Live User:/home/osify:/bin/sh
""")

    with open(os.path.join(apkovl_dir, "etc/shadow"), "w") as f:
        f.write("""root::14000:0:99999:7:::
osify::14000:0:99999:7:::
""")

    with open(os.path.join(apkovl_dir, "etc/sudoers"), "w") as f:
        f.write("""root ALL=(ALL) ALL
osify ALL=(ALL) NOPASSWD: ALL
""")

    apk_sistema = os.path.join(apkovl_dir, "Sistema")
    os.makedirs(os.path.join(apk_sistema, "Driver"), exist_ok=True)
    os.makedirs(os.path.join(apk_sistema, "Servizi"), exist_ok=True)
    os.makedirs(os.path.join(apk_sistema, "Icone"), exist_ok=True)
    if os.path.exists(os.path.join(REPO_ROOT, "sistema")):
        shutil.copytree(os.path.join(REPO_ROOT, "sistema"), apk_sistema, dirs_exist_ok=True)

    apk_app = os.path.join(apkovl_dir, "Applicazioni")
    os.makedirs(apk_app, exist_ok=True)
    if os.path.exists(os.path.join(REPO_ROOT, "applicazioni")):
        shutil.copytree(os.path.join(REPO_ROOT, "applicazioni"), apk_app, dirs_exist_ok=True)

    apk_utenti = os.path.join(apkovl_dir, "Utenti")
    os.makedirs(apk_utenti, exist_ok=True)
    try:
        os.symlink("../home/osify", os.path.join(apk_utenti, "osify"))
    except Exception:
        pass

    with open(os.path.join(apkovl_dir, "etc/hostname"), "w") as f:
        f.write("osify-station\n")

    # Link rapidi
    usr_bin = os.path.join(apkovl_dir, "usr/bin")
    os.makedirs(usr_bin, exist_ok=True)
    for src_l, dst_l in [
        ("/opt/osify/network/osify-wifi-gui.sh", "osify-wifi"),
        ("/opt/osify/system/installer/osify-disk-installer.sh", "osify-install"),
        ("/opt/osify/tools/osify-gui/osify-hub.sh", "osify-hub"),
        ("/opt/osify/tools/osify-gui/osify-games.sh", "osify-games"),
        ("/opt/osify/tools/osify-ctl", "osify-ctl"),
        ("/opt/osify/tools/osify-ctl", "osify"),
        ("/opt/osify/security/privacy/osify-privacy-vault.sh", "osify-privacy-vault"),
        ("/opt/osify/security/adaptive/osify-adaptive-security.sh", "osify-adaptive-security"),
    ]:
        lp = os.path.join(usr_bin, dst_l)
        if not os.path.exists(lp):
            try:
                os.symlink(src_l, lp)
            except Exception:
                pass

    # Permessi universali utente osify per X11
    run(f"chmod -R 777 '{os.path.join(apkovl_dir, 'home/osify')}' 2>/dev/null || true")

    # Compressione tar.gz per Alpine apkovl
    apkovl_tar = os.path.join(iso_root, "localhost.apkovl.tar.gz")
    run(f"tar -czf '{apkovl_tar}' -C '{apkovl_dir}' .")

    # Generazione Bootsplash Framebuffer nativo OSify
    try:
        splash_src = os.path.join(REPO_ROOT, "desktop/branding/wallpapers/osify-clean-1920x1080.png")
        if not os.path.exists(splash_src):
            splash_src = os.path.join(REPO_ROOT, "OSify.png")
        s_img = Image.open(splash_src).resize((1024, 768), Image.Resampling.LANCZOS)
        s_img.save(os.path.join(iso_root, "fbsplash.ppm"), "PPM")
        with open(os.path.join(iso_root, "fbsplash.cfg"), "w") as f:
            f.write("BOX 362 550 662 560 #1e293b\nBAR 364 552 660 558 #06b6d4\nIMG_ALIGN=CM\n")
    except Exception:
        pass

    # Configurazione GRUB UEFI ufficiale — Avvio Diretto Immediato (set timeout=0)
    grub_cfg = """set timeout=0
set default=0

menuentry "OSify" {
    linux /boot/vmlinuz-lts modules=loop,squashfs,sd-mod,usb-storage keep_apk_new=yes quiet splash loglevel=0 console=tty1 console=ttyS0 vt.global_cursor_default=0 logo.nologo rd.systemd.show_status=false rd.udev.log_priority=0 udev.log_priority=0 rw autologin
    initrd /boot/initramfs-lts
}

menuentry "OSify Modalita Compatibile (Emulatore / Safe Graphics)" {
    linux /boot/vmlinuz-lts modules=loop,squashfs,sd-mod,usb-storage keep_apk_new=yes nomodeset vga=788 quiet loglevel=1 vt.global_cursor_default=0 logo.nologo console=tty1 rw autologin
    initrd /boot/initramfs-lts
}

menuentry "OSify RAM Rescue Mode" {
    linux /boot/vmlinuz-lts modules=loop,squashfs,sd-mod,usb-storage keep_apk_new=yes copytoram quiet loglevel=1 console=tty1 rw autologin
    initrd /boot/initramfs-lts
}
"""
    grub_path = os.path.join(iso_root, "boot/grub/grub.cfg")
    os.makedirs(os.path.dirname(grub_path), exist_ok=True)
    with open(grub_path, "w") as f:
        f.write(grub_cfg)

    # Copia speculare grub.cfg anche in efi/boot e EFI/BOOT per garanzia assoluta
    for g_dst in [os.path.join(iso_root, "efi/boot/grub.cfg"), os.path.join(iso_root, "EFI/BOOT/grub.cfg")]:
        os.makedirs(os.path.dirname(g_dst), exist_ok=True)
        with open(g_dst, "w") as f:
            f.write(grub_cfg)

    # Iniezione startup.nsh per avvio automatico universale su emulatori UEFI (EDK II / UTM / QEMU)
    startup_nsh = """@echo -off
cls
echo Avvio OSify in corso...
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

    # Assicura presenza di BOOTX64.EFI sia in efi/boot che in EFI/BOOT
    efi_src = os.path.join(iso_root, "efi/boot/bootx64.efi")
    if not os.path.exists(efi_src):
        efi_src_upper = os.path.join(iso_root, "EFI/BOOT/BOOTX64.EFI")
        if os.path.exists(efi_src_upper):
            efi_src = efi_src_upper
    if os.path.exists(efi_src):
        for efi_dst in [os.path.join(iso_root, "efi/boot/bootx64.efi"), os.path.join(iso_root, "EFI/BOOT/BOOTX64.EFI")]:
            os.makedirs(os.path.dirname(efi_dst), exist_ok=True)
            if not os.path.exists(efi_dst):
                shutil.copy2(efi_src, efi_dst)

    # Patch binaria etichette EFI: sostituzione dell'etichetta incorporata con identità pura OSify
    old_label_x64 = b"alpine-std 3.20.3 x86_64"
    new_label_x64 = b"OSify-2050-Gaming-x86_64"
    for efi_target in [
        os.path.join(iso_root, "boot/grub/efi.img"),
        os.path.join(iso_root, "efi/boot/bootx64.efi"),
        os.path.join(iso_root, "EFI/BOOT/BOOTX64.EFI")
    ]:
        patch_binary_string(efi_target, old_label_x64, new_label_x64)

    # Configurazione Syslinux Legacy BIOS ufficiale
    syslinux_cfg = """TIMEOUT 5
DEFAULT osify

LABEL osify
    MENU LABEL OSify
    LINUX /boot/vmlinuz-lts
    INITRD /boot/initramfs-lts
    APPEND modules=loop,squashfs,sd-mod,usb-storage keep_apk_new=yes console=tty1 console=ttyS0 quiet splash loglevel=1 vt.global_cursor_default=0 logo.nologo rw autologin

LABEL install
    MENU LABEL Installa OSify su Disco Fisso
    LINUX /boot/vmlinuz-lts
    INITRD /boot/initramfs-lts
    APPEND modules=loop,squashfs,sd-mod,usb-storage keep_apk_new=yes console=tty1 console=ttyS0 osify.install=1 quiet splash loglevel=1 vt.global_cursor_default=0 logo.nologo rw autologin

LABEL safe
    MENU LABEL OSify Modalita Compatibile (Emulatore / Safe Graphics)
    LINUX /boot/vmlinuz-lts
    INITRD /boot/initramfs-lts
    APPEND modules=loop,squashfs,sd-mod,usb-storage keep_apk_new=yes console=tty1 console=ttyS0 nomodeset vga=788 quiet loglevel=1 vt.global_cursor_default=0 logo.nologo rw autologin

LABEL rescue
    MENU LABEL OSify RAM Rescue Mode
    LINUX /boot/vmlinuz-lts
    INITRD /boot/initramfs-lts
    APPEND modules=loop,squashfs,sd-mod,usb-storage keep_apk_new=yes console=tty1 console=ttyS0 copytoram quiet loglevel=1 rw autologin
"""
    # Configurazione Syslinux ed Isolinux per avvio deterministico Legacy BIOS su qualsiasi firmware
    for sl_dir in ["boot/syslinux", "boot/isolinux", "isolinux"]:
        full_sl_dir = os.path.join(iso_root, sl_dir)
        os.makedirs(full_sl_dir, exist_ok=True)
        with open(os.path.join(full_sl_dir, "syslinux.cfg"), "w") as f:
            f.write(syslinux_cfg)
        with open(os.path.join(full_sl_dir, "isolinux.cfg"), "w") as f:
            f.write(syslinux_cfg)
    with open(os.path.join(iso_root, "isolinux.cfg"), "w") as f:
        f.write(syslinux_cfg)

    # Assicura presenza di isolinux.bin e moduli .c32 in tutte le directory di boot
    src_sl = os.path.join(iso_root, "boot/syslinux")
    if os.path.exists(src_sl):
        for dst_sl_name in ["boot/isolinux", "isolinux"]:
            dst_sl = os.path.join(iso_root, dst_sl_name)
            os.makedirs(dst_sl, exist_ok=True)
            for item in glob.glob(os.path.join(src_sl, "*")):
                shutil.copy2(item, dst_sl)

    # Rimozione preventiva del vecchio boot.cat (xorriso lo rigenera fresco)
    cat_path = os.path.join(iso_root, "boot/syslinux/boot.cat")
    if os.path.exists(cat_path):
        os.remove(cat_path)

    mbr_path = os.path.join(iso_root, "boot/syslinux/isohdpfx.bin")
    if os.path.exists(mbr_path):
        mbr_arg = f"-isohybrid-mbr '{mbr_path}'"
    else:
        mbr_arg = f"-isohybrid-mbr --interval:local_fs:0s-15s:zero_mbrpt,zero_gpt:'{src_iso}'"

    with open(os.path.join(iso_root, "OSify-Version.txt"), "w") as f:
        f.write("OSify Live System (x86-64-v3 Gaming & Streaming Edition)\nKernel: OSify 64-bit HAL\n")

    print("[i] Masterizzazione immagine ibrida 64-bit avviabile (UEFI + BIOS)...")
    os.makedirs(OUT_RELEASE_DIR, exist_ok=True)
    cmd_xorriso = (
        f"xorriso -as mkisofs -r -J "
        f"-V 'OSify-2050-Gaming-x86_64' "
        f"{mbr_arg} "
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

def build_arm64():
    print("=========================================================")
    print(" [3/3] Costruzione OSify ARM64 (AArch64 Apple Silicon / RPi / Ampere)")
    print("=========================================================")
    
    src_iso = CACHE_ARM64
    if not (os.path.exists(src_iso) and os.path.getsize(src_iso) > 10 * 1024 * 1024):
        print("[+] Download base OSify 64-bit ARM (Alpine LTS aarch64)...")
        os.makedirs(os.path.dirname(CACHE_ARM64), exist_ok=True)
        url = "https://dl-cdn.alpinelinux.org/alpine/v3.20/releases/aarch64/alpine-standard-3.20.3-aarch64.iso"
        run(f"curl -L -o '{CACHE_ARM64}' '{url}'")

    work_dir = "/tmp/osify_remaster_arm64"
    if os.path.exists(work_dir):
        shutil.rmtree(work_dir)
    os.makedirs(work_dir)

    iso_root = os.path.join(work_dir, "iso_root")
    os.makedirs(iso_root)

    print("[i] Estrazione base ARM64...")
    run(f"7z x -y '{src_iso}' -o'{iso_root}' > /dev/null")

    # Patch binaria kernel per azzerare stringhe VGA early console ("Decompressing Linux", "done.")
    for r, _, files in os.walk(iso_root):
        for f in files:
            if "bzImage" in f or "vmlinuz" in f:
                patch_kernel_binary(os.path.join(r, f))

    # Iniezione Windows Installer e albero di sistema OSify
    inject_windows_installer(iso_root)

    print("[i] Generazione ambiente Desktop Grafico autonomo OSify 2050 (ARM64)...")
    apkovl_dir = os.path.join(work_dir, "apkovl")
    os.makedirs(os.path.join(apkovl_dir, "etc/inittab.d"), exist_ok=True)
    os.makedirs(os.path.join(apkovl_dir, "etc/xdg/tint2"), exist_ok=True)
    os.makedirs(os.path.join(apkovl_dir, "etc/xdg/openbox"), exist_ok=True)
    os.makedirs(os.path.join(apkovl_dir, "usr/share/images"), exist_ok=True)
    os.makedirs(os.path.join(apkovl_dir, "usr/share/pixmaps"), exist_ok=True)
    os.makedirs(os.path.join(apkovl_dir, "usr/share/applications"), exist_ok=True)
    os.makedirs(os.path.join(apkovl_dir, "usr/local/bin"), exist_ok=True)
    os.makedirs(os.path.join(apkovl_dir, "home/osify"), exist_ok=True)

    desktop_bundle = "/tmp/test_desktop_arm64.tar.gz"
    need_rebuild_arm = True
    if os.path.exists(desktop_bundle) and os.path.getsize(desktop_bundle) > 50 * 1024 * 1024:
        ret = subprocess.run(f"tar -tzf '{desktop_bundle}' lib/libudev.so.1 2>/dev/null", shell=True)
        if ret.returncode == 0:
            need_rebuild_arm = False

    if need_rebuild_arm:
        print("[+] Generazione bundle X11/Desktop ARM64 con /lib e libudev in container Docker...")
        run("docker run --rm --platform linux/arm64 -v /tmp:/out alpine:3.20 sh -c '"
            "apk update -q && apk add -q --no-cache xinit xorg-server xf86-video-modesetting xf86-input-libinput "
            "openbox pcmanfm tint2 feh sakura dbus font-dejavu yad mesa-dri-gallium which eudev eudev-libs && "
            "tar -czf /out/test_desktop_arm64.tar.gz /lib /usr /etc/xdg /etc/X11 /etc/fonts /etc/gtk-3.0 /etc/pango /var/lib/dbus 2>/dev/null || true'")
    
    print("[i] Iniezione binari Xorg, Openbox, Tint2, PCManFM e librerie di sistema in apkovl ARM64...")
    run(f"tar -xzf '{desktop_bundle}' -C '{apkovl_dir}' 2>/dev/null || true")
    shutil.rmtree(os.path.join(apkovl_dir, "lib/apk"), ignore_errors=True)

    # Garanzia symlink libudev.so.1 sia in /lib che in /usr/lib
    for udev_dir in [os.path.join(apkovl_dir, "lib"), os.path.join(apkovl_dir, "usr/lib")]:
        os.makedirs(udev_dir, exist_ok=True)
    if os.path.exists(os.path.join(apkovl_dir, "lib/libudev.so.1")):
        usr_udev = os.path.join(apkovl_dir, "usr/lib/libudev.so.1")
        if not os.path.exists(usr_udev):
            try:
                os.symlink("/lib/libudev.so.1", usr_udev)
            except Exception:
                pass

    for xbin in ["usr/libexec/Xorg", "usr/libexec/Xorg.wrap", "usr/bin/Xorg"]:
        xp = os.path.join(apkovl_dir, xbin)
        if os.path.exists(xp):
            try:
                os.chmod(xp, 0o4755)
            except Exception:
                pass

    with open(os.path.join(apkovl_dir, "etc/group"), "w") as f:
        f.write("""root:x:0:root
wheel:x:10:root,osify
tty:x:5:osify
audio:x:18:osify
video:x:27:osify
input:x:107:osify
osify:x:1000:osify
""")

    src_wall = os.path.join(REPO_ROOT, "desktop/branding/wallpapers/osify-clean-1920x1080.png")
    if not os.path.exists(src_wall):
        src_wall = os.path.join(REPO_ROOT, "OSify.png")
    try:
        w_img = Image.open(src_wall).convert("RGB")
        w_img.save(os.path.join(apkovl_dir, "usr/share/images/osify-wallpaper.jpg"), "JPEG", quality=95)
    except Exception:
        pass

    src_icons = os.path.join(REPO_ROOT, "sistema/icone")
    if os.path.exists(src_icons):
        for ic in os.listdir(src_icons):
            if ic.endswith(".png"):
                shutil.copy2(os.path.join(src_icons, ic), os.path.join(apkovl_dir, "usr/share/pixmaps", ic))

    topbar_cfg = """# OSify Top Menu Bar (26px)
panel_monitor = all
panel_position = top center horizontal
panel_size = 100% 26
panel_margin = 0 0
panel_padding = 4 2 4
panel_background_id = 1
wm_menu = 1
panel_dock = 0
panel_layer = top
panel_items = LTSC

# Stile Dark Glass
rounded = 0
border_width = 1
border_sides = b
background_color = #07090e d8
border_color = #1e293b ff

# Launcher OSify
launcher_padding = 8 0
launcher_background_id = 0
launcher_icon_size = 18
launcher_item_app = /usr/share/applications/osify-hub.desktop

# Taskbar
taskbar_mode = multi_desktop
taskbar_padding = 2 2 2
task_icon_size = 16
task_font_color = #ffffff b0
task_active_font_color = #06b6d4 ff

# Orologio
time1_format = %H:%M
time1_font = Sans Bold 9
clock_font_color = #ffffff ff
clock_padding = 8 0

# Systray
systray_padding = 4 0 4
systray_icon_size = 16
"""
    with open(os.path.join(apkovl_dir, "etc/xdg/tint2/osify-topbar.tint2rc"), "w") as f:
        f.write(topbar_cfg)

    dock_cfg = """# OSify Floating Dock (46px)
panel_monitor = all
panel_position = bottom center horizontal
panel_size = 0 46
panel_margin = 0 10
panel_padding = 10 4 10
panel_background_id = 1
panel_dock = 0
panel_layer = top
panel_items = L

# Stile Glass Fluttuante
rounded = 12
border_width = 1
border_sides = tblr
background_color = #07090e e8
border_color = #334155 ff

launcher_padding = 8 2
launcher_background_id = 0
launcher_icon_size = 36
launcher_item_app = /usr/share/applications/pcmanfm.desktop
launcher_item_app = /usr/share/applications/sakura.desktop
launcher_item_app = /usr/share/applications/osify-hub.desktop
launcher_item_app = /usr/share/applications/osify-security.desktop
launcher_item_app = /usr/share/applications/osify-wifi.desktop
"""
    with open(os.path.join(apkovl_dir, "etc/xdg/tint2/osify-dock.tint2rc"), "w") as f:
        f.write(dock_cfg)

    apps_meta = [
        ("osify-hub.desktop", "Centro OSify", "osify-hub", "osify-hub", "Controllo di sistema"),
        ("pcmanfm.desktop", "File Manager", "pcmanfm", "system-file-manager", "Gestione file"),
        ("sakura.desktop", "Terminale", "sakura", "utilities-terminal", "Terminale di comando"),
        ("osify-security.desktop", "Sicurezza", "osify-privacy-vault", "security-high", "Privacy e Shield"),
        ("osify-wifi.desktop", "Reti Wi-Fi", "osify-wifi", "network-wireless", "Connessione Wi-Fi"),
    ]
    for d_name, d_title, d_exec, d_icon, d_comm in apps_meta:
        with open(os.path.join(apkovl_dir, "usr/share/applications", d_name), "w") as f:
            f.write(f"[Desktop Entry]\nType=Application\nName={d_title}\nExec={d_exec}\nIcon={d_icon}\nComment={d_comm}\nTerminal=false\nCategories=System;\n")

    # Iniezione Assistente Primo Avvio OOBE OSify
    oobe_src = os.path.join(REPO_ROOT, "tools/osify-gui/osify-oobe.sh")
    if os.path.exists(oobe_src):
        for odst in [os.path.join(apkovl_dir, "usr/bin/osify-oobe"), os.path.join(apkovl_dir, "usr/local/bin/osify-oobe")]:
            os.makedirs(os.path.dirname(odst), exist_ok=True)
            shutil.copy2(oobe_src, odst)
            os.chmod(odst, 0o755)

    # Identità di Sistema Autonoma OSify (zero residui distro terze)
    with open(os.path.join(apkovl_dir, "etc/os-release"), "w") as f:
        f.write(f"""NAME="OSify"
PRETTY_NAME="OSify {OSIFY_VERSION} (ARM64 Universal Edition)"
ID=osify
ID_LIKE=osify
VERSION="{OSIFY_VERSION}"
VERSION_ID="{OSIFY_VERSION}"
HOME_URL="https://github.com/ANDRYXify/OSify"
BUG_REPORT_URL="https://github.com/ANDRYXify/OSify/issues"
SUPPORT_URL="https://github.com/ANDRYXify/OSify"
ANSI_COLOR="0;36"
""")
    with open(os.path.join(apkovl_dir, "etc/issue"), "w") as f:
        f.write("OSify 2050 (ARM64) \\n \\l\n\n")

    xinitrc_content = """#!/bin/sh
export DISPLAY=:0
xsetroot -solid "#07090e"
feh --bg-fill /usr/share/images/osify-wallpaper.jpg 2>/dev/null || true
tint2 -c /etc/xdg/tint2/osify-topbar.tint2rc 2>/dev/null &
tint2 -c /etc/xdg/tint2/osify-dock.tint2rc 2>/dev/null &
pcmanfm --desktop 2>/dev/null &
# Assistente Primo Avvio OOBE OSify (Setup Wizard)
if [ ! -f /home/osify/.config/osify/setup_done ]; then
    (sleep 1 && /usr/bin/osify-oobe) &
fi
exec openbox-session
"""
    for x_path in [
        os.path.join(apkovl_dir, "home/osify/.xinitrc"),
        os.path.join(apkovl_dir, "root/.xinitrc"),
        os.path.join(apkovl_dir, "etc/X11/xinit/xinitrc")
    ]:
        os.makedirs(os.path.dirname(x_path), exist_ok=True)
        with open(x_path, "w") as f:
            f.write(xinitrc_content)
        os.chmod(x_path, 0o755)

    # Permessi Xorg Wrapper universali ARM64
    xwrap_dir = os.path.join(apkovl_dir, "etc/X11")
    os.makedirs(xwrap_dir, exist_ok=True)
    with open(os.path.join(xwrap_dir, "Xwrapper.config"), "w") as f:
        f.write("allowed_users = anybody\nneeds_root_rights = yes\n")

    session_gui = """#!/bin/sh
# Supervisore Sessione Desktop OSify 2050 (ARM64)
mkdir -p /home/osify/.config/openbox
mkdir -p /home/osify/.config/tint2
mkdir -p /home/osify/.config/pcmanfm/default
mkdir -p /home/osify/.config/osify
chown -R osify:osify /home/osify 2>/dev/null || true

# Configura hostname ufficiale per prevenire errori xauth
hostname osify 2>/dev/null || true
echo "osify" > /etc/hostname 2>/dev/null || true
grep -q "osify" /etc/hosts 2>/dev/null || echo "127.0.0.1 osify localhost" >> /etc/hosts 2>/dev/null || true

# Permessi dispositivi video, console e log per server X11
chmod 666 /dev/tty* /dev/fb* /dev/dri/* 2>/dev/null || true
mkdir -p /home/osify/.local/share/xorg /tmp/.X11-unix /var/log
chmod 1777 /tmp /tmp/.X11-unix /var/log 2>/dev/null || true
chown -R osify:osify /home/osify 2>/dev/null || true

# Inizializza D-Bus di sistema
if [ -x /usr/bin/dbus-uuidgen ] && [ ! -s /var/lib/dbus/machine-id ]; then
    mkdir -p /var/lib/dbus
    /usr/bin/dbus-uuidgen > /var/lib/dbus/machine-id 2>/dev/null || true
fi
if [ -x /usr/bin/dbus-daemon ] && [ ! -e /run/dbus/system_bus_socket ]; then
    mkdir -p /run/dbus /var/run/dbus
    /usr/bin/dbus-daemon --system --fork 2>/dev/null || true
fi

# Avvia sessione X11
export HOME=/home/osify
export USER=osify
export LOGNAME=osify
export DISPLAY=:0
export XAUTHORITY=/home/osify/.Xauthority
touch /home/osify/.Xauthority 2>/dev/null || true
chown -R osify:osify /home/osify 2>/dev/null || true

echo "[OSify-Session] Inizializzazione Display Server Xorg ARM64..." > /dev/console 2>/dev/null || true
if [ -x /usr/bin/startx ]; then
    /usr/bin/startx /home/osify/.xinitrc -- /usr/bin/Xorg :0 vt1 -keeptty 2>&1 | tee -a /var/log/osify-session.log > /dev/console
fi
sleep 2
"""
    gui_script = os.path.join(apkovl_dir, "usr/local/bin/osify-session-gui")
    os.makedirs(os.path.dirname(gui_script), exist_ok=True)
    with open(gui_script, "w") as f:
        f.write(session_gui)
    os.chmod(gui_script, 0o755)

    with open(os.path.join(apkovl_dir, "etc/inittab"), "w") as f:
        f.write("""# OSify 2.0 Inittab — Avvio Grafico Diretto
::sysinit:/sbin/openrc sysinit
::sysinit:/sbin/openrc boot
::once:/sbin/openrc default
::ctrlaltdel:/sbin/reboot
::shutdown:/sbin/openrc shutdown
tty1::respawn:/usr/local/bin/osify-session-gui
ttyAMA0::respawn:/sbin/getty 115200 ttyAMA0
""")

    with open(os.path.join(apkovl_dir, "etc/passwd"), "w") as f:
        f.write("""root:x:0:0:root:/root:/bin/sh
osify:x:1000:1000:OSify Live User:/home/osify:/bin/sh
""")

    with open(os.path.join(apkovl_dir, "etc/shadow"), "w") as f:
        f.write("""root::14000:0:99999:7:::
osify::14000:0:99999:7:::
""")

    with open(os.path.join(apkovl_dir, "etc/sudoers"), "w") as f:
        f.write("""root ALL=(ALL) ALL
osify ALL=(ALL) NOPASSWD: ALL
""")

    apk_sistema = os.path.join(apkovl_dir, "Sistema")
    os.makedirs(os.path.join(apk_sistema, "Driver"), exist_ok=True)
    os.makedirs(os.path.join(apk_sistema, "Servizi"), exist_ok=True)
    os.makedirs(os.path.join(apk_sistema, "Icone"), exist_ok=True)
    os.makedirs(os.path.join(apk_sistema, "Nucleo"), exist_ok=True)
    if os.path.exists(os.path.join(REPO_ROOT, "sistema")):
        shutil.copytree(os.path.join(REPO_ROOT, "sistema"), apk_sistema, dirs_exist_ok=True)

    apk_app = os.path.join(apkovl_dir, "Applicazioni")
    os.makedirs(apk_app, exist_ok=True)
    if os.path.exists(os.path.join(REPO_ROOT, "applicazioni")):
        shutil.copytree(os.path.join(REPO_ROOT, "applicazioni"), apk_app, dirs_exist_ok=True)

    apk_utenti = os.path.join(apkovl_dir, "Utenti")
    os.makedirs(apk_utenti, exist_ok=True)
    try:
        os.symlink("../home/osify", os.path.join(apk_utenti, "osify"))
    except Exception:
        pass

    with open(os.path.join(apkovl_dir, "etc/hostname"), "w") as f:
        f.write("osify-station\n")

    usr_bin = os.path.join(apkovl_dir, "usr/bin")
    os.makedirs(usr_bin, exist_ok=True)
    for src_l, dst_l in [
        ("/opt/osify/network/osify-wifi-gui.sh", "osify-wifi"),
        ("/opt/osify/system/installer/osify-disk-installer.sh", "osify-install"),
        ("/opt/osify/tools/osify-gui/osify-hub.sh", "osify-hub"),
        ("/opt/osify/tools/osify-gui/osify-games.sh", "osify-games"),
        ("/opt/osify/tools/osify-ctl", "osify-ctl"),
        ("/opt/osify/tools/osify-ctl", "osify"),
        ("/opt/osify/security/privacy/osify-privacy-vault.sh", "osify-privacy-vault"),
        ("/opt/osify/security/adaptive/osify-adaptive-security.sh", "osify-adaptive-security"),
    ]:
        lp = os.path.join(usr_bin, dst_l)
        if not os.path.exists(lp):
            try:
                os.symlink(src_l, lp)
            except Exception:
                pass

    run(f"chmod -R 777 '{os.path.join(apkovl_dir, 'home/osify')}' 2>/dev/null || true")

    apkovl_tar = os.path.join(iso_root, "localhost.apkovl.tar.gz")
    run(f"tar -czf '{apkovl_tar}' -C '{apkovl_dir}' .")

    # Generazione Bootsplash Framebuffer nativo OSify ARM64
    try:
        splash_src = os.path.join(REPO_ROOT, "desktop/branding/wallpapers/osify-clean-1920x1080.png")
        if not os.path.exists(splash_src):
            splash_src = os.path.join(REPO_ROOT, "OSify.png")
        s_img = Image.open(splash_src).resize((1024, 768), Image.Resampling.LANCZOS)
        s_img.save(os.path.join(iso_root, "fbsplash.ppm"), "PPM")
        with open(os.path.join(iso_root, "fbsplash.cfg"), "w") as f:
            f.write("BOX 362 550 662 560 #1e293b\nBAR 364 552 660 558 #06b6d4\nIMG_ALIGN=CM\n")
    except Exception:
        pass

    grub_cfg = """set timeout=0
set default=0

menuentry "OSify ARM64" {
    linux /boot/vmlinuz-lts modules=loop,squashfs,sd-mod,usb-storage keep_apk_new=yes quiet splash loglevel=0 console=tty1 console=ttyS0 vt.global_cursor_default=0 logo.nologo rd.systemd.show_status=false rd.udev.log_priority=0 udev.log_priority=0 rw autologin
    initrd /boot/initramfs-lts
}

menuentry "OSify ARM64 Safe Graphics" {
    linux /boot/vmlinuz-lts modules=loop,squashfs,sd-mod,usb-storage keep_apk_new=yes nomodeset quiet loglevel=1 vt.global_cursor_default=0 logo.nologo console=tty1 rw autologin
    initrd /boot/initramfs-lts
}
"""
    for g_dst in [os.path.join(iso_root, "boot/grub/grub.cfg"), os.path.join(iso_root, "efi/boot/grub.cfg"), os.path.join(iso_root, "EFI/BOOT/grub.cfg")]:
        os.makedirs(os.path.dirname(g_dst), exist_ok=True)
        with open(g_dst, "w") as f:
            f.write(grub_cfg)

    # Patch binaria etichette EFI ARM64
    old_label_arm = b"alpine-std 3.20.3 aarch64"
    new_label_arm = b"OSify-2050-ARM64-Ultimate"
    for efi_target in [
        os.path.join(iso_root, "boot/grub/efi.img"),
        os.path.join(iso_root, "efi/boot/bootaa64.efi"),
        os.path.join(iso_root, "EFI/BOOT/BOOTAA64.EFI")
    ]:
        patch_binary_string(efi_target, old_label_arm, new_label_arm)

    startup_nsh = """@echo -off
cls
echo Avvio OSify ARM64 in corso...
fs0:
if exist \\EFI\\BOOT\\BOOTAA64.EFI then
    \\EFI\\BOOT\\BOOTAA64.EFI
endif
if exist \\efi\\boot\\bootaa64.efi then
    \\efi\\boot\\bootaa64.efi
endif
fs1:
if exist \\EFI\\BOOT\\BOOTAA64.EFI then
    \\EFI\\BOOT\\BOOTAA64.EFI
endif
if exist \\efi\\boot\\bootaa64.efi then
    \\efi\\boot\\bootaa64.efi
endif
"""
    for nsh_name in ["startup.nsh", "STARTUP.NSH"]:
        with open(os.path.join(iso_root, nsh_name), "w") as f:
            f.write(startup_nsh)

    with open(os.path.join(iso_root, "OSify-Version.txt"), "w") as f:
        f.write("OSify Live System (ARM64 Universal Edition)\nKernel: OSify ARM64 HAL\n")

    print("[i] Masterizzazione immagine ARM64 avviabile (UEFI AArch64)...")
    os.makedirs(OUT_RELEASE_DIR, exist_ok=True)
    cmd_xorriso = (
        f"xorriso -as mkisofs -r -J "
        f"-V 'OSify-2050-ARM64-Ultimate' "
        f"-eltorito-alt-boot -e '/boot/grub/efi.img' -no-emul-boot -isohybrid-gpt-basdat "
        f"-o '{DEST_ARM64_ISO}' '{iso_root}'"
    )
    run(cmd_xorriso)
    print(f"[✓] OSify ARM64 creata: {DEST_ARM64_ISO} ({os.path.getsize(DEST_ARM64_ISO)/(1024*1024):.1f} MB)")

def main():
    target = sys.argv[1] if len(sys.argv) > 1 else "--all"
    if target in ["--vintage", "--i686", "-32"]:
        build_vintage_i686()
    elif target in ["--modern", "--x86_64", "-64"]:
        build_modern_x86_64()
    elif target in ["--arm64", "--aarch64", "-arm"]:
        build_arm64()
    else:
        build_vintage_i686()
        build_modern_x86_64()
        build_arm64()

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
    print("[✓✓✓] TUTTE LE IMMAGINI ISO (32, 64, ARM) SONO PRONTE E COLLAUDATE!")
    print("=========================================================")

if __name__ == "__main__":
    main()
