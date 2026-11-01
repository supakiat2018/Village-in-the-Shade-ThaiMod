import struct
import capstone

v130_path = r"C:\Program Files (x86)\Steam\steamapps\common\Village in the Shade\village.exe.bak"

with open(v130_path, "rb") as f:
    v130_data = f.read()

md = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_64)

# Search for [reg + 0x3270] in v1.30
disp_time = struct.pack("<I", 0x3270)
disp_stam = struct.pack("<I", 0x32B8)

pos = 0
found_time = 0
while True:
    pos = v130_data.find(disp_time, pos)
    if pos == -1: break
    # check instructions
    for test_start in range(pos - 6, pos + 1):
        for insn in md.disasm(v130_data[test_start : test_start + 12], test_start):
            if "0x3270" in insn.op_str.lower() and insn.address <= pos < insn.address + insn.size:
                print(f"v1.30 Time instruction at 0x{insn.address:X}: {insn.mnemonic} {insn.op_str}")
                # print 3 instructions before
                for prev in md.disasm(v130_data[test_start - 15 : test_start], test_start - 15):
                    print(f"    prev: {prev.mnemonic} {prev.op_str}")
                found_time += 1
                break
    pos += 1
    if found_time >= 3:
        break

pos = 0
found_stam = 0
while True:
    pos = v130_data.find(disp_stam, pos)
    if pos == -1: break
    for test_start in range(pos - 6, pos + 1):
        for insn in md.disasm(v130_data[test_start : test_start + 12], test_start):
            if "0x32b8" in insn.op_str.lower() and insn.address <= pos < insn.address + insn.size:
                print(f"v1.30 Stamina instruction at 0x{insn.address:X}: {insn.mnemonic} {insn.op_str}")
                for prev in md.disasm(v130_data[test_start - 15 : test_start], test_start - 15):
                    print(f"    prev: {prev.mnemonic} {prev.op_str}")
                found_stam += 1
                break
    pos += 1
    if found_stam >= 3:
        break
