import re
import capstone

v130_path = r"C:\Program Files (x86)\Steam\steamapps\common\Village in the Shade\village.exe.bak"

with open(v130_path, "rb") as f:
    v130_data = f.read()

md = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_64)

# Pattern: 40 53 48 83 EC 30 48 8B 05 ? ? ? ? 48 33 C4 48 89 44 24 28 80 B9 4C 03 00 00 00
pat_str = "40 53 48 83 EC 30 48 8B 05 ? ? ? ? 48 33 C4 48 89 44 24 28 80 B9 4C 03 00 00 00"

def pat_to_regex(pat_str):
    tokens = pat_str.strip().split()
    rx_bytes = []
    for t in tokens:
        if t == '?' or t == '??':
            rx_bytes.append(b'.')
        else:
            rx_bytes.append(re.escape(bytes.fromhex(t)))
    return b''.join(rx_bytes)

rx = re.compile(pat_to_regex(pat_str), re.DOTALL)
matches = [m.start() for m in rx.finditer(v130_data)]
print("Matches in v1.30:", [hex(m) for m in matches])

for m in matches:
    rva = m - 0x400 + 0x1000
    print(f"RVA: 0x{rva:X}")
    for insn in md.disasm(v130_data[m : m + 35], 0x140000000 + rva):
        print(f"  0x{insn.address:X}: {insn.mnemonic:<8} {insn.op_str}")
