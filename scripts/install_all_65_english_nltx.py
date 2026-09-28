"""
Extract all 65 English .nltx files directly from old fairy_1_00.dat,
copy to Steam Mods/TextDump/textures, and update text_dump.c g_fad_subfiles table.
"""

import os
import struct
import shutil
import subprocess

TARGET_MAPPING = {
    3: ('ui_0020_カレンダー', 'ui_0020_カレンダー_thai', 1024, 1024),
    13: ('ui_0070_buttonicon_text', 'ui_0070_buttonicon_text_thai', 512, 256),
    25: ('ui_1070_メッセージポップアップtext0', 'ui_1070_メッセージポップアップtext0_thai', 512, 128),
    26: ('04_掟の張り紙A', '04_掟の張り紙A_thai', 2200, 1300),
    29: ('ui_2030_詳細ポップアップ', 'ui_2030_詳細ポップアップ_thai', 512, 512),
    30: ('ui_1153_ウィンドウ', 'ui_1153_ウィンドウ_thai', 1024, 1024),
    37: ('ui_0010_itemcategory', 'ui_0010_itemcategory_thai', 512, 1024),
    39: ('ui_5090_掲示板', 'ui_5090_掲示板_thai', 2048, 2048),
    41: ('ui_9000_01', 'ui_9000_01_thai', 1024, 2048),
    43: ('ui_0060_Charaname24pxB', 'ui_0060_Charaname24pxB_thai', 1024, 512),
    50: ('ui_0010_nameplate', 'ui_0010_nameplate_thai', 512, 512),
    52: ('ui_9000_02', 'ui_9000_02_thai', 1024, 2048),
    54: ('ui_0010_itemcategory03', 'ui_0010_itemcategory03_thai', 256, 512),
    97: ('title_white', 'title_white_thai', 2048, 1280),
    104: ('名前_steam版_04', '名前_steam版_04_thai', 1024, 2048),
    108: ('ui_5080_00', 'ui_5080_00_thai', 2048, 2048),
    115: ('ui_5100_bandolPU01', 'ui_5100_bandolPU01_thai', 256, 256),
    120: ('ui_1170_投げ銭_text', 'ui_1170_投げ銭_text_thai', 256, 128),
    122: ('ui_0120_汎用テキスト01', 'ui_0120_汎用テキスト01_thai', 512, 256),
    123: ('ui_5010_チラシ01', 'ui_5010_チラシ01_thai', 1024, 1024),
    124: ('ui_5010_チラシ02', 'ui_5010_チラシ02_thai', 1024, 1024),
    125: ('ui_5010_チラシ03', 'ui_5010_チラシ03_thai', 1024, 1024),
    126: ('ui_5010_チラシ04', 'ui_5010_チラシ04_thai', 1024, 1024),
    127: ('ui_5010_チラシ05', 'ui_5010_チラシ05_thai', 1024, 1024),
    128: ('ui_5010_チラシ06', 'ui_5010_チラシ06_thai', 1024, 1024),
    129: ('ui_5010_チラシ07', 'ui_5010_チラシ07_thai', 1024, 1024),
    130: ('ui_5010_チラシ08', 'ui_5010_チラシ08_thai', 1024, 1024),
    131: ('ui_5010_チラシ09', 'ui_5010_チラシ09_thai', 1024, 1024),
    132: ('ui_5010_チラシ10', 'ui_5010_チラシ10_thai', 1024, 1024),
    133: ('ui_5010_チラシ11', 'ui_5010_チラシ11_thai', 1024, 1024),
    134: ('ui_5010_チラシ12', 'ui_5010_チラシ12_thai', 1024, 1024),
    135: ('ui_5010_チラシ13', 'ui_5010_チラシ13_thai', 1024, 1024),
    136: ('ui_5010_チラシ14', 'ui_5010_チラシ14_thai', 1024, 1024),
    137: ('ui_5010_チラシ15', 'ui_5010_チラシ15_thai', 1024, 1024),
    138: ('ui_5010_チラシ16', 'ui_5010_チラシ16_thai', 1024, 1024),
    139: ('ui_5010_チラシ17', 'ui_5010_チラシ17_thai', 1024, 1024),
    140: ('ui_5010_チラシ18', 'ui_5010_チラシ18_thai', 1024, 1024),
    141: ('ui_5010_チラシ19', 'ui_5010_チラシ19_thai', 1024, 1024),
    142: ('ui_5010_チラシ20', 'ui_5010_チラシ20_thai', 1024, 1024),
    143: ('ui_5010_チラシ30', 'ui_5010_チラシ30_thai', 1024, 1024),
    144: ('ui_5010_チラシ31', 'ui_5010_チラシ31_thai', 1024, 1024),
    145: ('ui_5010_チラシ32', 'ui_5010_チラシ32_thai', 1024, 1024),
    146: ('ui_5010_チラシ33', 'ui_5010_チラシ33_thai', 1024, 1024),
    147: ('ui_5010_チラシ34', 'ui_5010_チラシ34_thai', 1024, 1024),
    148: ('ui_5010_チラシ35', 'ui_5010_チラシ35_thai', 1024, 1024),
    149: ('ui_5010_チラシ36', 'ui_5010_チラシ36_thai', 1024, 1024),
    171: ('鐘', '鐘_thai', 2200, 1300),
    174: ('ui_3440_00', 'ui_3440_00_thai', 4096, 2048),
    190: ('ui_5010_項目02', 'ui_5010_項目02_thai', 256, 1024),
    192: ('ui_5060_家畜一覧_01', 'ui_5060_家畜一覧_01_thai', 2048, 2048),
    194: ('ui_0010_itemcategory2', 'ui_0010_itemcategory2_thai', 1024, 256),
    198: ('ui_2220_post03', 'ui_2220_post03_thai', 512, 1024),
    199: ('ui_2220_post01', 'ui_2220_post01_thai', 2048, 2048),
    202: ('ui_0990_初回起動時ポエム', 'ui_0990_初回起動時ポエム_thai', 1024, 512),
    208: ('ui_1000_title01', 'ui_1000_title01_thai', 2048, 512),
    209: ('ui_0990_localize_00', 'ui_0990_localize_00_thai', 1024, 512),
    210: ('ui_1000_02', 'ui_1000_02_thai', 2048, 256),
    221: ('ui_2100_00', 'ui_2100_00_thai', 256, 256),
    229: ('ene_3020_1_02', 'ene_3020_1_02_thai', 512, 256),
    234: ('bg_8080_00_tex', 'bg_8080_00_tex_thai', 512, 256),
    235: ('bg_8080_04_tex', 'bg_8080_04_tex_thai', 1024, 2048),
    236: ('bg_8080_01_tex', 'bg_8080_01_tex_thai', 2048, 256),
    316: ('ui_2210_日リザルト02', 'ui_2210_日リザルト02_thai', 1024, 256),
    321: ('ui_0030_汎用アイコン_はんこ', 'ui_0030_汎用アイコン_はんこ_thai', 1024, 512),
    345: ('ui_3030_家具配置01', 'ui_3030_家具配置01_thai', 2048, 512),
}

def main():
    old_fairy_dat = r'C:\baidunetdiskdownload\XJ14294\待删除-旧版20260904\XJ14294\Village in the Shade\data\fairy_1_00.dat'
    old_texture_dat = r'C:\baidunetdiskdownload\XJ14294\待删除-旧版20260904\XJ14294\Village in the Shade\data\texture_1_00.dat'
    steam_fairy_dat = r'C:\Program Files (x86)\Steam\steamapps\common\Village in the Shade\data\fairy_1_00.dat'

    local_out_dir = r'C:\Users\Supakiat\Desktop\Village_in_the_Shade_ThaiMod_Dev\textures\english_nltx'
    steam_mod_dir = r'C:\Program Files (x86)\Steam\steamapps\common\Village in the Shade\Mods\TextDump\textures'

    os.makedirs(local_out_dir, exist_ok=True)
    os.makedirs(steam_mod_dir, exist_ok=True)

    print("=== 1. Extracting raw .nltx files from Old fairy_1_00.dat ===")
    with open(old_fairy_dat, 'rb') as f:
        f.seek(0x42545E00)
        old_fad = f.read(245845200)

    old_offsets = []
    pos = 0
    while True:
        idx = old_fad.find(b'NMPLTEX1', pos)
        if idx == -1: break
        old_offsets.append(idx)
        pos = idx + 8

    extracted_nltx_count = 0
    for idx, (base_name, alt_name, w, h) in sorted(TARGET_MAPPING.items()):
        off = old_offsets[idx]
        psz, doff = struct.unpack('<II', old_fad[off+0x30:off+0x38])
        nltx_bytes = old_fad[off : off + doff + psz]

        fn = f'{base_name}.nltx'
        local_path = os.path.join(local_out_dir, fn)
        steam_path = os.path.join(steam_mod_dir, fn)

        with open(local_path, 'wb') as f_out:
            f_out.write(nltx_bytes)
        with open(steam_path, 'wb') as f_out:
            f_out.write(nltx_bytes)

        extracted_nltx_count += 1
        print(f"[{extracted_nltx_count:02d}/65] Saved {fn:35s} ({len(nltx_bytes):,d} bytes)")

    # Also extract minimaps from texture_1_00.dat
    if os.path.exists(old_texture_dat):
        with open(old_texture_dat, 'rb') as f:
            for mm in [('minimap_01_spr.nltx', 0x214D6600), ('minimap_11_spr.nltx', 0x305A8200)]:
                fn, m_off = mm
                f.seek(m_off)
                hdr = f.read(128)
                psz, doff = struct.unpack('<II', hdr[0x30:0x38])
                f.seek(m_off)
                mm_bytes = f.read(doff + psz)
                with open(os.path.join(local_out_dir, fn), 'wb') as f_out:
                    f_out.write(mm_bytes)
                with open(os.path.join(steam_mod_dir, fn), 'wb') as f_out:
                    f_out.write(mm_bytes)
                print(f"[BONUS] Saved {fn:35s} ({len(mm_bytes):,d} bytes)")

    print(f"\n=== 2. Scanning Steam fairy_1_00.dat for exact Offsets ===")
    with open(steam_fairy_dat, 'rb') as f:
        f.seek(0x42590C00)
        steam_fad = f.read(245855360)

    steam_offsets = []
    pos = 0
    while True:
        idx = steam_fad.find(b'NMPLTEX1', pos)
        if idx == -1: break
        steam_offsets.append(0x42590C00 + idx)
        pos = idx + 8

    print(f"Scanned {len(steam_offsets)} textures in Steam resident_lang_jp.fad")

    # Generate g_fad_subfiles C entries
    c_entries = []
    for idx in sorted(TARGET_MAPPING.keys()):
        base_name, alt_name, w, h = TARGET_MAPPING[idx]
        nmpl_off = steam_offsets[idx]
        desc_off = nmpl_off - 32
        c_entries.append((base_name, alt_name, desc_off, nmpl_off, w, h, idx))

    print(f"\n=== 3. Updating src/text_dump.c with 65 texture hooks ===")
    c_file = r'C:\Users\Supakiat\Desktop\Village_in_the_Shade_ThaiMod_Dev\src\text_dump.c'
    with open(c_file, 'r', encoding='utf-8') as f:
        c_content = f.read()

    # Build replacement C code
    table_lines = ["static const FadSubFile g_fad_subfiles[] = {"]
    for base_name, alt_name, desc_off, nmpl_off, w, h, idx in c_entries:
        table_lines.append(f'    /* {base_name} ({w}x{h}, index {idx}) */')
        table_lines.append(f'    {{ 0x{desc_off:08X}ULL, "{base_name}.nltx", "{alt_name}.nltx", {w}, {h}, TRUE }},')
        table_lines.append(f'    {{ 0x{nmpl_off:08X}ULL, "{base_name}.nltx", "{alt_name}.nltx", {w}, {h}, FALSE }},')
    table_lines.append("};")
    new_table_str = "\n".join(table_lines)

    # Replace existing g_fad_subfiles
    start_tag = "static const FadSubFile g_fad_subfiles[] = {"
    end_tag = "};"
    start_idx = c_content.find(start_tag)
    end_idx = c_content.find(end_tag, start_idx) + len(end_tag)
    assert start_idx != -1 and end_idx != -1

    updated_c = c_content[:start_idx] + new_table_str + c_content[end_idx:]
    with open(c_file, 'w', encoding='utf-8') as f:
        f.write(updated_c)
    print(f"Updated {c_file} successfully! Total hook entries: {len(c_entries) * 2}")

    print(f"\n=== 4. Compiling text_dump.dll with Zig CC ===")
    build_cmd = [
        "zig", "cc", "-shared", "-O2", "-s",
        r"src\text_dump.c",
        r"src\addrsig.c",
        r"src\minhook-master\src\buffer.c",
        r"src\minhook-master\src\hook.c",
        r"src\minhook-master\src\trampoline.c",
        r"src\minhook-master\src\hde\hde64.c",
        "-o", r"bin\text_dump.dll",
        "-lkernel32", "-luser32"
    ]
    dev_root = r'C:\Users\Supakiat\Desktop\Village_in_the_Shade_ThaiMod_Dev'
    res = subprocess.run(build_cmd, cwd=dev_root, capture_output=True, text=True)
    if res.returncode == 0:
        print("[SUCCESS] Compiled bin\\text_dump.dll successfully!")
    else:
        print(f"[ERROR] Compilation failed:\n{res.stderr}")
        return

    # Install DLL to Steam
    steam_target_dll = r"C:\Program Files (x86)\Steam\steamapps\common\Village in the Shade\Mods\TextDump\text_dump.dll"
    shutil.copy2(r"bin\text_dump.dll", steam_target_dll)
    print(f"[INSTALLED] Copied text_dump.dll to:\n{steam_target_dll}")

    print("\n=== ALL 65 ENGLISH TEXTURES INSTALLED TO MOD SUCCESSFULLY! ===")

if __name__ == '__main__':
    main()
