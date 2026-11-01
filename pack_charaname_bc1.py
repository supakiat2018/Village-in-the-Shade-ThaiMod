import os
import subprocess
import struct
import ctypes

temp_dir = r"D:\Users\Supakiat\Desktop\Village_in_the_Shade_ThaiMod_Dev\scratch\temp_tex"
os.makedirs(temp_dir, exist_ok=True)

# Input clean PNG
clean_png = r"D:\Users\Supakiat\Desktop\Village_in_the_Shade_ThaiMod_Dev\scratch\charaname_clean.png"
texconv = r"D:\Users\Supakiat\Desktop\Village_in_the_Shade_ThaiMod_Dev\texconv.exe"

# 1. Convert to BC1_UNORM DDS (1 mip)
cmd = [texconv, "-f", "BC1_UNORM", "-m", "1", "-nologo", "-y", "-o", temp_dir, clean_png]
res = subprocess.run(cmd, capture_output=True, text=True)
if res.returncode != 0:
    raise RuntimeError(f"texconv error: {res.stderr}")

dds_path = os.path.join(temp_dir, "charaname_clean.dds")
with open(dds_path, "rb") as f:
    f.seek(128) # standard DDS header is 128 bytes for BC1
    raw_bc1 = f.read()

width = 1024
height = 512
expected_bc1_size = (width * height) // 2
print(f"Raw BC1 size: {len(raw_bc1)} bytes (expected: {expected_bc1_size})")

# 2. Compress with YKCMP Type 4
dll = ctypes.CDLL(r"D:\Users\Supakiat\Desktop\Village_in_the_Shade_ThaiMod_Dev\bin\ykcmp_fast.dll")
dst_max = len(raw_bc1) + 65536
dst = (ctypes.c_uint8 * dst_max)()
c_sz = dll.compress_ykcmp_type4_c(raw_bc1, len(raw_bc1), dst, dst_max)
comp_data = bytes(dst[:c_sz])
print(f"YKCMP Type 4 compressed size: {c_sz} bytes")

# 3. Build 64-byte NMPLTEX1 header
# format = 0x60 (BC1)
hdr = bytearray(64)
hdr[0:8] = b'NMPLTEX1'
struct.pack_into('<I', hdr, 0x10, 0x60)           # Format: 0x60 = BC1_UNORM
struct.pack_into('<I', hdr, 0x14, 0x00800006)     # Type / flags
struct.pack_into('<II', hdr, 0x18, width, height) # Width, Height
struct.pack_into('<H', hdr, 0x20, 0x0004)
struct.pack_into('<H', hdr, 0x22, 0xFFFF)
struct.pack_into('<H', hdr, 0x24, 0x0001)         # Mip levels: 1
struct.pack_into('<H', hdr, 0x26, 0x0001)
struct.pack_into('<I', hdr, 0x2C, len(raw_bc1))   # Uncompressed size: 262144
struct.pack_into('<I', hdr, 0x30, c_sz)           # Compressed data size
struct.pack_into('<I', hdr, 0x34, 0x00000080)

nltx_data = bytes(hdr) + comp_data
print(f"Total NLTX size: {len(nltx_data)} bytes (Slot budget: 107,504 bytes, Leftover: {107504 - len(nltx_data)} bytes)")

out_path = r"D:\Users\Supakiat\Desktop\Village_in_the_Shade_ThaiMod_Dev\scratch\temp_tex\ui_0060_Charaname24pxB_bc1.nltx"
with open(out_path, "wb") as f:
    f.write(nltx_data)
print(f"Saved to {out_path}")
