import re
import struct

exe_path = r"C:\Program Files (x86)\Steam\steamapps\common\Village in the Shade\village.exe.bak"

with open(exe_path, "rb") as f:
    exe_data = f.read()

# Parse PE header to get .text section and ImageBase
e_lfanew = struct.unpack_from("<I", exe_data, 0x3C)[0]
num_sections = struct.unpack_from("<H", exe_data, e_lfanew + 6)[0]
opt_hdr_size = struct.unpack_from("<H", exe_data, e_lfanew + 20)[0]
sec_tbl_offset = e_lfanew + 24 + opt_hdr_size
image_base = struct.unpack_from("<Q", exe_data, e_lfanew + 24 + 24)[0]

print(f"ImageBase: 0x{image_base:X}, Sections: {num_sections}")

text_sec = None
for i in range(num_sections):
    sec_off = sec_tbl_offset + i * 40
    name = exe_data[sec_off:sec_off+8].rstrip(b'\x00').decode('latin1')
    vsize, vaddr, rsize, raddr = struct.unpack_from("<IIII", exe_data, sec_off + 8)
    if name == ".text":
        text_sec = (vaddr, vsize, raddr, rsize)
        print(f"Found .text: VA=0x{vaddr:X}, VSize=0x{vsize:X}, RawOff=0x{raddr:X}, RawSize=0x{rsize:X}")
        break

patterns = {
    "Items Won't Decrease": "48 89 5C 24 08 48 89 74 24 10 48 89 7C 24 20 41 56 48 83 EC 20 48 63 DA 48 8B F1 45 85 C0 0F 88 ? ? ? ? 85 D2",
    "God Mode": "40 53 48 83 EC 20 48 8B 05 ? ? ? ? 48 8B D9 0F 57 C9 48 8B 90 68 02 00 00 4C 8B 82 40 03 00 00",
    "Crafting No Materials": "48 89 5C 24 18 55 56 57 41 54 41 55 41 56 41 57 48 8D 6C 24 D9 48 81 EC C0 00 00 00 48 8B 05 ? ? ? ? 48 33 C4 48 89 45 17 48 8B DA 48 89 4D 9F 48 8B 0D ? ? ? ? E8 ? ? ? ? 4C 8B D8 48 89 5D 87",
    "Cooking No Materials": "48 89 5C 24 18 55 56 57 41 54 41 55 41 56 41 57 48 8D 6C 24 D9 48 81 EC D0 00 00 00 48 8B 05 ? ? ? ?",
    "Smithing No Materials": "48 89 5C 24 08 48 89 74 24 18 48 89 7C 24 20 55 41 54 41 55 41 56 41 57 48 8D 6C 24 C9 48 81 EC C0 00 00 00 48 8B 05 ? ? ? ? 48 33 C4 48 89 45 27",
    "Building No Materials": "48 89 5C 24 08 55 56 57 41 54 41 55 41 56 41 57 48 8D 6C 24 D9 48 81 EC C0 00 00 00",
    "Dyeing No Materials": "48 89 5C 24 18 55 56 57 41 54 41 55 41 56 41 57 48 8D 6C 24 D9 48 81 EC F0 00 00 00 48 8B 05 ? ? ? ? 48 33 C4 48 89 45 17 48 8B FA",
    "Can Submit Any Item": "48 89 5C 24 18 48 89 74 24 20 55 57 41 54 41 56 41 57 48 8D AC 24 40 FF FF FF 48 81 EC C0 01 00 00 48 63 DA",
    "Global Getter 1": "48 8B 05 ? ? ? ? 48 8B 6C 24 38 48 8B 74 24 40 49 8B 50 10 48 8B 88 08 02 00 00 48 8B 7C 24 48 48 8B 81 70 32 00 00",
    "Global Getter 2 (from God Mode)": "48 8B 05 ? ? ? ? 48 8B D9 0F 57 C9 48 8B 90 68 02 00 00"
}

def pat_to_regex(pat_str):
    tokens = pat_str.strip().split()
    rx_bytes = []
    for t in tokens:
        if t == '?' or t == '??':
            rx_bytes.append(b'.')
        else:
            rx_bytes.append(re.escape(bytes.fromhex(t)))
    return b''.join(rx_bytes)

text_bytes = exe_data[text_sec[2] : text_sec[2] + text_sec[3]]

for name, pat in patterns.items():
    rx = pat_to_regex(pat)
    matches = [m.start() for m in re.finditer(rx, text_bytes, re.DOTALL)]
    if matches:
        for idx, m in enumerate(matches):
            raw_off = text_sec[2] + m
            rva = text_sec[0] + m
            va = image_base + rva
            print(f"[MATCH] {name} #{idx+1}: FileOffset=0x{raw_off:X}, RVA=0x{rva:X}, VA=0x{va:X}")
            if "Global Getter" in name:
                # Resolve RIP-relative pointer: 48 8B 05 [disp32]
                disp = struct.unpack_from("<i", exe_data, raw_off + 3)[0]
                ptr_rva = rva + 7 + disp
                ptr_va = image_base + ptr_rva
                print(f"        -> Resolved Global Pointer RVA=0x{ptr_rva:X}, VA=0x{ptr_va:X}")
    else:
        print(f"[MISS] {name}")
