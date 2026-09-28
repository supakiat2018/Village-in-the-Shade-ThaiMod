"""
================================================================================
 Village in the Shade - Title Screen Texture Packer (PNG -> BC7 -> NLTX)
 เครื่องมือแปลงไฟล์ภาพ PNG กลับเป็น .nltx (NMPLTEX1 + YKCMP_V1 + BC7)
================================================================================
"""

import os
import sys
import struct
import subprocess

def check_dependencies():
    required_packages = ["lz4", "texture2ddecoder", "Pillow"]
    missing = []
    for pkg in required_packages:
        try:
            __import__(pkg if pkg != "Pillow" else "PIL")
        except ImportError:
            missing.append(pkg)
    if missing:
        print(f"[*] Installing dependencies: {missing}...")
        subprocess.check_call([sys.executable, "-m", "pip", "install"] + missing)

check_dependencies()

import lz4.block
from PIL import Image

def find_texconv():
    candidates = [
        os.path.join(os.path.dirname(__file__), "texconv.exe"),
        os.path.join(os.path.dirname(__file__), "..", "..", "texconv.exe"),
        os.path.join(os.path.dirname(__file__), "..", "texconv.exe"),
        r"C:\Users\Supakiat\Desktop\Village_in_the_Shade_ThaiMod_Dev\texconv.exe",
    ]
    for p in candidates:
        if os.path.exists(p):
            return os.path.abspath(p)
    return None

def png_to_dds_bc7(png_path, dds_path, texconv_path):
    print(f"[*] Converting {os.path.basename(png_path)} -> BC7 DDS...")
    out_dir = os.path.dirname(dds_path)
    cmd = [
        texconv_path,
        "-f", "BC7_UNORM",
        "-m", "1",
        "-nologo",
        "-y",
        "-o", out_dir,
        png_path
    ]
    res = subprocess.run(cmd, capture_output=True, text=True)
    if res.returncode != 0:
        print(f"[!] texconv error:\n{res.stderr}")
        return False
    
    # Check output filename (texconv outputs with same base name as input)
    base_name = os.path.splitext(os.path.basename(png_path))[0]
    generated_dds = os.path.join(out_dir, f"{base_name}.dds")
    if generated_dds != dds_path and os.path.exists(generated_dds):
        if os.path.exists(dds_path):
            os.remove(dds_path)
        os.rename(generated_dds, dds_path)
        
    return os.path.exists(dds_path)

def pack_nltx(raw_bc7, width, height, template_hdr):
    """
    บีบอัดข้อมูล BC7 ดิบด้วย YKCMP_V1 Type 9 (LZ4) และประกอบเข้ากับ Header NMPLTEX1
    """
    comp_data = lz4.block.compress(raw_bc7, mode='high_compression', store_size=False)
    comp_sz = len(comp_data) + 20
    uncomp_sz = len(raw_bc7)
    
    ykcmp_hdr = struct.pack('<8sIII', b'YKCMP_V1', 9, comp_sz, uncomp_sz)
    payload = ykcmp_hdr + comp_data
    
    hdr = bytearray(template_hdr)
    struct.pack_into('<II', hdr, 0x18, width, height)
    struct.pack_into('<I', hdr, 0x2C, uncomp_sz)
    struct.pack_into('<II', hdr, 0x30, len(payload), 128)
    
    return bytes(hdr) + payload

def main():
    cur_dir = os.path.dirname(os.path.abspath(__file__))
    texconv = find_texconv()
    if not texconv:
        print("[!] Error: texconv.exe not found!")
        return 1

    targets = [
        {
            "name": "ui_1000_title01",
            "png": os.path.join(cur_dir, "ui_1000_title01_thai.png"),
            "dds": os.path.join(cur_dir, "ui_1000_title01_thai.dds"),
            "orig_nltx": os.path.join(cur_dir, "ui_1000_title01.nltx"),
            "out_nltx": os.path.join(cur_dir, "ui_1000_title01.nltx_packed"),
            "target_nltx": os.path.join(cur_dir, "ui_1000_title01.nltx"),
            "width": 2048,
            "height": 512,
        },
        {
            "name": "title_white",
            "png": os.path.join(cur_dir, "title_white_thai.png"),
            "dds": os.path.join(cur_dir, "title_white_thai.dds"),
            "orig_nltx": os.path.join(cur_dir, "title_white.nltx"),
            "out_nltx": os.path.join(cur_dir, "title_white.nltx_packed"),
            "target_nltx": os.path.join(cur_dir, "title_white.nltx"),
            "width": 2048,
            "height": 1280,
        }
    ]

    print("=" * 70)
    print(" Packing Thai Title Textures -> NLTX")
    print("=" * 70)

    for item in targets:
        print(f"\n[*] Processing: {item['name']} ({item['width']}x{item['height']})...")
        if not os.path.exists(item['png']):
            print(f"[!] PNG file not found: {item['png']}")
            continue

        # Convert PNG to DDS
        if not os.path.exists(item['dds']) or os.path.getmtime(item['png']) > os.path.getmtime(item['dds']):
            if not png_to_dds_bc7(item['png'], item['dds'], texconv):
                print(f"[!] Failed to convert {item['png']} to DDS")
                continue
        else:
            print(f"    DDS is up to date: {os.path.basename(item['dds'])}")

        # Read DDS BC7 payload (skip 148 bytes header)
        with open(item['dds'], "rb") as f:
            f.seek(148)
            raw_bc7 = f.read()

        expected_size = item['width'] * item['height']
        if len(raw_bc7) != expected_size:
            print(f"[!] Warning: Raw BC7 size ({len(raw_bc7)}) != expected ({expected_size})")

        # Read template header
        with open(item['orig_nltx'], "rb") as f:
            template_hdr = f.read(128)

        # Pack to NLTX
        nltx_bytes = pack_nltx(raw_bc7, item['width'], item['height'], template_hdr)

        # Save to output files
        with open(item['out_nltx'], "wb") as f:
            f.write(nltx_bytes)

        # Also save as canonical .nltx in current folder
        canon_path = os.path.join(cur_dir, f"{item['name']}.nltx_thai")
        with open(canon_path, "wb") as f:
            f.write(nltx_bytes)

        # Deploy destinations
        dest_dirs = [
            cur_dir,
            os.path.join(cur_dir, "..", "..", "textures"),
            r"C:\Program Files (x86)\Steam\steamapps\common\Village in the Shade\Mods\TextDump\textures",
            r"C:\Program Files (x86)\Steam\steamapps\common\Village in the Shade\Mods\TextDump",
        ]

        for d in dest_dirs:
            if os.path.exists(d):
                p1 = os.path.join(d, f"{item['name']}.nltx")
                p2 = os.path.join(d, f"{item['name']}_thai.nltx")
                with open(p1, "wb") as f:
                    f.write(nltx_bytes)
                with open(p2, "wb") as f:
                    f.write(nltx_bytes)
                print(f"    [DEPLOYED] -> {p1}")

        orig_size = os.path.getsize(item['orig_nltx'])
        new_size = len(nltx_bytes)
        print(f"[+] Successfully packed {item['name']}.nltx:")
        print(f"    Original Size : {orig_size:,} bytes")
        print(f"    New LZ4 Size  : {new_size:,} bytes ({new_size / orig_size * 100:.1f}%)")

    print("\n" + "=" * 70)
    print("[+] All textures packed successfully!")
    print("=" * 70)
    return 0

if __name__ == "__main__":
    sys.exit(main())
