import struct
import os

fairy_path = r"C:\Program Files (x86)\Steam\steamapps\common\Village in the Shade\data\fairy_1_00.dat"

with open(fairy_path, "rb") as f:
    f.seek(0x6F74F400)
    fad_hdr = f.read(0x5000)

entries = []
pos = 0x0FC0
idx = 0
while pos + 32 <= len(fad_hdr):
    u1, u2, u3, u4 = struct.unpack_from("<QQQQ", fad_hdr, pos)
    rel_off = u1 & 0xFFFFFFFF
    str_id = (u1 >> 32) & 0xFFFFFFFF
    w = u2 & 0xFFFF
    h = (u2 >> 32) & 0xFFFF
    sz = u4 & 0xFFFFFFFF
    
    if rel_off == 0 and sz == 0:
        break
        
    entries.append({
        "index": idx,
        "toc_pos": hex(pos),
        "rel_off": hex(rel_off),
        "str_id": hex(str_id),
        "width": w,
        "height": h,
        "size": sz
    })
    pos += 32
    idx += 1

print(f"Decoded {len(entries)} FAD TOC entries starting at 0x0FC0!")
for e in entries[:40]:
    print(f"Index {e['index']:3d} (TOC {e['toc_pos']}): RelOff={e['rel_off']:>10}, Dim=({e['width']:4d}x{e['height']:4d}), Size={e['size']:8d}, StrID={e['str_id']}")
