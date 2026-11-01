import struct

dat_path = r"C:\Program Files (x86)\Steam\steamapps\common\Village in the Shade\data.dat"

with open(dat_path, "rb") as f:
    magic = f.read(8)
    count = struct.unpack("<I", f.read(4))[0]
    total_sz = struct.unpack("<I", f.read(4))[0]
    print(f"Magic: {magic}, File Count: {count}, Total Size: {total_sz}")
    
    # In FAD format, let's see how entries are structured
    f.seek(0xFC0)
    for i in range(min(count, 30)):
        entry_raw = f.read(32)
        off, sz, unk, sz2 = struct.unpack("<QQQQ", entry_raw)
        print(f"Entry {i}: offset=0x{off:X}, size={sz}")
