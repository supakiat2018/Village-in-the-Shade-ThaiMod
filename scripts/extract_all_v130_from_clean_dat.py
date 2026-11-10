import os, sys, glob, csv, re, struct
from collections import OrderedDict

dev_dir = r"D:\Users\Supakiat\Desktop\Village_in_the_Shade_ThaiMod_Dev"
clean_db_dir = r"D:\Users\Supakiat\Desktop\Mover\QuickBMS\Extracted_Data_v130\data\database"
csv_dir = os.path.join(dev_dir, "Village_PC_v130_Database_CSVs1")
out_path = os.path.join(dev_dir, "translation.txt")

# 1. Load PUA map
pua_map = {}
pua_header_path = os.path.join(dev_dir, "src", "pua_mapping.h")
if os.path.exists(pua_header_path):
    with open(pua_header_path, "r", encoding="utf-8") as f:
        for line in f:
            m = re.search(r'\{\s*L"([^"]+)",\s*L\'\\u([0-9A-Fa-f]{4})\'\s*\}', line)
            if m:
                key_raw = m.group(1)
                val_code = int(m.group(2), 16)
                key = key_raw.encode().decode("unicode_escape")
                val = chr(val_code)
                pua_map[key] = val

_sorted_pua_keys = sorted(pua_map.keys(), key=lambda k: -len(k)) if pua_map else []

def to_pua(text):
    if not text or not _sorted_pua_keys:
        return text
    if any(0xF000 <= ord(c) <= 0xF8FF for c in text):
        return text
    res = text
    for k in _sorted_pua_keys:
        res = res.replace(k, pua_map[k])
    return res

def clean_str(s):
    if not s: return ""
    s = s.strip()
    s = s.replace("\r\n", "<br>").replace("\n", "<br>").replace("\r", "<br>")
    return s

def clean_trans(trans):
    if not trans: return ""
    trans = re.sub(r"คะ\.\.\.\s*คุณ", "คุ... คุณ", trans)
    trans = re.sub(r"[ \t]+", " ", trans).strip()
    return trans

# Build master translation dictionaries from all CSVs
print("Building translation dictionary from master CSVs...")
th_by_jp = {}
th_by_en = {}

for fpath in glob.glob(csv_dir + r"\**\*.csv", recursive=True):
    with open(fpath, "r", encoding="utf-8-sig", errors="replace") as f:
        reader = csv.reader(f)
        try: header = next(reader)
        except: continue
        for r in reader:
            if len(r) >= 5:
                jp = clean_str(r[3]) if len(r) > 3 else ""
                th = clean_str(r[4]) if len(r) > 4 else ""
                pua = clean_str(r[5]) if len(r) > 5 else ""
                en = clean_str(r[6]) if len(r) > 6 else ""
                if not pua and th:
                    pua = to_pua(th)
                pua = clean_trans(pua)
                if jp and pua:
                    th_by_jp[jp] = pua
                if en and pua:
                    th_by_en[en] = pua

# Also load from talk_แปลจาก_EN.csv specifically
talk_en_csv = os.path.join(csv_dir, "talk", "talk_แปลจาก_EN.csv")
if os.path.exists(talk_en_csv):
    with open(talk_en_csv, "r", encoding="utf-8-sig", errors="replace") as f:
        reader = csv.reader(f)
        next(reader)
        for r in reader:
            en = clean_str(r[3]) if len(r) > 3 else ""
            th = clean_str(r[4]) if len(r) > 4 else ""
            pua = clean_str(r[5]) if len(r) > 5 else ""
            if not pua and th: pua = to_pua(th)
            pua = clean_trans(pua)
            if en and pua:
                th_by_en[en] = pua

print(f"Loaded {len(th_by_jp)} JP translation entries and {len(th_by_en)} EN translation entries.")

def is_jp_text(s):
    return any('\u3040' <= c <= '\u30ff' for c in s)

def is_en_text(s):
    return any('a' <= c <= 'z' or 'A' <= c <= 'Z' for c in s) and not any('\u3040' <= c <= '\u9fff' or '\uac00' <= c <= '\ud7af' for c in s)

master_en_pairs = OrderedDict()
master_jp_pairs = OrderedDict()

# Special Hardcode Overrides
SPECIAL_OVERRIDES = OrderedDict([
    ('Spring', to_pua('ฤดูใบไม้ผลิ')),
    ('Summer', to_pua('ฤดูร้อน')),
    ('Autumn', to_pua('ฤดูใบไม้ร่วง')),
    ('Winter', to_pua('ฤดูหนาว')),
    ('Fall', to_pua('ฤดูใบไม้ร่วง')),
    ('Year <value 1> - <value 2> <value 3>', to_pua('ปีที่ <value 1> <value 2> วันที่ <value 3>')),
    ('<value 1>年目 <value 2> <value 3>日', to_pua('ปีที่ <value 1> <value 2> วันที่ <value 3>')),
    ('K-Kisuke! This is bad!', to_pua('คุ... คุณคิสึเกะ! แย่แล้วค่ะ!')),
    ('คะ... คุณคิสึเกะ! แย่แล้วค่ะ!', to_pua('คุ... คุณคิสึเกะ! แย่แล้วค่ะ!')),
    ('คะ... คุณคิสึเกะ!', to_pua('คุ... คุณคิสึเกะ!')),
    ('キ、キスケさん！', to_pua('คุ... คุณคิสึเกะ!')),
    ('Move the inventory bar cursor left and right', to_pua('เลื่อนเคอร์เซอร์แถบอุปกรณ์ (ซ้าย/ขวา)')),
    ("Now, at last, you've made something precious.", to_pua('เท่านี้เธอก็มีสิ่งล้ำค่า<br>เป็นของตัวเองแล้วนะ')),
    ("Okay, I'll show you what to do next. Come with me.", to_pua('เอาล่ะเดี๋ยวฉันจะบอกว่า<br>ต้องทำอะไรต่อตามฉันมานี่สิ')),
])

for k, v in SPECIAL_OVERRIDES.items():
    master_en_pairs[k] = v

def add_entry(pairs_dict, orig, trans):
    if not orig or not trans or orig == trans: return
    orig = orig.strip()
    trans = trans.strip()
    if not orig or not trans: return
    pairs_dict[orig] = trans
    orig_trim = orig.rstrip('、,。.!?！？')
    if orig_trim and orig_trim != orig and orig_trim not in pairs_dict:
        pairs_dict[orig_trim] = trans

# 2. Extract directly from talk.dat (The true v1.30 source of all dialogue)
talk_dat_path = os.path.join(clean_db_dir, "talk.dat")
print(f"Extracting all real v1.30 strings from {talk_dat_path}...")

with open(talk_dat_path, "rb") as f:
    talk_data = f.read()

# Split talk_data into null-terminated UTF-8 strings
raw_parts = talk_data.split(b"\x00")
str_list = []
for p in raw_parts:
    if p:
        try: str_list.append(p.decode("utf-8"))
        except: str_list.append("")
    else:
        str_list.append("")

print(f"Total string tokens in talk.dat: {len(str_list)}")

# Traverse talk.dat tokens using 7-language stride
i = 0
n = len(str_list)
talk_extracted = 0
boxes_extracted = 0

while i < n:
    s = str_list[i]
    if s.startswith("TALK_ID_"):
        # Found record! Parse consecutive dialogue lines in this TALK_ID
        cur_box_jp = []
        cur_box_en = []
        cur_box_th = []
        
        j = i + 1
        while j < n and not str_list[j].startswith("TALK_ID_"):
            # Check if str_list[j] is JP
            if is_jp_text(str_list[j]):
                jp_line = str_list[j]
                en_line = str_list[j+1] if j+1 < n and is_en_text(str_list[j+1]) else ""
                
                # Find translation
                th_line = th_by_jp.get(jp_line) or th_by_en.get(en_line) or ""
                
                # Add single lines
                if en_line and th_line:
                    add_entry(master_en_pairs, en_line, th_line)
                if jp_line and th_line:
                    add_entry(master_jp_pairs, jp_line, th_line)
                talk_extracted += 1
                
                # Accumulate for dialogue box
                if en_line:
                    cur_box_en.append(en_line)
                if jp_line:
                    cur_box_jp.append(jp_line)
                if th_line:
                    cur_box_th.append(th_line)
                
                # Advance by language stride (JP, EN, FR, ES, TC, KO, SC = 7)
                j += 7
                # If there are empty tokens after stride, that indicates dialogue box boundary
                empty_gap = 0
                while j < n and not str_list[j] and not str_list[j].startswith("TALK_ID_"):
                    empty_gap += 1
                    j += 1
                
                if empty_gap >= 2:
                    # Dialogue box completed!
                    if len(cur_box_en) > 1 and len(cur_box_th) >= len(cur_box_en):
                        joined_en = "<br>".join(cur_box_en)
                        joined_th = "<br>".join(cur_box_th[:len(cur_box_en)])
                        add_entry(master_en_pairs, joined_en, joined_th)
                        boxes_extracted += 1
                    if len(cur_box_jp) > 1 and len(cur_box_th) >= len(cur_box_jp):
                        joined_jp = "<br>".join(cur_box_jp)
                        joined_th = "<br>".join(cur_box_th[:len(cur_box_jp)])
                        add_entry(master_jp_pairs, joined_jp, joined_th)
                    cur_box_jp = []
                    cur_box_en = []
                    cur_box_th = []
            else:
                j += 1
                
        # Final box at end of TALK_ID
        if len(cur_box_en) > 1 and len(cur_box_th) >= len(cur_box_en):
            joined_en = "<br>".join(cur_box_en)
            joined_th = "<br>".join(cur_box_th[:len(cur_box_en)])
            add_entry(master_en_pairs, joined_en, joined_th)
            boxes_extracted += 1
        if len(cur_box_jp) > 1 and len(cur_box_th) >= len(cur_box_jp):
            joined_jp = "<br>".join(cur_box_jp)
            joined_th = "<br>".join(cur_box_th[:len(cur_box_jp)])
            add_entry(master_jp_pairs, joined_jp, joined_th)
        i = j
    else:
        i += 1

print(f"Extracted {talk_extracted} dialogue lines and {boxes_extracted} reconstructed multi-line boxes from talk.dat!")

# 3. Extract all strings from the other 35 clean .dat files
for fpath in glob.glob(os.path.join(clean_db_dir, "*.dat")):
    fname = os.path.basename(fpath)
    if fname == "talk.dat": continue
    try:
        with open(fpath, "rb") as df:
            d = df.read()
        parts = d.split(b"\x00")
        for p in parts:
            if len(p) >= 2:
                try:
                    s = p.decode("utf-8").strip()
                    if not s: continue
                    if is_en_text(s):
                        if s in th_by_en:
                            add_entry(master_en_pairs, s, th_by_en[s])
                    elif is_jp_text(s):
                        if s in th_by_jp:
                            add_entry(master_jp_pairs, s, th_by_jp[s])
                except:
                    pass
    except Exception as e:
        print(f"Error processing {fname}: {e}")

# 4. Also merge any remaining entries from our CSV pool
for en, th in th_by_en.items():
    if en not in master_en_pairs:
        add_entry(master_en_pairs, en, th)

for jp, th in th_by_jp.items():
    if jp not in master_jp_pairs:
        add_entry(master_jp_pairs, jp, th)

# Re-apply special overrides to guarantee they are never overwritten
for k, v in SPECIAL_OVERRIDES.items():
    master_en_pairs[k] = v

print(f"Total English entries: {len(master_en_pairs)}")
print(f"Total Japanese entries: {len(master_jp_pairs)}")

# 5. Write to translation.txt
with open(out_path, "w", encoding="utf-8") as out_f:
    out_f.write("# ==============================================================================\n")
    out_f.write("# Village in the Shade - True v1.30 Extracted & Simulated Translation Database\n")
    out_f.write("# Extracted directly from clean v1.30 .dat archives with multi-line box assembly\n")
    out_f.write("# ==============================================================================\n\n")

    out_f.write("# --- ENGLISH MASTER ENTRIES & ASSEMBLED BOXES ---\n")
    for orig, trans in master_en_pairs.items():
        out_f.write(f"{orig}={trans}\n")

    out_f.write("\n# --- JAPANESE MASTER ENTRIES & ASSEMBLED BOXES ---\n")
    for orig, trans in master_jp_pairs.items():
        if orig not in master_en_pairs:
            out_f.write(f"{orig}={trans}\n")

print(f"[SUCCESS] Generated complete v1.30 translation database at {out_path}!")
