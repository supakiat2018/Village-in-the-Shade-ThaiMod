import struct
import capstone

exe_path = r"C:\Program Files (x86)\Steam\steamapps\common\Village in the Shade\village.exe"
with open(exe_path, "rb") as f:
    data = f.read()

md = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_64)

# Search for any instruction with 0x26
# mov word ptr [...+0x26], ...
# 66 C7 4? 26 xx xx or 66 89 4? 26
print("Searching for writes to +0x26 in .text...")
for foff in range(0x400, 0xA00000):
    b = data[foff:foff+8]
    if len(b) < 6: break
    # 66 c7 41 26 (mov word ptr [rcx+0x26], imm16)
    # 66 c7 43 26 (mov word ptr [rbx+0x26], imm16)
    # 66 89 ... 26
    if b[0] == 0x66 and (b[1] in (0xC7, 0x89)) and b[3] == 0x26:
        # disassemble this instruction
        for ins in md.disasm(data[foff:foff+15], 0x140000000 + foff + 0xC00):
            print(f"FileOffset 0x{foff:X} (RVA 0x{foff+0xC00:X}): {ins.mnemonic} {ins.op_str} (hex: {ins.bytes.hex()})")
            break

