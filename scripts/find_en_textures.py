import struct

path = r"D:\Users\Supakiat\Desktop\Mover\QuickBMS\Extracted_Data_v130\data\database\texture.dat"
with open(path, "rb") as f:
    data = f.read()

record_count, payload_sum, blob_size = struct.unpack("<III", data[:12])
blob_start = 12 + record_count * 120
blob = data[blob_start:]

def get_str(offset, length):
    if offset >= len(blob) or length == 0:
        return ""
    s = blob[offset:offset+length].split(b"\x00")[0]
    return s.decode("utf-8", errors="ignore")

diff_list = []
en_specific_list = []

for i in range(record_count):
    rec = data[12 + i*120 : 12 + (i+1)*120]
    u32s = struct.unpack("<30I", rec)
    rid = u32s[1]
    
    key = get_str(u32s[3], u32s[4])
    desc = get_str(u32s[5], u32s[6])
    jp_path = get_str(u32s[7], u32s[8])
    en_path = get_str(u32s[9], u32s[10])
    
    if en_path and jp_path != en_path:
        diff_list.append((rid, key, desc, jp_path, en_path))
    
    if en_path and ("_en" in en_path.lower() or "en" in en_path.lower()):
        en_specific_list.append((rid, key, desc, jp_path, en_path))

print(f"=== Total records where EN path != JP path: {len(diff_list)} ===")
for rid, key, desc, jp, en in diff_list:
    print(f"ID {rid}: Key='{key}' | Desc='{desc}'")
    print(f"   JP: {jp}")
    print(f"   EN: {en}")
    print()

print(f"=== Total records where EN path has '_en': {len(en_specific_list)} ===")
