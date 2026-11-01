import struct
import capstone

exe_path = r"C:\Program Files (x86)\Steam\steamapps\common\Village in the Shade\village.exe"
with open(exe_path, "rb") as f:
    data = f.read()

# putStr RVA is 0x009AC180
# In x86_64, call rel32: E8 xx xx xx xx
# rel32 = target_rva - (call_ins_rva + 5)
target_rva = 0x009AC180
target_rva_alt = 0x009AC1A8 # internal label

print(f"Searching calls to putStr (0x{target_rva:X})...")
calls = []
for i in range(len(data) - 5):
    if data[i] == 0xE8:
        rel32 = struct.unpack_from("<i", data, i+1)[0]
        # In village.exe, file offset ~= RVA - 0xC00 in .text? Let's check sections
        # Or let's check with rva mapping
        pass

# Let's map .text
# In find_exact_cmp: RVA = FileOffset + 0xC00? Let's verify:
# File offset 0x9AB580 -> RVA 0x9AC180 (diff = +0xC00)
# Let's check:
text_raw_start = 0x400
text_raw_end = 0xDE0000 # approximate

for foff in range(0x400, len(data) - 5):
    if data[foff] == 0xE8:
        rel32 = struct.unpack_from("<i", data, foff + 1)[0]
        call_rva = foff + 0xC00
        target = call_rva + 5 + rel32
        if target in (0x009AC180, 0x009AC1A8):
            calls.append((foff, call_rva, target))

print(f"Found {len(calls)} calls to putStr:")
for foff, rva, tgt in calls:
    print(f"  FileOffset: 0x{foff:X}, RVA: 0x{rva:X} -> Target: 0x{tgt:X}")
