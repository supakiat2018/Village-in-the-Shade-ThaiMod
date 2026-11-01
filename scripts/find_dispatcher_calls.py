import struct

exe_path = r"C:\Program Files (x86)\Steam\steamapps\common\Village in the Shade\village.exe"
with open(exe_path, "rb") as f:
    data = f.read()

target_rva = 0x009ACA40
print(f"Searching calls to dispatcher (0x{target_rva:X})...")

calls = []
for foff in range(0x400, len(data) - 5):
    if data[foff] == 0xE8:
        rel32 = struct.unpack_from("<i", data, foff + 1)[0]
        call_rva = foff + 0xC00
        target = call_rva + 5 + rel32
        if target == target_rva:
            calls.append((foff, call_rva))

print(f"Found {len(calls)} calls to dispatcher:")
for foff, rva in calls:
    print(f"  FileOffset: 0x{foff:X}, RVA: 0x{rva:X}")
