import struct
import capstone

exe_path = r"C:\Program Files (x86)\Steam\steamapps\common\Village in the Shade\village.exe"
with open(exe_path, "rb") as f:
    data = f.read()

md = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_64)

# putStrAlign: RVA 0x9ACC10 (FileOffset 0x9AC010)
foff = 0x9AC010
code = data[foff : foff + 150]

print("putStrAlign disassembly:")
for ins in md.disasm(code, 0x1409ACC10):
    print(f"0x{ins.address:X}:  {ins.mnemonic:8s} {ins.op_str}")

