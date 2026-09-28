"""
Extract all 65 original Japanese textures from fairy_1_00.dat (old version).
Also optionally extracts minimap_01_spr and minimap_11_spr from texture_1_00.dat.
"""

import os
import struct
import time
import ctypes
import lz4.block
import texture2ddecoder
from PIL import Image

# Mapping of index in resident_lang_jp.fad to standard filename
TARGET_MAPPING = {
    3: 'ui_0020_カレンダー.png',
    13: 'ui_0070_buttonicon_text.png',
    25: 'ui_1070_メッセージポップアップtext0.png',
    26: '04_掟の張り紙A.png',
    29: 'ui_2030_詳細ポップアップ.png',
    30: 'ui_1153_ウィンドウ.png',
    37: 'ui_0010_itemcategory.png',
    39: 'ui_5090_掲示板.png',
    41: 'ui_9000_01.png',
    43: 'ui_0060_Charaname24pxB.png',
    50: 'ui_0010_nameplate.png',
    52: 'ui_9000_02.png',
    54: 'ui_0010_itemcategory03.png',
    97: 'タイトル白.png',
    104: '名前_steam版_04.png',
    108: 'ui_5080_00.png',
    115: 'ui_5100_bandolPU01.png',
    120: 'ui_1170_投げ銭_text.png',
    122: 'ui_0120_汎用テキスト01.png',
    123: 'ui_5010_チラシ01.png',
    124: 'ui_5010_チラシ02.png',
    125: 'ui_5010_チラシ03.png',
    126: 'ui_5010_チラシ04.png',
    127: 'ui_5010_チラシ05.png',
    128: 'ui_5010_チラシ06.png',
    129: 'ui_5010_チラシ07.png',
    130: 'ui_5010_チラシ08.png',
    131: 'ui_5010_チラシ09.png',
    132: 'ui_5010_チラシ10.png',
    133: 'ui_5010_チラシ11.png',
    134: 'ui_5010_チラシ12.png',
    135: 'ui_5010_チラシ13.png',
    136: 'ui_5010_チラシ14.png',
    137: 'ui_5010_チラシ15.png',
    138: 'ui_5010_チラシ16.png',
    139: 'ui_5010_チラシ17.png',
    140: 'ui_5010_チラシ18.png',
    141: 'ui_5010_チラシ19.png',
    142: 'ui_5010_チラシ20.png',
    143: 'ui_5010_チラシ30.png',
    144: 'ui_5010_チラシ31.png',
    145: 'ui_5010_チラシ32.png',
    146: 'ui_5010_チラシ33.png',
    147: 'ui_5010_チラシ34.png',
    148: 'ui_5010_チラシ35.png',
    149: 'ui_5010_チラシ36.png',
    171: '鐘.png',
    174: 'ui_3440_00.png',
    190: 'ui_5010_項目02.png',
    192: 'ui_5060_家畜一覧_01.png',
    194: 'ui_0010_itemcategory2.png',
    198: 'ui_2220_post03.png',
    199: 'ui_2220_post01.png',
    202: 'ui_0990_初回起動時ポエム.png',
    208: 'ui_1000_タイトル01.png',
    209: 'ui_0990_localize_00.png',
    210: 'ui_1000_02.png',
    221: 'ui_2100_00.png',
    229: 'ene_3020_1_02.png',
    234: 'bg_8080_00_tex.png',
    235: 'bg_8080_04_tex.png',
    236: 'bg_8080_01_tex.png',
    316: 'ui_2210_日リザルト02.png',
    321: 'ui_0030_汎用アイコン_はんこ.png',
    345: 'ui_3030_家具配置01.png',
}

# Try loading fast C decompressor DLL
decompress_c = None
dll_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'bin', 'ykcmp_fast.dll')
if os.path.exists(dll_path):
    try:
        lib = ctypes.CDLL(dll_path)
        decompress_c = lib.decompress_ykcmp_type4_c
        decompress_c.argtypes = [
            ctypes.c_char_p, ctypes.c_uint32,
            ctypes.c_char_p, ctypes.c_uint32
        ]
        decompress_c.restype = ctypes.c_int
        print(f"[OK] Loaded fast C decompressor: {dll_path}")
    except Exception as e:
        print(f"[WARN] Failed to load C DLL: {e}")

def decompress_ykcmp_type4_py(payload, uncomp_sz):
    dst = bytearray()
    src_idx = 0
    src_len = len(payload)
    while src_idx < src_len and len(dst) < uncomp_sz:
        b = payload[src_idx]
        src_idx += 1
        if (b & 0x80) == 0:
            length = b
            for _ in range(length):
                if src_idx < src_len and len(dst) < uncomp_sz:
                    dst.append(payload[src_idx])
                    src_idx += 1
        elif (b & 0x40) == 0:
            length = ((b >> 4) & 3) + 1
            offset = (b & 0x0F) + 1
            for _ in range(length):
                if len(dst) < uncomp_sz:
                    dst.append(dst[-offset] if offset <= len(dst) else 0)
        elif (b & 0x20) == 0:
            length = (b & 0x1F) + 2
            if src_idx < src_len:
                b1 = payload[src_idx]
                src_idx += 1
                offset = b1 + 1
                for _ in range(length):
                    if len(dst) < uncomp_sz:
                        dst.append(dst[-offset] if offset <= len(dst) else 0)
        else:
            if src_idx + 1 < src_len:
                b1 = payload[src_idx]
                b2 = payload[src_idx + 1]
                src_idx += 2
                length = (((b & 0x1F) << 4) | (b1 >> 4)) + 3
                offset = (((b1 & 0x0F) << 8) | b2) + 1
                for _ in range(length):
                    if len(dst) < uncomp_sz:
                        dst.append(dst[-offset] if offset <= len(dst) else 0)
    return bytes(dst)

def decompress_ykcmp_type4(payload, uncomp_sz):
    if decompress_c:
        dst = bytearray(uncomp_sz)
        res = decompress_c(
            bytes(payload), len(payload),
            (ctypes.c_char * uncomp_sz).from_buffer(dst), uncomp_sz
        )
        return bytes(dst[:res])
    else:
        return decompress_ykcmp_type4_py(payload, uncomp_sz)

def get_fad_info(dat_path, target_name):
    with open(dat_path, 'rb') as f:
        hdr = f.read(48)
        magic, count, unk, str_off, str_len, toc_off, pad = struct.unpack('<8sIIQQQQ', hdr)
        assert magic == b'FAFULLFS'
        f.seek(str_off)
        str_data = f.read(str_len)
        f.seek(toc_off)
        for _ in range(count):
            entry_data = f.read(48)
            hash_val, name_off, unk1, size, offset, unk2 = struct.unpack('<QQQQQQ', entry_data)
            null_pos = str_data.find(b'\x00', name_off)
            name = str_data[name_off:null_pos].decode('utf-8', errors='ignore') if null_pos != -1 else ''
            if name == target_name:
                return offset, size
    return None, None

def main():
    old_data_dir = r'C:\baidunetdiskdownload\XJ14294\待删除-旧版20260904\XJ14294\Village in the Shade\data'
    fairy_dat = os.path.join(old_data_dir, 'fairy_1_00.dat')
    texture_dat = os.path.join(old_data_dir, 'texture_1_00.dat')

    out_dir = r'C:\Users\Supakiat\Desktop\Village_in_the_Shade_ThaiMod_Dev\extracted_old_version_65'
    os.makedirs(out_dir, exist_ok=True)

    print(f"=== Extracting 65 Textures from Old Version ===")
    print(f"Source fairy_1_00.dat: {fairy_dat}")
    print(f"Output Directory:      {out_dir}")

    # 1. Locate resident_lang_jp.fad
    fad_off, fad_size = get_fad_info(fairy_dat, 'data/fairy/resident_lang_jp.fad')
    if not fad_off:
        fad_off, fad_size = 0x42545E00, 245845200
        print(f"[NOTE] Using fallback resident_lang_jp.fad offset: 0x{fad_off:08X}")
    else:
        print(f"[OK] Found resident_lang_jp.fad in TOC: offset=0x{fad_off:08X}, size={fad_size:,} bytes")

    # 2. Read resident_lang_jp.fad
    t_start = time.time()
    with open(fairy_dat, 'rb') as f:
        f.seek(fad_off)
        fad_bytes = f.read(fad_size)

    # 3. Scan for NMPLTEX1 headers
    offsets = []
    pos = 0
    while True:
        idx = fad_bytes.find(b'NMPLTEX1', pos)
        if idx == -1: break
        offsets.append(idx)
        pos = idx + 8
    print(f"[OK] Scanned {len(offsets)} textures in resident_lang_jp.fad")

    # 4. Extract all 65 textures
    success_count = 0
    for idx in sorted(TARGET_MAPPING.keys()):
        fn = TARGET_MAPPING[idx]
        if idx >= len(offsets):
            print(f"[ERROR] Index {idx} out of range ({len(offsets)}) for {fn}")
            continue

        off = offsets[idx]
        w, h = struct.unpack('<II', fad_bytes[off+0x18:off+0x20])
        doff = struct.unpack('<I', fad_bytes[off+0x34:off+0x38])[0]
        yk_off = off + doff

        magic = fad_bytes[yk_off:yk_off+8]
        if magic != b'YKCMP_V1':
            print(f"[ERROR] Invalid YKCMP magic at index {idx} ({fn}): {magic}")
            continue

        ptype, comp_sz, uncomp_sz = struct.unpack('<III', fad_bytes[yk_off+8 : yk_off+20])
        comp_data = fad_bytes[yk_off+20 : yk_off+20+comp_sz]

        t0 = time.time()
        if ptype == 4:
            decomp = decompress_ykcmp_type4(comp_data, uncomp_sz)
        elif ptype == 9:
            decomp = lz4.block.decompress(comp_data, uncompressed_size=uncomp_sz)
        else:
            print(f"[ERROR] Unsupported compression type {ptype} for {fn}")
            continue

        decoded = texture2ddecoder.decode_bc7(decomp, w, h)
        img = Image.frombytes('RGBA', (w, h), decoded, 'raw', 'BGRA')
        out_path = os.path.join(out_dir, fn)
        img.save(out_path)
        dt = (time.time() - t0) * 1000
        sz_kb = os.path.getsize(out_path) / 1024
        print(f"[{success_count+1:02d}/65] Extracted: {fn:32s} ({w:4d}x{h:<4d}) -> {sz_kb:7.1f} KB ({dt:5.1f}ms)")
        success_count += 1

    # 5. Extract minimap_01_spr and minimap_11_spr from texture_1_00.dat as bonus
    if os.path.exists(texture_dat):
        print(f"\n--- Checking Minimap Textures in texture_1_00.dat ---")
        for mm_name in ['minimap_01_spr', 'minimap_11_spr']:
            sub_path = f'data/texture/{mm_name}.nltx'
            m_off, m_size = get_fad_info(texture_dat, sub_path)
            if m_off:
                with open(texture_dat, 'rb') as f:
                    f.seek(m_off)
                    hdr = f.read(128)
                    w, h = struct.unpack('<II', hdr[0x18:0x20])
                    doff = struct.unpack('<I', hdr[0x34:0x38])[0]
                    f.seek(m_off + doff)
                    yk = f.read(20)
                    ptype, comp_sz, uncomp_sz = struct.unpack('<III', yk[8:20])
                    comp_data = f.read(comp_sz - 20)
                    decomp = lz4.block.decompress(comp_data, uncompressed_size=uncomp_sz)
                    decoded = texture2ddecoder.decode_bc7(decomp, w, h)
                    img = Image.frombytes('RGBA', (w, h), decoded, 'raw', 'BGRA')
                    mm_out = os.path.join(out_dir, f'{mm_name}.png')
                    img.save(mm_out)
                    print(f"[BONUS] Extracted minimap: {mm_name}.png ({w}x{h}) -> {mm_out}")

    print(f"\n=== Extraction Complete! ===")
    print(f"Successfully extracted {success_count} / 65 images into:")
    print(f"{out_dir}")
    print(f"Total time elapsed: {time.time() - t_start:.2f} seconds")

if __name__ == '__main__':
    main()
