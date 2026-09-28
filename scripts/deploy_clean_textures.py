import os
import shutil

dev_root = r'C:\Users\Supakiat\Desktop\Village_in_the_Shade_ThaiMod_Dev'
steam_tex_dir = r'C:\Program Files (x86)\Steam\steamapps\common\Village in the Shade\Mods\TextDump\textures'
local_nltx_dir = os.path.join(dev_root, 'textures', 'thai_edited_nltx')
local_title_nltx = os.path.join(dev_root, 'textures', 'ui_1000_title01.nltx')
bin_dll = os.path.join(dev_root, 'bin', 'text_dump.dll')
steam_dll = r'C:\Program Files (x86)\Steam\steamapps\common\Village in the Shade\Mods\TextDump\text_dump.dll'

print("=== 1. Wiping Steam textures directory ===")
if os.path.exists(steam_tex_dir):
    for fn in os.listdir(steam_tex_dir):
        fp = os.path.join(steam_tex_dir, fn)
        try:
            if os.path.isfile(fp):
                os.remove(fp)
            elif os.path.isdir(fp):
                shutil.rmtree(fp)
        except Exception as e:
            print(f"Error removing {fn}: {e}")
else:
    os.makedirs(steam_tex_dir, exist_ok=True)

print("Steam textures directory cleaned!")

print("\n=== 2. Copying 63 Thai Edited Textures ===")
nltx_files = sorted([f for f in os.listdir(local_nltx_dir) if f.endswith('.nltx')])
print(f"Found {len(nltx_files)} files in {local_nltx_dir}")
assert len(nltx_files) == 63, f"Expected 63 files, found {len(nltx_files)}"

for fn in nltx_files:
    src = os.path.join(local_nltx_dir, fn)
    dst = os.path.join(steam_tex_dir, fn)
    shutil.copy2(src, dst)
print("Copied 63 edited textures successfully.")

print("\n=== 3. Copying Thai Title Screen (64th file) ===")
assert os.path.exists(local_title_nltx), "Missing local ui_1000_title01.nltx"
dst_title = os.path.join(steam_tex_dir, 'ui_1000_title01.nltx')
shutil.copy2(local_title_nltx, dst_title)
print(f"Copied {os.path.basename(local_title_nltx)} -> {dst_title}")

print("\n=== 4. Verifying Steam textures directory contents ===")
installed_files = sorted(os.listdir(steam_tex_dir))
print(f"Total installed files: {len(installed_files)}")
for i, fn in enumerate(installed_files, 1):
    sz = os.path.getsize(os.path.join(steam_tex_dir, fn))
    print(f"[{i:02d}/64] {fn:32s} ({sz:8d} bytes)")

assert len(installed_files) == 64, f"Expected exactly 64 files, got {len(installed_files)}"

print("\n=== 5. Installing updated text_dump.dll ===")
shutil.copy2(bin_dll, steam_dll)
print(f"Updated {steam_dll} successfully!")

print("\n=== DEPLOYMENT COMPLETED PERFECTLY! ===")
