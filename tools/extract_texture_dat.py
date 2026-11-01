#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
extract_texture_dat.py
-----------------------
Extracts all 6,143 NLTX texture files from texture_1_00.dat into a separate directory:
C:\\Users\\Supakiat\\Desktop\\Village_in_the_Shade_ThaiMod_Dev\\extracted_texture_1_00
"""

import os
import sys
import struct
import time

SOURCE_DAT = r"C:\Program Files (x86)\Steam\steamapps\common\Village in the Shade\data\texture_1_00.dat"
OUTPUT_DIR = r"C:\Users\Supakiat\Desktop\Village_in_the_Shade_ThaiMod_Dev\extracted_texture_1_00"

def extract_all():
    t0 = time.time()
    print("=" * 80)
    print(" Extracting ALL textures from texture_1_00.dat")
    print(f" Source:      {SOURCE_DAT}")
    print(f" Destination: {OUTPUT_DIR}")
    print("=" * 80)

    if not os.path.exists(SOURCE_DAT):
        raise FileNotFoundError(f"Source file not found: {SOURCE_DAT}")

    os.makedirs(OUTPUT_DIR, exist_ok=True)

    with open(SOURCE_DAT, "rb") as f_in:
        # 1. Read FAFULLFS Header
        hdr = f_in.read(48)
        magic, count, unk, str_off, str_len, toc_off, pad = struct.unpack("<8sIIQQQQ", hdr)
        if magic != b"FAFULLFS":
            raise ValueError(f"Invalid magic: {magic}")

        print(f"[*] Archive Header: Magic={magic.decode()}, File Count={count:,}")
        print(f"[*] Reading String Table at 0x{str_off:08X} ({str_len:,} bytes)...")
        f_in.seek(str_off)
        str_table = f_in.read(str_len)

        print(f"[*] Reading TOC at 0x{toc_off:08X} ({count:,} entries)...")
        f_in.seek(toc_off)
        tocs = [struct.unpack("<QQQQQQ", f_in.read(48)) for _ in range(count)]

        print(f"[*] Beginning extraction of {count:,} texture files...")

        extracted_count = 0
        total_bytes = 0
        last_print = time.time()

        for idx, entry in enumerate(tocs):
            name_off = entry[1]
            null_pos = str_table.find(b"\x00", name_off)
            rel_name = str_table[name_off:null_pos].decode("latin1", "ignore")
            
            # Normalize path for Windows
            norm_rel_path = os.path.normpath(rel_name)
            target_path = os.path.join(OUTPUT_DIR, norm_rel_path)

            file_sz = entry[3]
            file_off = entry[4]

            # Create parent folder if not exists
            parent_dir = os.path.dirname(target_path)
            if not os.path.exists(parent_dir):
                os.makedirs(parent_dir, exist_ok=True)

            # Read and write payload
            f_in.seek(file_off)
            data = f_in.read(file_sz)
            with open(target_path, "wb") as f_out:
                f_out.write(data)

            extracted_count += 1
            total_bytes += len(data)

            if extracted_count % 500 == 0 or idx == count - 1 or (time.time() - last_print > 3):
                elapsed = time.time() - t0
                pct = (extracted_count / count) * 100
                print(f"    [{pct:5.1f}%] Extracted {extracted_count:,} / {count:,} files ({total_bytes / 1024 / 1024:.1f} MB) in {elapsed:.1f}s")
                last_print = time.time()

    elapsed = time.time() - t0
    print("\n" + "=" * 80)
    print(f" EXTRACTION COMPLETE in {elapsed:.1f}s!")
    print(f" Total Files Extracted: {extracted_count:,}")
    print(f" Total Data Size:       {total_bytes:,} bytes ({total_bytes / 1024 / 1024:.2f} MB)")
    print(f" Extracted Directory:   {OUTPUT_DIR}")
    print("=" * 80)

if __name__ == "__main__":
    extract_all()
