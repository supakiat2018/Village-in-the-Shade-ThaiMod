import os
import struct

v130_mapping = [
    (   3, "ui_0020_カレンダー.nltx", "ui_0020_カレンダー_thai.nltx", 1024, 1024),
    (  12, "ui_2210_日リザルト02.nltx", "ui_2210_日リザルト02_thai.nltx", 1024, 256),
    (  13, "ui_0070_buttonicon_text.nltx", "ui_0070_buttonicon_text_thai.nltx", 512, 256),
    (  25, "ui_1070_メッセージポップアップtext0.nltx", "ui_1070_メッセージポップアップtext0_thai.nltx", 512, 128),
    (  26, "04_掟の張り紙A.nltx", "04_掟の張り紙A_thai.nltx", 2200, 1300),
    (  29, "ui_2030_詳細ポップアップ.nltx", "ui_2030_詳細ポップアップ_thai.nltx", 512, 512),
    (  30, "ui_1153_ウィンドウ.nltx", "ui_1153_ウィンドウ_thai.nltx", 1024, 1024),
    (  37, "ui_0010_itemcategory.nltx", "ui_0010_itemcategory_thai.nltx", 512, 1024),
    (  39, "ui_5090_掲示板.nltx", "ui_5090_掲示板_thai.nltx", 2048, 2048),
    (  41, "ui_9000_01.nltx", "ui_9000_01_thai.nltx", 1024, 2048),
    (  43, "ui_0060_Charaname24pxB.nltx", "ui_0060_Charaname24pxB_thai.nltx", 1024, 512),
    (  50, "ui_0010_nameplate.nltx", "ui_0010_nameplate_thai.nltx", 512, 512),
    (  52, "ui_9000_02.nltx", "ui_9000_02_thai.nltx", 1024, 2048),
    (  54, "ui_0010_itemcategory03.nltx", "ui_0010_itemcategory03_thai.nltx", 256, 512),
    (  97, "タイトル白.nltx", "title_white.nltx", 2048, 1280),
    (  98, "名前_steam版_04.nltx", "名前_steam版_04_thai.nltx", 1024, 2048),
    ( 108, "ui_5080_00.nltx", "ui_5080_00_thai.nltx", 2048, 2048),
    ( 113, "ui_keyboard_font.nltx", "ui_keyboard_font_thai.nltx", 1024, 2048),
    ( 115, "ui_5100_bandolPU01.nltx", "ui_5100_bandolPU01_thai.nltx", 256, 256),
    ( 120, "ui_1170_投げ銭_text.nltx", "ui_1170_投げ銭_text_thai.nltx", 256, 128),
    ( 122, "ui_0120_汎用テキスト01.nltx", "ui_0120_汎用テキスト01_thai.nltx", 512, 256),
    ( 123, "ui_5010_チラシ01.nltx", "ui_5010_チラシ01_thai.nltx", 1024, 1024),
    ( 124, "ui_5010_チラシ02.nltx", "ui_5010_チラシ02_thai.nltx", 1024, 1024),
    ( 125, "ui_5010_チラシ03.nltx", "ui_5010_チラシ03_thai.nltx", 1024, 1024),
    ( 126, "ui_5010_チラシ04.nltx", "ui_5010_チラシ04_thai.nltx", 1024, 1024),
    ( 127, "ui_5010_チラシ05.nltx", "ui_5010_チラシ05_thai.nltx", 1024, 1024),
    ( 128, "ui_5010_チラシ06.nltx", "ui_5010_チラシ06_thai.nltx", 1024, 1024),
    ( 129, "ui_5010_チラシ07.nltx", "ui_5010_チラシ07_thai.nltx", 1024, 1024),
    ( 130, "ui_5010_チラシ08.nltx", "ui_5010_チラシ08_thai.nltx", 1024, 1024),
    ( 131, "ui_5010_チラシ09.nltx", "ui_5010_チラシ09_thai.nltx", 1024, 1024),
    ( 132, "ui_5010_チラシ10.nltx", "ui_5010_チラシ10_thai.nltx", 1024, 1024),
    ( 133, "ui_5010_チラシ11.nltx", "ui_5010_チラシ11_thai.nltx", 1024, 1024),
    ( 134, "ui_5010_チラシ12.nltx", "ui_5010_チラシ12_thai.nltx", 1024, 1024),
    ( 135, "ui_5010_チラシ13.nltx", "ui_5010_チラシ13_thai.nltx", 1024, 1024),
    ( 136, "ui_5010_チラシ14.nltx", "ui_5010_チラシ14_thai.nltx", 1024, 1024),
    ( 137, "ui_5010_チラシ15.nltx", "ui_5010_チラシ15_thai.nltx", 1024, 1024),
    ( 138, "ui_5010_チラシ16.nltx", "ui_5010_チラシ16_thai.nltx", 1024, 1024),
    ( 139, "ui_5010_チラシ17.nltx", "ui_5010_チラシ17_thai.nltx", 1024, 1024),
    ( 140, "ui_5010_チラシ18.nltx", "ui_5010_チラシ18_thai.nltx", 1024, 1024),
    ( 141, "ui_5010_チラシ19.nltx", "ui_5010_チラシ19_thai.nltx", 1024, 1024),
    ( 142, "ui_5010_チラシ20.nltx", "ui_5010_チラシ20_thai.nltx", 1024, 1024),
    ( 143, "ui_5010_チラシ30.nltx", "ui_5010_チラシ30_thai.nltx", 1024, 1024),
    ( 144, "ui_5010_チラシ31.nltx", "ui_5010_チラシ31_thai.nltx", 1024, 1024),
    ( 145, "ui_5010_チラシ32.nltx", "ui_5010_チラシ32_thai.nltx", 1024, 1024),
    ( 146, "ui_5010_チラシ33.nltx", "ui_5010_チラシ33_thai.nltx", 1024, 1024),
    ( 147, "ui_5010_チラシ34.nltx", "ui_5010_チラシ34_thai.nltx", 1024, 1024),
    ( 148, "ui_5010_チラシ35.nltx", "ui_5010_チラシ35_thai.nltx", 1024, 1024),
    ( 149, "ui_5010_チラシ36.nltx", "ui_5010_チラシ36_thai.nltx", 1024, 1024),
    ( 150, "ui_5010_チラシ37.nltx", "ui_5010_チラシ37_thai.nltx", 1024, 1024),
    ( 151, "ui_5010_チラシ38.nltx", "ui_5010_チラシ38_thai.nltx", 1024, 1024),
    ( 152, "ui_5010_チラシ39.nltx", "ui_5010_チラシ39_thai.nltx", 1024, 1024),
    ( 153, "ui_5010_チラシ40.nltx", "ui_5010_チラシ40_thai.nltx", 1024, 1024),
    ( 171, "鐘.nltx", "鐘_thai.nltx", 2200, 1300),
    ( 174, "ui_3440_00.nltx", "ui_3440_00_thai.nltx", 4096, 2048),
    ( 190, "ui_5010_項目02.nltx", "ui_5010_項目02_thai.nltx", 256, 1024),
    ( 192, "ui_5060_家畜一覧_01.nltx", "ui_5060_家畜一覧_01_thai.nltx", 2048, 2048),
    ( 194, "ui_0010_itemcategory2.nltx", "ui_0010_itemcategory2_thai.nltx", 1024, 256),
    ( 198, "ui_2220_post03.nltx", "ui_2220_post03_thai.nltx", 512, 1024),
    ( 199, "ui_2220_post01.nltx", "ui_2220_post01_thai.nltx", 2048, 2048),
    ( 202, "ui_0990_初回起動時ポエム.nltx", "ui_0990_初回起動時ポエム_thai.nltx", 1024, 512),
    ( 208, "ui_1000_title01.nltx", "ui_1000_タイトル01.nltx", 2048, 512),
    ( 209, "ui_0990_localize_00.nltx", "ui_0990_localize_00_thai.nltx", 1024, 512),
    ( 210, "ui_1000_02.nltx", "ui_1000_02_thai.nltx", 2048, 256),
    ( 221, "ui_2100_00.nltx", "ui_2100_00_thai.nltx", 256, 256),
    ( 229, "ene_3020_1_02.nltx", "ene_3020_1_02_thai.nltx", 512, 256),
    ( 234, "bg_8080_00_tex.nltx", "bg_8080_00_tex_thai.nltx", 512, 256),
    ( 235, "bg_8080_04_tex.nltx", "bg_8080_04_tex_thai.nltx", 1024, 2048),
    ( 236, "bg_8080_01_tex.nltx", "bg_8080_01_tex_thai.nltx", 2048, 256),
    ( 321, "ui_0030_汎用アイコン_はんこ.nltx", "ui_0030_汎用アイコン_はんこ_thai.nltx", 1024, 512),
    ( 344, "ui_2020_コックピット_text.nltx", "ui_2020_コックピット_text_thai.nltx", 512, 256),
    ( 345, "ui_3030_家具配置01.nltx", "ui_3030_家具配置01_thai.nltx", 2048, 512)
]

fairy_path = r"C:\Program Files (x86)\Steam\steamapps\common\Village in the Shade\data\fairy_1_00.dat"

with open(fairy_path, "rb") as f:
    f.seek(0x6F74F400)
    fad_hdr = f.read(0x5000)

print(f"Total mappings to verify: {len(v130_mapping)}")
all_matched = True
for idx, fn, alt_fn, exp_w, exp_h in v130_mapping:
    pos = 0x0FC0 + idx * 32
    u1, u2, u3, u4 = struct.unpack_from("<QQQQ", fad_hdr, pos)
    rel_off = u1 & 0xFFFFFFFF
    act_w = u2 & 0xFFFF
    act_h = (u2 >> 32) & 0xFFFF
    sz = u4 & 0xFFFFFFFF
    
    ok = (act_w == exp_w and act_h == exp_h and rel_off > 0)
    if not ok:
        all_matched = False
        print(f"[FAIL] Idx {idx:3d} ({fn}): Expected ({exp_w}x{exp_h}) -> Actual ({act_w}x{act_h}), RelOff=0x{rel_off:X}")
    else:
        print(f"[OK]   Idx {idx:3d} ({fn:<30}): ({act_w:4d}x{act_h:4d}) at RelOff=0x{rel_off:08X}, Sz={sz:7d}")

print(f"\nFinal Verification Result: {'100% PERFECT MATCH!' if all_matched else 'SOME MISMATCHES FOUND'}")
