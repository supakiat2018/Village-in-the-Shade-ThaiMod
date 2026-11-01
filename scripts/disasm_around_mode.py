import struct
import capstone

exe_path = r"C:\Program Files (x86)\Steam\steamapps\common\Village in the Shade\village.exe"
with open(exe_path, "rb") as f:
    data = f.read()

md = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_64)

# Disassemble around 0x1409ACA30
# 0x1409ACA30 - 0x1409AC180 = 0x8B0
# File offset: 0x9AB580 + 0x8B0 = 0x9ABE30
foff = 0x9ABE30 - 0x30
code = data[foff : foff + 0x120]

for ins in md.disasm(code, 0x1409ACA00):
    print(f"0x{ins.address:X}:  {ins.mnemonic:8s} {ins.op_str}  (bytes: {ins.bytes.hex()})")

