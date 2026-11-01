import struct
import capstone

exe_path = r"C:\Program Files (x86)\Steam\steamapps\common\Village in the Shade\village.exe"
with open(exe_path, "rb") as f:
    data = f.read()

md = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_64)

for foff, name in [(0x9ABF92, "setMode_9ACB92"), (0x7F88AE, "setMode_7F94AE")]:
    print(f"\n=== {name} (FileOffset 0x{foff:X}) ===")
    code = data[foff - 20 : foff + 40]
    for ins in md.disasm(code, 0x140000000 + foff + 0xC00 - 20):
        print(f"0x{ins.address:X}:  {ins.mnemonic:8s} {ins.op_str}  (bytes: {ins.bytes.hex()})")

