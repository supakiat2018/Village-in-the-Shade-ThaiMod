import os
import sys
import struct
import shutil
import subprocess
import lz4.block
from PIL import Image

DEV_DIR = r"C:\Users\Supakiat\Desktop\Village_in_the_Shade_ThaiMod_Dev"
INPUT_PNG = os.path.join(DEV_DIR, "คียบอด", "tex_113_1024x2048.png")
STEAM_TEXTURES_DIR = r"C:\Program Files (x86)\Steam\steamapps\common\Village in the Shade\Mods\TextDump\textures"
DEV_TEXTURES_DIR = os.path.join(DEV_DIR, "textures")
TEXCONV_PATH = os.path.join(DEV_DIR, "texconv.exe")
TEMP_DIR = os.path.join(DEV_DIR, "temp_pack_kb")

os.makedirs(TEMP_DIR, exist_ok=True)
os.makedirs(STEAM_TEXTURES_DIR, exist_ok=True)
os.makedirs(DEV_TEXTURES_DIR, exist_ok=True)

def convert_png_to_nltx(png_path, out_nltx_path):
    im = Image.open(png_path)
    width, height = im.size
    base_no_ext = os.path.splitext(os.path.basename(png_path))[0]
    dds_path = os.path.join(TEMP_DIR, f"{base_no_ext}.dds")

    print(f"[*] Converting {base_no_ext}.png ({width}x{height}) -> BC7 DDS...")
    cmd = [
        TEXCONV_PATH,
        "-f", "BC7_UNORM",
        "-m", "1",
        "-nologo",
        "-y",
        "-o", TEMP_DIR,
        png_path
    ]
    res = subprocess.run(cmd, capture_output=True, text=True)
    if res.returncode != 0:
        raise RuntimeError(f"texconv error: {res.stderr}")

    with open(dds_path, "rb") as f:
        f.seek(148)
        raw_bc7 = f.read()

    expected_size = width * height
    if len(raw_bc7) != expected_size:
        print(f"  [!] Warning: raw_bc7 size {len(raw_bc7)} != expected {expected_size}")

    print(f"[*] Compressing {base_no_ext} with LZ4 mode=high_compression...")
    comp_data = lz4.block.compress(raw_bc7, mode='high_compression', store_size=False)
    comp_sz = len(comp_data) + 20
    uncomp_sz = len(raw_bc7)

    ykcmp_hdr = struct.pack('<8sIII', b'YKCMP_V1', 9, comp_sz, uncomp_sz)
    payload = ykcmp_hdr + comp_data

    # 128-byte NMPLTEX1 header
    hdr = bytearray(128)
    hdr[0:8] = b'NMPLTEX1'
    struct.pack_into('<I', hdr, 0x10, 0x66)
    struct.pack_into('<I', hdr, 0x14, 0x00800006)
    struct.pack_into('<II', hdr, 0x18, width, height)
    hdr[0x20:0x28] = bytes.fromhex('04 00 FF FF 00 01 01 00')
    struct.pack_into('<I', hdr, 0x2C, uncomp_sz)
    struct.pack_into('<II', hdr, 0x30, len(payload), 128)

    nltx_data = bytes(hdr) + payload
    with open(out_nltx_path, "wb") as f:
        f.write(nltx_data)

    print(f"  [SUCCESS] Generated: {out_nltx_path} ({len(nltx_data):,} bytes)")
    return out_nltx_path

# 1. Convert
out_temp_nltx = os.path.join(TEMP_DIR, "ui_keyboard_font.nltx")
convert_png_to_nltx(INPUT_PNG, out_temp_nltx)

# 2. Deploy names to support both primary and alt filenames
target_names = [
    "ui_keyboard_font.nltx",
    "ui_keyboard_font_thai.nltx",
    "ui_keyboard_tex113.nltx",
    "ui_keyboard_tex113_thai.nltx"
]

for name in target_names:
    dest_dev = os.path.join(DEV_TEXTURES_DIR, name)
    shutil.copy2(out_temp_nltx, dest_dev)
    print(f"  [DEPLOY DEV] -> {dest_dev}")

    dest_steam = os.path.join(STEAM_TEXTURES_DIR, name)
    shutil.copy2(out_temp_nltx, dest_steam)
    print(f"  [DEPLOY STEAM] -> {dest_steam}")

# 3. Clean temp
for f in os.listdir(TEMP_DIR):
    try:
        os.remove(os.path.join(TEMP_DIR, f))
    except:
        pass
try:
    os.rmdir(TEMP_DIR)
except:
    pass

print("\n[+] Thai keyboard texture packaged and deployed successfully!")
