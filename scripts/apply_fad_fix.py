import re

src_path = r'D:\Users\Supakiat\Desktop\Village_in_the_Shade_ThaiMod_Dev\src\text_dump.c'

with open(src_path, 'r', encoding='utf-8') as f:
    content = f.read()

# 1. Update g_fad_mapping_defs
old_tbl = """    {  94, "タイトル白.nltx", "title_white.nltx", 2048, 1280 },
    { 101, "名前_steam版_04.nltx", "名前_steam版_04_thai.nltx", 1024, 2048 },
    { 105, "ui_5080_00.nltx", "ui_5080_00_thai.nltx", 2048, 2048 },
    #ifdef ENABLE_THAI_KEYBOARD
    { 110, "ui_keyboard_font.nltx", "ui_keyboard_font_thai.nltx", 1024, 2048 },
#else
    { 110, "ui_keyboard_font.nltx", "ui_keyboard_font.nltx", 1024, 2048 },
#endif
    { 112, "ui_5100_bandolPU01.nltx", "ui_5100_bandolPU01_thai.nltx", 256, 256 },
    { 117, "ui_1170_投げ銭_text.nltx", "ui_1170_投げ銭_text_thai.nltx", 256, 128 },
    { 119, "ui_0120_汎用テキスト01.nltx", "ui_0120_汎用テキスト01_thai.nltx", 512, 256 },
    { 120, "ui_5010_チラシ01.nltx", "ui_5010_チラシ01_thai.nltx", 1024, 1024 },
    { 121, "ui_5010_チラシ02.nltx", "ui_5010_チラシ02_thai.nltx", 1024, 1024 },
    { 122, "ui_5010_チラシ03.nltx", "ui_5010_チラシ03_thai.nltx", 1024, 1024 },
    { 123, "ui_5010_チラシ04.nltx", "ui_5010_チラシ04_thai.nltx", 1024, 1024 },
    { 124, "ui_5010_チラシ05.nltx", "ui_5010_チラシ05_thai.nltx", 1024, 1024 },
    { 125, "ui_5010_チラシ06.nltx", "ui_5010_チラシ06_thai.nltx", 1024, 1024 },
    { 126, "ui_5010_チラシ07.nltx", "ui_5010_チラシ07_thai.nltx", 1024, 1024 },
    { 127, "ui_5010_チラシ08.nltx", "ui_5010_チラシ08_thai.nltx", 1024, 1024 },
    { 128, "ui_5010_チラシ09.nltx", "ui_5010_チラシ09_thai.nltx", 1024, 1024 },
    { 129, "ui_5010_チラシ10.nltx", "ui_5010_チラシ10_thai.nltx", 1024, 1024 },
    { 130, "ui_5010_チラシ11.nltx", "ui_5010_チラシ11_thai.nltx", 1024, 1024 },
    { 131, "ui_5010_チラシ12.nltx", "ui_5010_チラシ12_thai.nltx", 1024, 1024 },
    { 132, "ui_5010_チラシ13.nltx", "ui_5010_チラシ13_thai.nltx", 1024, 1024 },
    { 133, "ui_5010_チラシ14.nltx", "ui_5010_チラシ14_thai.nltx", 1024, 1024 },
    { 134, "ui_5010_チラシ15.nltx", "ui_5010_チラシ15_thai.nltx", 1024, 1024 },
    { 135, "ui_5010_チラシ16.nltx", "ui_5010_チラシ16_thai.nltx", 1024, 1024 },
    { 136, "ui_5010_チラシ17.nltx", "ui_5010_チラシ17_thai.nltx", 1024, 1024 },
    { 137, "ui_5010_チラシ18.nltx", "ui_5010_チラシ18_thai.nltx", 1024, 1024 },
    { 138, "ui_5010_チラシ19.nltx", "ui_5010_チラシ19_thai.nltx", 1024, 1024 },
    { 139, "ui_5010_チラシ20.nltx", "ui_5010_チラシ20_thai.nltx", 1024, 1024 },
    { 140, "ui_5010_チラシ30.nltx", "ui_5010_チラシ30_thai.nltx", 1024, 1024 },
    { 141, "ui_5010_チラシ31.nltx", "ui_5010_チラシ31_thai.nltx", 1024, 1024 },
    { 142, "ui_5010_チラシ32.nltx", "ui_5010_チラシ32_thai.nltx", 1024, 1024 },
    { 143, "ui_5010_チラシ33.nltx", "ui_5010_チラシ33_thai.nltx", 1024, 1024 },
    { 144, "ui_5010_チラシ34.nltx", "ui_5010_チラシ34_thai.nltx", 1024, 1024 },
    { 145, "ui_5010_チラシ35.nltx", "ui_5010_チラシ35_thai.nltx", 1024, 1024 },
    { 146, "ui_5010_チラシ36.nltx", "ui_5010_チラシ36_thai.nltx", 1024, 1024 },
    { 147, "ui_5010_チラシ37.nltx", "ui_5010_チラシ37_thai.nltx", 1024, 1024 },
    { 148, "ui_5010_チラシ38.nltx", "ui_5010_チラシ38_thai.nltx", 1024, 1024 },
    { 149, "ui_5010_チラシ39.nltx", "ui_5010_チラシ39_thai.nltx", 1024, 1024 },
    { 150, "ui_5010_チラシ40.nltx", "ui_5010_チラシ40_thai.nltx", 1024, 1024 },
    { 168, "鐘.nltx", "鐘_thai.nltx", 2200, 1300 },
    { 171, "ui_3440_00.nltx", "ui_3440_00_thai.nltx", 4096, 2048 },
    { 187, "ui_5010_項目02.nltx", "ui_5010_項目02_thai.nltx", 256, 1024 },
    { 189, "ui_5060_家畜一覧_01.nltx", "ui_5060_家畜一覧_01_thai.nltx", 2048, 2048 },
    { 191, "ui_0010_itemcategory2.nltx", "ui_0010_itemcategory2_thai.nltx", 1024, 256 },
    { 195, "ui_2220_post03.nltx", "ui_2220_post03_thai.nltx", 512, 1024 },
    { 196, "ui_2220_post01.nltx", "ui_2220_post01_thai.nltx", 2048, 2048 },
    { 199, "ui_0990_初回起動時ポエム.nltx", "ui_0990_初回起動時ポエム_thai.nltx", 1024, 512 },
    { 205, "ui_1000_title01.nltx", "ui_1000_タイトル01.nltx", 2048, 512 },
    { 206, "ui_0990_localize_00.nltx", "ui_0990_localize_00_thai.nltx", 1024, 512 },
    { 207, "ui_1000_02.nltx", "ui_1000_02_thai.nltx", 2048, 256 },
    { 218, "ui_2100_00.nltx", "ui_2100_00_thai.nltx", 256, 256 },
    { 226, "ene_3020_1_02.nltx", "ene_3020_1_02_thai.nltx", 512, 256 },
    { 231, "bg_8080_00_tex.nltx", "bg_8080_00_tex_thai.nltx", 512, 256 },
    { 232, "bg_8080_04_tex.nltx", "bg_8080_04_tex_thai.nltx", 1024, 2048 },
    { 233, "bg_8080_01_tex.nltx", "bg_8080_01_tex_thai.nltx", 2048, 256 },
    { 313, "ui_2210_日リザルト02.nltx", "ui_2210_日リザルト02_thai.nltx", 1024, 256 },
    { 318, "ui_0030_汎用アイコン_はんこ.nltx", "ui_0030_汎用アイコン_はんこ_thai.nltx", 1024, 512 },
    { 341, "ui_2020_コックピット_text.nltx", "ui_2020_コックピット_text_thai.nltx", 512, 256 },
    { 342, "ui_3030_家具配置01.nltx", "ui_3030_家具配置01_thai.nltx", 2048, 512 },"""

new_tbl = """    {  94, "タイトル白.nltx", "title_white.nltx", 2048, 1280 },
    { 102, "名前_steam版_04.nltx", "名前_steam版_04_thai.nltx", 1024, 2048 },
    { 107, "ui_5080_00.nltx", "ui_5080_00_thai.nltx", 2048, 2048 },
#ifdef ENABLE_THAI_KEYBOARD
    { 112, "ui_keyboard_font.nltx", "ui_keyboard_font_thai.nltx", 1024, 2048 },
#else
    { 112, "ui_keyboard_font.nltx", "ui_keyboard_font.nltx", 1024, 2048 },
#endif
    { 114, "ui_5100_bandolPU01.nltx", "ui_5100_bandolPU01_thai.nltx", 256, 256 },
    { 119, "ui_1170_投げ銭_text.nltx", "ui_1170_投げ銭_text_thai.nltx", 256, 128 },
    { 121, "ui_0120_汎用テキスト01.nltx", "ui_0120_汎用テキスト01_thai.nltx", 512, 256 },
    { 122, "ui_5010_チラシ01.nltx", "ui_5010_チラシ01_thai.nltx", 1024, 1024 },
    { 123, "ui_5010_チラシ02.nltx", "ui_5010_チラシ02_thai.nltx", 1024, 1024 },
    { 124, "ui_5010_チラシ03.nltx", "ui_5010_チラシ03_thai.nltx", 1024, 1024 },
    { 125, "ui_5010_チラシ04.nltx", "ui_5010_チラシ04_thai.nltx", 1024, 1024 },
    { 126, "ui_5010_チラシ05.nltx", "ui_5010_チラシ05_thai.nltx", 1024, 1024 },
    { 127, "ui_5010_チラシ06.nltx", "ui_5010_チラシ06_thai.nltx", 1024, 1024 },
    { 128, "ui_5010_チラシ07.nltx", "ui_5010_チラシ07_thai.nltx", 1024, 1024 },
    { 129, "ui_5010_チラシ08.nltx", "ui_5010_チラシ08_thai.nltx", 1024, 1024 },
    { 130, "ui_5010_チラシ09.nltx", "ui_5010_チラシ09_thai.nltx", 1024, 1024 },
    { 131, "ui_5010_チラシ10.nltx", "ui_5010_チラシ10_thai.nltx", 1024, 1024 },
    { 132, "ui_5010_チラシ11.nltx", "ui_5010_チラシ11_thai.nltx", 1024, 1024 },
    { 133, "ui_5010_チラシ12.nltx", "ui_5010_チラシ12_thai.nltx", 1024, 1024 },
    { 134, "ui_5010_チラシ13.nltx", "ui_5010_チラシ13_thai.nltx", 1024, 1024 },
    { 135, "ui_5010_チラシ14.nltx", "ui_5010_チラシ14_thai.nltx", 1024, 1024 },
    { 136, "ui_5010_チラシ15.nltx", "ui_5010_チラシ15_thai.nltx", 1024, 1024 },
    { 137, "ui_5010_チラシ16.nltx", "ui_5010_チラシ16_thai.nltx", 1024, 1024 },
    { 138, "ui_5010_チラシ17.nltx", "ui_5010_チラシ17_thai.nltx", 1024, 1024 },
    { 139, "ui_5010_チラシ18.nltx", "ui_5010_チラシ18_thai.nltx", 1024, 1024 },
    { 140, "ui_5010_チラシ19.nltx", "ui_5010_チラシ19_thai.nltx", 1024, 1024 },
    { 141, "ui_5010_チラシ20.nltx", "ui_5010_チラシ20_thai.nltx", 1024, 1024 },
    { 142, "ui_5010_チラシ30.nltx", "ui_5010_チラシ30_thai.nltx", 1024, 1024 },
    { 143, "ui_5010_チラシ31.nltx", "ui_5010_チラシ31_thai.nltx", 1024, 1024 },
    { 144, "ui_5010_チラシ32.nltx", "ui_5010_チラシ32_thai.nltx", 1024, 1024 },
    { 145, "ui_5010_チラシ33.nltx", "ui_5010_チラシ33_thai.nltx", 1024, 1024 },
    { 146, "ui_5010_チラシ34.nltx", "ui_5010_チラシ34_thai.nltx", 1024, 1024 },
    { 147, "ui_5010_チラシ35.nltx", "ui_5010_チラシ35_thai.nltx", 1024, 1024 },
    { 148, "ui_5010_チラシ36.nltx", "ui_5010_チラシ36_thai.nltx", 1024, 1024 },
    { 149, "ui_5010_チラシ37.nltx", "ui_5010_チラシ37_thai.nltx", 1024, 1024 },
    { 150, "ui_5010_チラシ38.nltx", "ui_5010_チラシ38_thai.nltx", 1024, 1024 },
    { 151, "ui_5010_チラシ39.nltx", "ui_5010_チラシ39_thai.nltx", 1024, 1024 },
    { 152, "ui_5010_チラシ40.nltx", "ui_5010_チラシ40_thai.nltx", 1024, 1024 },
    { 170, "鐘.nltx", "鐘_thai.nltx", 2200, 1300 },
    { 173, "ui_3440_00.nltx", "ui_3440_00_thai.nltx", 4096, 2048 },
    { 189, "ui_5010_項目02.nltx", "ui_5010_項目02_thai.nltx", 256, 1024 },
    { 191, "ui_5060_家畜一覧_01.nltx", "ui_5060_家畜一覧_01_thai.nltx", 2048, 2048 },
    { 193, "ui_0010_itemcategory2.nltx", "ui_0010_itemcategory2_thai.nltx", 1024, 256 },
    { 197, "ui_2220_post03.nltx", "ui_2220_post03_thai.nltx", 512, 1024 },
    { 198, "ui_2220_post01.nltx", "ui_2220_post01_thai.nltx", 2048, 2048 },
    { 201, "ui_0990_初回起動時ポエム.nltx", "ui_0990_初回起動時ポエム_thai.nltx", 1024, 512 },
    { 207, "ui_1000_title01.nltx", "ui_1000_タイトル01.nltx", 2048, 512 },
    { 208, "ui_0990_localize_00.nltx", "ui_0990_localize_00_thai.nltx", 1024, 512 },
    { 209, "ui_1000_02.nltx", "ui_1000_02_thai.nltx", 2048, 256 },
    { 220, "ui_2100_00.nltx", "ui_2100_00_thai.nltx", 256, 256 },
    { 228, "ene_3020_1_02.nltx", "ene_3020_1_02_thai.nltx", 512, 256 },
    { 233, "bg_8080_00_tex.nltx", "bg_8080_00_tex_thai.nltx", 512, 256 },
    { 234, "bg_8080_04_tex.nltx", "bg_8080_04_tex_thai.nltx", 1024, 2048 },
    { 235, "bg_8080_01_tex.nltx", "bg_8080_01_tex_thai.nltx", 2048, 256 },
    { 315, "ui_2210_日リザルト02.nltx", "ui_2210_日リザルト02_thai.nltx", 1024, 256 },
    { 320, "ui_0030_汎用アイコン_はんこ.nltx", "ui_0030_汎用アイコン_はんこ_thai.nltx", 1024, 512 },
    { 343, "ui_2020_コックピット_text.nltx", "ui_2020_コックピット_text_thai.nltx", 512, 256 },
    { 344, "ui_3030_家具配置01.nltx", "ui_3030_家具配置01_thai.nltx", 2048, 512 },"""

# Normalize newlines for replacement
content_norm = content.replace('\r\n', '\n')
old_tbl_norm = old_tbl.replace('\r\n', '\n')
new_tbl_norm = new_tbl.replace('\r\n', '\n')

assert old_tbl_norm in content_norm, 'old_tbl_norm not found'
content_norm = content_norm.replace(old_tbl_norm, new_tbl_norm)

# 2. Update resolve_dynamic_fad_offsets_w buffer size
old_hdr = 'uint8_t fad_hdr[0x4000];'
new_hdr = 'uint8_t fad_hdr[0x5000];'
assert old_hdr in content_norm, 'old_hdr not found'
content_norm = content_norm.replace(old_hdr, new_hdr)

old_nread = 'if (nread < 0x4000) {'
new_nread = 'if (nread < 0x5000) {'
assert old_nread in content_norm, 'old_nread not found'
content_norm = content_norm.replace(old_nread, new_nread)

# 3. Update hk_ReadFile FAD TOC check and patch loop
old_read_check = 'if (arch_id == 4 && g_fad_base_offset != 0 && offset == g_fad_base_offset && nNumberOfBytesToRead >= 0x4000) {'
new_read_check = 'if (arch_id == 4 && g_fad_base_offset != 0 && offset == g_fad_base_offset && nNumberOfBytesToRead >= 0x1000) {'
assert old_read_check in content_norm, 'old_read_check not found'
content_norm = content_norm.replace(old_read_check, new_read_check)

old_walk = """                    /* Walk FAD entry table in lpBuffer between 0x1018 and 0x3B00 in 32-byte strides */
                    for (size_t pos = 0x1018; pos + 32 <= nNumberOfBytesToRead && pos < 0x4000; pos += 32) {
                        uint32_t entry_off = *(uint32_t*)((char*)lpBuffer + pos + 8);
                        if (entry_off == target_rel_off) {
                            uint64_t* p_sz = (uint64_t*)((char*)lpBuffer + pos + 0);"""

new_walk = """                    /* Walk FAD entry table in lpBuffer starting at 0x0FC0 in 32-byte strides */
                    for (size_t pos = 0x0FC0; pos + 32 <= nNumberOfBytesToRead && pos < 0x5000; pos += 32) {
                        uint32_t entry_off = *(uint32_t*)((char*)lpBuffer + pos + 0);
                        if (entry_off == target_rel_off) {
                            uint64_t* p_sz = (uint64_t*)((char*)lpBuffer + pos + 24);"""

assert old_walk.replace('\r\n', '\n') in content_norm, 'old_walk not found'
content_norm = content_norm.replace(old_walk.replace('\r\n', '\n'), new_walk.replace('\r\n', '\n'))

# Write back preserving CRLF if original had CRLF
if '\r\n' in content:
    final_content = content_norm.replace('\n', '\r\n')
else:
    final_content = content_norm

with open(src_path, 'w', encoding='utf-8') as f:
    f.write(final_content)

print("SUCCESS: text_dump.c patched successfully!")
