import struct

dat_path = r"C:\Program Files (x86)\Steam\steamapps\common\Village in the Shade\data.dat"

with open(dat_path, "rb") as f:
    header = f.read(0x20)
    print("Header:", header[:16])

# Let's inspect data.dat format: usually has file count, TOC
# Let's check if it starts with FAD or NMPL or something
