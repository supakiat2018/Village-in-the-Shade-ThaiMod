import os
import sys
import pefile
import struct

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

EXE_PATH = r"C:\Program Files (x86)\Steam\steamapps\common\Village in the Shade\village.exe"

pe = pefile.PE(EXE_PATH)
with open(EXE_PATH, 'rb') as f:
    exe_data = f.read()

raw_start = pe.get_offset_from_rva(0x403000)
raw_end = pe.get_offset_from_rva(0x408000)

hira_keys = []
kata_keys = []
seen_hira = set()
seen_kata = set()

for i in range(raw_start, raw_end - 7):
    if exe_data[i] in (0x48, 0x4c) and exe_data[i+1] == 0x8d:
        disp = struct.unpack('<i', exe_data[i+3:i+7])[0]
        curr_rva = pe.get_rva_from_offset(i)
        dest = curr_rva + 7 + disp
        if 0xE53000 <= dest <= 0xE54000:
            str_raw = pe.get_offset_from_rva(dest)
            b = exe_data[str_raw:str_raw+4].split(b'\x00')[0]
            try:
                s = b.decode('utf-8')
                if curr_rva < 0x405500:
                    if dest not in seen_hira:
                        hira_keys.append((curr_rva, dest, s))
                        seen_hira.add(dest)
                elif 0x405500 <= curr_rva < 0x407500:
                    if dest not in seen_kata:
                        kata_keys.append((curr_rva, dest, s))
                        seen_kata.add(dest)
            except:
                pass

hira_91 = hira_keys[:91]
kata_91 = hira_keys[91:] + kata_keys

print(f"Hira count: {len(hira_91)}")
print(f"Kata count: {len(kata_91)}")
assert len(hira_91) == 91
assert len(kata_91) == 91
assert len(p1_chars) == 91
assert len(p2_chars) == 91

entries = []
for idx, (cr, dest, orig) in enumerate(hira_91):
    thai = p1_chars[idx]
    entries.append((dest, thai, orig, f"Hira [{idx:2d}]"))

for idx, (cr, dest, orig) in enumerate(kata_91):
    thai = p2_chars[idx]
    entries.append((dest, thai, orig, f"Kata [{idx:2d}]"))

print(f"Total key patch entries: {len(entries)}")

header_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src", "keyboard_v120_patch.h")
header_path = os.path.abspath(header_path)

with open(header_path, "w", encoding="utf-8") as f:
    f.write("/* Auto-generated verified keyboard memory patch for Village in the Shade v1.20 */\n")
    f.write("#pragma once\n#include <stdint.h>\n#include <windows.h>\n\n")
    f.write("typedef struct {\n    uint32_t rva;\n    const char* thai;\n    const char* orig;\n    const char* desc;\n} VirtualKeyPatchEntry;\n\n")
    f.write("static const VirtualKeyPatchEntry g_virtual_key_patches[] = {\n")
    for dest, thai, orig, desc in entries:
        t_esc = thai.replace('\\', '\\\\').replace('"', '\\"')
        o_esc = orig.replace('\\', '\\\\').replace('"', '\\"')
        f.write(f'    {{ 0x{dest:08X}, "{t_esc}", "{o_esc}", "{desc}" }},\n')
    f.write("};\n#define NUM_VIRTUAL_KEY_PATCHES (sizeof(g_virtual_key_patches) / sizeof(g_virtual_key_patches[0]))\n\n")
    f.write("""static void patch_virtual_keyboard_in_memory(uintptr_t base, void (*log_fn)(const char*, ...))
{
    DWORD old_protect;
    /* Unprotect the keyboard string table region in .rdata (RVA 0x00E53900 .. 0x00E54000) */
    uintptr_t table_start = base + 0x00E53900;
    size_t table_len = 0x1000;

    if (VirtualProtect((LPVOID)table_start, table_len, PAGE_EXECUTE_READWRITE, &old_protect)) {
        int count = 0;
        for (size_t i = 0; i < NUM_VIRTUAL_KEY_PATCHES; i++) {
            char* dest = (char*)(base + g_virtual_key_patches[i].rva);
            const char* src = g_virtual_key_patches[i].thai;
            size_t src_len = strlen(src);
            if (src_len <= 3) {
                memset(dest, 0, 4);
                memcpy(dest, src, src_len);
                count++;
            }
        }
        VirtualProtect((LPVOID)table_start, table_len, old_protect, &old_protect);
        if (log_fn) log_fn("[KEYBOARD V1.20] Successfully patched %d virtual keyboard keys to Thai in memory!", count);
    } else {
        if (log_fn) log_fn("[KEYBOARD V1.20] ERROR: Failed to VirtualProtect keyboard memory!");
    }
}
""")

print(f"Successfully generated {header_path}!")
