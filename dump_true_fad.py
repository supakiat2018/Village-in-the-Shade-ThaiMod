import struct
import os

fairy_path = r"C:\Program Files (x86)\Steam\steamapps\common\Village in the Shade\data\fairy_1_00.dat"
base_off = 0x6F74F400

with open(fairy_path, "rb") as f:
    f.seek(base_off)
    fad_hdr = f.read(0x6000)
    
    entries = []
    # TOC starts at 0x0FC0, 32 bytes per entry
    for idx in range(360):
        pos = 0x0FC0 + idx * 32
        rel_off, str_off, w, h, pad, sz = struct.unpack('<IIIIQQ', fad_hdr[pos:pos+32])
        if rel_off == 0 and sz == 0:
            continue
        
        # Read descriptor at base_off + rel_off + 32
        f.seek(base_off + rel_off + 32)
        desc = f.read(32)
        desc_tex_sz = struct.unpack('<Q', desc[:8])[0]
        desc_w = struct.unpack('<H', desc[8:10])[0]
        desc_h = struct.unpack('<H', desc[10:12])[0]
        
        # Read NLTX at base_off + rel_off + 64
        nltx_hdr = f.read(64)
        is_nltx = (nltx_hdr[:8] == b'NMPLTEX1')
        nltx_w = struct.unpack('<I', nltx_hdr[24:28])[0] if is_nltx else 0
        nltx_h = struct.unpack('<I', nltx_hdr[28:32])[0] if is_nltx else 0
        nltx_fmt = struct.unpack('<I', nltx_hdr[16:20])[0] if is_nltx else 0
        nltx_body_sz = struct.unpack('<I', nltx_hdr[48:52])[0] if is_nltx else 0
        
        entries.append({
            'idx': idx,
            'pos': pos,
            'rel_off': rel_off,
            'desc_off': rel_off + 32,
            'data_off': rel_off + 64,
            'w': desc_w,
            'h': desc_h,
            'nltx_w': nltx_w,
            'nltx_h': nltx_h,
            'sz': sz,
            'desc_tex_sz': desc_tex_sz,
            'nltx_body_sz': nltx_body_sz,
            'is_nltx': is_nltx
        })

print(f"Total entries in FAD: {len(entries)}")

out_path = r"D:\Users\Supakiat\Desktop\Village_in_the_Shade_ThaiMod_Dev\v130_true_fad_entries.txt"
with open(out_path, "w", encoding="utf-8") as out:
    for e in entries:
        out.write(f"TOC[{e['idx']:3d}]: rel_off=0x{e['rel_off']:08X}, desc_off=0x{e['desc_off']:08X}, "
                  f"dim=({e['w']:4d}x{e['h']:4d}), nltx_dim=({e['nltx_w']:4d}x{e['nltx_h']:4d}), "
                  f"sz={e['sz']:8d}, nltx_sz={e['nltx_body_sz']:8d}\n")

print(f"Wrote {len(entries)} entries to {out_path}")
