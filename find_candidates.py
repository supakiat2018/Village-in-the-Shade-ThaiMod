# Search for candidate entries matching dimensions of failed textures

with open(r"D:\Users\Supakiat\Desktop\Village_in_the_Shade_ThaiMod_Dev\v130_true_fad_entries.txt", "r", encoding="utf-8") as f:
    lines = f.readlines()

def find_by_dim(w, h, start_idx=0, end_idx=360):
    res = []
    for line in lines:
        if not line.startswith("TOC["):
            continue
        idx = int(line.split(']')[0].split('[')[1].strip())
        if start_idx <= idx <= end_idx:
            # find dim=( w x h )
            dim_part = line.split("dim=(")[1].split(")")[0]
            dw, dh = [int(x.strip()) for x in dim_part.split("x")]
            if dw == w and dh == h:
                res.append((idx, line.strip()))
    return res

failed = [
    ("ui_5080_00.nltx", 2048, 2048, 100, 115),
    ("ui_keyboard_font.nltx", 1024, 2048, 105, 120),
    ("ui_5100_bandolPU01.nltx", 256, 256, 110, 125),
    ("ui_1170_投げ銭_text.nltx", 256, 128, 115, 125),
    ("ui_0120_汎用テキスト01.nltx", 512, 256, 115, 125),
    ("ui_5010_チラシ01.nltx", 1024, 1024, 120, 130),
    ("ui_5010_チラシ02.nltx", 1024, 1024, 120, 130),
    ("鐘.nltx", 2200, 1300, 165, 175),
    ("ui_3440_00.nltx", 4096, 2048, 170, 180),
    ("ui_5010_項目02.nltx", 256, 1024, 185, 195),
    ("ui_5060_家畜一覧_01.nltx", 2048, 2048, 188, 198),
    ("ui_0010_itemcategory2.nltx", 1024, 256, 190, 200),
    ("ui_2220_post03.nltx", 512, 1024, 195, 205),
    ("ui_2220_post01.nltx", 2048, 2048, 195, 205),
    ("ui_0990_初回起動時ポエム.nltx", 1024, 512, 200, 215),
    ("ui_1000_title01.nltx", 2048, 512, 205, 215),
    ("ui_0990_localize_00.nltx", 1024, 512, 205, 215),
    ("ui_1000_02.nltx", 2048, 256, 208, 218),
    ("ui_2100_00.nltx", 256, 256, 218, 228),
    ("ene_3020_1_02.nltx", 512, 256, 225, 235),
    ("bg_8080_04_tex.nltx", 1024, 2048, 230, 240),
    ("bg_8080_01_tex.nltx", 2048, 256, 234, 242),
    ("ui_0030_汎用アイコン_はんこ.nltx", 1024, 512, 315, 330),
    ("ui_2020_コックピット_text.nltx", 512, 256, 340, 350),
    ("ui_3030_家具配置01.nltx", 2048, 512, 340, 350),
]

for name, w, h, s_idx, e_idx in failed:
    candidates = find_by_dim(w, h, s_idx - 10, e_idx + 10)
    print(f"\nCandidates for {name} ({w}x{h}) around [{s_idx}..{e_idx}]:")
    for c_idx, line in candidates:
        print(f"  -> TOC[{c_idx:3d}]: {line}")
