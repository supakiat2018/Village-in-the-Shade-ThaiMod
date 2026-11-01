#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
convert_onsen_to_nltx.py
-------------------------
Converts edited onsen PNG images into valid NLTX textures for Village in the Shade.
Ensures that transparent pixels (Alpha = 0) retain high-entropy RGB noise
so that LZ4 compression maintains a robust payload size (~8,000 bytes)
matching original DirectX BC7 allocation structures.

Output:
  - C:\\Program Files (x86)\\Steam\\steamapps\\common\\Village in the Shade\\Mods\\TextDump\\textures\\
"""

import os
import sys
import struct
import random
import subprocess
import lz4.block
from PIL import Image

DEFAULT_DEV_DIR = r"C:\Users\Supakiat\Desktop\Village_in_the_Shade_ThaiMod_Dev"
DEFAULT_GAME_DIR = r"C:\Program Files (x86)\Steam\steamapps\common\Village in the Shade"

TEXCONV_EXE = os.path.join(DEFAULT_DEV_DIR, "texconv.exe")
INPUT_DIR = os.path.join(DEFAULT_DEV_DIR, "onsen_textures_original")
OUTPUT_DIR = os.path.join(DEFAULT_GAME_DIR, "Mods", "TextDump", "textures")
SCRATCH_DIR = os.path.join(DEFAULT_DEV_DIR, "scratch")

def apply_transparent_noise(image_path, target_path):
    """
    Reads PNG image. For any pixel where Alpha == 0,
    injects patterned RGB values while strictly keeping Alpha == 0.
    This guarantees 100% visual transparency in-game while preventing
    LZ4 from over-compressing identical empty blocks down to 79 bytes.
    """
    img = Image.open(image_path).convert("RGBA")
    w, h = img.size
    pixels = img.load()
    
    random.seed(42)
    step = 6
    for y in range(h):
        for x in range(w):
            r, g, b, a = pixels[x, y]
            if a == 0:
                # Patterned noise block for transparent background
                rx = (x // step) * step
                ry = (y // step) * step
                noise_r = (rx * 17 + ry * 31 + random.randint(0, 30)) % 256
                noise_g = (rx * 37 + ry * 13 + random.randint(0, 30)) % 256
                noise_b = (rx * 53 + ry * 71 + random.randint(0, 30)) % 256
                pixels[x, y] = (noise_r, noise_g, noise_b, 0)
                
    img.save(target_path)
    return w, h

def encode_png_to_nltx(png_path, out_nltx_path):
    os.makedirs(SCRATCH_DIR, exist_ok=True)
    temp_noisy_png = os.path.join(SCRATCH_DIR, "temp_noisy.png")
    temp_dds = os.path.join(SCRATCH_DIR, "temp_noisy.DDS")
    
    # 1. Apply noise to transparent areas
    w, h = apply_transparent_noise(png_path, temp_noisy_png)
    
    # 2. Encode to BC7 DDS using texconv
    if not os.path.exists(TEXCONV_EXE):
        raise FileNotFoundError(f"texconv.exe not found at: {TEXCONV_EXE}")
        
    cmd = [
        TEXCONV_EXE,
        "-f", "BC7_UNORM",
        "-m", "1",
        "-y",
        "-o", SCRATCH_DIR,
        temp_noisy_png
    ]
    res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if res.returncode != 0:
        raise RuntimeError(f"texconv failed:\n{res.stderr.decode('utf-8', 'ignore')}")
        
    # 3. Read raw BC7 data (skip 148 bytes DDS header)
    with open(temp_dds, "rb") as f:
        dds_data = f.read()
    raw_bc7 = dds_data[148:]
    expected_size = w * h
    if len(raw_bc7) != expected_size:
        raise ValueError(f"Unexpected BC7 payload length: {len(raw_bc7)} (expected {expected_size})")
        
    # 4. Compress BC7 data with LZ4 (Type 9)
    comp_data = lz4.block.compress(raw_bc7, mode="high_compression", store_size=False)
    comp_size = len(comp_data) + 20
    uncomp_size = len(raw_bc7)
    
    # 5. Build YKCMP_V1 header (20 bytes)
    ykcmp_header = struct.pack("<8sIII", b"YKCMP_V1", 9, comp_size, uncomp_size)
    ykcmp_payload = ykcmp_header + comp_data
    
    # 6. Build NMPLTEX1 header (128 bytes)
    nmpl_header = bytearray(128)
    nmpl_header[0:8] = b"NMPLTEX1"
    struct.pack_into("<II", nmpl_header, 0x18, w, h)
    struct.pack_into("<II", nmpl_header, 0x30, len(ykcmp_payload), 128)
    
    full_nltx = bytes(nmpl_header) + ykcmp_payload
    
    # 7. Write final .nltx file
    with open(out_nltx_path, "wb") as f:
        f.write(full_nltx)
        
    # Cleanup temp
    if os.path.exists(temp_noisy_png): os.remove(temp_noisy_png)
    if os.path.exists(temp_dds): os.remove(temp_dds)
    
    return len(full_nltx)

def process_all():
    print("=" * 70)
    print(" Converting Onsen PNGs -> NLTX (Alpha=0 Transparent with LZ4 Noise)")
    print(f" Source: {INPUT_DIR}")
    print(f" Target: {OUTPUT_DIR}")
    print("=" * 70)
    
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    
    targets = [
        "minimap_onsen_aut.png",
        "minimap_onsen_spr.png",
        "minimap_onsen_sum.png",
        "minimap_onsen_win.png"
    ]
    
    success_count = 0
    for fn in targets:
        src = os.path.join(INPUT_DIR, fn)
        if not os.path.exists(src):
            print(f"[!] Warning: {src} not found, skipping...")
            continue
            
        base_name = os.path.splitext(fn)[0] + ".nltx"
        dst = os.path.join(OUTPUT_DIR, base_name)
        
        sz = encode_png_to_nltx(src, dst)
        print(f"[+] Converted: {fn} -> {base_name} ({sz:,} bytes)")
        success_count += 1
        
    print("=" * 70)
    print(f"Successfully converted {success_count} onsen textures to NLTX!")
    print("=" * 70)

if __name__ == "__main__":
    process_all()
