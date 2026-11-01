import struct
import capstone

v120_path = r"D:\Users\Supakiat\Desktop\Village_in_the_Shade_ThaiMod_Dev\village_thai_keyboard_patched_v120.exe"
v130_path = r"C:\Program Files (x86)\Steam\steamapps\common\Village in the Shade\village.exe.bak"

with open(v120_path, "rb") as f:
    v120_data = f.read()

with open(v130_path, "rb") as f:
    v130_data = f.read()

md = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_64)

# In v1.20, noclip RVA was 0x6C4A80 -> File offset was:
# Let's find PE file offset for RVA 0x6C4A80
# In v1.20, .text starts at raw 0x400, VA 0x1000, so file offset = 0x6C4A80 - 0x1000 + 0x400 = 0x6C3E80
file_off_120 = 0x6C4A80 - 0x1000 + 0x400
print("v1.20 noclip context:")
chunk120 = v120_data[file_off_120 : file_off_120 + 30]
print("bytes:", chunk120[:16].hex(" "))
for insn in md.disasm(chunk120, 0x1406C4A80):
    print(f"  {insn.mnemonic} {insn.op_str}")

# Now search for this function pattern in v1.30
pat = chunk120[:24]
pos130 = v130_data.find(pat)
print(f"\nPattern match in v1.30: file 0x{pos130:X}")
if pos130 != -1:
    rva130 = pos130 - 0x400 + 0x1000
    print(f"v1.30 noclip RVA: 0x{rva130:X}")
    chunk130 = v130_data[pos130 : pos130 + 30]
    for insn in md.disasm(chunk130, 0x140000000 + rva130):
        print(f"  {insn.mnemonic} {insn.op_str}")
