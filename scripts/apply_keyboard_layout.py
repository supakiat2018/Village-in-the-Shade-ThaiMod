#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
apply_keyboard_layout.py
Patches Village in the Shade (village.exe) virtual keyboard tables:
Page 1 (Hiragana) -> Thai Consonants (ก-ฮ), Arabic digits, Thai digits, punctuation
Page 2 (Katakana) -> Thai Vowels, Tone marks, Arabic digits, Thai digits, math symbols
"""

import os
import shutil
import struct

EXE_PATH = r"C:\Program Files (x86)\Steam\steamapps\common\Village in the Shade\village.exe"
BAK_PATH = r"C:\Program Files (x86)\Steam\steamapps\common\Village in the Shade\village.exe.bak_original"

# Ensure backup exists
if not os.path.exists(BAK_PATH):
    shutil.copy2(EXE_PATH, BAK_PATH)
    print(f"Created backup at {BAK_PATH}")
else:
    print(f"Backup already exists at {BAK_PATH}")

with open(BAK_PATH, "rb") as f:
    exe_data = bytearray(f.read())

raw_start = 0x3F2D30 - 0x1000 + 0x400
raw_end = 0x3F9D00 - 0x1000 + 0x400

hiragana_keys = []
katakana_keys = []

for i in range(raw_start, raw_end):
    if exe_data[i] in (0x48, 0x4c) and exe_data[i+1] == 0x8d:
        disp = struct.unpack('<i', exe_data[i+3:i+7])[0]
        curr_rva = i - 0x400 + 0x1000
        dest = curr_rva + 7 + disp
        if 0xE3A000 <= dest <= 0xE3C500:
            str_raw = dest - 0x1800
            if curr_rva < 0x3F4F00:
                hiragana_keys.append((dest, str_raw))
            elif curr_rva < 0x3F6F00:
                katakana_keys.append((dest, str_raw))

print(f"Found {len(hiragana_keys)} Hiragana keys and {len(katakana_keys)} Katakana keys.")
assert len(hiragana_keys) == 91
assert len(katakana_keys) == 91

# Page 1: Consonants (ก-ฮ) + Digits
p1_chars = [
    # Row 1 (Cols 1-5 Left, Cols 6,8,10 Mid, Cols 11-15 Right)
    'ก', 'ข', 'ฃ', 'ค', 'ฅ',      'ล', 'ว', 'ศ',      '๐', '๑', '๒', '๓', '๔',
    # Row 2
    'ฆ', 'ง', 'จ', 'ฉ', 'ช',      'ษ', 'ส', 'ห', 'ฬ', 'อ',      '๕', '๖', '๗', '๘', '๙',
    # Row 3
    'ซ', 'ฌ', 'ญ', 'ฎ', 'ฏ',      'ฮ', ' ', '.',      '(', ')', '[', ']', '{',
    # Row 4
    'ฐ', 'ฑ', 'ฒ', 'ณ', 'ด',      '0', '1', '2', '3', '4',      '}', '+', '=', '*', ':',
    # Row 5
    'ต', 'ถ', 'ท', 'ธ', 'น',      '5', '6', '7', '8', '9',      ';', '"', "'", '<', '>',
    # Row 6
    'บ', 'ป', 'ผ', 'ฝ', 'พ',      ',', '-', '!', '?', '/',      'ー', '～', '＝', '♥', '★',
    # Row 7
    'ฟ', 'ภ', 'ม', 'ย', 'ร'
]

# Page 2: Vowels, Tone marks, Digits, Math symbols
p2_chars = [
    # Row 1
    'ะ', 'า', 'ำ', 'ิ', 'ี',      '0', '1', '2',      '๐', '๑', '๒', '๓', '๔',
    # Row 2
    'ึ', 'ื', 'ุ', 'ู', 'เ',      '3', '4', '5', '6', '7',      '๕', '๖', '๗', '๘', '๙',
    # Row 3
    'แ', 'โ', 'ใ', 'ไ', '็',      '8', '9', ' ',      '[', ']', '{', '}', '<',
    # Row 4
    'ั', '่', '้', '๊', '๋',      '+', '-', '*', '/', '=',      '>', '"', "'", ':', ';',
    # Row 5
    '์', 'ๆ', 'ฯ', 'ฺ', 'ํ',      '%', '^', '&', '(', ')',      '~', '\\', '|', '_', '฿',
    # Row 6
    '๎', '๏', '๚', '๛', '฿',      ',', '-', '!', '?', '/',      'ー', '～', '＝', '♥', '★',
    # Row 7
    'ฤ', 'ฦ', '.', ',', '-'
]

assert len(p1_chars) == 91
assert len(p2_chars) == 91

patched_offsets = set()

def patch_key(str_raw, char_str, label):
    utf8_b = char_str.encode('utf-8')
    assert len(utf8_b) <= 3, f"{char_str} UTF-8 len {len(utf8_b)} > 3!"
    payload = utf8_b + b'\x00' * (4 - len(utf8_b))
    exe_data[str_raw : str_raw + 4] = payload
    patched_offsets.add(str_raw)

# Patch Hiragana
for idx, (dest, str_raw) in enumerate(hiragana_keys):
    patch_key(str_raw, p1_chars[idx], f"Hira key {idx}")

# Patch Katakana
for idx, (dest, str_raw) in enumerate(katakana_keys):
    patch_key(str_raw, p2_chars[idx], f"Kata key {idx}")

print(f"Total unique raw offsets patched: {len(patched_offsets)}")

# Save to village.exe
with open(EXE_PATH, "wb") as f:
    f.write(exe_data)

print(f"SUCCESS: Successfully patched {EXE_PATH}!")
