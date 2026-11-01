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
         r"src\text_dump.c", r"src\addrsig.c", r"src\cheats.c"] + minhook_sources +
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

if os.path.exists(steam_root):
    shutil.copy2(bin_dll, os.path.join(steam_mod, "text_dump.dll"))
    shutil.copy2(bin_winmm, os.path.join(steam_root, "winmm.dll"))
    shutil.copy2(cheats_ini, os.path.join(steam_root, "cheats.ini"))
    dup_steam = os.path.join(steam_mod, "cheats.ini")
    if os.path.exists(dup_steam):
        os.remove(dup_steam)
    print(f"[OK] Deployed to Steam Game Directory: {steam_root}")

# Deploy to Desktop Complete Mod Package
desktop_pkg = r"C:\Users\Administrator\Desktop\ม็อดภาษาไทย_เวอร์ชันสมบูรณ์_มีสูตรโกง_v1.30"
if os.path.exists(desktop_pkg):
    pkg_mod = os.path.join(desktop_pkg, "Mods", "TextDump")
    shutil.copy2(bin_dll, os.path.join(pkg_mod, "text_dump.dll"))
    shutil.copy2(bin_winmm, os.path.join(desktop_pkg, "winmm.dll"))
    shutil.copy2(cheats_ini, os.path.join(desktop_pkg, "cheats.ini"))
    dup_pkg = os.path.join(pkg_mod, "cheats.ini")
    if os.path.exists(dup_pkg):
        os.remove(dup_pkg)
    print(f"[OK] Deployed to Desktop Complete Package: {desktop_pkg}")

print("\n[COMPLETE] Unified All-in-One build and deployment finished successfully!")
