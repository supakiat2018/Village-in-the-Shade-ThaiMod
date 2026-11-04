import os, subprocess, sys, shutil

dev_dir = r"D:\Users\Supakiat\Desktop\Village_in_the_Shade_ThaiMod_Dev"
os.chdir(dev_dir)

minhook_sources = [
    r"src\minhook-master\src\buffer.c",
    r"src\minhook-master\src\hook.c",
    r"src\minhook-master\src\trampoline.c",
    r"src\minhook-master\src\hde\hde64.c"
]

tasks = [
    (
        "text_dump.dll (All-in-One: Thai + Keyboard + Cheats + Speedhack + Hotkeys)",
        ["zig", "cc", "-shared", "-O2", "-s", "-m64", "-DENABLE_THAI_KEYBOARD", "-DENABLE_CHEATS",
         r"src\text_dump.c", r"src\addrsig.c", r"src\cheats.c", r"src\speedhack.c"] + minhook_sources +
        ["-Isrc", "-o", r"bin\text_dump.dll", "-lkernel32", "-luser32", "-lgdi32"]
    ),
    (
        "winmm.dll",
        ["zig", "cc", "-shared", "-O2", "-s", r"src\proxy_winmm.c", r"src\winmm.def",
         "-o", r"bin\winmm.dll", "-lkernel32"]
    )
]

for name, cmd in tasks:
    print(f"[*] Compiling {name}...")
    res = subprocess.run(cmd, capture_output=True, text=True)
    if res.returncode != 0:
        print(f"[ERROR] Failed to compile {name}:")
        print(res.stderr)
        print(res.stdout)
        sys.exit(1)
    else:
        print(f"[OK] Successfully built {name}!")

# Deploy to Active Steam Game Folder
steam_root = r"C:\Program Files (x86)\Steam\steamapps\common\Village in the Shade"
steam_mod  = os.path.join(steam_root, "Mods", "TextDump")
bin_dll    = os.path.join(dev_dir, "bin", "text_dump.dll")
bin_winmm  = os.path.join(dev_dir, "bin", "winmm.dll")
cheats_ini = os.path.join(dev_dir, "cheats.ini")
settings_ini = os.path.join(dev_dir, "settings.ini")
trans_txt  = os.path.join(dev_dir, "translation.txt")

def safe_copy(src, dst):
    try:
        shutil.copy2(src, dst)
    except PermissionError:
        old = dst + ".old"
        if os.path.exists(old):
            try: os.remove(old)
            except: pass
        try:
            if os.path.exists(old):
                os.replace(dst, old)
            else:
                os.rename(dst, old)
        except Exception:
            pass
        shutil.copy2(src, dst)

if os.path.exists(steam_root):
    safe_copy(bin_dll, os.path.join(steam_mod, "text_dump.dll"))
    safe_copy(bin_winmm, os.path.join(steam_root, "winmm.dll"))
    safe_copy(cheats_ini, os.path.join(steam_root, "cheats.ini"))
    safe_copy(settings_ini, os.path.join(steam_root, "settings.ini"))
    if os.path.exists(trans_txt):
        safe_copy(trans_txt, os.path.join(steam_root, "translation.txt"))
    # Ensure no translation.txt remains inside steam_mod (keep it only at steam_root)
    dup_steam_mod_trans = os.path.join(steam_mod, "translation.txt")
    if os.path.exists(dup_steam_mod_trans):
        try: os.remove(dup_steam_mod_trans)
        except: pass
    dup_steam = os.path.join(steam_mod, "cheats.ini")
    if os.path.exists(dup_steam):
        os.remove(dup_steam)
    print(f"[OK] Deployed to Steam Game Directory: {steam_root}")

print("\n[COMPLETE] Unified All-in-One Full build deployed to Steam successfully!")
