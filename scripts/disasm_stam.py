import capstone

v130_path = r"C:\Program Files (x86)\Steam\steamapps\common\Village in the Shade\village.exe.bak"

with open(v130_path, "rb") as f:
    v130_data = f.read()

md = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_64)

print("--- v1.30 Stamina function around 0xF2399 ---")
chunk = v130_data[0xF2380 : 0xF2430]
for insn in md.disasm(chunk, 0xF2380):
    print(f"  0x{insn.address:X}: {insn.mnemonic:<8} {insn.op_str}")
