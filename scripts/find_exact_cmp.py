exe_path = r"C:\Program Files (x86)\Steam\steamapps\common\Village in the Shade\village.exe"
with open(exe_path, "rb") as f:
    data = f.read()

import capstone
md = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_64)

# find the exact bytes of `cmp word ptr [rcx + 0x26], 0`
# 66 83 79 26 00 or 66 81 79 26 00 00
pat = bytes.fromhex("66 83 79 26 00")
idx = data.find(pat)
print("Index:", hex(idx))
if idx == -1:
    pat = bytes.fromhex("66 81 79 26 00 00")
    idx = data.find(pat)
    print("Index 2:", hex(idx))

if idx != -1:
    code = data[idx - 40 : idx + 100]
    for ins in md.disasm(code, 0x140000000 + idx - (0x9AB580 - 0x9AC180)): # rough
        print(f"0x{ins.address:X}:  {ins.mnemonic:8s} {ins.op_str}  (bytes: {ins.bytes.hex()})")
