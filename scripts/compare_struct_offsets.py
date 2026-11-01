import struct
import capstone

v120_path = r"D:\Users\Supakiat\Desktop\Village_in_the_Shade_ThaiMod_Dev\village_thai_keyboard_patched_v120.exe"
v130_path = r"C:\Program Files (x86)\Steam\steamapps\common\Village in the Shade\village.exe.bak"

with open(v120_path, "rb") as f:
    v120_data = f.read()

with open(v130_path, "rb") as f:
    v130_data = f.read()

def get_text(exe_data):
    e_lfanew = struct.unpack_from("<I", exe_data, 0x3C)[0]
    num_sections = struct.unpack_from("<H", exe_data, e_lfanew + 6)[0]
    opt_hdr_size = struct.unpack_from("<H", exe_data, e_lfanew + 20)[0]
    sec_tbl_offset = e_lfanew + 24 + opt_hdr_size
    image_base = struct.unpack_from("<Q", exe_data, e_lfanew + 24 + 24)[0]

    for i in range(num_sections):
        sec_off = sec_tbl_offset + i * 40
        name = exe_data[sec_off:sec_off+8].rstrip(b'\x00').decode('latin1')
        vsize, vaddr, rsize, raddr = struct.unpack_from("<IIII", exe_data, sec_off + 8)
        if name == ".text":
            return image_base, vaddr, vsize, raddr, rsize
    return None

base_120, va_120, vsz_120, roff_120, rsz_120 = get_text(v120_data)
base_130, va_130, vsz_130, roff_130, rsz_130 = get_text(v130_data)

md = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_64)

# In v1.20, Global Getter 1 was at:
# 48 8B 05 ? ? ? ? 48 8B 6C 24 38 48 8B 74 24 40 49 8B 50 10 48 8B 88 08 02 00 00 48 8B 7C 24 48 48 8B 81 70 32 00 00
# Notice 48 8B 81 70 32 00 00 -> [rcx + 0x3270] !!
# Let's inspect the exact same function in v1.30!

pat_prefix = bytes.fromhex("48 8B 6C 24 38 48 8B 74 24 40 49 8B 50 10 48 8B 88 08 02 00 00 48 8B 7C 24 48")

idx_120 = v120_data.find(pat_prefix)
idx_130 = v130_data.find(pat_prefix)

print(f"Pat prefix in v1.20: file 0x{idx_120:X}")
print(f"Pat prefix in v1.30: file 0x{idx_130:X}")

if idx_120 != -1:
    print("\n--- v1.20 Instructions ---")
    chunk = v120_data[idx_120 - 7 : idx_120 + 60]
    for insn in md.disasm(chunk, base_120 + va_120 + (idx_120 - 7 - roff_120)):
        print(f"  {insn.mnemonic:<8} {insn.op_str}")

if idx_130 != -1:
    print("\n--- v1.30 Instructions ---")
    chunk = v130_data[idx_130 - 7 : idx_130 + 60]
    for insn in md.disasm(chunk, base_130 + va_130 + (idx_130 - 7 - roff_130)):
        print(f"  {insn.mnemonic:<8} {insn.op_str}")
