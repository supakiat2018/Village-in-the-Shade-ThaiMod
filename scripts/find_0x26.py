import struct
import capstone

exe_path = r"C:\Program Files (x86)\Steam\steamapps\common\Village in the Shade\village.exe"
with open(exe_path, "rb") as f:
    data = f.read()

md = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_64)

# Disassemble putStr from 0x9AC180 for 0x900 bytes
rva = 0x009AC180
foff = 0x9AB580
code = data[foff : foff + 0x900]

print("Searching for 0x26 in putStr...")
for ins in md.disasm(code, 0x1409AC180):
    if "26" in ins.op_str:
        print(f"0x{ins.address:X}:  {ins.mnemonic:8s} {ins.op_str}")

print("\nSearching for calls or references around putStr...")
