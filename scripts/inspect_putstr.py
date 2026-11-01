import os
import struct
import capstone

exe_path = r"C:\Program Files (x86)\Steam\steamapps\common\Village in the Shade\village.exe"

with open(exe_path, "rb") as f:
    data = f.read()

# Parse PE header
pe_offset = struct.unpack_from("<I", data, 0x3C)[0]
num_sections = struct.unpack_from("<H", data, pe_offset + 6)[0]
opt_hdr_size = struct.unpack_from("<H", data, pe_offset + 20)[0]
opt_hdr_offset = pe_offset + 24
image_base = struct.unpack_from("<Q", data, opt_hdr_offset + 24)[0]

sections_offset = opt_hdr_offset + opt_hdr_size
sections = []
for i in range(num_sections):
    sec = data[sections_offset + i*40 : sections_offset + (i+1)*40]
    name = sec[:8].rstrip(b'\x00').decode('latin1')
    vsize, vrva, rsize, rraw = struct.unpack_from("<IIII", sec, 8)
    sections.append((name, vrva, vsize, rraw, rsize))

def rva_to_file_offset(rva):
    for name, vrva, vsize, rraw, rsize in sections:
        if vrva <= rva < vrva + max(vsize, rsize):
            return rraw + (rva - vrva)
    return None

md = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_64)

# Disassemble putStr and putStrProp
for name, rva in [("putStr", 0x009AC180), ("putStrProp", 0x009AB910)]:
    foff = rva_to_file_offset(rva)
    print(f"\n=== {name} (RVA 0x{rva:X}, File Offset 0x{foff:X}) ===")
    code = data[foff : foff + 120]
    for ins in md.disasm(code, image_base + rva):
        print(f"0x{ins.address:X}:  {ins.mnemonic:8s} {ins.op_str}")

