import os, struct

EXE_PATH = r"C:\Program Files (x86)\Steam\steamapps\common\Village in the Shade\village.exe"
with open(EXE_PATH, "rb") as f:
    exe_data = f.read()

dos = exe_data[:64]
e_lfanew = struct.unpack("<I", dos[0x3C:0x40])[0]
num_sections = struct.unpack("<H", exe_data[e_lfanew+6:e_lfanew+8])[0]
opt_hdr_size = struct.unpack("<H", exe_data[e_lfanew+20:e_lfanew+22])[0]
sec_table_off = e_lfanew + 24 + opt_hdr_size

sections = []
for i in range(num_sections):
    sec = exe_data[sec_table_off + i*40 : sec_table_off + (i+1)*40]
    name = sec[:8].rstrip(b"\x00").decode("latin1")
    vsize, va, rsize, rptr = struct.unpack("<IIII", sec[8:24])
    sections.append((name, va, vsize, rptr, rsize))

def rva_to_offset(rva):
    for name, va, vsize, rptr, rsize in sections:
        if va <= rva < va + vsize:
            return rptr + (rva - va)
    return None

def offset_to_rva(off):
    for name, va, vsize, rptr, rsize in sections:
        if rptr <= off < rptr + rsize:
            return va + (off - rptr)
    return None

rdata_min = 0x00E6E200
rdata_max = 0x00E6F000

hira_keys = []
kata_keys = []
seen_hira = set()
seen_kata = set()

for i in range(rva_to_offset(0x00418900), rva_to_offset(0x0041C900) - 7):
    if exe_data[i] in (0x48, 0x4c) and exe_data[i+1] == 0x8d:
        disp = struct.unpack("<i", exe_data[i+3:i+7])[0]
        curr_rva = offset_to_rva(i)
        dest = curr_rva + 7 + disp
        if rdata_min <= dest <= rdata_max:
            str_raw = rva_to_offset(dest)
            if str_raw:
                b = exe_data[str_raw:str_raw+4].split(b"\x00")[0]
                try:
                    s = b.decode("utf-8")
                    if curr_rva < 0x0041A900:
                        if dest not in seen_hira:
                            hira_keys.append((curr_rva, dest, s))
                            seen_hira.add(dest)
                    elif 0x0041A900 <= curr_rva < 0x0041C900:
                        if dest not in seen_kata:
                            kata_keys.append((curr_rva, dest, s))
                            seen_kata.add(dest)
                except:
                    pass

print(f"Hira keys: {len(hira_keys)}, Kata keys: {len(kata_keys)}")
assert len(hira_keys) == 91
assert len(kata_keys) == 91

p1_chars = [
    'ก', 'ข', 'ฃ', 'ค', 'ฅ',      'ล', 'ว', 'ศ',      '๐', '๑', '๒', '๓', '๔',
    'ฆ', 'ง', 'จ', 'ฉ', 'ช',      'ษ', 'ส', 'ห', 'ฬ', 'อ',      '๕', '๖', '๗', '๘', '๙',
    'ซ', 'ฌ', 'ญ', 'ฎ', 'ฏ',      'ฮ', ' ', '.',      '(', ')', '[', ']', '{',
    'ฐ', 'ฑ', 'ฒ', 'ณ', 'ด',      '0', '1', '2', '3', '4',      '}', '+', '=', '*', ':',
    'ต', 'ถ', 'ท', 'ธ', 'น',      '5', '6', '7', '8', '9',      ';', '"', "'", '<', '>',
    'บ', 'ป', 'ผ', 'ฝ', 'พ',      ',', '-', '!', '?', '/',      'ー', '～', '＝', '♥', '★',
    'ฟ', 'ภ', 'ม', 'ย', 'ร'
]

p2_chars = [
    'ะ', 'า', 'ำ', 'ิ', 'ี',      '0', '1', '2',      '๐', '๑', '๒', '๓', '๔',
    'ึ', 'ื', 'ุ', 'ู', 'เ',      '3', '4', '5', '6', '7',      '๕', '๖', '๗', '๘', '๙',
    'แ', 'โ', 'ใ', 'ไ', '็',      '8', '9', ' ',      '[', ']', '{', '}', '<',
    'ั', '่', '้', '๊', '๋',      '+', '-', '*', '/', '=',      '>', '"', "'", ':', ';',
    '์', 'ๆ', 'ฯ', 'ฺ', 'ํ',      '%', '^', '&', '(', ')',      '~', '\\', '|', '_', '฿',
    '๎', '๏', '๚', '๛', '฿',      ',', '-', '!', '?', '/',      'ー', '～', '＝', '♥', '★',
    'ฤ', 'ฦ', '.', ',', '-'
]

entries = []
for idx, (cr, dest, orig) in enumerate(hira_keys):
    thai = p1_chars[idx]
    entries.append((dest, thai, orig, f"Hira [{idx:2d}]"))

for idx, (cr, dest, orig) in enumerate(kata_keys):
    thai = p2_chars[idx]
    entries.append((dest, thai, orig, f"Kata [{idx:2d}]"))

header_path = r"D:\Users\Supakiat\Desktop\Village_in_the_Shade_ThaiMod_Dev\src\keyboard_v130_patch.h"
with open(header_path, "w", encoding="utf-8") as f:
    f.write("/* Auto-generated verified keyboard memory patch for Village in the Shade v1.30 */\n")
    f.write("#pragma once\n#include <stdint.h>\n#include <windows.h>\n\n")
    f.write("typedef struct {\n    uint32_t rva;\n    const char* thai;\n    const char* orig;\n    const char* desc;\n} VirtualKeyPatchEntry;\n\n")
    f.write("static const VirtualKeyPatchEntry g_virtual_key_patches[] = {\n")
    for dest, thai, orig, desc in entries:
        t_esc = thai.replace('\\', '\\\\').replace('"', '\\"')
        o_esc = orig.replace('\\', '\\\\').replace('"', '\\"')
        f.write(f'    {{ 0x{dest:08X}, "{t_esc}", "{o_esc}", "{desc}" }},\n')
    f.write("};\n#define NUM_VIRTUAL_KEY_PATCHES (sizeof(g_virtual_key_patches) / sizeof(g_virtual_key_patches[0]))\n\n")
    f.write("""static void patch_virtual_keyboard_v130(uintptr_t base, void (*log_fn)(const char*, ...))
{
    DWORD old_protect;
    /* Unprotect the keyboard string table region in .rdata (RVA 0x00E6E200 .. 0x00E6E700) */
    uintptr_t table_start = base + 0x00E6E200;
    size_t table_len = 0x800;

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
        if (log_fn) log_fn("[KEYBOARD V1.30] Successfully patched %d virtual keyboard keys to Thai in memory!", count);
    } else {
        if (log_fn) log_fn("[KEYBOARD V1.30] ERROR: Failed to VirtualProtect keyboard memory!");
    }
}
""")

print("Successfully generated keyboard_v130_patch.h!")
