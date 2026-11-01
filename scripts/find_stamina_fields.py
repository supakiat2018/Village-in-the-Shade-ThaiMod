import struct
import capstone

v120_path = r"D:\Users\Supakiat\Desktop\Village_in_the_Shade_ThaiMod_Dev\village_thai_keyboard_patched_v120.exe"
v130_path = r"C:\Program Files (x86)\Steam\steamapps\common\Village in the Shade\village.exe.bak"

with open(v120_path, "rb") as f:
    v120_data = f.read()

with open(v130_path, "rb") as f:
    v130_data = f.read()

md = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_64)

# Search for [reg + 0x398] and [reg + 0x3A4]
needle_398 = struct.pack("<I", 0x398)
needle_3a4 = struct.pack("<I", 0x3A4)

# Find in v1.20
print("--- v1.20 instances of 0x398 & 0x3A4 ---")
pos = 0
found = []
while True:
    pos = v120_data.find(needle_398, pos)
    if pos == -1: break
    for start in range(pos - 6, pos + 1):
        for insn in md.disasm(v120_data[start : start + 12], start):
            if "0x398" in insn.op_str.lower() and insn.address <= pos < insn.address + insn.size:
                # check if near 0x3A4
                near_data = v120_data[start - 20 : start + 40]
                if needle_3a4 in near_data:
                    found.append(insn.address)
                    print(f"  v1.20 at 0x{insn.address:X}: {insn.mnemonic} {insn.op_str}")
                    # print chunk
                    for sub in md.disasm(v120_data[start - 10 : start + 30], start - 10):
                        print(f"      {sub.mnemonic} {sub.op_str}")
                    break
    pos += 1
    if len(found) >= 2: break

# Now find corresponding function in v1.30
print("\n--- v1.30 instances of 0x398 & 0x3A4 ---")
pos = 0
found130 = []
while True:
    pos = v130_data.find(needle_398, pos)
    if pos == -1: break
    for start in range(pos - 6, pos + 1):
        for insn in md.disasm(v130_data[start : start + 12], start):
            if "0x398" in insn.op_str.lower() and insn.address <= pos < insn.address + insn.size:
                near_data = v130_data[start - 20 : start + 40]
                if needle_3a4 in near_data:
                    found130.append(insn.address)
                    print(f"  v1.30 at 0x{insn.address:X}: {insn.mnemonic} {insn.op_str}")
                    for sub in md.disasm(v130_data[start - 10 : start + 30], start - 10):
                        print(f"      {sub.mnemonic} {sub.op_str}")
                    break
    pos += 1
    if len(found130) >= 2: break
