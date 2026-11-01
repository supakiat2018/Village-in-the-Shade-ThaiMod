import struct
import os

game_dat = r'C:\Program Files (x86)\Steam\steamapps\common\Village in the Shade\data\fairy_1_00.dat'
fad_base = 0x6F74F400

with open(game_dat, 'rb') as f:
    f.seek(fad_base)
    fad_hdr = f.read(0x5000)
    
    entries = []
    for idx in range(360):
        off = 0x0FC0 + idx * 32
        rel_off, str_off, w, h, pad, sz = struct.unpack('<IIIIQQ', fad_hdr[off:off+32])
        if rel_off == 0:
            continue
        
        # Read descriptor
        f.seek(fad_base + rel_off + 32)
        desc = f.read(32)
        tex_sz = struct.unpack('<Q', desc[:8])[0]
        desc_w = struct.unpack('<H', desc[8:10])[0]
        desc_h = struct.unpack('<H', desc[10:12])[0]
        entries.append({
            'idx': idx,
            'rel_off': rel_off,
            'w': desc_w,
            'h': desc_h,
            'sz': sz,
            'tex_sz': tex_sz
        })

print(f"Total entries in FAD: {len(entries)}")

# Now let's inspect the files in textures directory
tex_dir = r'C:\Program Files (x86)\Steam\steamapps\common\Village in the Shade\Mods\TextDump\textures'
mod_files = os.listdir(tex_dir)

# For each mod file, read its NMPLTEX1 header to get width and height!
mod_tex_info = {}
for fname in mod_files:
    if not fname.endswith('.nltx'):
        continue
    fpath = os.path.join(tex_dir, fname)
    with open(fpath, 'rb') as tf:
        magic = tf.read(8)
        if magic == b'NMPLTEX1':
            tf.seek(0x20) # width and height in NLTX?
            # Let's inspect the first 64 bytes of NLTX
            tf.seek(0)
            data = tf.read(64)
            # Find width and height in NLTX
            w, h = struct.unpack('<II', data[16:24])
            mod_tex_info[fname] = (w, h, os.path.getsize(fpath))

print("\n--- Mod Textures and their dimensions ---")
for fname, (w, h, sz) in sorted(mod_tex_info.items()):
    print(f"{fname:<40}: {w:4d}x{h:<4d} ({sz} bytes)")
