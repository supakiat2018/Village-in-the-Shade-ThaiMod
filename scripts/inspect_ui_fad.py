import os
import struct

# Let's search which texture has "Sold Out" or what files were in 100-110 in v1.30 data_ui.fad
v130_ui_fad = r"C:\Program Files (x86)\Steam\steamapps\common\Village in the Shade\data_ui.fad"

with open(v130_ui_fad, "rb") as f:
    fad_data = f.read(0x10000)

count = struct.unpack_from("<I", fad_data, 4)[0]
print("Total entries in v1.30 data_ui.fad:", count)

# Read TOC: entries start at 0xFC0, 32 bytes each
# Entry: [offset(8), size(8), unk(8), size2(8)]
for i in range(min(count, 120)):
    pos = 0xFC0 + i * 32
    off, sz = struct.unpack_from("<QQ", fad_data, pos)
    if 95 <= i <= 115:
        print(f"Entry {i}: offset=0x{off:X}, size={sz}")
