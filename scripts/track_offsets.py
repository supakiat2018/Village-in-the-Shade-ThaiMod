import struct
import capstone

v120_path = r"D:\Users\Supakiat\Desktop\Village_in_the_Shade_ThaiMod_Dev\village_thai_keyboard_patched_v120.exe"
v130_path = r"C:\Program Files (x86)\Steam\steamapps\common\Village in the Shade\village.exe.bak"

with open(v120_path, "rb") as f:
    v120_data = f.read()

with open(v130_path, "rb") as f:
    v130_data = f.read()

# Let's search in v1.20 for instructions accessing 0x3270, 0x32A0, 0x32B8
# e.g. [reg + 0x3270] -> opcode encoding for disp32 0x00003270 is 70 32 00 00
# disp32 for 0x32A0 is A0 32 00 00
# disp32 for 0x32B8 is B8 32 00 00
# disp32 for 0x32C0 is C0 32 00 00

md = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_64)

for target_disp, name in [(0x3270, "Time"), (0x32A0, "Money"), (0x32B8, "StaminaPtr"), (0x32C0, "Inv0")]:
    needle = struct.pack("<I", target_disp)
    matches_120 = []
    pos = 0
    while True:
        pos = v120_data.find(needle, pos)
        if pos == -1: break
        matches_120.append(pos)
        pos += 1
    
    print(f"\n==================== {name} (0x{target_disp:X}) in v1.20 ====================")
    # Check instructions at these offsets
    valid_contexts = []
    for off in matches_120:
        # Check 15 bytes before
        for test_start in range(off - 10, off + 1):
            chunk = v120_data[test_start : test_start + 15]
            for insn in md.disasm(chunk, test_start):
                if hex(target_disp) in insn.op_str.lower() and insn.address <= off < insn.address + insn.size:
                    # Valid instruction!
                    ctx_before = v120_data[insn.address - 20 : insn.address]
                    valid_contexts.append((insn.address, insn.mnemonic + " " + insn.op_str, ctx_before))
                    break
    
    print(f"Found {len(valid_contexts)} instruction sites in v1.20")
    for addr, text, ctx in valid_contexts[:3]:
        print(f"  v1.20 [0x{addr:X}]: {text}")
        # Now search for ctx in v1.30!
        if len(ctx) >= 12:
            # try fuzzy matching or exact matching
            c_pos = v130_data.find(ctx[-12:])
            if c_pos != -1:
                chunk130 = v130_data[c_pos + 12 : c_pos + 30]
                for insn130 in md.disasm(chunk130, c_pos + 12):
                    print(f"      -> v1.30 match: {insn130.mnemonic} {insn130.op_str}")
                    break
