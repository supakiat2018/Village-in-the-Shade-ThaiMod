#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
generate_cmd_pua.py
-------------------
Converts cmd_จับคู่คำแปล_PC_JP_TH.txt into cmd_table_pua.txt
using Mapping.json.
"""

import os
import json
import shutil

SOURCE_FILE = r"C:\Users\Supakiat\Desktop\คลังคำแปล_Village_in_the_Shade\01_PC\cmd_จับคู่คำแปล_PC_JP_TH.txt"
MAPPING_JSON = r"C:\Users\Supakiat\Desktop\Mover\out\Mapping.json"

PROJECT_OUTPUT = r"C:\Users\Supakiat\Desktop\Village-in-the-Shade-ThaiMod\Mods\TextDump\cmd_table_pua.txt"
STEAM_OUTPUT = r"C:\Program Files (x86)\Steam\steamapps\common\Village in the Shade\Mods\TextDump\cmd_table_pua.txt"

def main():
    print(f"[*] Reading mapping: {MAPPING_JSON}")
    with open(MAPPING_JSON, "r", encoding="utf-8") as f:
        mapping = json.load(f)
    max_k = max(len(k) for k in mapping.keys())

    def to_pua(text):
        if not text:
            return ""
        res = []
        i, n = 0, len(text)
        while i < n:
            if text[i] == "<":
                end_tag = text.find(">", i)
                if end_tag != -1:
                    res.append(text[i:end_tag+1])
                    i = end_tag + 1
                    continue
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

    print(f"[*] Reading source: {SOURCE_FILE}")
    entries = []
    with open(SOURCE_FILE, "r", encoding="utf-8", errors="ignore") as f:
        for line in f:
            line = line.strip("\r\n")
            if not line or line.startswith("#"):
                continue
            if "=" in line:
                jp, th = line.split("=", 1)
                jp = jp.strip()
                th = th.strip()
                if not jp or not th:
                    continue
                th_pua = to_pua(th)
                entries.append((jp, th_pua, th))

    print(f"[*] Parsed {len(entries)} entries from cmd.")
    
    # Write project file
    with open(PROJECT_OUTPUT, "w", encoding="utf-8", newline="\n") as out:
        out.write("# cmd PUA Translation Table (File #2)\n")
        out.write(f"# Total entries: {len(entries)}\n")
        out.write("# Format: Original_JP=Translated_TH_PUA\n\n")
        for jp, th_pua, _ in entries:
            out.write(f"{jp}={th_pua}\n")
    print(f"[+] Wrote project file: {PROJECT_OUTPUT}")

    # Synchronize to Steam
    if os.path.exists(os.path.dirname(STEAM_OUTPUT)):
        shutil.copy2(PROJECT_OUTPUT, STEAM_OUTPUT)
        print(f"[+] Synced to Steam: {STEAM_OUTPUT}")

    # Print sample
    print("\n--- First 10 entries ---")
    for jp, th_pua, th_orig in entries[:10]:
        print(f"  {jp} = {th_orig}  (PUA len={len(th_pua)})")

if __name__ == "__main__":
    main()
