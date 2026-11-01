import capstone

v130_path = r"C:\Program Files (x86)\Steam\steamapps\common\Village in the Shade\village.exe.bak"

with open(v130_path, "rb") as f:
    v130_data = f.read()

md = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_64)

# In scan_v130.py, Can Submit Any Item was at: FileOffset=0x355620, RVA=0x356220
# Let's inspect bytes at 0x355620 + 0x44 = 0x355664
patch_site = 0x355620 + 0x44
print("Bytes at Can Submit Any Item + 0x44 in v1.30:", v130_data[patch_site : patch_site + 6].hex(" "))
for insn in md.disasm(v130_data[patch_site - 10 : patch_site + 20], 0x140356220 + 0x44 - 10):
    print(f"  0x{insn.address:X}: {insn.mnemonic:<8} {insn.op_str}")
