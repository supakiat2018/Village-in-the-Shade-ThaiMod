import struct

game_dat = r'C:\Program Files (x86)\Steam\steamapps\common\Village in the Shade\data\fairy_1_00.dat'
with open(game_dat, 'rb') as f:
    f.seek(0x6F74F400)
    fad_hdr = f.read(0x6000)

print("=== Name Records (0x0040 to 0x0FC0) ===")
name_dict = {}
for i, off in enumerate(range(0x0040, 0x0FC0, 32)):
    chunk = fad_hdr[off:off+32]
    # Name might be up to 32 bytes or 16 bytes + metadata
    s = chunk.split(b'\x00')[0].decode('shift-jis', errors='ignore')
    name_dict[i] = s
    if s:
        print(f"Record {i:3d} (0x{off:04X}): {s}")

print("\n=== TOC Records (from 0x0FC0) ===")
# Let's count how many TOC records
# In TOC, each entry is 32 bytes:
# uint32_t rel_off
# uint32_t str_id
# uint32_t width
# uint32_t height
# uint64_t pad
# uint64_t size
toc_entries = []
for idx in range(400):
    off = 0x0FC0 + idx * 32
    if off + 32 > len(fad_hdr):
        break
    entry = fad_hdr[off:off+32]
    rel_off, str_id, w, h, pad, sz = struct.unpack('<IIIIQQ', entry)
    if rel_off == 0 and sz == 0:
        continue
    name = name_dict.get(str_id, f"unknown_str_{str_id}")
    toc_entries.append((idx, off, rel_off, str_id, w, h, sz, name))

print(f"Total non-empty TOC entries found: {len(toc_entries)}")
for idx, off, rel_off, str_id, w, h, sz, name in toc_entries:
    print(f"TOC[{idx:3d}] @ 0x{off:04X}: rel_off=0x{rel_off:08X}, str_id={str_id:3d} ({name:<24}), {w:4d}x{h:<4d}, sz={sz:8d}")
