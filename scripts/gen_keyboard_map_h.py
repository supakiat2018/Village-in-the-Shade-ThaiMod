#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import os, sys, struct
from apply_keyboard_layout import p1_chars, p2_chars

raw_start = 0x3F2D30 - 0x1000 + 0x400
raw_end = 0x3F9D00 - 0x1000 + 0x400

bak_path = r"C:\Program Files (x86)\Steam\steamapps\common\Village in the Shade\village.exe.bak_original"
with open(bak_path, "rb") as f:
    orig_data = f.read()

hiragana_keys = []
katakana_keys = []

for i in range(raw_start, raw_end):
    if orig_data[i] in (0x48, 0x4c) and orig_data[i+1] == 0x8d:
        disp = struct.unpack('<i', orig_data[i+3:i+7])[0]
        curr_rva = i - 0x400 + 0x1000
        dest = curr_rva + 7 + disp
        if 0xE3A000 <= dest <= 0xE3C500:
            str_raw = dest - 0x1800
            if curr_rva < 0x3F4F00:
                hiragana_keys.append((dest, str_raw))
            elif curr_rva < 0x3F6F00:
                katakana_keys.append((dest, str_raw))

entries = []
seen_rvas = set()

for idx, (dest, str_raw) in enumerate(hiragana_keys):
    if dest not in seen_rvas:
        orig_s = orig_data[str_raw:str_raw+4].split(b'\x00')[0].decode('utf-8', errors='ignore')
        entries.append((dest, p1_chars[idx], orig_s))
        seen_rvas.add(dest)

for idx, (dest, str_raw) in enumerate(katakana_keys):
    if dest not in seen_rvas:
        orig_s = orig_data[str_raw:str_raw+4].split(b'\x00')[0].decode('utf-8', errors='ignore')
        entries.append((dest, p2_chars[idx], orig_s))
        seen_rvas.add(dest)

print(f"Total unique entries: {len(entries)}")

header_path = r"C:\Users\Supakiat\Desktop\Village_in_the_Shade_ThaiMod_Dev\src\keyboard_map.h"
with open(header_path, "w", encoding="utf-8") as out:
    out.write("/* Auto-generated verified keyboard mapping for Village in the Shade */\n")
    out.write("#pragma once\n#include <stdint.h>\n#include <string.h>\n\n")
    out.write("typedef struct { uint32_t rva; const char* thai; const char* orig; } KeyPatchEntry;\n\n")
    out.write("static const KeyPatchEntry g_key_patches[] = {\n")
    for dest, thai, orig in entries:
        thai_esc = thai.replace('\\', '\\\\').replace('"', '\\"')
        orig_esc = orig.replace('\\', '\\\\').replace('"', '\\"')
        out.write(f'    {{ 0x{dest:08X}, "{thai_esc}", "{orig_esc}" }},\n')
    out.write("};\n#define NUM_KEY_PATCHES (sizeof(g_key_patches) / sizeof(g_key_patches[0]))\n\n")
    out.write("""static const char* lookup_keyboard_thai_char(const char* orig)
{
    if (!orig || orig[0] == '\\0') return NULL;
    for (size_t i = 0; i < NUM_KEY_PATCHES; i++) {
        if (strcmp(orig, g_key_patches[i].orig) == 0) {
            return g_key_patches[i].thai;
        }
    }
    return NULL;
}
""")

print("Successfully wrote keyboard_map.h!")
