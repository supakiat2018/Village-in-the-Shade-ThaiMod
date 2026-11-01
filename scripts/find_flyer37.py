import os
from PIL import Image

kb_dir = r"D:\Users\Supakiat\Desktop\Village_in_the_Shade_ThaiMod_Dev\คียบอด"
mod_tex_dir = r"D:\Users\Supakiat\Desktop\Village_in_the_Shade_ThaiMod_Dev\01_ภาพที่ม็อดเดิมแก้ไข_ทั้งหมด_65ภาพ"

fly_path = os.path.join(mod_tex_dir, "ui_5010_チラシ37.png")
with Image.open(fly_path) as fimg:
    ft = list(fimg.convert("L").resize((32, 32), Image.Resampling.BILINEAR).getdata())

matches = []
for f in os.listdir(kb_dir):
    if f.startswith("tex_") and "1024x1024" in f:
        idx = int(f.split("_")[1])
        path = os.path.join(kb_dir, f)
        with Image.open(path) as kimg:
            kt = list(kimg.convert("L").resize((32, 32), Image.Resampling.BILINEAR).getdata())
        diff = sum(abs(a - b) for a, b in zip(kt, ft)) / 1024.0
        matches.append((idx, diff, f))

for idx, diff, f in sorted(matches, key=lambda x: x[1])[:10]:
    print(f"Index {idx:3d}: diff={diff:.1f} ({f})")
