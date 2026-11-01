import struct
import capstone

v120_path = r"D:\Users\Supakiat\Desktop\Village_in_the_Shade_ThaiMod_Dev\village_thai_keyboard_patched_v120.exe"
v130_path = r"C:\Program Files (x86)\Steam\steamapps\common\Village in the Shade\village.exe.bak"

with open(v120_path, "rb") as f:
    v120_data = f.read()

with open(v130_path, "rb") as f:
    v130_data = f.read()

md = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_64)

# Look at Stamina: 0xEFAE9 in v1.20:
print("--- v1.20 around 0xEFAE9 ---")
for insn in md.disasm(v120_data[0xEFAE9 - 20 : 0xEFAE9 + 40], 0xEFAE9 - 20):
    print(f"  0x{insn.address:X}: {insn.mnemonic} {insn.op_str}")

# Find surrounding bytes in v1.30
needle = v120_data[0xEFAE9 - 15 : 0xEFAE9]
pos130 = v130_data.find(needle)
print(f"\nFound in v1.30 at 0x{pos130:X}")
if pos130 != -1:
    print("--- v1.30 around matched site ---")
    for insn in md.disasm(v130_data[pos130 : pos130 + 40], pos130):
        print(f"  0x{insn.address:X}: {insn.mnemonic} {insn.op_str}")

# Look at Time: 0xE705B in v1.20
print("\n--- v1.20 around 0xE705B ---")
for insn in md.disasm(v120_data[0xE705B - 20 : 0xE705B + 40], 0xE705B - 20):
    print(f"  0x{insn.address:X}: {insn.mnemonic} {insn.op_str}")

needle2 = v120_data[0xE705B - 15 : 0xE705B]
pos130_2 = v130_data.find(needle2)
print(f"\nFound in v1.30 at 0x{pos130_2:X}")
if pos130_2 != -1:
    print("--- v1.30 around matched site ---")
    for insn in md.disasm(v130_data[pos130_2 : pos130_2 + 40], pos130_2):
        print(f"  0x{insn.address:X}: {insn.mnemonic} {insn.op_str}")
