#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
repack_fairy_dat.py
-------------------
Repacks fairy_1_00.dat using the "Safe Append" technique (identical to Chinese translation mod).
Preserves the entire original body of resident_lang_jp.fad (~248 MB) 100% byte-for-byte,
appends modified Thai UI textures to the end of the FAD, and updates the FAD TOC at 0x1018
to point to the appended textures.

Zero offset shifting for unmodified assets inside the FAD!
"""

import os
import sys
import struct
import re
import time
import argparse

DEFAULT_GAME_DIR = r"C:\Program Files (x86)\Steam\steamapps\common\Village in the Shade"
DEFAULT_DEV_DIR = r"C:\Users\Supakiat\Desktop\Village_in_the_Shade_ThaiMod_Dev"
CHUNK_SIZE = 16 * 1024 * 1024  # 16 MB streaming chunk

def repack_fairy(game_dir=DEFAULT_GAME_DIR, dev_dir=DEFAULT_DEV_DIR):
    t0 = time.time()
    source_fairy = os.path.join(game_dir, "data", "fairy_1_00 - Copy.dat")
    if not os.path.exists(source_fairy):
        source_fairy = os.path.join(game_dir, "data", "fairy_1_00.dat")
    
    target_fairy = os.path.join(game_dir, "data", "fairy_1_00.dat")
    textures_dir = os.path.join(game_dir, "Mods", "TextDump", "textures")
    text_dump_c = os.path.join(dev_dir, "src", "text_dump.c")

    print("=" * 75)
    print(" Repacking fairy_1_00.dat (Safe Append to End - Zero Shift)")
    print(f" Source:   {source_fairy}")
    print(f" Target:   {target_fairy}")
    print(f" Textures: {textures_dir}")
    print("=" * 75)

    if not os.path.exists(source_fairy):
        raise FileNotFoundError(f"Source fairy archive not found: {source_fairy}")
    if not os.path.exists(textures_dir):
        raise FileNotFoundError(f"Textures directory not found: {textures_dir}")

    # 1. Parse g_fad_mapping_defs from src/text_dump.c
    print("[*] Parsing texture mapping definitions from text_dump.c...")
    with open(text_dump_c, "r", encoding="utf-8", errors="ignore") as f:
        c_src = f.read()

    pattern = r'\{\s*(\d+),\s*"([^"]+)",\s*"([^"]+)",\s*(\d+),\s*(\d+)\s*\}'
    matches = re.findall(pattern, c_src)
    print(f"    Found {len(matches)} mapping definitions in text_dump.c")

    # Build replacement dictionary: toc_index -> (chosen_path, width, height)
    replacements = {}
    for idx_str, fn1, fn2, w_str, h_str in matches:
        idx = int(idx_str)
        p1 = os.path.join(textures_dir, fn1)
        p2 = os.path.join(textures_dir, fn2)
        chosen = None
        if os.path.exists(p2):
            chosen = p2
        elif os.path.exists(p1):
            chosen = p1

        if chosen:
            replacements[idx] = (chosen, int(w_str), int(h_str))

    print(f"[*] Found {len(replacements)}/{len(matches)} replacement textures in textures folder")

    # 2. Read source fairy_1_00.dat FAFULLFS header & TOC
    print(f"\n[*] Reading source fairy archive: {source_fairy}")
    f_in = open(source_fairy, "rb")
    hdr = f_in.read(48)
    magic, count, unk, str_off, str_len, toc_off, pad = struct.unpack("<8sIIQQQQ", hdr)
    if magic != b"FAFULLFS":
        f_in.close()
        raise ValueError(f"Invalid magic: {magic}")

    f_in.seek(str_off)
    str_table = f_in.read(str_len)
    f_in.seek(toc_off)
    orig_fairy_toc = [list(struct.unpack("<QQQQQQ", f_in.read(48))) for _ in range(count)]

    # Locate resident_lang_jp.fad in fairy TOC
    jp_fad_idx = None
    for i, entry in enumerate(orig_fairy_toc):
        n_off = entry[1]
        null_pos = str_table.find(b"\x00", n_off)
        name = str_table[n_off:null_pos].decode("latin1", "ignore")
        if "resident_lang_jp.fad" in name:
            jp_fad_idx = i
            break

    if jp_fad_idx is None:
        f_in.close()
        raise RuntimeError("resident_lang_jp.fad not found in fairy_1_00.dat TOC!")

    jp_fad_entry = orig_fairy_toc[jp_fad_idx]
    orig_fad_off = jp_fad_entry[4]
    orig_fad_sz = jp_fad_entry[3]
    print(f"    resident_lang_jp.fad is entry [{jp_fad_idx}]: offset=0x{orig_fad_off:08X}, size={orig_fad_sz:,} bytes")

    # 3. Build resident_lang_jp.fad using Safe Append Method
    temp_fad_path = target_fairy + ".temp_fad"
    print(f"\n[*] Rebuilding resident_lang_jp.fad via Safe Append into: {temp_fad_path}...")
    f_fad_out = open(temp_fad_path, "wb")

    # Step A: Copy original FAD body byte-for-byte (100% UNTOUCHED)
    f_in.seek(orig_fad_off)
    rem = orig_fad_sz
    while rem > 0:
        to_read = min(CHUNK_SIZE, rem)
        c = f_in.read(to_read)
        if not c:
            break
        f_fad_out.write(c)
        rem -= len(c)

    # Step B: Read FAD header (first 0x4000 bytes) to patch TOC
    f_in.seek(orig_fad_off)
    fad_header = bytearray(f_in.read(0x4000))
    fad_count = struct.unpack_from("<Q", fad_header, 0)[0]
    print(f"    Original FAD has {fad_count} subfiles. Original size: {orig_fad_sz:,} bytes")

    # Step C: Append replacement textures to EOF
    cur_rel_off = orig_fad_sz
    replaced_count = 0

    print(f"[*] Appending {len(replacements)} replacement textures starting at FAD+0x{cur_rel_off:X}...")
    for idx in sorted(replacements.keys()):
        if idx >= fad_count:
            print(f"    [!] Skipping idx {idx} (exceeds FAD count {fad_count})")
            continue

        nltx_path, w, h = replacements[idx]
        with open(nltx_path, "rb") as mf:
            nltx_data = mf.read()

        nltx_sz = len(nltx_data)
        new_w, new_h = struct.unpack("<II", nltx_data[0x18:0x20])
        entry_sz = (64 + nltx_sz + 15) & ~15  # 16-byte alignment

        # Read unk1 from original TOC
        pos = 0x1018 + idx * 32
        orig_entry_sz, orig_rel_off, unk1, orig_w, orig_h, unk2 = struct.unpack("<QIIIIQ", fad_header[pos:pos+32])

        # 32-byte subheader
        subhdr = bytearray(32)
        struct.pack_into("<Q", subhdr, 8, entry_sz)
        struct.pack_into("<Q", subhdr, 16, unk1)

        # 32-byte descriptor
        desc = bytearray(32)
        struct.pack_into("<Q", desc, 0, nltx_sz)
        struct.pack_into("<HH", desc, 8, new_w, new_h)
        struct.pack_into("<I", desc, 16, 0x0B010080)
        struct.pack_into("<HH", desc, 20, new_w, new_h)

        pad_len = entry_sz - (64 + nltx_sz)
        payload = bytes(subhdr) + bytes(desc) + nltx_data + (b"\x00" * pad_len)

        # Append payload to EOF
        f_fad_out.write(payload)

        # Update TOC in header to point to appended location
        struct.pack_into("<QIIIIQ", fad_header, pos, entry_sz, cur_rel_off, unk1, new_w, new_h, unk2)

        cur_rel_off += entry_sz
        replaced_count += 1
        fn_display = os.path.basename(nltx_path)
        print(f"    [+] Appended [{idx:3d}]: {fn_display:30s} at FAD+0x{cur_rel_off - entry_sz:08X} ({entry_sz:,} B)")

    # Step D: Overwrite updated FAD header (with patched TOC)
    f_fad_out.seek(0)
    f_fad_out.write(fad_header)
    f_fad_out.close()

    new_fad_sz = cur_rel_off
    print(f"\n    [+] resident_lang_jp.fad completed! New size: {new_fad_sz:,} bytes (injected {replaced_count} textures)")

    # 4. Stream and assemble fairy_1_00.dat
    temp_fairy_path = target_fairy + ".temp_fairy"
    print(f"\n[*] Assembling final fairy_1_00.dat into: {temp_fairy_path}...")
    f_out = open(temp_fairy_path, "wb")
    f_out.write(b"\x00" * 48)  # Reserve header

    cur_fairy_pos = 48
    new_fairy_toc = [list(e) for e in orig_fairy_toc]

    # Sort entries by physical offset to stream sequentially
    fairy_order = []
    for idx, entry in enumerate(orig_fairy_toc):
        fairy_order.append((entry[4], idx))
    fairy_order.sort(key=lambda x: x[0])

    for orig_off, idx in fairy_order:
        entry = orig_fairy_toc[idx]
        orig_sz = entry[3]
        n_off = entry[1]
        null_pos = str_table.find(b"\x00", n_off)
        entry_name = str_table[n_off:null_pos].decode("latin1", "ignore")

        new_off = cur_fairy_pos

        if idx == jp_fad_idx:
            # Stream rebuilt resident_lang_jp.fad
            with open(temp_fad_path, "rb") as rf:
                while True:
                    c = rf.read(CHUNK_SIZE)
                    if not c:
                        break
                    f_out.write(c)
            new_sz = new_fad_sz
            print(f"    [+] Injected resident_lang_jp.fad ({orig_sz:,} -> {new_sz:,} B) at 0x{new_off:08X}")
        else:
            # Copy original entry
            f_in.seek(orig_off)
            rem = orig_sz
            while rem > 0:
                to_read = min(CHUNK_SIZE, rem)
                c = f_in.read(to_read)
                f_out.write(c)
                rem -= len(c)
            new_sz = orig_sz

        cur_fairy_pos += new_sz

        # 512-byte alignment padding
        pad_bytes = (512 - (cur_fairy_pos % 512)) % 512
        if pad_bytes:
            f_out.write(b"\x00" * pad_bytes)
            cur_fairy_pos += pad_bytes

        new_fairy_toc[idx][3] = new_sz
        new_fairy_toc[idx][4] = new_off

    f_in.close()

    # Clean up temp FAD
    if os.path.exists(temp_fad_path):
        os.remove(temp_fad_path)

    # 5. Write new TOC and String Table for fairy_1_00.dat
    new_toc_off = cur_fairy_pos
    for ne in new_fairy_toc:
        f_out.write(struct.pack("<QQQQQQ", *ne))
    cur_fairy_pos += len(new_fairy_toc) * 48

    new_str_off = cur_fairy_pos
    f_out.write(str_table)
    cur_fairy_pos += len(str_table)

    # 6. Write final header
    f_out.seek(0)
    final_hdr = struct.pack("<8sIIQQQQ", b"FAFULLFS", count, unk, new_str_off, len(str_table), new_toc_off, 0)
    f_out.write(final_hdr)
    f_out.close()

    # 7. Verify repacked archive
    print("\n[*] Verifying integrity of repacked fairy_1_00.dat...")
    with open(temp_fairy_path, "rb") as vf:
        v_hdr = vf.read(48)
        v_magic, v_count, v_unk, v_str_off, v_str_len, v_toc_off, _ = struct.unpack("<8sIIQQQQ", v_hdr)
        if v_magic != b"FAFULLFS" or v_count != count:
            os.remove(temp_fairy_path)
            raise RuntimeError("Verification failed: Magic or file count mismatch!")

    # 8. Atomically replace target
    if os.path.exists(target_fairy):
        os.remove(target_fairy)
    os.rename(temp_fairy_path, target_fairy)

    final_sz = os.path.getsize(target_fairy)
    elapsed = time.time() - t0

    print("\n" + "=" * 75)
    print(" [SUCCESS] Repacked fairy_1_00.dat deployed successfully!")
    print(f" - Target: {target_fairy}")
    print(f" - Injected UI textures:  {replaced_count} files (appended to EOF)")
    print(f" - Original assets kept: 100% untouched byte-for-byte")
    print(f" - Final size: {final_sz:,} bytes ({final_sz / (1024 * 1024):.2f} MB)")
    print(f" - Elapsed time: {elapsed:.2f} seconds")
    print("=" * 75)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Repack fairy_1_00.dat with Safe Append Method")
    parser.add_argument("--game-dir", default=DEFAULT_GAME_DIR)
    parser.add_argument("--dev-dir", default=DEFAULT_DEV_DIR)
    args = parser.parse_args()
    repack_fairy(args.game_dir, args.dev_dir)
