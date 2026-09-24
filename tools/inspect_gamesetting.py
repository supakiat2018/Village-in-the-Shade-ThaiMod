import struct
import os
import json

archive_path = r"C:\Program Files (x86)\Steam\steamapps\common\Village in the Shade\data.dat"

with open(archive_path, "rb") as f:
    magic = f.read(8)
    assert magic == b"FAFULLFS"
    count, unk, str_off, str_len, toc_off, pad = struct.unpack("<IIQQQQ", f.read(40))
    f.seek(toc_off)
    tocs = []
    for _ in range(count):
        h, n_off, u1, sz, off, u2 = struct.unpack("<QQQQQQ", f.read(48))
        tocs.append((off, sz, n_off))
    f.seek(str_off)
    str_table = f.read(str_len)
    
    gs_off = None
    gs_sz = None
    for off, sz, n_off in tocs:
        name = str_table[n_off:].split(b"\x00")[0].decode("latin1")
        if name == "data/database/gamesetting.dat":
            gs_off = off
            gs_sz = sz
            break

print(f"gamesetting.dat at 0x{gs_off:X}, size {gs_sz}")

with open(archive_path, "rb") as f:
    f.seek(gs_off)
    data = f.read(gs_sz)

rec_count, rec_data_sz, orig_text_sz = struct.unpack("<III", data[:12])
print(f"rec_count: {rec_count}, rec_data_sz: {rec_data_sz}, orig_text_sz: {orig_text_sz}")

# Let's see the structure of records in gamesetting.dat
# In gamesetting.dat, is it variable length or fixed length?
# Note: rec_data_sz is 8544. 12 + 8544 = 8556? Or text starts at 12 + rec_data_sz?
text_start = 12 + rec_data_sz
print(f"text_start: {text_start}, text_sz: {orig_text_sz}, total: {text_start + orig_text_sz} vs gs_sz: {gs_sz}")

text_blob = data[text_start:]
print(f"Actual text blob length: {len(text_blob)}")

# Let's inspect records
pos = 12
for r in range(min(rec_count, 10)):
    sz = struct.unpack("<I", data[pos:pos+4])[0]
    rec_bytes = data[pos:pos+sz+4]
    u = struct.unpack(f"<{len(rec_bytes)//4}I", rec_bytes)
    print(f"Record {r}: size={sz}, fields={u[:10]}")
    # Let's find string references in this record
    for idx, val in enumerate(u):
        if val < len(text_blob):
            s = text_blob[val:].split(b"\x00")[0]
            if len(s) > 0 and len(s) < 100:
                try:
                    s_str = s.decode("utf-8")
                    if any(ord(c) > 127 for c in s_str) or s_str.isascii():
                        # print field
                        pass
                except:
                    pass
    pos += sz + 4

# Let's find occurrences of あり and なし in data
for target in [b"\xe3\x81\x82\xe3\x82\x8a\x00", b"\xe3\x81\xaa\xe3\x81\x97\x00"]:
    idx = 0
    tname = target.decode("utf-8", errors="ignore")
    print(f"\nOccurrences of '{tname}':")
    while True:
        idx = data.find(target, idx)
        if idx == -1:
            break
        # Check context
        ctx = data[max(0, idx-10):idx+len(target)+10]
        in_text_blob = idx >= text_start
        print(f"  at 0x{idx:X} (in text blob: {in_text_blob}, rel off: 0x{idx - text_start:X}): {ctx.hex()}")
        idx += len(target)
