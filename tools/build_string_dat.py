#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
build_string_dat.py
-------------------
Dynamically builds a Thai PUA translated string.dat from the current game's
data.dat and the translation CSV.

Target: Mods/TextDump/string.dat (loaded dynamically by text_dump.dll VFS)
"""

import os
import struct
import json
import pandas as pd

# Paths
STEAM_GAME_DIR = r"C:\Program Files (x86)\Steam\steamapps\common\Village in the Shade"
DATA_DAT_PATH = os.path.join(STEAM_GAME_DIR, "data.dat")
MOD_DIR = os.path.join(STEAM_GAME_DIR, "Mods", "TextDump")
TARGET_STRING_DAT = os.path.join(MOD_DIR, "string.dat")

CSV_PATH = r"C:\Users\Supakiat\Desktop\Mover\QuickBMS\ตารางแปล\string_ตารางจับคู่_ปกติ_vs_MODEN.csv"
MAPPING_JSON_PATH = r"C:\Users\Supakiat\Desktop\Mover\out\Mapping.json"

def main():
    print("=================================================================")
    print(" Building Dynamic Thai PUA string.dat for Village in the Shade")
    print("=================================================================")

    if not os.path.exists(DATA_DAT_PATH):
        raise FileNotFoundError(f"data.dat not found at: {DATA_DAT_PATH}")
    if not os.path.exists(CSV_PATH):
        raise FileNotFoundError(f"Translation CSV not found at: {CSV_PATH}")
    if not os.path.exists(MAPPING_JSON_PATH):
        raise FileNotFoundError(f"Mapping.json not found at: {MAPPING_JSON_PATH}")

    # 1. Load PUA mapping
    print(f"[*] Loading PUA Mapping: {MAPPING_JSON_PATH}")
    with open(MAPPING_JSON_PATH, "r", encoding="utf-8") as f:
        mapping = json.load(f)
    max_len = max(len(k) for k in mapping.keys())
    print(f"    PUA rules: {len(mapping):,}, max rule length: {max_len}")

    def to_pua(text: str) -> str:
        if not text or not isinstance(text, str):
            return ""
        res = []
        i, n = 0, len(text)
        while i < n:
            matched = False
            for l in range(min(max_len, n - i), 0, -1):
                sub = text[i:i+l]
                if sub in mapping:
                    res.append(mapping[sub])
                    i += l
                    matched = True
                    break
            if not matched:
                res.append(text[i])
                i += 1
        return "".join(res)

    # 2. Load Translations
    print(f"[*] Loading CSV translations: {CSV_PATH}")
    df = pd.read_csv(CSV_PATH)
    trans_map = {}
    for _, row in df.iterrows():
        rec_id = int(row["id"])
        th = row["th_switch"]
        if pd.notna(th) and str(th).strip():
            trans_map[rec_id] = to_pua(str(th).strip())
    print(f"    Loaded {len(trans_map):,} translations from CSV")

    # 3. Read current game string.dat from data.dat
    print(f"[*] Extracting clean string.dat from: {DATA_DAT_PATH}")
    with open(DATA_DAT_PATH, "rb") as f:
        # Locate data/database/string.dat in TOC
        magic = f.read(8)
        assert magic == b"FAFULLFS", "Invalid archive magic"
        count, unk, str_off, str_len, toc_off, pad = struct.unpack("<IIQQQQ", f.read(40))
        
        f.seek(toc_off)
        tocs = []
        for _ in range(count):
            h, n_off, u1, sz, off, u2 = struct.unpack("<QQQQQQ", f.read(48))
            tocs.append((off, sz, n_off))
            
        f.seek(str_off)
        str_table = f.read(str_len)
        
        string_dat_off = None
        string_dat_sz = None
        for off, sz, n_off in tocs:
            name = str_table[n_off:].split(b"\x00")[0].decode("latin1")
            if name == "data/database/string.dat":
                string_dat_off = off
                string_dat_sz = sz
                break
                
        assert string_dat_off is not None, "data/database/string.dat not found in TOC"
        f.seek(string_dat_off)
        orig_data = f.read(string_dat_sz)

    print(f"    Found data/database/string.dat at 0x{string_dat_off:X} ({len(orig_data):,} bytes)")

    # 4. Parse Header
    rec_count, rec_data_sz, orig_text_sz, esz = struct.unpack("<4I", orig_data[:16])
    stride = esz + 4
    text_base = 12 + rec_count * stride
    print(f"    Header: records={rec_count}, rec_data_sz={rec_data_sz}, text_sz={orig_text_sz}, esz={esz}")

    # 5. Inject Thai PUA Translations into Slot 1
    new_records = bytearray()
    new_text = bytearray()
    injected_count = 0

    for i in range(rec_count):
        off = 12 + i * stride
        sz, rec_id = struct.unpack("<II", orig_data[off:off+8])
        u = list(struct.unpack(f"<{esz//4}I", orig_data[off+4:off+stride]))
        
        # 8 language slots
        for s in range(8):
            orig_off = u[2 + s * 2]
            orig_len = u[3 + s * 2]
            
            if s == 1 and rec_id in trans_map:
                token = trans_map[rec_id].encode("utf-8")
                injected_count += 1
            else:
                token = orig_data[text_base + orig_off : text_base + orig_off + orig_len]
                
            new_off = len(new_text)
            new_len = len(token)
            u[2 + s * 2] = new_off
            u[3 + s * 2] = new_len
            new_text.extend(token)
            new_text.append(0)  # null terminator

        new_records.extend(struct.pack("<I", esz))
        new_records.extend(struct.pack(f"<{esz//4}I", *u))

    header_12 = struct.pack("<3I", rec_count, rec_data_sz, len(new_text))
    final_data = header_12 + bytes(new_records) + bytes(new_text)

    # 6. Verification
    print("[*] Verifying generated binary...")
    v_count, v_rsz, v_tsz = struct.unpack("<3I", final_data[:12])
    v_esz = struct.unpack("<I", final_data[12:16])[0]
    v_text_base = 12 + v_count * (v_esz + 4)
    assert v_count == rec_count, "Verification failed: record count mismatch"
    assert v_text_base + v_tsz == len(final_data), "Verification failed: file length mismatch"

    # Verify ID 1006 (STR_ID_SAVE_NEW_SLOT_NAME)
    found_1006 = False
    for i in range(rec_count):
        off = 12 + i * stride
        sz, rec_id = struct.unpack("<II", final_data[off:off+8])
        if rec_id == 1006:
            u = struct.unpack(f"<{esz//4}I", final_data[off+4:off+stride])
            k_off, k_len = u[2], u[3]
            s1_off, s1_len = u[4], u[5]
            key = final_data[v_text_base + k_off : v_text_base + k_off + k_len].decode("ascii")
            s1 = final_data[v_text_base + s1_off : v_text_base + s1_off + s1_len].decode("utf-8")
            assert key == "STR_ID_SAVE_NEW_SLOT_NAME"
            assert s1 == trans_map[1006]
            found_1006 = True
            print(f"    Verified STR_ID_SAVE_NEW_SLOT_NAME (1006): {repr(s1)}")
            break
            
    assert found_1006, "ID 1006 not found in output"

    # 7. Write to Target
    os.makedirs(MOD_DIR, exist_ok=True)
    with open(TARGET_STRING_DAT, "wb") as f:
        f.write(final_data)

    # Also save a copy in project directory
    proj_copy = os.path.join(os.path.dirname(__file__), "..", "bin", "string.dat")
    os.makedirs(os.path.dirname(proj_copy), exist_ok=True)
    with open(proj_copy, "wb") as f:
        f.write(final_data)

    print(f"[SUCCESS] Injected {injected_count:,} translations!")
    print(f"[SUCCESS] Saved string.dat to: {TARGET_STRING_DAT} ({len(final_data):,} bytes)")
    print("=================================================================")

if __name__ == "__main__":
    main()
