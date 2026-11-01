import os
from PIL import Image

kb_dir = r"D:\Users\Supakiat\Desktop\Village_in_the_Shade_ThaiMod_Dev\คียบอด"
mod_tex_dir = r"D:\Users\Supakiat\Desktop\Village_in_the_Shade_ThaiMod_Dev\01_ภาพที่ม็อดเดิมแก้ไข_ทั้งหมด_65ภาพ"

for idx in [150, 151, 152, 153]:
    kb_path = os.path.join(kb_dir, f"tex_{idx}_1024x1024.png")
    if not os.path.exists(kb_path):
        print(f"Missing {kb_path}")
        continue
    with Image.open(kb_path) as kimg:
        kt = list(kimg.convert("L").resize((32, 32), Image.Resampling.BILINEAR).getdata())
        
    for fly_num in [37, 38, 39, 40]:
        fly_path = os.path.join(mod_tex_dir, f"ui_5010_チラシ{fly_num}.png")
        if os.path.exists(fly_path):
            with Image.open(fly_path) as fimg:
                ft = list(fimg.convert("L").resize((32, 32), Image.Resampling.BILINEAR).getdata())
            diff = sum(abs(a - b) for a, b in zip(kt, ft)) / 1024.0
            print(f"Index {idx} vs チラシ{fly_num}: diff={diff:.1f}")
