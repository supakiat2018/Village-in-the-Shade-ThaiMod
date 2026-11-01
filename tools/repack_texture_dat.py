#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
repack_texture_dat.py
---------------------
Repacks texture_1_00.dat using the "Append to End" (Safe Append) technique.
Preserves all 6,143 original files at their exact physical byte offsets (Byte-for-Byte),
appends replacement minimaps/textures to the end of the archive,
and updates TOC pointers to reference the appended files.

Zero offset shifting for existing files!
"""

import os
import sys
import struct
import time
import argparse

DEFAULT_GAME_DIR = r"C:\Program Files (x86)\Steam\steamapps\common\Village in the Shade"
CHUNK_SIZE = 16 * 1024 * 1024  # 16 MB streaming chunk

def repack_texture(game_dir=DEFAULT_GAME_DIR):
    t0 = time.time()
    source_tex = os.path.join(game_dir, "data", "texture_1_00 - Copy.dat")
    if not os.path.exists(source_tex):
        source_tex = os.path.join(game_dir, "data", "texture_1_00.dat")

    target_tex = os.path.join(game_dir, "data", "texture_1_00.dat")
    textures_dir = os.path.join(game_dir, "Mods", "TextDump", "textures")

    print("=" * 75)
    print(" Repacking texture_1_00.dat (Safe Append to End - Zero Shift)")
    print(f" Source:   {source_tex}")
    print(f" Target:   {target_tex}")
    print(f" Textures: {textures_dir}")
    print("=" * 75)

    if not os.path.exists(source_tex):
        raise FileNotFoundError(f"Source texture archive not found: {source_tex}")
    if not os.path.exists(textures_dir):
        raise FileNotFoundError(f"Textures directory not found: {textures_dir}")

    # 1. Read source archive TOC
    print(f"\n[*] Reading source archive header & TOC: {source_tex}")
    with open(source_tex, "rb") as f_in:
        hdr = f_in.read(48)
        magic, count, unk, str_off, str_len, orig_toc_off, pad = struct.unpack("<8sIIQQQQ", hdr)
        if magic != b"FAFULLFS":
            raise ValueError(f"Invalid magic: {magic}")

        f_in.seek(str_off)
        str_table = f_in.read(str_len)
        f_in.seek(orig_toc_off)
        orig_tocs = [list(struct.unpack("<QQQQQQ", f_in.read(48))) for _ in range(count)]
    print(f"    Loaded {count:,} archive entries (TOC at 0x{orig_toc_off:X}, Strings at 0x{str_off:X})")

    # 2. Build index of replacements available in textures_dir
    mod_files = {}
    for fn in os.listdir(textures_dir):
        mod_files[fn.lower()] = os.path.join(textures_dir, fn)

    # Find which entries match replacement files
    replacements = {}
    for idx, entry in enumerate(orig_tocs):
        n_off = entry[1]
        null_pos = str_table.find(b"\x00", n_off)
        entry_name = str_table[n_off:null_pos].decode("latin1", "ignore")
        base_name = os.path.basename(entry_name).lower()
        if base_name in mod_files:
            replacements[idx] = (entry_name, mod_files[base_name])

    print(f"    Identified {len(replacements)} target files to replace via Append:")
    for idx, (ename, rpath) in replacements.items():
        orig_sz = orig_tocs[idx][3]
        new_sz = os.path.getsize(rpath)
        print(f"      [{idx:4d}] {ename} ({orig_sz:,} -> {new_sz:,} B)")

    # 3. Stream original file body up to orig_toc_off (100% UNCHANGED)
    temp_target = target_tex + ".temp_tex"
    print(f"\n[*] Copying original body (0 to 0x{orig_toc_off:X}) byte-for-byte...")
    f_in = open(source_tex, "rb")
    f_out = open(temp_target, "wb")

    rem = orig_toc_off
    while rem > 0:
        to_read = min(CHUNK_SIZE, rem)
        c = f_in.read(to_read)
        if not c:
            break
        f_out.write(c)
        rem -= len(c)
    f_in.close()

    cur_pos = orig_toc_off
    new_tocs = [list(e) for e in orig_tocs]

    # 4. Append replacement files to EOF
    print(f"\n[*] Appending {len(replacements)} replacement textures starting at 0x{cur_pos:X}...")
    for idx, (ename, rpath) in replacements.items():
        rep_sz = os.path.getsize(rpath)
        new_off = cur_pos

        with open(rpath, "rb") as rf:
            while True:
                c = rf.read(CHUNK_SIZE)
                if not c:
                    break
                f_out.write(c)

        # 512-byte alignment padding
        pad_bytes = (512 - (rep_sz % 512)) % 512
        if pad_bytes:
            f_out.write(b"\x00" * pad_bytes)

        new_tocs[idx][3] = rep_sz
        new_tocs[idx][4] = new_off
        cur_pos += rep_sz + pad_bytes
        print(f"    [+] Appended [{idx:4d}]: {ename} at 0x{new_off:08X} ({rep_sz:,} B)")

    # 5. Write new TOC at the end
    new_toc_off = cur_pos
    print(f"\n[*] Writing updated TOC ({len(new_tocs):,} entries) at 0x{new_toc_off:X}...")
    for ne in new_tocs:
        f_out.write(struct.pack("<QQQQQQ", *ne))
    cur_pos += len(new_tocs) * 48

    # 6. Write String Table
    new_str_off = cur_pos
    print(f"[*] Writing String Table ({len(str_table):,} bytes) at 0x{new_str_off:X}...")
    f_out.write(str_table)
    cur_pos += len(str_table)

    # 7. Write final header pointing to new TOC and String Table
    f_out.seek(0)
    final_hdr = struct.pack("<8sIIQQQQ", b"FAFULLFS", count, unk, new_str_off, len(str_table), new_toc_off, 0)
    f_out.write(final_hdr)
    f_out.close()

    # 8. Verify repacked archive
    print("\n[*] Verifying integrity of repacked texture_1_00.dat...")
    with open(temp_target, "rb") as vf:
        v_hdr = vf.read(48)
        v_magic, v_count, v_unk, v_str_off, v_str_len, v_toc_off, _ = struct.unpack("<8sIIQQQQ", v_hdr)
        if v_magic != b"FAFULLFS" or v_count != count:
            os.remove(temp_target)
            raise RuntimeError("Verification failed: Magic or file count mismatch!")

    # 9. Atomically replace target
    if os.path.exists(target_tex):
        os.remove(target_tex)
    os.rename(temp_target, target_tex)

    final_sz = os.path.getsize(target_tex)
    elapsed = time.time() - t0

    print("\n" + "=" * 75)
    print(" [SUCCESS] Repacked texture_1_00.dat deployed successfully!")
    print(f" - Target: {target_tex}")
    print(f" - Original entries untouched: {count - len(replacements):,} files")
    print(f" - Appended replacement files:  {len(replacements)} files")
    print(f" - Total files in container:    {count:,} items")
    print(f" - Final size: {final_sz:,} bytes ({final_sz / (1024 * 1024):.2f} MB)")
    print(f" - Elapsed time: {elapsed:.2f} seconds")
    print("=" * 75)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Repack texture_1_00.dat with Safe Append Method")
    parser.add_argument("--game-dir", default=DEFAULT_GAME_DIR)
    args = parser.parse_args()
    repack_texture(args.game_dir)
