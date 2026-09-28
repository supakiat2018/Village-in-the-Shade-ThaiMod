"""
Extract all English minimap textures from texture_1_00.dat and decode to PNG.
"""

import os
import struct
import time
import lz4.block
import texture2ddecoder
from PIL import Image

def extract_minimaps():
    steam_dat = r'C:\Program Files (x86)\Steam\steamapps\common\Village in the Shade\data\texture_1_00.dat'
    out_dir = r'C:\Users\Supakiat\Desktop\Village_in_the_Shade_ThaiMod_Dev\extracted_minimap_en'
    os.makedirs(out_dir, exist_ok=True)

    en_files = [
        ('minimap_01_spr_en', 'Spring Minimap 01 (ฤดูใบไม้ผลิ)'),
        ('minimap_01_sum_en', 'Summer Minimap 01 (ฤดูร้อน)'),
        ('minimap_01_aut_en', 'Autumn Minimap 01 (ฤดูใบไม้ร่วง)'),
        ('minimap_01_win_en', 'Winter Minimap 01 (ฤดูหนาว)'),
        ('minimap_11_spr_en', 'Spring Minimap 11 (ฤดูใบไม้ผลิ 11)'),
    ]

    print(f"Reading TOC from: {steam_dat}")
    with open(steam_dat, 'rb') as f:
        hdr = f.read(48)
        magic, count, unk, str_off, str_len, toc_off, pad = struct.unpack('<8sIIQQQQ', hdr)
        f.seek(str_off)
        str_data = f.read(str_len)
        f.seek(toc_off)
        toc = {}
        for _ in range(count):
            h, name_off, unk1, size, offset, unk2 = struct.unpack('<QQQQQQ', f.read(48))
            end = str_data.find(b'\x00', name_off)
            n = str_data[name_off:end].decode('utf-8', errors='ignore') if end != -1 else ''
            for base_name, _ in en_files:
                if n == f'data/texture/{base_name}.nltx':
                    toc[base_name] = (offset, size)

    print(f"Found {len(toc)} English minimap files in TOC!\n")

    for base_name, desc in en_files:
        if base_name not in toc:
            print(f"[-] Not found: {base_name}")
            continue

        off, sz = toc[base_name]
        t0 = time.time()
        with open(steam_dat, 'rb') as f:
            f.seek(off)
            hdr128 = f.read(128)
            w, h = struct.unpack('<II', hdr128[0x18:0x20])
            psz, doff = struct.unpack('<II', hdr128[0x30:0x38])
            
            # Save raw .nltx
            f.seek(off)
            nltx_data = f.read(doff + psz)
            nltx_path = os.path.join(out_dir, f'{base_name}.nltx')
            with open(nltx_path, 'wb') as fn:
                fn.write(nltx_data)

            # Decompress and decode PNG
            f.seek(off + doff)
            yk = f.read(20)
            ptype, comp_sz, uncomp_sz = struct.unpack('<III', yk[8:20])
            comp_data = f.read(comp_sz - 20)

        decomp = lz4.block.decompress(comp_data, uncompressed_size=uncomp_sz)
        decoded = texture2ddecoder.decode_bc7(decomp, w, h)
        img = Image.frombytes('RGBA', (w, h), decoded, 'raw', 'BGRA')
        png_path = os.path.join(out_dir, f'{base_name}.png')
        img.save(png_path)
        dt = time.time() - t0
        png_sz_mb = os.path.getsize(png_path) / (1024 * 1024)
        print(f"[+] Extracted: {base_name}.png ({w}x{h}) -> {png_sz_mb:.2f} MB ({dt:.2f}s) [{desc}]")

    # Also check other EN UI textures
    other_en = [
        'data/texture/fairy_ui_0070/ui_0070_buttonicon_text_en.nltx',
        'data/texture/fairy_ui_5080/ui_5080_02_en.nltx',
        'data/texture/number_framework_en.nltx',
    ]
    with open(steam_dat, 'rb') as f:
        f.seek(toc_off)
        for _ in range(count):
            h, name_off, unk1, size, offset, unk2 = struct.unpack('<QQQQQQ', f.read(48))
            end = str_data.find(b'\x00', name_off)
            n = str_data[name_off:end].decode('utf-8', errors='ignore') if end != -1 else ''
            if n in other_en:
                base_n = os.path.basename(n).replace('.nltx', '')
                f_cur = f.tell()
                f.seek(offset)
                hdr128 = f.read(128)
                w, h = struct.unpack('<II', hdr128[0x18:0x20])
                psz, doff = struct.unpack('<II', hdr128[0x30:0x38])
                f.seek(offset + doff)
                yk = f.read(20)
                ptype, comp_sz, uncomp_sz = struct.unpack('<III', yk[8:20])
                comp_data = f.read(comp_sz - 20)
                decomp = lz4.block.decompress(comp_data, uncompressed_size=uncomp_sz)
                decoded = texture2ddecoder.decode_bc7(decomp, w, h)
                img = Image.frombytes('RGBA', (w, h), decoded, 'raw', 'BGRA')
                png_path = os.path.join(out_dir, f'{base_n}.png')
                img.save(png_path)
                f.seek(f_cur)
                print(f"[+] Other UI EN: {base_n}.png ({w}x{h}) -> {png_path}")

    print("\nExtraction finished!")

if __name__ == '__main__':
    extract_minimaps()
