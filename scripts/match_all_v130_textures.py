import struct
import os

fairy_path = r"C:\Program Files (x86)\Steam\steamapps\common\Village in the Shade\data\fairy_1_00.dat"
mod_tex_dir = r"C:\Program Files (x86)\Steam\steamapps\common\Village in the Shade\Mods\TextDump\textures"
out_dir = r"D:\Users\Supakiat\Desktop\Village_in_the_Shade_ThaiMod_Dev\v130_fad_dump"
os.makedirs(out_dir, exist_ok=True)

with open(fairy_path, "rb") as f:
    base_off = 0x6F74F400
    f.seek(base_off)
    fad_hdr = f.read(0x5000)
    
    pos = 0x0FC0
    idx = 0
    fad_entries = []
    while pos + 32 <= len(fad_hdr):
        u1, u2, u3, u4 = struct.unpack_from("<QQQQ", fad_hdr, pos)
        rel_off = u1 & 0xFFFFFFFF
        str_id = (u1 >> 32) & 0xFFFFFFFF
        w = u2 & 0xFFFF
        h = (u2 >> 32) & 0xFFFF
        sz = u4 & 0xFFFFFFFF
        
        if rel_off == 0 and sz == 0:
            break
            
        fad_entries.append({
            "index": idx,
            "rel_off": rel_off,
            "desc_off": base_off + rel_off + 32,
            "data_off": base_off + rel_off + 64,
            "width": w,
            "height": h,
            "size": sz
        })
        pos += 32
        idx += 1

    print(f"Total entries to dump: {len(fad_entries)}")
    
    # Read the data header of each entry (first 64 bytes)
    for e in fad_entries:
        abs_off = base_off + e["rel_off"]
        f.seek(abs_off)
        header = f.read(128)
        # Check if NLTX
        nltx_pos = header.find(b"NLTX")
        if nltx_pos != -1:
            e["has_nltx"] = True
            e["nltx_off"] = nltx_pos
            # format at nltx_pos + 12
            fmt = struct.unpack_from("<I", header, nltx_pos + 12)[0]
            e["fmt"] = fmt
        else:
            e["has_nltx"] = False
            e["fmt"] = 0

print("Dumping index, dimensions, and searching for character name textures...")
for e in fad_entries:
    if (e["width"], e["height"]) in [(1024, 512), (512, 512), (1024, 2048), (256, 512), (2048, 1280), (2048, 2048), (512, 256), (1024, 1024)]:
        print(f"Idx {e['index']:3d}: RelOff=0x{e['rel_off']:08X}, Dim=({e['width']:4d}x{e['height']:4d}), Sz={e['size']:8d}")
