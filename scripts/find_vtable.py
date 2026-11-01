import struct

exe_path = r"C:\Program Files (x86)\Steam\steamapps\common\Village in the Shade\village.exe"
with open(exe_path, "rb") as f:
    data = f.read()

# 0x1409ACA40 as 64-bit uint:
va = 0x140000000 + 0x009ACA40
va_bytes = struct.pack("<Q", va)

print(f"Searching for pointer 0x{va:X}...")
idx = 0
while True:
    idx = data.find(va_bytes, idx)
    if idx == -1:
        break
    print(f"  Found at FileOffset: 0x{idx:X}")
    idx += 1
