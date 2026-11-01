import os
import struct

fairy_path = r"C:\Program Files (x86)\Steam\steamapps\common\Village in the Shade\data\fairy_1_00.dat"
out_dir = r"D:\Users\Supakiat\Desktop\Village_in_the_Shade_ThaiMod_Dev\extracted_v130_resident_fad"
os.makedirs(out_dir, exist_ok=True)

with open(fairy_path, "rb") as f:
    base_off = 0x6F74F400
    f.seek(base_off)
    
    # Read FAD header
    fad_hdr = f.read(0x5000)
    magic = fad_hdr[:8]
    count = struct.unpack_from("<I", fad_hdr, 8)[0]
    print(f"FAD Magic: {magic}, Subfile count: {count}")
    
    entries = []
    for i in range(count):
        pos = 0x1018 + i * 32
        if pos + 32 > len(fad_hdr):
            break
        entry_sz = struct.unpack_from("<Q", fad_hdr, pos)[0]
        rel_off = struct.unpack_from("<I", fad_hdr, pos + 8)[0]
        entries.append((i, rel_off, entry_sz))
        
    print(f"Read {len(entries)} TOC entries from resident_lang_jp.fad")

    report = []
    for idx, rel_off, sz in entries:
        if sz == 0:
            continue
        abs_off = base_off + rel_off
        f.seek(abs_off)
        header_chunk = f.read(64)
        desc = header_chunk[:32]
        data_header = header_chunk[32:64]
        
        m1 = desc[:4]
        m2 = data_header[:4]
        w, h = 0, 0
        fmt = ""
        if b'NLTX' in header_chunk:
            nltx_pos = header_chunk.find(b'NLTX')
            w, h = struct.unpack_from("<HH", header_chunk, nltx_pos + 8)
            fmt_id = struct.unpack_from("<I", header_chunk, nltx_pos + 12)[0]
            fmt = hex(fmt_id)
        
        report.append((idx, rel_off, sz, m1, m2, w, h, fmt))

print(f"Total non-zero entries: {len(report)}")
with open(os.path.join(out_dir, "v130_toc_report.txt"), "w", encoding="utf-8") as rf:
    for idx, rel_off, sz, m1, m2, w, h, fmt in report:
        rf.write(f"Index {idx:3d}: RelOff=0x{rel_off:08X}, Size={sz:8d}, Desc={m1}, Data={m2}, Dim=({w:4d}x{h:4d}), Fmt={fmt}\n")

print("Wrote v130_toc_report.txt successfully!")
