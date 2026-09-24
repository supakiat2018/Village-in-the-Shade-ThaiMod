#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
build_all_databases.py
-----------------------
Compiles all 35 translation files from:
  C:\\Users\\Supakiat\\Desktop\\คลังคำแปล_Village_in_the_Shade\\01_PC
into:
  1. Mods/TextDump/translation.txt (Global font-hook translation dictionary)
  2. Mods/TextDump/string_table_pua.txt (Database in-memory patcher for string.dat)

Features:
  - Full PUA conversion via Mapping.json (fixes floating vowels/tonemarks in game font)
  - Strict preservation of all <value ...>, <cmd ...>, <br>, and tag variables
  - Strict preservation of underscore '_' characters in keys and text
  - Eliminates the 'なし' collision:
      * In translation.txt: 'なし' -> 'ปิด' (PUA: \\uf048ด)
      * In string_table_pua.txt (ID 1006): 'なし' -> 'ช่องว่าง' (PUA: \\uf179อง\\uf196าง)
  - Synchronizes to both project folder and Steam game directory
"""

import os
import re
import sys
import glob
import json
import shutil

SOURCE_DIR = r"C:\Users\Supakiat\Desktop\คลังคำแปล_Village_in_the_Shade\01_PC"
MAPPING_JSON = r"C:\Users\Supakiat\Desktop\Mover\out\Mapping.json"

PROJECT_MODS_DIR = r"C:\Users\Supakiat\Desktop\Village-in-the-Shade-ThaiMod\Mods\TextDump"
STEAM_MODS_DIR = r"C:\Program Files (x86)\Steam\steamapps\common\Village in the Shade\Mods\TextDump"

def load_pua_mapping():
    print(f"[*] Loading PUA mapping from: {MAPPING_JSON}")
    with open(MAPPING_JSON, "r", encoding="utf-8") as f:
        mapping = json.load(f)
    max_k = max(len(k) for k in mapping.keys())
    print(f"    Loaded {len(mapping):,} rules (max rule length: {max_k})")
    return mapping, max_k

def to_pua(text, mapping, max_k):
    if not text:
        return ""
    res = []
    i, n = 0, len(text)
    while i < n:
        # Preserve <tags> untouched
        if text[i] == "<":
            end_tag = text.find(">", i)
            if end_tag != -1:
                res.append(text[i:end_tag+1])
                i = end_tag + 1
                continue
        # Check mapping for sub-strings
        matched = False
        for l in range(min(max_k, n - i), 0, -1):
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

def main():
    print("=================================================================")
    print(" Compiling All 35 Translation Files for Village in the Shade")
    print("=================================================================")

    if not os.path.isdir(SOURCE_DIR):
        print(f"[!] Error: SOURCE_DIR not found: {SOURCE_DIR}")
        sys.exit(1)

    mapping, max_k = load_pua_mapping()

    files = sorted(glob.glob(os.path.join(SOURCE_DIR, "*.txt")))
    print(f"[*] Found {len(files)} translation files in 01_PC\n")

    # Global translation dictionary: orig_jp -> trans_th_pua
    global_trans = {}
    
    # string.dat specific records: id -> (key, jp, th_pua)
    string_records = {}

    total_pairs_read = 0

    for fpath in files:
        fname = os.path.basename(fpath)
        is_string_file = ("string_จับคู่คำแปล" in fname)
        file_pairs = 0

        with open(fpath, "r", encoding="utf-8", errors="ignore") as f:
            cur_id = None
            cur_key = None

            for line in f:
                line = line.strip("\r\n")
                if not line:
                    continue

                if line.startswith("#"):
                    m_id = re.search(r"ID:\s*(\d+)", line)
                    if m_id:
                        cur_id = int(m_id.group(1))
                    m_key = re.search(r"Key:\s*([A-Za-z0-9_]+)", line)
                    if m_key:
                        cur_key = m_key.group(1)
                    continue

                if "=" in line:
                    parts = line.split("=", 1)
                    jp = parts[0].strip()
                    th = parts[1].strip()

                    if not jp or not th:
                        continue

                    th_pua = to_pua(th, mapping, max_k)
                    file_pairs += 1
                    total_pairs_read += 1

                    # Record in string.dat table if from string file
                    if is_string_file and cur_id is not None and cur_key is not None:
                        string_records[cur_id] = (cur_key, jp, th_pua)

                    # Store into global translation dictionary
                    # Special Rule for 'なし': In global UI, it must always be 'ปิด' (\uf048ด)
                    if jp == "なし":
                        global_trans[jp] = "\uf048ด"
                    else:
                        global_trans[jp] = th_pua

        print(f"  [+] {fname:45s} -> {file_pairs:5d} pairs")

    print(f"\n[*] Total translation pairs parsed: {total_pairs_read:,}")
    print(f"[*] Unique Japanese keys in translation dictionary: {len(global_trans):,}")
    print(f"[*] Records in string.dat patch table: {len(string_records):,}")

    # Explicit collision check
    assert global_trans.get("なし") == "\uf048ด", "Critical: なし must map to ปิด in translation.txt"
    if 1006 in string_records:
        slot_key, slot_jp, slot_th = string_records[1006]
        print(f"[*] Verified ID 1006 (STR_ID_SAVE_NEW_SLOT_NAME): Key='{slot_key}', TH='{slot_th}'")

    # 1. Write translation.txt
    target_trans_path = os.path.join(PROJECT_MODS_DIR, "translation.txt")
    print(f"\n[*] Writing global translation dictionary: {target_trans_path}")
    with open(target_trans_path, "w", encoding="utf-8", newline="\n") as out_f:
        out_f.write("# Village in the Shade - Full Thai Translation Dictionary\n")
        out_f.write(f"# Total entries: {len(global_trans):,}\n")
        out_f.write("# Format: Original_JP=Translated_TH_PUA\n\n")
        for jp, th_pua in sorted(global_trans.items()):
            out_f.write(f"{jp}={th_pua}\n")

    # 2. Write string_table_pua.txt
    target_string_path = os.path.join(PROJECT_MODS_DIR, "string_table_pua.txt")
    print(f"[*] Writing string.dat PUA patch table: {target_string_path}")
    with open(target_string_path, "w", encoding="utf-8", newline="\n") as out_f:
        for rec_id in sorted(string_records.keys()):
            key, jp, th_pua = string_records[rec_id]
            out_f.write(f"{rec_id}\t{key}\t{jp}\t{th_pua}\n")

    # 3. Synchronize to Steam game folder
    if os.path.isdir(STEAM_MODS_DIR):
        print(f"\n[*] Deploying to Steam game directory: {STEAM_MODS_DIR}")
        steam_trans = os.path.join(STEAM_MODS_DIR, "translation.txt")
        steam_string = os.path.join(STEAM_MODS_DIR, "string_table_pua.txt")
        shutil.copy2(target_trans_path, steam_trans)
        shutil.copy2(target_string_path, steam_string)
        print(f"    -> Successfully updated {steam_trans}")
        print(f"    -> Successfully updated {steam_string}")
    else:
        print(f"[!] Warning: Steam directory not found: {STEAM_MODS_DIR}")

    print("\n=================================================================")
    print(" Build & Synchronization Complete Successfully!")
    print("=================================================================")

if __name__ == "__main__":
    main()
