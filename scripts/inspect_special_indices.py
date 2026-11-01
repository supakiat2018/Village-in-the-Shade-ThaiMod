import os
from PIL import Image

kb_dir = r"D:\Users\Supakiat\Desktop\Village_in_the_Shade_ThaiMod_Dev\คียบอด"

# Check files in kb_dir around 105 to 125
for f in os.listdir(kb_dir):
    if f.startswith("tex_"):
        parts = f.split("_")
        try:
            idx = int(parts[1])
            if (105 <= idx <= 125) or (150 <= idx <= 170):
                path = os.path.join(kb_dir, f)
                with Image.open(path) as img:
                    w, h = img.size
                print(f"Index {idx:3d}: {f} ({w}x{h})")
        except ValueError:
            pass
