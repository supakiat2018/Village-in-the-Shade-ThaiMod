import os
import sys
import struct
import shutil
import subprocess
import lz4.block
from PIL import Image

DEV_DIR = r"C:\Users\Supakiat\Desktop\Village_in_the_Shade_ThaiMod_Dev"
INPUT_DIR = os.path.join(DEV_DIR, "คียบอด", "ภาพไก่ใหม่")
STEAM_TEXTURES_DIR = r"C:\Program Files (x86)\Steam\steamapps\common\Village in the Shade\Mods\TextDump\textures"
DEV_TEXTURES_DIR = os.path.join(DEV_DIR, "textures")
DEV_THAI_NLTX_DIR = os.path.join(DEV_TEXTURES_DIR, "thai_edited_nltx")
DEV_65_DIR = os.path.join(DEV_DIR, "01_ภาพที่ม็อดเดิมแก้ไข_ทั้งหมด_65ภาพ")
DEV_65_FIXED_DIR = os.path.join(DEV_65_DIR, "แก้แล้ว")
TEXCONV_PATH = os.path.join(DEV_DIR, "texconv.exe")
TEMP_DIR = os.path.join(DEV_DIR, "temp_pack_chirashi")

os.makedirs(TEMP_DIR, exist_ok=True)
os.makedirs(STEAM_TEXTURES_DIR, exist_ok=True)
os.makedirs(DEV_TEXTURES_DIR, exist_ok=True)
os.makedirs(DEV_THAI_NLTX_DIR, exist_ok=True)
os.makedirs(DEV_65_FIXED_DIR, exist_ok=True)

ITEMS = [
    (150, "ui_5010_チラシ37"),
    (151, "ui_5010_チラシ38"),
    (152, "ui_5010_チラシ39"),
    (153, "ui_5010_チラシ40"),
]

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

for idx, chirashi_name in ITEMS:
    src_png = os.path.join(INPUT_DIR, f"tex_{idx}_1024x1024.png")
    if not os.path.exists(src_png):
        print(f"[!] File not found: {src_png}")
        continue

    # Also copy PNG to 65 files folder with chirashi naming
    dest_png1 = os.path.join(DEV_65_DIR, f"{chirashi_name}.png")
    shutil.copy2(src_png, dest_png1)
    dest_png2 = os.path.join(DEV_65_FIXED_DIR, f"{chirashi_name}.png")
    shutil.copy2(src_png, dest_png2)
    print(f"[PNG COPY] -> {dest_png1}")

    temp_nltx = os.path.join(TEMP_DIR, f"{chirashi_name}.nltx")
    convert_png_to_nltx(src_png, temp_nltx)

    deploy_names = [
        f"{chirashi_name}.nltx",
        f"{chirashi_name}_thai.nltx",
        f"tex_{idx}_1024x1024.nltx"
    ]

    for name in deploy_names:
        p_steam = os.path.join(STEAM_TEXTURES_DIR, name)
        shutil.copy2(temp_nltx, p_steam)
        print(f"  [DEPLOY STEAM] -> {p_steam}")

        p_dev = os.path.join(DEV_TEXTURES_DIR, name)
        shutil.copy2(temp_nltx, p_dev)
        print(f"  [DEPLOY DEV] -> {p_dev}")

        p_dev_thai = os.path.join(DEV_THAI_NLTX_DIR, name)
        shutil.copy2(temp_nltx, p_dev_thai)

# Clean temp
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
print(" ALL 4 CHIRASHI TEXTURES PACKED AND DEPLOYED!")
print("=======================================================")
