import struct

archive_path = r"C:\Program Files (x86)\Steam\steamapps\common\Village in the Shade\data.dat"

with open(archive_path, "rb") as f:
    count, unk, str_off, str_len, toc_off, pad = struct.unpack("<IIQQQQ", f.read(48)[8:])
    f.seek(toc_off)
    tocs = []
    for _ in range(count):
        h, n_off, u1, sz, off, u2 = struct.unpack("<QQQQQQ", f.read(48))
        tocs.append((off, sz, n_off))
    f.seek(str_off)
    str_table = f.read(str_len)
    
db_files = []
for off, sz, n_off in tocs:
    name = str_table[n_off:].split(b"\x00")[0].decode("latin1")
    if name.startswith("data/database/"):
        db_files.append((name, sz, off))

db_files.sort(key=lambda x: x[0])
print(f"Found {len(db_files)} files in data/database/:")
for name, sz, off in db_files:
    print(f"  {name:40s} size={sz:8d} (0x{sz:X}) off=0x{off:X}")
