import os
import sys
import struct
import shutil
import subprocess
import time
import lz4.block
from PIL import Image

DEV_DIR = r"C:\Users\Supakiat\Desktop\Village_in_the_Shade_ThaiMod_Dev"
INPUT_DIR = os.path.join(DEV_DIR, "04ภาพen")
OUTPUT_NLTX_DIR = os.path.join(INPUT_DIR, "nltx_thai")
STEAM_TEXTURES_DIR = r"C:\Program Files (x86)\Steam\steamapps\common\Village in the Shade\Mods\TextDump\textures"
DEV_TEXTURES_DIR = os.path.join(DEV_DIR, "textures")
TEXCONV_PATH = os.path.join(DEV_DIR, "texconv.exe")
TEMP_DIR = os.path.join(DEV_DIR, "temp_minimap_pack")

os.makedirs(TEMP_DIR, exist_ok=True)
os.makedirs(OUTPUT_NLTX_DIR, exist_ok=True)
os.makedirs(STEAM_TEXTURES_DIR, exist_ok=True)
os.makedirs(DEV_TEXTURES_DIR, exist_ok=True)

targets = [
    "minimap_01_aut_en.png",
    "minimap_01_spr_en.png",
    "minimap_01_sum_en.png",
    "minimap_01_win_en.png",
    "minimap_11_spr_en.png",
]

def convert_png_to_nltx(png_path, out_nltx_path):
    im = Image.open(png_path)
    width, height = im.size
    base_no_ext = os.path.splitext(os.path.basename(png_path))[0]
    dds_path = os.path.join(TEMP_DIR, f"{base_no_ext}.dds")

    print(f"\n[*] Processing '{base_no_ext}.png' ({width}x{height}, mode={im.mode})...")
    t0 = time.time()

    # 1. Convert to BC7 DDS
    print(f"  [1/3] Converting PNG -> BC7 DDS via texconv...")
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
        raise RuntimeError(f"texconv failed on {png_path}: {res.stderr}")

    with open(dds_path, "rb") as f:
        f.seek(148)
        raw_bc7 = f.read()

    expected_size = width * height
    if len(raw_bc7) != expected_size:
        print(f"  [!] Warning: raw_bc7 size {len(raw_bc7)} != expected {expected_size}")

    # 2. LZ4 Compression
    print(f"  [2/3] Compressing {len(raw_bc7):,} bytes BC7 with LZ4...")
    comp_data = lz4.block.compress(raw_bc7, mode='high_compression', store_size=False)
    comp_sz = len(comp_data) + 20
    uncomp_sz = len(raw_bc7)

    ykcmp_hdr = struct.pack('<8sIII', b'YKCMP_V1', 9, comp_sz, uncomp_sz)
    payload = ykcmp_hdr + comp_data

    # 3. 128-byte NMPLTEX1 header
    print(f"  [3/3] Generating NMPLTEX1 header ({width}x{height})...")
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

    dt = time.time() - t0
    print(f"  [+] SUCCESS: {os.path.basename(out_nltx_path)} ({len(nltx_data):,} bytes) in {dt:.2f}s")
    
    # Clean up DDS
    try:
        os.remove(dds_path)
    except:
        pass

    return out_nltx_path

def main():
    print("=" * 60)
    print(" BATCH PACKING 5 THAI MINIMAP TEXTURES TO NLTX")
    print("=" * 60)

    for png_name in targets:
        png_path = os.path.join(INPUT_DIR, png_name)
        if not os.path.exists(png_path):
            print(f"[-] ERROR: File not found: {png_path}")
            continue

        base_no_ext = os.path.splitext(png_name)[0]
        out_nltx = os.path.join(OUTPUT_NLTX_DIR, f"{base_no_ext}.nltx")

        convert_png_to_nltx(png_path, out_nltx)

        # Deploy to Steam Mod Textures (deploy both _en and non-en names for 100% fail-safe)
        alt_name = base_no_ext.replace("_en", "")
        steam_en = os.path.join(STEAM_TEXTURES_DIR, f"{base_no_ext}.nltx")
        steam_alt = os.path.join(STEAM_TEXTURES_DIR, f"{alt_name}.nltx")

        shutil.copy2(out_nltx, steam_en)
        shutil.copy2(out_nltx, steam_alt)
        print(f"  -> Deployed to Steam: {os.path.basename(steam_en)} & {os.path.basename(steam_alt)}")

        # Deploy to Dev Textures folder
        dev_en = os.path.join(DEV_TEXTURES_DIR, f"{base_no_ext}.nltx")
        dev_alt = os.path.join(DEV_TEXTURES_DIR, f"{alt_name}.nltx")
        shutil.copy2(out_nltx, dev_en)
        shutil.copy2(out_nltx, dev_alt)

    # Clean temp dir
    try:
        shutil.rmtree(TEMP_DIR)
    except:
        pass

    print("\n" + "=" * 60)
    print(" ALL 5 MINIMAP TEXTURES SUCCESSFULLY CONVERTED AND DEPLOYED!")
    print("=" * 60)

if __name__ == '__main__':
    main()
