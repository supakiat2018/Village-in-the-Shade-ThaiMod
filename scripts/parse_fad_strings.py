import struct

fairy_path = r"C:\Program Files (x86)\Steam\steamapps\common\Village in the Shade\data\fairy_1_00.dat"

with open(fairy_path, "rb") as f:
    f.seek(0x6F74F400)
    fad_hdr = f.read(0x10000)

print("FAD Header length:", len(fad_hdr))

# Let's see how strings are stored in this FAD header
# Let's find all null-terminated ASCII strings of length >= 4
strings = []
pos = 0
while pos < 0x2000:
    # check if printable ASCII
    if 32 <= fad_hdr[pos] <= 126:
        start = pos
        while pos < len(fad_hdr) and 32 <= fad_hdr[pos] <= 126:
            pos += 1
        if pos - start >= 4:
            s = fad_hdr[start:pos].decode('latin1')
            strings.append((start, s))
    pos += 1

print(f"Found {len(strings)} strings in FAD header:")
for off, s in strings[:30]:
    print(f"  0x{off:04X}: {s}")
