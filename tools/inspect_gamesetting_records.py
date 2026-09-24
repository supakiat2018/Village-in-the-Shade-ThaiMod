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
    
    for off, sz, n_off in tocs:
        name = str_table[n_off:].split(b"\x00")[0].decode("latin1")
        if name == "data/database/gamesetting.dat":
            f.seek(off)
            data = f.read(sz)
            break

rec_count, rec_data_sz, orig_text_sz = struct.unpack("<III", data[:12])
text_start = 12 + rec_data_sz
text_blob = data[text_start:]

pos = 12
for r in range(rec_count):
    rec_len = struct.unpack("<I", data[pos:pos+4])[0]
    rec_bytes = data[pos:pos+4+rec_len]
    u = struct.unpack(f"<{len(rec_bytes)//4}I", rec_bytes)
    # Check fields
    string_fields = []
    for idx, val in enumerate(u[1:]): # skip rec_len
        # If val is an offset into text_blob
        if val < len(text_blob):
            # check if at text_blob[val] there is a valid null-terminated utf-8 string
            end = text_blob.find(b"\0", val)
            if end != -1 and end > val:
                s = text_blob[val:end]
                try:
                    s_str = s.decode("utf-8")
                    if len(s_str) > 0:
                        string_fields.append((idx+1, val, s_str))
                except:
                    pass
    print(f"Record #{r:2d} (len={rec_len:4d}, id={u[1]}): {len(string_fields)} string refs")
    for field_idx, val, s_str in string_fields[:6]:
        print(f"   field[{field_idx:2d}] = off 0x{val:X}: '{s_str[:30]}'")
    pos += 4 + rec_len
