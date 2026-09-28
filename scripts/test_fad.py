import struct, re

fad_path = 'C:/Program Files (x86)/Steam/steamapps/common/Village in the Shade/data/fairy_1_00.dat'
fad_base = 0x42590C00

with open(fad_path, 'rb') as f:
    f.seek(fad_base)
    header = f.read(0x4000)

entries = []
pos = 0x1018
while pos + 32 <= len(header):
    sz, off = struct.unpack('<QI', header[pos:pos+12])
    if sz == 0 and off == 0:
        break
    entries.append((sz, off))
    pos += 32

print(f"Total entries in TOC: {len(entries)}")

with open('C:/Users/Supakiat/Desktop/Village-in-the-Shade-ThaiMod/src/text_dump.c', 'r', encoding='utf-8') as f:
    lines = f.readlines()

subfiles = []
for line in lines:
    m = re.search(r'(0x[0-9A-Fa-f]+ULL),\s*"([^"]+)",\s*"([^"]+)",\s*(\d+),\s*(\d+),\s*(TRUE|FALSE)', line)
    if m:
        subfiles.append((int(m.group(1).replace('ULL',''), 16), m.group(2), m.group(3), int(m.group(4)), int(m.group(5)), m.group(6) == 'TRUE'))

matched = 0
mapping_dict = {}
for off, fn, alt_fn, w, h, is_desc in subfiles:
    if not is_desc:
        rel = off - fad_base - 64
        found_idx = None
        for i, (sz, eoff) in enumerate(entries):
            if eoff == rel:
                found_idx = i
                break
        if found_idx is not None:
            matched += 1
            mapping_dict[found_idx] = (fn, w, h)
        else:
            print('Unmatched:', fn, hex(off), hex(rel))

print(f'Total subfiles in code: {len(subfiles)//2}, Matched with TOC index: {matched}')
for k in sorted(mapping_dict.keys()):
    print(f"TOC Index {k:3d} -> {mapping_dict[k][0]} ({mapping_dict[k][1]}x{mapping_dict[k][2]})")
