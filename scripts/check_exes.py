import os
import struct

bak_path = r"C:\Program Files (x86)\Steam\steamapps\common\Village in the Shade\village.exe.bak"
cur_path = r"C:\Program Files (x86)\Steam\steamapps\common\Village in the Shade\village.exe"

print("bak exists:", os.path.exists(bak_path), "size:", os.path.getsize(bak_path) if os.path.exists(bak_path) else 0)
print("cur exists:", os.path.exists(cur_path), "size:", os.path.getsize(cur_path) if os.path.exists(cur_path) else 0)
