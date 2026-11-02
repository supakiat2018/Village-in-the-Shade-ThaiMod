import struct
path = r"D:\Users\Supakiat\Desktop\Mover\QuickBMS\Extracted_Data_v130\data\database\texture.dat"
with open(path, "rb") as f:
    data = f.read()

header = data[:64]
rec_count, unk1, str_table_offset, rec_size = struct.unpack_from("<IIII", data, 0)
header_size = 64  # or let's find header size

print(f"Header: count={rec_count}, unk1={unk1}, str_offset=0x{str_table_offset:X}, rec_size={rec_size}")

for i in range(5):
    offset = 64 + i * rec_size
    rec = data[offset : offset + rec_size]
    print(f"\n--- Record {i} ---")
    vals = struct.unpack("<29I", rec)
    for j, v in enumerate(vals):
        str_val = ""
        if str_table_offset <= v < len(data):
            end = data.find(b"\x00", v)
            if end != -1:
                str_val = data[v:end].decode("ascii", errors="ignore")
        if str_val:
            print(f"  Field {j:2d}: 0x{v:06X} -> \"{str_val}\"")
        elif v != 0:
            print(f"  Field {j:2d}: {v} (0x{v:X})")
