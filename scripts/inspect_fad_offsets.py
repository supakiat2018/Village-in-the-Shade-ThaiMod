import struct

fairy_path = r"C:\Program Files (x86)\Steam\steamapps\common\Village in the Shade\data\fairy_1_00.dat"

with open(fairy_path, "rb") as f:
    f.seek(0x6F74F400)
    fad_hdr = f.read(0x5000)

print("Let's inspect 0x0F80 to 0x1400 in 32-byte chunks:")
for pos in range(0x0F80, 0x1500, 32):
    chunk = fad_hdr[pos : pos + 32]
    u1, u2, u3, u4 = struct.unpack("<QQQQ", chunk)
    print(f"0x{pos:04X}: u1=0x{u1:016X}, u2=0x{u2:016X}, u3=0x{u3:016X}, u4=0x{u4:016X}")
