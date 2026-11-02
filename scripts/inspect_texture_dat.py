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

print(f"record_count={record_count}")

# Check slots in records
all_slots = []
for i in range(record_count):
    rec = data[12 + i*120 : 12 + (i+1)*120]
    u32s = struct.unpack("<30I", rec)
    # u32s: [0]=payload_size(116), [1]=ID, [2]=flags, then pairs (off, len)
    pairs = []
    for s_idx in range(3, 29, 2):
        off, length = u32s[s_idx], u32s[s_idx+1]
        s = get_str(off, length)
        pairs.append(s)
    all_slots.append((u32s[1], pairs))

# Print first 5
for rid, pairs in all_slots[:5]:
    print(f"ID={rid}: {pairs}")
