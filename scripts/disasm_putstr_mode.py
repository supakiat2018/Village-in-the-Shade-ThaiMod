import struct
import capstone

exe_path = r"C:\Program Files (x86)\Steam\steamapps\common\Village in the Shade\village.exe"
with open(exe_path, "rb") as f:
    data = f.read()

md = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_64)

# File offset for 0x1409ACA30
# RVA = 0x9ACA30
# File offset = 0x9ACA30 - 0xC00 = 0x9ABE30
foff = 0x9ABE30
code = data[foff : foff + 200]

for ins in md.disasm(code, 0x1409ACA30):
    print(f"0x{ins.address:X}:  {ins.mnemonic:8s} {ins.op_str}  (bytes: {ins.bytes.hex()})")
