import os, shutil

BASE_DEV = r"D:\Users\Supakiat\Desktop\Village_in_the_Shade_ThaiMod_Dev"
BIN_DIR = os.path.join(BASE_DEV, "bin")
OUT_ROOT = os.path.join(BASE_DEV, "MOD_OUTPUT_V130")

single_dir = os.path.join(OUT_ROOT, "Village_in_the_Shade_ThaiMod_v130")
os.makedirs(os.path.join(single_dir, "Mods", "TextDump"), exist_ok=True)

bin_dll = os.path.join(BIN_DIR, "text_dump.dll")
if not os.path.exists(bin_dll):
    bin_dll = os.path.join(BIN_DIR, "text_dump_full.dll")

shutil.copy2(bin_dll, os.path.join(single_dir, "Mods", "TextDump", "text_dump.dll"))
shutil.copy2(os.path.join(BIN_DIR, "winmm.dll"), os.path.join(single_dir, "winmm.dll"))

settings_ini = os.path.join(BASE_DEV, "settings.ini")
if os.path.exists(settings_ini):
    shutil.copy2(settings_ini, os.path.join(single_dir, "settings.ini"))
    shutil.copy2(settings_ini, os.path.join(single_dir, "Mods", "settings.ini"))

print(f"Packaged unified single-edition mod into {single_dir}")
