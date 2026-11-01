import os
from PIL import Image

kb_dir = r"D:\Users\Supakiat\Desktop\Village_in_the_Shade_ThaiMod_Dev\คียบอด"

# Check every texture in g_fad_mapping_defs:
# We will match each file in Mods/TextDump/textures with tex_XXX in kb_dir
mod_dir = r"D:\Users\Supakiat\Desktop\Village_in_the_Shade_ThaiMod_Dev\Mods\TextDump\textures"
orig_dir = r"D:\Users\Supakiat\Desktop\Village_in_the_Shade_ThaiMod_Dev\01_ภาพที่ม็อดเดิมแก้ไข_ทั้งหมด_65ภาพ"

# Build kb_thumbs
kb_thumbs = {}
for f in os.listdir(kb_dir):
    if f.startswith("tex_") and f.endswith(".png") and not f.startswith("tex_index_"):
        parts = f.split("_")
        try:
            idx = int(parts[1])
            path = os.path.join(kb_dir, f)
            with Image.open(path) as img:
                w, h = img.size
                t = list(img.convert("L").resize((32, 32), Image.Resampling.BILINEAR).getdata())
            kb_thumbs[idx] = (w, h, t, f)
        except ValueError:
            pass

print(f"Loaded {len(kb_thumbs)} kb_thumbs")

# Check all original PNGs
results = {}
for f in os.listdir(orig_dir):
    if f.endswith(".png") and not f.startswith("idx"):
        path = os.path.join(orig_dir, f)
        base_name = os.path.splitext(f)[0]
        with Image.open(path) as img:
            tw, th = img.size
            t_thumb = list(img.convert("L").resize((32, 32), Image.Resampling.BILINEAR).getdata())
            
        best_idx = None
        best_diff = float("inf")
        for idx, (kw, kh, kt, kf) in kb_thumbs.items():
            if kw == tw and kh == th:
                diff = sum(abs(a - b) for a, b in zip(t_thumb, kt))
                if diff < best_diff:
                    best_diff = diff
                    best_idx = idx
        results[base_name] = (best_idx, best_diff / 1024.0, tw, th)

for name, (idx, diff, w, h) in sorted(results.items(), key=lambda x: (x[1][0] if x[1][0] is not None else 999)):
    print(f"{name:<35} -> Index {idx:3d} (diff={diff:5.1f}, {w}x{h})")
