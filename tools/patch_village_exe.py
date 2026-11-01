#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
patch_village_exe.py
--------------------
Patches Village in the Shade v1.20 executable (village.exe) directly on disk:
1. Dynamic Proportional Font Kerning Patch (ตัวชิดกัน: putStr, putStrProp, putStrAlign)
2. Thai Virtual Keyboard Patch (182 Thai Unicode characters into in-game keyboard)
3. Native In-Game Cheats Patch:
   - god_mode: Invincible / No Damage
   - infinite_items: Items won't decrease
   - no_materials_crafting: Free Crafting
   - no_materials_cooking: Free Cooking
   - no_materials_smithing: Free Smithing
   - no_materials_building: Free Building
   - no_materials_dyeing: Free Dyeing
   - submit_any_item: Submit any item for bundle/quest
   - infinite_stamina: Stamina won't decrease on actions
   - infinite_money: Always afford items in shops & locked min 999,999 coins

Usage:
    python patch_village_exe.py
    python patch_village_exe.py --dest "path/to/village.exe"
"""

import os
import sys
import shutil
import argparse

DEFAULT_SRC = r"C:\Program Files (x86)\Steam\steamapps\common\Village in the Shade\village.exe.bak"
DEFAULT_TARGET_GAME = r"C:\Program Files (x86)\Steam\steamapps\common\Village in the Shade\village.exe"
DEFAULT_TARGET_GAMEHUB = r"C:\Program Files (x86)\Steam\steamapps\common\Gamehub\village.exe"

# 182 Virtual Keyboard entries from keyboard_v120_patch.h
# Format: (RVA, Thai_char, Orig_char, Desc)
KEYBOARD_PATCHES = [
    (0x00E539BC, "ก", "あ", "Hira [ 0]"),
    (0x00E539C0, "ข", "い", "Hira [ 1]"),
    (0x00E539C4, "ฃ", "う", "Hira [ 2]"),
    (0x00E539A4, "ค", "え", "Hira [ 3]"),
    (0x00E539A8, "ฅ", "お", "Hira [ 4]"),
    (0x00E539AC, "ล", "や", "Hira [ 5]"),
    (0x00E539B0, "ว", "ゆ", "Hira [ 6]"),
    (0x00E539D8, "ศ", "よ", "Hira [ 7]"),
    (0x00E539DC, "๐", "が", "Hira [ 8]"),
    (0x00E539E0, "๑", "ぎ", "Hira [ 9]"),
    (0x00E539E4, "๒", "ぐ", "Hira [10]"),
    (0x00E539C8, "๓", "げ", "Hira [11]"),
    (0x00E539CC, "๔", "ご", "Hira [12]"),
    (0x00E539D0, "ฆ", "か", "Hira [13]"),
    (0x00E539D4, "ง", "き", "Hira [14]"),
    (0x00E539F8, "จ", "く", "Hira [15]"),
    (0x00E539FC, "ฉ", "け", "Hira [16]"),
    (0x00E53A00, "ช", "こ", "Hira [17]"),
    (0x00E53A04, "ษ", "ら", "Hira [18]"),
    (0x00E539E8, "ส", "り", "Hira [19]"),
    (0x00E539EC, "ห", "る", "Hira [20]"),
    (0x00E539F0, "ฬ", "れ", "Hira [21]"),
    (0x00E539F4, "อ", "ろ", "Hira [22]"),
    (0x00E53A18, "๕", "ざ", "Hira [23]"),
    (0x00E53A1C, "๖", "じ", "Hira [24]"),
    (0x00E53A20, "๗", "ず", "Hira [25]"),
    (0x00E53A24, "๘", "ぜ", "Hira [26]"),
    (0x00E53A08, "๙", "ぞ", "Hira [27]"),
    (0x00E53A0C, "ซ", "さ", "Hira [28]"),
    (0x00E53A10, "ฌ", "し", "Hira [29]"),
    (0x00E53A14, "ญ", "す", "Hira [30]"),
    (0x00E53A38, "ฎ", "せ", "Hira [31]"),
    (0x00E53A3C, "ฏ", "そ", "Hira [32]"),
    (0x00E53A40, "ฮ", "わ", "Hira [33]"),
    (0x00E53A44, " ", "を", "Hira [34]"),
    (0x00E53A28, ".", "ん", "Hira [35]"),
    (0x00E53A2C, "(", "だ", "Hira [36]"),
    (0x00E53A30, ")", "ぢ", "Hira [37]"),
    (0x00E53A34, "[", "づ", "Hira [38]"),
    (0x00E53A58, "]", "で", "Hira [39]"),
    (0x00E53A5C, "{", "ど", "Hira [40]"),
    (0x00E53A60, "ฐ", "た", "Hira [41]"),
    (0x00E53A64, "ฑ", "ち", "Hira [42]"),
    (0x00E53A48, "ฒ", "つ", "Hira [43]"),
    (0x00E53A4C, "ณ", "て", "Hira [44]"),
    (0x00E53A50, "ด", "と", "Hira [45]"),
    (0x00E53A54, "0", "ぁ", "Hira [46]"),
    (0x00E53A78, "1", "ぃ", "Hira [47]"),
    (0x00E53A7C, "2", "ぅ", "Hira [48]"),
    (0x00E53A80, "3", "ぇ", "Hira [49]"),
    (0x00E53A84, "4", "ぉ", "Hira [50]"),
    (0x00E53A68, "}", "ば", "Hira [51]"),
    (0x00E53A6C, "+", "び", "Hira [52]"),
    (0x00E53A70, "=", "ぶ", "Hira [53]"),
    (0x00E53A74, "*", "べ", "Hira [54]"),
    (0x00E53A98, ":", "ぼ", "Hira [55]"),
    (0x00E53A9C, "ต", "な", "Hira [56]"),
    (0x00E53AA0, "ถ", "に", "Hira [57]"),
    (0x00E53AA4, "ท", "ぬ", "Hira [58]"),
    (0x00E53A88, "ธ", "ね", "Hira [59]"),
    (0x00E53A8C, "น", "の", "Hira [60]"),
    (0x00E53A90, "5", "ゃ", "Hira [61]"),
    (0x00E53A94, "6", "ゅ", "Hira [62]"),
    (0x00E53AB8, "7", "ょ", "Hira [63]"),
    (0x00E53ABC, "8", "っ", "Hira [64]"),
    (0x00E53AC0, "9", "ゎ", "Hira [65]"),
    (0x00E53AC4, ";", "ぱ", "Hira [66]"),
    (0x00E53AA8, "\"", "ぴ", "Hira [67]"),
    (0x00E53AAC, "'", "ぷ", "Hira [68]"),
    (0x00E53AB0, "<", "ぺ", "Hira [69]"),
    (0x00E53AB4, ">", "ぽ", "Hira [70]"),
    (0x00E53AD8, "บ", "は", "Hira [71]"),
    (0x00E53ADC, "ป", "ひ", "Hira [72]"),
    (0x00E53AE0, "ผ", "ふ", "Hira [73]"),
    (0x00E53AE4, "ฝ", "へ", "Hira [74]"),
    (0x00E53AC8, "พ", "ほ", "Hira [75]"),
    (0x00E53ACC, "ฟ", "ー", "Hira [76]"),
    (0x00E53AD0, "ภ", "〜", "Hira [77]"),
    (0x00E53AD4, "ม", "…", "Hira [78]"),
    (0x00E53AF8, "ย", "・", "Hira [79]"),
    (0x00E53AFC, "ร", "！", "Hira [80]"),
    (0x00E53B00, "ฤ", "？", "Hira [81]"),
    (0x00E53AE8, "ะ", "ア", "Kata [ 0]"),
    (0x00E53AEC, "ั", "イ", "Kata [ 1]"),
    (0x00E53AF0, "า", "ウ", "Kata [ 2]"),
    (0x00E53AF4, "ำ", "エ", "Kata [ 3]"),
    (0x00E53B18, "ิ", "オ", "Kata [ 4]"),
    (0x00E53B1C, "ี", "ヤ", "Kata [ 5]"),
    (0x00E53B20, "ึ", "ユ", "Kata [ 6]"),
    (0x00E53B24, "ื", "ヨ", "Kata [ 7]"),
    (0x00E53B08, "ุ", "ガ", "Kata [ 8]"),
    (0x00E53B0C, "ู", "ギ", "Kata [ 9]"),
    (0x00E53B10, "ฺ", "グ", "Kata [10]"),
    (0x00E53B14, "เ", "ゲ", "Kata [11]"),
    (0x00E53B38, "แ", "ゴ", "Kata [12]"),
    (0x00E53B3C, "โ", "カ", "Kata [13]"),
    (0x00E53B40, "ใ", "キ", "Kata [14]"),
    (0x00E53B44, "ไ", "ク", "Kata [15]"),
    (0x00E53B28, "ๅ", "ケ", "Kata [16]"),
    (0x00E53B2C, "ๆ", "コ", "Kata [17]"),
    (0x00E53B30, "็", "ラ", "Kata [18]"),
    (0x00E53B34, "่", "リ", "Kata [19]"),
    (0x00E53B58, "้", "ル", "Kata [20]"),
    (0x00E53B5C, "๊", "レ", "Kata [21]"),
    (0x00E53B60, "๋", "ロ", "Kata [22]"),
    (0x00E53B64, "์", "ザ", "Kata [23]"),
    (0x00E53B48, "ํ", "ジ", "Kata [24]"),
    (0x00E53B4C, "๎", "ズ", "Kata [25]"),
    (0x00E53B50, "๏", "ゼ", "Kata [26]"),
    (0x00E53B54, "ฯ", "ゾ", "Kata [27]"),
    (0x00E53B78, "a", "サ", "Kata [28]"),
    (0x00E53B7C, "b", "シ", "Kata [29]"),
    (0x00E53B80, "c", "ス", "Kata [30]"),
    (0x00E53B84, "d", "セ", "Kata [31]"),
    (0x00E53B68, "e", "ソ", "Kata [32]"),
    (0x00E53B6C, "f", "ワ", "Kata [33]"),
    (0x00E53B70, "g", "ヲ", "Kata [34]"),
    (0x00E53B74, "h", "ン", "Kata [35]"),
    (0x00E53B98, "i", "ダ", "Kata [36]"),
    (0x00E53B9C, "j", "ヂ", "Kata [37]"),
    (0x00E53BA0, "k", "ヅ", "Kata [38]"),
    (0x00E53BA4, "l", "デ", "Kata [39]"),
    (0x00E53B88, "m", "ド", "Kata [40]"),
    (0x00E53B8C, "n", "タ", "Kata [41]"),
    (0x00E53B90, "o", "チ", "Kata [42]"),
    (0x00E53B94, "p", "ツ", "Kata [43]"),
    (0x00E53BB8, "q", "テ", "Kata [44]"),
    (0x00E53BBC, "r", "ト", "Kata [45]"),
    (0x00E53BC0, "s", "ァ", "Kata [46]"),
    (0x00E53BC4, "t", "ィ", "Kata [47]"),
    (0x00E53BA8, "u", "ゥ", "Kata [48]"),
    (0x00E53BAC, "v", "ェ", "Kata [49]"),
    (0x00E53BB0, "w", "ォ", "Kata [50]"),
    (0x00E53BB4, "x", "バ", "Kata [51]"),
    (0x00E53BD8, "y", "ビ", "Kata [52]"),
    (0x00E53BDC, "z", "ブ", "Kata [53]"),
    (0x00E53BE0, "A", "ベ", "Kata [54]"),
    (0x00E53BE4, "B", "ボ", "Kata [55]"),
    (0x00E53BC8, "C", "ナ", "Kata [56]"),
    (0x00E53BCC, "D", "ニ", "Kata [57]"),
    (0x00E53BD0, "E", "ヌ", "Kata [58]"),
    (0x00E53BD4, "F", "ネ", "Kata [59]"),
    (0x00E53BF8, "G", "ノ", "Kata [60]"),
    (0x00E53BFC, "H", "ャ", "Kata [61]"),
    (0x00E53C00, "I", "ュ", "Kata [62]"),
    (0x00E53C04, "J", "ョ", "Kata [63]"),
    (0x00E53BE8, "K", "ッ", "Kata [64]"),
    (0x00E53BEC, "L", "ヮ", "Kata [65]"),
    (0x00E53BF0, "M", "パ", "Kata [66]"),
    (0x00E53BF4, "N", "ピ", "Kata [67]"),
    (0x00E53C18, "O", "プ", "Kata [68]"),
    (0x00E53C1C, "P", "ペ", "Kata [69]"),
    (0x00E53C20, "Q", "ポ", "Kata [70]"),
    (0x00E53C24, "R", "ハ", "Kata [71]"),
    (0x00E53C08, "S", "ヒ", "Kata [72]"),
    (0x00E53C0C, "T", "フ", "Kata [73]"),
    (0x00E53C10, "U", "ヘ", "Kata [74]"),
    (0x00E53C14, "V", "ホ", "Kata [75]"),
    (0x00E53C38, "W", "ヴ", "Kata [76]"),
    (0x00E53C3C, "X", "ヵ", "Kata [77]"),
    (0x00E53C40, "Y", "ヶ", "Kata [78]"),
    (0x00E53C44, "Z", "・", "Kata [79]"),
    (0x00E53C28, "%", "！", "Kata [80]"),
    (0x00E53C2C, "&", "？", "Kata [81]"),
    (0x00E53C30, "@", "(",  "Sym [ 0]"),
    (0x00E53C34, "#", ")",  "Sym [ 1]"),
    (0x00E53C58, "$", "0",  "Sym [ 2]"),
    (0x00E53C5C, "/", "1",  "Sym [ 3]"),
    (0x00E53C60, "\\","2",  "Sym [ 4]"),
    (0x00E53C64, "|", "3",  "Sym [ 5]"),
    (0x00E53C48, "~", "4",  "Sym [ 6]"),
    (0x00E53C4C, "^", "5",  "Sym [ 7]"),
    (0x00E53C50, "`", "6",  "Sym [ 8]"),
    (0x00E53C54, "_", "7",  "Sym [ 9]"),
    (0x00E53C78, "-", "8",  "Sym [10]"),
    (0x00E53C7C, "?", "9",  "Sym [11]"),
    (0x00E53C80, "!", "-",  "Sym [12]"),
    (0x00E53C84, ",", "/",  "Sym [13]")
]

ANCHOR_RVA = 0x00E539BC
ANCHOR_PATTERN = bytes([0xE3, 0x81, 0x82, 0x00, 0xE3, 0x81, 0x84, 0x00, 0xE3, 0x81, 0x86, 0x00])
ANCHOR_FILE_OFFSET = 0x00E52DBC

def patch_executable(src_path=DEFAULT_SRC, dest_paths=[DEFAULT_TARGET_GAME, DEFAULT_TARGET_GAMEHUB]):
    print("=" * 75)
    print(" Village in the Shade v1.20 - Complete Executable Patcher")
    print(" 1. Dynamic Proportional Font Kerning (ตัวชิดกัน)")
    print(" 2. Thai Virtual Keyboard (182 Thai Unicode Keys)")
    print(" 3. Native Built-in Cheats (อมตะ, ไอเทมไม่ลด, คราฟต์ฟรี, สตามิน่าเต็ม, เงินไม่จำกัด)")
    print(f" Source: {src_path}")
    print("=" * 75)

    if not os.path.exists(src_path):
        raise FileNotFoundError(f"Clean source executable not found: {src_path}")

    with open(src_path, "rb") as f:
        data = bytearray(f.read())
    print(f"[*] Loaded executable: {len(data):,} bytes")

    # =============================================================
    # Patch 1: Proportional Font Kerning (ตัวชิดกัน)
    # =============================================================
    print("\n[*] Applying Patch 1: Proportional Font Kerning (ตัวชิดกัน)...")
    
    # 1a. putStr (File offset 0x993580)
    # Original: 48 8B C4 55 53 -> Patched: E9 8B F7 FF FF (jmp putStrProp)
    putstr_off = 0x993580
    data[putstr_off:putstr_off+5] = bytes.fromhex("e98bf7ffff")
    print(f"    [+] putStr @ 0x{putstr_off:X}: Redirected to putStrProp")

    # 1b. putStrAlign (File offset 0x994041)
    # Original: 0F 85 9F 01 00 00 -> Patched: E9 A0 01 00 00 90
    align_off = 0x994041
    data[align_off:align_off+6] = bytes.fromhex("e9a001000090")
    print(f"    [+] putStrAlign @ 0x{align_off:X}: Forced proportional alignment")

    # 1c. Text Router (File offset 0x993E49)
    # Original: 66 83 79 26 00 0F 85 BC EE FF FF -> Patched: E9 C2 EE FF FF 90 90 90 90 90 90
    router_off = 0x993E49
    data[router_off:router_off+11] = bytes.fromhex("e9c2eeffff909090909090")
    print(f"    [+] Text Router @ 0x{router_off:X}: Forced proportional routing")

    # =============================================================
    # Patch 2: Thai Virtual Keyboard (คีย์บอร์ดไทย 182 ปุ่ม)
    # =============================================================
    print("\n[*] Applying Patch 2: Thai Virtual Keyboard (คีย์บอร์ดไทย)...")
    anchor_pos = data.find(ANCHOR_PATTERN)
    if anchor_pos == -1:
        if data[ANCHOR_FILE_OFFSET:ANCHOR_FILE_OFFSET+12] == ANCHOR_PATTERN:
            anchor_pos = ANCHOR_FILE_OFFSET
        else:
            raise ValueError("Keyboard anchor pattern not found in executable!")
    print(f"    Found keyboard table anchor at file offset 0x{anchor_pos:X}")

    patched_keys = 0
    for rva, thai, orig, desc in KEYBOARD_PATCHES:
        rel = rva - ANCHOR_RVA
        target_offset = anchor_pos + rel
        thai_bytes = thai.encode("utf-8")
        if len(thai_bytes) <= 3:
            data[target_offset:target_offset+4] = b"\x00\x00\x00\x00"
            data[target_offset:target_offset+len(thai_bytes)] = thai_bytes
            patched_keys += 1
    print(f"    [+] Patched {patched_keys} / {len(KEYBOARD_PATCHES)} virtual keys to Thai Unicode!")

    # =============================================================
    # Patch 3: Native Built-in Cheats
    # =============================================================
    print("\n[*] Applying Patch 3: Native Built-in Cheats...")

    cheats = [
        ("God Mode (Invincible - เลือดไม่ลด)", 0x13A410, bytes.fromhex("b001c3")),
        ("Items Won't Decrease (ไอเทมไม่ลด)", 0x152A00, bytes.fromhex("b801000000c3")),
        ("Crafting No Materials (คราฟต์ของฟรี)", 0x375110, bytes.fromhex("b001c3")),
        ("Cooking No Materials (ทำอาหารฟรี)", 0x36ECD0, bytes.fromhex("b001c3")),
        ("Smithing No Materials (ตีเหล็กฟรี)", 0x339000, bytes.fromhex("b001c3")),
        ("Building No Materials (ก่อสร้างฟรี)", 0x367CD0, bytes.fromhex("b001c3")),
        ("Dyeing No Materials (ย้อมสีฟรี)", 0x389430, bytes.fromhex("b001c3")),
        ("Submit Any Item (ส่งของเควสต์ได้ทุกไอเทม)", 0x3407F4, bytes.fromhex("909090909090")),
        ("Infinite Stamina 1 (สตามิน่าไม่ลด จุดที่ 1)", 0x293F46, bytes.fromhex("909090909090")),
        ("Infinite Stamina 2 (สตามิน่าไม่ลด จุดที่ 2)", 0x3793B8, bytes.fromhex("909090909090")),
        ("Infinite Stamina 3 (สตามิน่าไม่ลด จุดที่ 3)", 0x4AA830, bytes.fromhex("909090909090")),
        ("Shop Free Buying (ซื้อของในร้านฟรี)", 0x1201F6, bytes.fromhex("b00190")),
        ("Shop Purchase Bypass (ผ่านการตรวจเงินซื้อของ)", 0x120262, bytes.fromhex("9090")),
        ("Infinite Money Lock (เงินไม่ต่ำกว่า 999,999)", 0x155669, bytes.fromhex("b93f420f009090")),
    ]

    for name, off, pbytes in cheats:
        data[off:off+len(pbytes)] = pbytes
        print(f"    [+] {name:45s} @ 0x{off:08X} ({len(pbytes)} bytes patched)")

    # Save to all target destinations
    print("\n[*] Saving patched executable to targets:")
    for dest in dest_paths:
        os.makedirs(os.path.dirname(dest), exist_ok=True)
        with open(dest, "wb") as f:
            f.write(data)
        print(f"    [SUCCESS] Deployed to: {dest} ({len(data):,} bytes)")

    print("\n" + "=" * 75)
    print(" ALL 3 PATCHES COMPLETED & DEPLOYED SUCCESSFULLY!")
    print("=" * 75)

def main():
    parser = argparse.ArgumentParser(description="Complete village.exe Patcher for Thai Mod")
    parser.add_argument("--src", default=DEFAULT_SRC, help="Clean source village.exe.bak")
    args = parser.parse_args()
    patch_executable(args.src)

if __name__ == "__main__":
    main()
