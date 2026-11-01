import os
import re

kb_dir = r"D:\Users\Supakiat\Desktop\Village_in_the_Shade_ThaiMod_Dev\คียบอด"
mod_tex_dir = r"C:\Program Files (x86)\Steam\steamapps\common\Village in the Shade\Mods\TextDump\textures"

# List all tex_XXX files in kb_dir
kb_files = os.listdir(kb_dir)
print(f"Total files in kb_dir: {len(kb_files)}")

# Check named idx files
idx_named = [f for f in kb_files if f.startswith("idx") or "名前" in f]
print("Named index files:")
for f in idx_named:
    print(" ", f)
