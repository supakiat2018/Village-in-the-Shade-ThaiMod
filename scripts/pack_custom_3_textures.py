import os
import sys
import struct
import shutil
import subprocess
import lz4.block
from PIL import Image
from datetime import datetime

DEV_DIR = r"C:\Users\Supakiat\Desktop\Village_in_the_Shade_ThaiMod_Dev"
INPUT_DIR = os.path.join(DEV_DIR, "3ภาพที่แก้ใหม่")
STEAM_TEXTURES_DIR = r"C:\Program Files (x86)\Steam\steamapps\common\Village in the Shade\Mods\TextDump\textures"
DEV_TEXTURES_DIR = os.path.join(DEV_DIR, "textures")
DEV_EDITED_PNG_DIR = os.path.join(DEV_DIR, "01_ภาพที่ม็อดเดิมแก้ไข_ทั้งหมด_65ภาพ", "แก้แล้ว")
TEXCONV_PATH = os.path.join(DEV_DIR, "texconv.exe")
TEMP_DIR = os.path.join(DEV_DIR, "temp_pack")

os.makedirs(TEMP_DIR, exist_ok=True)

# 1. Backup existing Steam textures
backup_dir = os.path.join(os.path.dirname(STEAM_TEXTURES_DIR), f"textures_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}")
os.makedirs(backup_dir, exist_ok=True)
print(f"[*] Creating backup in: {backup_dir}")

target_names = [
    "04_掟の張り紙A.nltx",
    "ui_0020_カレンダー.nltx",
    "ui_0020_カレンダー_thai.nltx",
    "鐘.nltx"
]

for name in target_names:
    src_f = os.path.join(STEAM_TEXTURES_DIR, name)
    if os.path.exists(src_f):
        shutil.copy2(src_f, os.path.join(backup_dir, name))
        print(f"  [+] Backed up: {name}")

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
    struct.pack_into('<I', hdr, 0x20, 0x00010004)
    struct.pack_into('<I', hdr, 0x24, 0x00000101)
    struct.pack_into('<I', hdr, 0x2C, uncomp_sz)
    struct.pack_into('<II', hdr, 0x30, len(payload), 128)

    nltx_data = bytes(hdr) + payload
    with open(out_nltx_path, "wb") as f:
        f.write(nltx_data)

    print(f"  [SUCCESS] Generated: {out_nltx_path} ({len(nltx_data):,} bytes)")
    return out_nltx_path

# Process each image
images_to_process = [
    "04_掟の張り紙A.png",
    "ui_0020_カレンダー.png",
    "鐘.png"
]

for img_name in images_to_process:
    png_path = os.path.join(INPUT_DIR, img_name)
    base_no_ext = os.path.splitext(img_name)[0]
    out_nltx = os.path.join(TEMP_DIR, f"{base_no_ext}.nltx")

    convert_png_to_nltx(png_path, out_nltx)

    # Deploy to Steam Textures
    dest_steam = os.path.join(STEAM_TEXTURES_DIR, f"{base_no_ext}.nltx")
    shutil.copy2(out_nltx, dest_steam)
    print(f"  [DEPLOY STEAM] -> {dest_steam}")

    # If calendar, also deploy ui_0020_カレンダー_thai.nltx
    if base_no_ext == "ui_0020_カレンダー":
        dest_thai = os.path.join(STEAM_TEXTURES_DIR, "ui_0020_カレンダー_thai.nltx")
        shutil.copy2(out_nltx, dest_thai)
        print(f"  [DEPLOY STEAM] -> {dest_thai}")

    # Also deploy to dev textures folders
    dest_dev = os.path.join(DEV_TEXTURES_DIR, f"{base_no_ext}.nltx")
    shutil.copy2(out_nltx, dest_dev)
    print(f"  [DEPLOY DEV] -> {dest_dev}")

    dest_dev_thai = os.path.join(DEV_TEXTURES_DIR, "thai_edited_nltx", f"{base_no_ext}.nltx")
    if os.path.exists(os.path.dirname(dest_dev_thai)):
        shutil.copy2(out_nltx, dest_dev_thai)
        print(f"  [DEPLOY DEV THAI] -> {dest_dev_thai}")

    # Update PNG in dev edited folder
    dest_png = os.path.join(DEV_EDITED_PNG_DIR, img_name)
    shutil.copy2(png_path, dest_png)
    print(f"  [UPDATE DEV PNG] -> {dest_png}")

# Clean up temp dds and temp files
for f in os.listdir(TEMP_DIR):
    try:
        os.remove(os.path.join(TEMP_DIR, f))
    except:
        pass
try:
    os.rmdir(TEMP_DIR)
except:
    pass

print("\n=======================================================")
print(" ALL 3 TEXTURES CONVERTED AND DEPLOYED SUCCESSFULLY!")
print("=======================================================")
