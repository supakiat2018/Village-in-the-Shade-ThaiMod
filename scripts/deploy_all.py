import os
import shutil
import subprocess

DEV_DIR     = r'D:\Users\Supakiat\Desktop\Village_in_the_Shade_ThaiMod_Dev'
bin_dll     = os.path.join(DEV_DIR, 'bin', 'text_dump.dll')
winmm_src   = os.path.join(DEV_DIR, 'bin', 'winmm.dll')
cheats_ini  = os.path.join(DEV_DIR, 'cheats.ini')
settings_ini = os.path.join(DEV_DIR, 'settings.ini')
steam_game  = r'C:\Program Files (x86)\Steam\steamapps\common\Village in the Shade'
output_dir  = os.path.join(DEV_DIR, 'output')
desktop_mod = r'C:\Users\Administrator\Desktop\Village in the Shade Mod'

if not os.path.exists(bin_dll):
    # Fallback to text_dump_full.dll if bin_dll not yet named text_dump.dll
    alt_full = os.path.join(DEV_DIR, 'bin', 'text_dump_full.dll')
    if os.path.exists(alt_full):
        shutil.copy2(alt_full, bin_dll)

print("========================================================")
print(" Deploying Unified Single-Edition Thai Mod (v1.30)")
print("========================================================")

def safe_copy(src, dst):
    try:
        shutil.copy2(src, dst)
    except PermissionError:
        # If file is locked by running village.exe, rename old file first then copy
        old_file = dst + ".old"
        try:
            if os.path.exists(old_file):
                os.remove(old_file)
        except Exception:
            pass
        try:
            os.rename(dst, old_file)
            shutil.copy2(src, dst)
        except Exception as e:
            print(f"Warning: could not overwrite locked file {dst}: {e}")

# 1. Deploy to Steam Active Game
steam_textdump = os.path.join(steam_game, 'Mods', 'TextDump')
os.makedirs(steam_textdump, exist_ok=True)
safe_copy(bin_dll, os.path.join(steam_textdump, 'text_dump.dll'))
safe_copy(winmm_src, os.path.join(steam_game, 'winmm.dll'))
if os.path.exists(settings_ini):
    shutil.copy2(settings_ini, os.path.join(steam_game, 'Mods', 'settings.ini'))
if os.path.exists(cheats_ini):
    shutil.copy2(cheats_ini, os.path.join(steam_game, 'Mods', 'cheats.ini'))
# Remove stray ini files and translation.txt in root
for stray in ['settings.ini', 'cheats.ini', 'translation.txt']:
    sp = os.path.join(steam_game, stray)
    if os.path.exists(sp):
        try: os.remove(sp)
        except: pass
print(f"[OK] Deployed to Steam: {steam_game}")

# 2. Deploy to Desktop Mod (Optional / Legacy)
if os.path.exists(desktop_mod):
    core_dir = os.path.join(desktop_mod, 'core')
    mod_textdump = os.path.join(desktop_mod, 'Mods', 'TextDump')
    os.makedirs(core_dir, exist_ok=True)
    os.makedirs(mod_textdump, exist_ok=True)
    shutil.copy2(bin_dll, os.path.join(mod_textdump, 'text_dump.dll'))
    shutil.copy2(winmm_src, os.path.join(desktop_mod, 'winmm.dll'))
    shutil.copy2(bin_dll, os.path.join(core_dir, 'text_dump.dll'))
    shutil.copy2(winmm_src, os.path.join(core_dir, 'winmm.dll'))
    if os.path.exists(settings_ini):
        shutil.copy2(settings_ini, os.path.join(desktop_mod, 'Mods', 'settings.ini'))
    print(f"[OK] Deployed to Desktop Mod: {desktop_mod}")

# 3. Deploy to Output Directory
out_textdump = os.path.join(output_dir, 'Mods', 'TextDump')
os.makedirs(out_textdump, exist_ok=True)
shutil.copy2(bin_dll, os.path.join(out_textdump, 'text_dump.dll'))
shutil.copy2(winmm_src, os.path.join(output_dir, 'winmm.dll'))
if os.path.exists(settings_ini):
    shutil.copy2(settings_ini, os.path.join(output_dir, 'Mods', 'settings.ini'))
print(f"[OK] Deployed to Output: {output_dir}")

# 4. Update ZIP Archive (Single Official Format)
seven_zip = r'C:\Program Files\7-Zip\7z.exe'
zip_path = os.path.join(output_dir, 'Village.in.the.Shade.Thai.Windows.1.30.zip')

if os.path.exists(zip_path) and os.path.exists(seven_zip):
    print("Updating ZIP package...")
    cmd = [seven_zip, 'u', zip_path, 'Mods\\TextDump\\text_dump.dll', 'winmm.dll', 'Mods\\settings.ini', 'Mods\\translations\\*.txt']
    subprocess.run(cmd, cwd=output_dir, stdout=subprocess.DEVNULL)
    # Sync to Steam folder
    shutil.copy2(zip_path, os.path.join(steam_game, 'Village.in.the.Shade.Thai.Windows.1.30.zip'))
    print("[OK] Updated ZIP package in output and Steam!")

print("\nSUCCESS: All targets updated with the unified single-edition build!")
