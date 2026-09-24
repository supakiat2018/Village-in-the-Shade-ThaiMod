import struct
import json
import os

archive_path = r"C:\Program Files (x86)\Steam\steamapps\common\Village in the Shade\data.dat"
trans_path = r"C:\Users\Supakiat\Desktop\คลังคำแปล_Village_in_the_Shade\01_PC\cmd_จับคู่คำแปล_PC_JP_TH.txt"
mapping_path = r"C:\Users\Supakiat\Desktop\Mover\out\Mapping.json"

with open(mapping_path, "r", encoding="utf-8") as f:
    mapping = json.load(f)
max_len = max(len(k) for k in mapping.keys())

def to_pua(text):
    if not text:
        return ""
    res = []
    i, n = 0, len(text)
    while i < n:
        if text[i] == "<":
            end_tag = text.find(">", i)
            if end_tag != -1:
                res.append(text[i:end_tag+1])
                i = end_tag + 1
                continue
        matched = False
        for l in range(min(max_len, n - i), 0, -1):
            sub = text[i:i+l]
            if sub in mapping:
                res.append(mapping[sub])
                i += l
                matched = True
                break
        if not matched:
            res.append(text[i])
            i += 1
    return "".join(res)

with open(archive_path, "rb") as f:
    count, unk, str_off, str_len, toc_off, pad = struct.unpack("<IIQQQQ", f.read(48)[8:])
    f.seek(toc_off)
    tocs = []
    for _ in range(count):
        h, n_off, u1, sz, off, u2 = struct.unpack("<QQQQQQ", f.read(48))
        tocs.append((off, sz, n_off))
    f.seek(str_off)
    str_table = f.read(str_len)
    
    cmd_off = None
    cmd_sz = None
    for off, sz, n_off in tocs:
        name = str_table[n_off:].split(b"\x00")[0].decode("latin1")
        if name == "data/database/cmd.dat":
            cmd_off = off
            cmd_sz = sz
            break

print(f"data/database/cmd.dat at 0x{cmd_off:X}, size {cmd_sz}")

with open(archive_path, "rb") as f:
    f.seek(cmd_off)
    data = f.read(cmd_sz)

rec_count, rec_data_sz, orig_text_sz = struct.unpack("<III", data[:12])
print(f"Header: rec_count={rec_count}, rec_data_sz={rec_data_sz}, orig_text_sz={orig_text_sz}")
text_start = 12 + rec_data_sz

# Check pairs in cmd translation file
pairs = []
with open(trans_path, "r", encoding="utf-8") as f:
    for line in f:
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        jp, th = line.split("=", 1)
        pairs.append((jp.strip(), th.strip()))

print(f"Total pairs in cmd txt: {len(pairs)}")

matches_in_data = 0
not_found = []
for jp, th in pairs:
    jp_bytes = jp.encode("utf-8") + b"\0"
    pos = data.find(jp_bytes)
    if pos != -1:
        matches_in_data += 1
    else:
        not_found.append((jp, th))

print(f"Found in cmd.dat: {matches_in_data}/{len(pairs)}")
if not_found:
    print(f"Not found in cmd.dat ({len(not_found)}):")
    for jp, th in not_found[:10]:
        print(f"  '{jp}' -> '{th}'")

# Check for あり or なし in cmd.dat
print("\nChecking for あり or なし in cmd.dat:")
for word in [b"\xe3\x81\x82\xe3\x82\x8a\x00", b"\xe3\x81\xaa\xe3\x81\x97\x00"]:
    pos = data.find(word)
    wname = word.decode('utf-8', errors='ignore')
    print(f"  '{wname}' found: {pos != -1} (at 0x{pos:X} if found)")
