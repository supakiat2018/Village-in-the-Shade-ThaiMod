"""
Village in the Shade - Title Screen Texture Extractor
Decompresses YKCMP_V1 (Type 4) and decodes BC7 textures from fairy_1_00.dat (resident_lang_jp.fad)
"""

import os
import struct
import texture2ddecoder
from PIL import Image

def decompress_ykcmp_type4(payload, uncomp_sz):
    dst = bytearray()
    src_idx = 0
    src_len = len(payload)
    while src_idx < src_len and len(dst) < uncomp_sz:
        b = payload[src_idx]
        src_idx += 1
        if (b & 0x80) == 0:
            length = b
            dst.extend(payload[src_idx : src_idx + length])
            src_idx += length
        elif (b & 0x40) == 0:
            length = ((b >> 4) & 3) + 1
            offset = (b & 0x0F) + 1
            for _ in range(length):
                dst.append(dst[-offset])
        elif (b & 0x20) == 0:
            length = (b & 0x1F) + 2
            b1 = payload[src_idx]
            src_idx += 1
            offset = b1 + 1
            for _ in range(length):
                dst.append(dst[-offset])
        else:
            b1 = payload[src_idx]
            b2 = payload[src_idx + 1]
            src_idx += 2
            length = (((b & 0x1F) << 4) | (b1 >> 4)) + 3
            offset = (((b1 & 0x0F) << 8) | b2) + 1
            for _ in range(length):
                dst.append(dst[-offset])
    return bytes(dst)

def main():
    fad_path = r'C:\Program Files (x86)\Steam\steamapps\common\Village in the Shade\data\fairy_1_00.dat'
    fad_base = 0x42590C00 # resident_lang_jp.fad offset in fairy_1_00.dat

    targets = [
        ('title_white', 0x44DC5F0, 'High-contrast White Title Logo'),
        ('ui_1000_Localize_00', 0x7792DA0, 'English Title Logo (VILLAGE IN THE SHADE) & CLE Logo'),
        ('ui_1000_title01', 0x7DC07D0, 'Full Japanese Title Spritesheet (Logo + Press any button + Menu)'),
        ('ui_1000_02', 0x7E0EAF0, 'Title Bar Shadow Gradient'),
    ]

    out_dir = r'C:\Users\Supakiat\Desktop\Village_in_the_Shade_ThaiMod_Dev\extracted_textures\title_elements'
    os.makedirs(out_dir, exist_ok=True)

    with open(fad_path, 'rb') as f:
        for name, off, desc in targets:
            f.seek(fad_base + off)
            hdr = f.read(128)
            assert hdr[:8] == b'NMPLTEX1'
            w, h = struct.unpack('<II', hdr[0x18:0x20])
            psz, doff = struct.unpack('<II', hdr[0x30:0x38])
            f.seek(fad_base + off + doff)
            payload = f.read(psz)
            ptype, comp_sz, uncomp_sz = struct.unpack('<III', payload[8:20])
            
            comp_data = payload[20:comp_sz]
            decomp = decompress_ykcmp_type4(comp_data, uncomp_sz)
            
            decoded = texture2ddecoder.decode_bc7(decomp, w, h)
            img = Image.frombytes('RGBA', (w, h), decoded, 'raw', 'BGRA')
            out_png = os.path.join(out_dir, f'{name}.png')
            img.save(out_png)
            print(f'[SUCCESS] {name:20s} ({w}x{h}) -> {out_png} [{desc}]')

if __name__ == '__main__':
    main()
