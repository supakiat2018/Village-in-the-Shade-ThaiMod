fairy_path = r"C:\Program Files (x86)\Steam\steamapps\common\Village in the Shade\data\fairy_1_00.dat"

with open(fairy_path, "rb") as f:
    f.seek(0x6F74F400)
    fad_hdr = f.read(0x2000)

# Print entries in 32-byte chunks from 0x0040 to 0x1000
for i in range(2, 60):
    pos = i * 32
    chunk = fad_hdr[pos : pos + 32]
    # Check if there is a string in chunk
    text = chunk[:16].rstrip(b'\x00').decode('latin1', errors='ignore')
    hex_rest = chunk[16:].hex(' ')
    print(f"[{i:2d}] 0x{pos:04X}: {text:<16} | {hex_rest}")
