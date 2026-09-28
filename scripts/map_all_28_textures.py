import os, glob, struct
from PIL import Image
import numpy as np

fad_path = r'C:\Program Files (x86)\Steam\steamapps\common\Village in the Shade\data\fairy_1_00.dat'
fad_base = 0x42590C00
fad_size = 245855360

print("1. Scanning all NMPLTEX1 in fairy_1_00.dat...")
offsets = []
with open(fad_path, 'rb') as f:
    f.seek(fad_base)
    chunk_size = 16 * 1024 * 1024
    pos = 0
    prev_tail = b''
    while pos < fad_size:
        to_read = min(chunk_size, fad_size - pos)
        buf = prev_tail + f.read(to_read)
        idx = 0
        while True:
            idx = buf.find(b'NMPLTEX1', idx)
            if idx == -1:
                break
            abs_off = fad_base + pos - len(prev_tail) + idx
            offsets.append(abs_off)
            idx += 8
        prev_tail = buf[-64:]
        pos += to_read

print(f"   Found {len(offsets)} textures in fairy_1_00.dat")

src_dir = r'C:\Users\Supakiat\Desktop\Village_in_the_Shade_ThaiMod_Dev\extracted_pc_original_textures\modified_ui_original_jp'
elem_dir = r'C:\Users\Supakiat\Desktop\Village_in_the_Shade_ThaiMod_Dev\extracted_pc_original_textures\ui_elements'

target_files = [
    'ui_0060_Charaname24pxB.png',
    'ui_0070_buttonicon_text.png',
    'ui_0010_nameplate.png',
    'ui_0120_汎用テキスト01.png',
    'ui_1070_メッセージポップアップtext0.png',
    'ui_1153_ウィンドウ.png',
    'ui_1170_投げ銭_text.png',
    'ui_2030_詳細ポップアップ.png',
    'ui_2100_00.png',
    'ui_2210_日リザルト02.png',
    'ui_2220_post03.png',
    'ui_3030_家具配置01.png',
    'ui_5010_項目02.png',
    'ui_5100_bandolPU01.png',
    'ui_0020_カレンダー.png',
    'ui_0010_itemcategory.png',
    'ui_0010_itemcategory03.png',
    'ui_0010_itemcategory2.png',
    'ui_0030_汎用アイコン_はんこ.png',
    'ui_9000_01.png',
    'ui_9000_02.png',
    '名前_steam版_04.png',
    'ui_0990_localize_00.png',
    'ui_1000_02.png',
    'ui_1000_タイトル01.png',
    'タイトル白.png',
    'bg_8080_00_tex.png',
    'bg_8080_01_tex.png',
    'bg_8080_04_tex.png',
    'ene_3020_1_02.png',
]

entries = []

for tf in target_files:
    sp = os.path.join(src_dir, tf)
    if not os.path.exists(sp):
        print(f"[-] Not found: {tf}", flush=True)
        continue
    im = Image.open(sp).convert('RGBA')
    w, h = im.size
    arr = np.array(im)[::16, ::16]

    cands = glob.glob(os.path.join(elem_dir, f'ui_tex_*_{w}x{h}.png'))
    best_c, best_diff = None, 1e9
    for c in cands:
        c_arr = np.array(Image.open(c).convert('RGBA'))[::16, ::16]
        diff = np.mean(np.abs(arr.astype(int) - c_arr.astype(int)))
        if diff < best_diff:
            best_diff = diff
            best_c = c

    if best_c and best_diff < 5.0:
        idx = int(os.path.basename(best_c).split('_')[2])
        base_name = os.path.splitext(tf)[0]
        if base_name == 'ui_1000_タイトル01': base_name = 'ui_1000_title01'
        if base_name == 'タイトル白': base_name = 'title_white'
        nmpl_off = offsets[idx]
        desc_off = nmpl_off - 32
        entries.append((base_name, desc_off, nmpl_off, w, h, idx, best_diff))
        print(f"[+] Matched: {tf:32s} -> Index {idx:3d} (0x{desc_off:08X}) diff={best_diff:.2f}")
    else:
        print(f"[?] Failed to match {tf} (best diff: {best_diff})")

print("\n" + "=" * 80)
print("Generated C FadSubFile entries:")
print("=" * 80)
for base_name, desc_off, nmpl_off, w, h, idx, diff in entries:
    print(f'    /* {base_name} ({w}x{h}, index {idx}) */')
    print(f'    {{ 0x{desc_off:08X}, "{base_name}.nltx", "{base_name}_thai.nltx", {w}, {h}, TRUE }},')
    print(f'    {{ 0x{nmpl_off:08X}, "{base_name}.nltx", "{base_name}_thai.nltx", {w}, {h}, FALSE }},')
