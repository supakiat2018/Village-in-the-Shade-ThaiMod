import struct
import capstone

exe_path = r"C:\Program Files (x86)\Steam\steamapps\common\Village in the Shade\village.exe.bak"

with open(exe_path, "rb") as f:
    exe_data = f.read()

e_lfanew = struct.unpack_from("<I", exe_data, 0x3C)[0]
num_sections = struct.unpack_from("<H", exe_data, e_lfanew + 6)[0]
opt_hdr_size = struct.unpack_from("<H", exe_data, e_lfanew + 20)[0]
sec_tbl_offset = e_lfanew + 24 + opt_hdr_size
image_base = struct.unpack_from("<Q", exe_data, e_lfanew + 24 + 24)[0]

text_sec = None
for i in range(num_sections):
    sec_off = sec_tbl_offset + i * 40
    name = exe_data[sec_off:sec_off+8].rstrip(b'\x00').decode('latin1')
    vsize, vaddr, rsize, raddr = struct.unpack_from("<IIII", exe_data, sec_off + 8)
    if name == ".text":
        text_sec = (vaddr, vsize, raddr, rsize)
        break

md = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_64)

# Global Pointer in v1.30 is RVA 0x111CC90 -> VA 0x14111CC90
target_ptr_va = image_base + 0x111CC90

print(f"Disassembling references to Global Pointer (0x{target_ptr_va:X})...")

text_bytes = exe_data[text_sec[2] : text_sec[2] + text_sec[3]]
text_rva_base = text_sec[0]

# Find all instructions referencing target_ptr_va
for insn in md.disasm(text_bytes, image_base + text_rva_base):
    # Check RIP-relative operand
    if f"0x{target_ptr_va:x}" in insn.op_str.lower():
        print(f"\nRef at 0x{insn.address:X}: {insn.mnemonic} {insn.op_str}")
        # Disassemble next 15 instructions
        file_offset = insn.address - image_base - text_rva_base + text_sec[2]
        next_bytes = exe_data[file_offset : file_offset + 100]
        for sub_insn in md.disasm(next_bytes, insn.address):
            print(f"    0x{sub_insn.address:X}: {sub_insn.mnemonic} {sub_insn.op_str}")
