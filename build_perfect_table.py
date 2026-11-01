import os

# Read v130_toc_dump.txt
with open(r"D:\Users\Supakiat\Desktop\Village_in_the_Shade_ThaiMod_Dev\scratch\v130_toc_dump.txt", "r", encoding="utf-8") as f:
    toc_lines = f.readlines()

toc_map = {}
for line in toc_lines:
    if line.startswith("TOC["):
        # TOC[ 43]: ui_0060_Charaname24pxB.tga (1024x512) rel_off=0x0138DF30 sz=15584
        idx = int(line.split("]")[0].split("[")[1].strip())
        name = line.split(":")[1].split("(")[0].strip()
        # strip .tga or .png
        base_name = os.path.splitext(name)[0]
        dim_str = line.split("(")[1].split(")")[0]
        w, h = [int(x.strip()) for x in dim_str.split("x")]
        rel_off = int(line.split("rel_off=")[1].split()[0], 16)
        sz = int(line.split("sz=")[1].strip())
        toc_map[base_name] = {
            "idx": idx,
            "orig_name": name,
            "w": w,
            "h": h,
            "rel_off": rel_off,
            "sz": sz
        }

print(f"Loaded {len(toc_map)} TOC entries from v130_toc_dump.txt")

# Now check all 71 textures
mod_textures = [
    ("ui_0020_カレンダー.nltx", "ui_0020_カレンダー_thai.nltx"),
    ("ui_2210_日リザルト02.nltx", "ui_2210_日リザルト02_thai.nltx"),
    ("ui_0070_buttonicon_text.nltx", "ui_0070_buttonicon_text_thai.nltx"),
    ("ui_1070_メッセージポップアップtext0.nltx", "ui_1070_メッセージポップアップtext0_thai.nltx"),
    ("04_掟の張り紙A.nltx", "04_掟の張り紙A_thai.nltx"),
    ("ui_2030_詳細ポップアップ.nltx", "ui_2030_詳細ポップアップ_thai.nltx"),
    ("ui_1153_ウィンドウ.nltx", "ui_1153_ウィンドウ_thai.nltx"),
    ("ui_0010_itemcategory.nltx", "ui_0010_itemcategory_thai.nltx"),
    ("ui_5090_掲示板.nltx", "ui_5090_掲示板_thai.nltx"),
    ("ui_9000_01.nltx", "ui_9000_01_thai.nltx"),
    ("ui_0060_Charaname24pxB.nltx", "ui_0060_Charaname24pxB_thai.nltx"),
    ("ui_0010_nameplate.nltx", "ui_0010_nameplate_thai.nltx"),
    ("ui_9000_02.nltx", "ui_9000_02_thai.nltx"),
    ("ui_0010_itemcategory03.nltx", "ui_0010_itemcategory03_thai.nltx"),
    ("タイトル白.nltx", "title_white.nltx"),
    ("名前_steam版_04.nltx", "名前_steam版_04_thai.nltx"),
    ("ui_5080_00.nltx", "ui_5080_00_thai.nltx"),
    ("ui_keyboard_font.nltx", "ui_keyboard_font_thai.nltx"),
    ("ui_5100_bandolPU01.nltx", "ui_5100_bandolPU01_thai.nltx"),
    ("ui_1170_投げ銭_text.nltx", "ui_1170_投げ銭_text_thai.nltx"),
    ("ui_0120_汎用テキスト01.nltx", "ui_0120_汎用テキスト01_thai.nltx"),
    ("ui_5010_チラシ01.nltx", "ui_5010_チラシ01_thai.nltx"),
    ("ui_5010_チラシ02.nltx", "ui_5010_チラシ02_thai.nltx"),
    ("ui_5010_チラシ03.nltx", "ui_5010_チラシ03_thai.nltx"),
    ("ui_5010_チラシ04.nltx", "ui_5010_チラシ04_thai.nltx"),
    ("ui_5010_チラシ05.nltx", "ui_5010_チラシ05_thai.nltx"),
    ("ui_5010_チラシ06.nltx", "ui_5010_チラシ06_thai.nltx"),
    ("ui_5010_チラシ07.nltx", "ui_5010_チラシ07_thai.nltx"),
    ("ui_5010_チラシ08.nltx", "ui_5010_チラシ08_thai.nltx"),
    ("ui_5010_チラシ09.nltx", "ui_5010_チラシ09_thai.nltx"),
    ("ui_5010_チラシ10.nltx", "ui_5010_チラシ10_thai.nltx"),
    ("ui_5010_チラシ11.nltx", "ui_5010_チラシ11_thai.nltx"),
    ("ui_5010_チラシ12.nltx", "ui_5010_チラシ12_thai.nltx"),
    ("ui_5010_チラシ13.nltx", "ui_5010_チラシ13_thai.nltx"),
    ("ui_5010_チラシ14.nltx", "ui_5010_チラシ14_thai.nltx"),
    ("ui_5010_チラシ15.nltx", "ui_5010_チラシ15_thai.nltx"),
    ("ui_5010_チラシ16.nltx", "ui_5010_チラシ16_thai.nltx"),
    ("ui_5010_チラシ17.nltx", "ui_5010_チラシ17_thai.nltx"),
    ("ui_5010_チラシ18.nltx", "ui_5010_チラシ18_thai.nltx"),
    ("ui_5010_チラシ19.nltx", "ui_5010_チラシ19_thai.nltx"),
    ("ui_5010_チラシ20.nltx", "ui_5010_チラシ20_thai.nltx"),
    ("ui_5010_チラシ30.nltx", "ui_5010_チラシ30_thai.nltx"),
    ("ui_5010_チラシ31.nltx", "ui_5010_チラシ31_thai.nltx"),
    ("ui_5010_チラシ32.nltx", "ui_5010_チラシ32_thai.nltx"),
    ("ui_5010_チラシ33.nltx", "ui_5010_チラシ33_thai.nltx"),
    ("ui_5010_チラシ34.nltx", "ui_5010_チラシ34_thai.nltx"),
    ("ui_5010_チラシ35.nltx", "ui_5010_チラシ35_thai.nltx"),
    ("ui_5010_チラシ36.nltx", "ui_5010_チラシ36_thai.nltx"),
    ("ui_5010_チラシ37.nltx", "ui_5010_チラシ37_thai.nltx"),
    ("ui_5010_チラシ38.nltx", "ui_5010_チラシ38_thai.nltx"),
    ("ui_5010_チラシ39.nltx", "ui_5010_チラシ39_thai.nltx"),
    ("ui_5010_チラシ40.nltx", "ui_5010_チラシ40_thai.nltx"),
    ("鐘.nltx", "鐘_thai.nltx"),
    ("ui_3440_00.nltx", "ui_3440_00_thai.nltx"),
    ("ui_5010_項目02.nltx", "ui_5010_項目02_thai.nltx"),
    ("ui_5060_家畜一覧_01.nltx", "ui_5060_家畜一覧_01_thai.nltx"),
    ("ui_0010_itemcategory2.nltx", "ui_0010_itemcategory2_thai.nltx"),
    ("ui_2220_post03.nltx", "ui_2220_post03_thai.nltx"),
    ("ui_2220_post01.nltx", "ui_2220_post01_thai.nltx"),
    ("ui_0990_初回起動時ポエム.nltx", "ui_0990_初回起動時ポエム_thai.nltx"),
    ("ui_1000_title01.nltx", "ui_1000_タイトル01.nltx"),
    ("ui_0990_localize_00.nltx", "ui_0990_localize_00_thai.nltx"),
    ("ui_1000_02.nltx", "ui_1000_02_thai.nltx"),
    ("ui_2100_00.nltx", "ui_2100_00_thai.nltx"),
    ("ene_3020_1_02.nltx", "ene_3020_1_02_thai.nltx"),
    ("bg_8080_00_tex.nltx", "bg_8080_00_tex_thai.nltx"),
    ("bg_8080_04_tex.nltx", "bg_8080_04_tex_thai.nltx"),
    ("bg_8080_01_tex.nltx", "bg_8080_01_tex_thai.nltx"),
    ("ui_0030_汎用アイコン_はんこ.nltx", "ui_0030_汎用アイコン_はんこ_thai.nltx"),
    ("ui_2020_コックピット_text.nltx", "ui_2020_コックピット_text_thai.nltx"),
    ("ui_3030_家具配置01.nltx", "ui_3030_家具配置01_thai.nltx")
]

# Map aliases:
name_aliases = {
    "ui_keyboard_font": "ui_1100_名前入力_text",
    "ui_1000_title01": "ui_1000_タイトル01",
    "ui_5010_チラシ37": "ui_5010_チラシ101",
    "ui_5010_チラシ38": "ui_5010_チラシ102",
    "ui_5010_チラシ39": "ui_5010_チラシ103",
    "ui_5010_チラシ40": "ui_5010_チラシ104",
}

mapped_entries = []
for orig_file, alt_file in mod_textures:
    base = os.path.splitext(orig_file)[0]
    lookup_key = name_aliases.get(base, base)
    
    if lookup_key in toc_map:
        info = toc_map[lookup_key]
        mapped_entries.append((info["idx"], orig_file, alt_file, info["w"], info["h"], info["rel_off"]))
    else:
        print(f"NOT FOUND IN TOC: {base} (key: {lookup_key})")

print(f"\nSuccessfully mapped {len(mapped_entries)} of {len(mod_textures)} textures!")
print("\nGenerated C Table:")
for idx, orig_file, alt_file, w, h, rel_off in sorted(mapped_entries, key=lambda x: x[0]):
    print(f'    {{ {idx:3d}, "{orig_file}", "{alt_file}", {w:4d}, {h:4d} }}, /* RelOff=0x{rel_off:08X} */')
