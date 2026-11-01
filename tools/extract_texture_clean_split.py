#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
extract_texture_clean_split.py
--------------------------------
Extracts texture_1_00.dat into two clean, separate subfolders:
1. extracted_texture_1_00/nltx/  -> All 6,143 original .nltx files
2. extracted_texture_1_00/png/   -> All 6,143 decoded .png image files
"""

import os
import sys
import struct
import time
import lz4.block
import texture2ddecoder
from PIL import Image
from concurrent.futures import ThreadPoolExecutor

SOURCE_DAT = r"C:\Program Files (x86)\Steam\steamapps\common\Village in the Shade\data\texture_1_00.dat"
BASE_OUT = r"C:\Users\Supakiat\Desktop\Village_in_the_Shade_ThaiMod_Dev\extracted_texture_1_00"
NLTX_DIR = os.path.join(BASE_OUT, "nltx")
PNG_DIR = os.path.join(BASE_OUT, "png")

def decode_and_save_png(raw_nltx, out_png_path):
    if len(raw_nltx) < 148 or raw_nltx[:8] != b"NMPLTEX1":
        return False
    
    fmt = struct.unpack("<I", raw_nltx[0x14:0x18])[0]
    w, h = struct.unpack("<II", raw_nltx[0x18:0x20])
    doff = struct.unpack("<I", raw_nltx[0x34:0x38])[0]
    
    yk = raw_nltx[doff:doff+20]
    if len(yk) < 20 or yk[:8] != b"YKCMP_V1":
        return False
        
    ptype, comp_sz, uncomp_sz = struct.unpack("<III", yk[8:20])
    comp_data = raw_nltx[doff+20 : doff+comp_sz]
    
    decomp = lz4.block.decompress(comp_data, uncompressed_size=uncomp_sz)
    
    if fmt == 0x2000001:
        # Raw 32-bit RGBA/BGRA
        img = Image.frombytes("RGBA", (w, h), decomp, "raw", "BGRA")
    else:
        # BC7 format
        dec = texture2ddecoder.decode_bc7(decomp, w, h)
        img = Image.frombytes("RGBA", (w, h), dec, "raw", "BGRA")
        
    os.makedirs(os.path.dirname(out_png_path), exist_ok=True)
    img.save(out_png_path)
    return True

def process_item(item):
    rel_path, raw_nltx = item
    
    # 1. Save NLTX
    out_nltx = os.path.join(NLTX_DIR, rel_path)
    os.makedirs(os.path.dirname(out_nltx), exist_ok=True)
    with open(out_nltx, "wb") as f:
        f.write(raw_nltx)
        
    # 2. Decode and save PNG
    png_rel = os.path.splitext(rel_path)[0] + ".png"
    out_png = os.path.join(PNG_DIR, png_rel)
    
    try:
        success = decode_and_save_png(raw_nltx, out_png)
    except Exception as e:
        success = False
        
    return success

def main():
    t0 = time.time()
    print("=" * 80)
    print(" Extracting texture_1_00.dat into separate NLTX and PNG folders")
    print(f" Source:      {SOURCE_DAT}")
    print(f" NLTX Folder: {NLTX_DIR}")
    print(f" PNG Folder:  {PNG_DIR}")
    print("=" * 80)

    if not os.path.exists(SOURCE_DAT):
        raise FileNotFoundError(f"Source file not found: {SOURCE_DAT}")

    os.makedirs(NLTX_DIR, exist_ok=True)
    os.makedirs(PNG_DIR, exist_ok=True)

    with open(SOURCE_DAT, "rb") as f_in:
        hdr = f_in.read(48)
        magic, count, unk, str_off, str_len, toc_off, pad = struct.unpack("<8sIIQQQQ", hdr)
        f_in.seek(str_off)
        str_table = f_in.read(str_len)
        f_in.seek(toc_off)
        tocs = [struct.unpack("<QQQQQQ", f_in.read(48)) for _ in range(count)]

        print(f"[*] Reading and processing {count:,} entries with 4 worker threads...")
        
        # We can read in chunks and process in parallel
        # Read items sequentially (fast disk read), decode in parallel pool
        BATCH_SIZE = 100
        total_processed = 0
        total_png_success = 0
        last_log = time.time()

        with ThreadPoolExecutor(max_workers=4) as executor:
            batch = []
            for idx, entry in enumerate(tocs):
                name_off = entry[1]
                null_pos = str_table.find(b"\x00", name_off)
                rel_name = str_table[name_off:null_pos].decode("latin1", "ignore")
                norm_rel = os.path.normpath(rel_name)
                
                f_in.seek(entry[4])
                raw_bytes = f_in.read(entry[3])
                batch.append((norm_rel, raw_bytes))

                if len(batch) >= BATCH_SIZE or idx == count - 1:
                    results = list(executor.map(process_item, batch))
                    total_processed += len(batch)
                    total_png_success += sum(1 for r in results if r)
                    batch = []

                    if time.time() - last_log > 3 or total_processed == count:
                        pct = (total_processed / count) * 100
                        el = time.time() - t0
                        print(f"    [{pct:5.1f}%] Processed {total_processed:,} / {count:,} files (PNGs: {total_png_success:,}) in {el:.1f}s")
                        last_log = time.time()

    elapsed = time.time() - t0
    print("\n" + "=" * 80)
    print(f" ALL OPERATIONS COMPLETED in {elapsed:.1f}s!")
    print(f" Total NLTX Files Saved: {total_processed:,} in {NLTX_DIR}")
    print(f" Total PNG Images Saved: {total_png_success:,} in {PNG_DIR}")
    print("=" * 80)

if __name__ == "__main__":
    main()
