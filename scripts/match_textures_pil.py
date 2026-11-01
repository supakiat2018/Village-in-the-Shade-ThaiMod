import os
import glob
from PIL import Image
import numpy as np

kb_dir = r"D:\Users\Supakiat\Desktop\Village_in_the_Shade_ThaiMod_Dev\คียบอด"
orig_dirs = [
    r"D:\Users\Supakiat\Desktop\Village_in_the_Shade_ThaiMod_Dev\01_ภาพที่ม็อดเดิมแก้ไข_ทั้งหมด_65ภาพ",
    r"D:\Users\Supakiat\Desktop\Village_in_the_Shade_ThaiMod_Dev\extracted_pc_original_textures",
    r"D:\Users\Supakiat\Desktop\Village_in_the_Shade_ThaiMod_Dev\extracted_old_version_65"
]

# Load all tex_XXX from kb_dir
kb_images = {}
for f in os.listdir(kb_dir):
    if f.startswith("tex_") and f.endswith(".png") and not f.startswith("tex_index_"):
        parts = f.split("_")
        try:
            idx = int(parts[1])
            kb_images[idx] = os.path.join(kb_dir, f)
        except ValueError:
            pass

print(f"Loaded {len(kb_images)} dumped game textures from kb_dir")

# Check all original mod images
orig_files = {}
for d in orig_dirs:
    if os.path.exists(d):
        for f in os.listdir(d):
            if f.endswith(".png") and not f.startswith("idx"):
                name = os.path.splitext(f)[0]
                if name not in orig_files:
                    orig_files[name] = os.path.join(d, f)

print(f"Found {len(orig_files)} original texture templates")

# Also check texture files currently in mod
mod_dir = r"C:\Program Files (x86)\Steam\steamapps\common\Village in the Shade\Mods\TextDump\textures"
mod_files = [f for f in os.listdir(mod_dir) if f.endswith(".nltx")]
print(f"Found {len(mod_files)} mod textures (.nltx)")

# Let's inspect size of each
