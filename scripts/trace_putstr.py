import struct
import capstone

exe_path = r"C:\Program Files (x86)\Steam\steamapps\common\Village in the Shade\village.exe"
with open(exe_path, "rb") as f:
    data = f.read()

md = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_64)

# Disassemble putStr: RVA 0x9AC180 (FileOffset 0x9AB580)
foff = 0x9AB580
code = data[foff : foff + 0x8B0] # to 0x1409ACA30

print("Disassembling entire putStr...")
lines = []
for ins in md.disasm(code, 0x1409AC180):
    lines.append(f"0x{ins.address:X}:  {ins.mnemonic:8s} {ins.op_str}")

print(f"Total instructions in putStr: {len(lines)}")
# Find any access to 0x26, 0x28, or calls
for l in lines:
    if "0x26" in l or "0x28" in l or "call" in l or "xmm" in l and ("add" in l or "sub" in l):
        print(l)
