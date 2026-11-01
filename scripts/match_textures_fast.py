import os
from PIL import Image

kb_dir = r"D:\Users\Supakiat\Desktop\Village_in_the_Shade_ThaiMod_Dev\คียบอด"
orig_dirs = [
    r"D:\Users\Supakiat\Desktop\Village_in_the_Shade_ThaiMod_Dev\01_ภาพที่ม็อดเดิมแก้ไข_ทั้งหมด_65ภาพ",
    r"D:\Users\Supakiat\Desktop\Village_in_the_Shade_ThaiMod_Dev\extracted_old_version_65"
]

# 1. Load all tex_XXX from kb_dir
kb_entries = []
for f in os.listdir(kb_dir):
    if f.startswith("tex_") and f.endswith(".png") and not f.startswith("tex_index_"):
        parts = f.split("_")
        try:
            idx = int(parts[1])
            path = os.path.join(kb_dir, f)
            with Image.open(path) as img:
                w, h = img.size
                # Downsample to 32x32 for fast comparison
                thumb = img.convert("L").resize((32, 32), Image.Resampling.BILINEAR)
                raw_thumb = list(thumb.getdata())
            kb_entries.append((idx, w, h, raw_thumb, path))
        except Exception as e:
            pass

print(f"Loaded {len(kb_entries)} textures from kb_dir")

# 2. Collect all target mod textures
targets = {}
for d in orig_dirs:
    if os.path.exists(d):
        for f in os.listdir(d):
            if f.endswith(".png") and not f.startswith("idx"):
                name = os.path.splitext(f)[0]
                if name not in targets:
                    targets[name] = os.path.join(d, f)

print(f"Collected {len(targets)} target textures to match.")

matches = []
for name, path in sorted(targets.items()):
    try:
        with Image.open(path) as img:
            tw, th = img.size
            t_thumb = list(img.convert("L").resize((32, 32), Image.Resampling.BILINEAR).getdata())
    except Exception as e:
        print(f"Failed to open {path}: {e}")
        continue

    best_idx = None
    best_diff = float("inf")
    best_info = ""

    for idx, w, h, raw_thumb, kb_path in kb_entries:
        if w == tw and h == th:
            diff = sum(abs(a - b) for a, b in zip(t_thumb, raw_thumb))
            if diff < best_diff:
                best_diff = diff
                best_idx = idx
                best_info = f"Dim=({w}x{h})"

    avg_diff = best_diff / 1024.0 if best_idx is not None else 9999
    matches.append((name, best_idx, avg_diff, tw, th))

print("\n================ MATCH RESULTS ================")
for name, idx, diff, w, h in sorted(matches, key=lambda x: (x[1] if x[1] is not None else 999)):
    status = "EXACT" if diff < 5 else ("GOOD" if diff < 20 else "UNCERTAIN")
    print(f"Index {idx:3d} [{status:>9} diff={diff:5.1f}]: {name:<35} ({w}x{h})")
