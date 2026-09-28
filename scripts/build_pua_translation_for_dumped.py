# -*- coding: utf-8 -*-
import os, glob, csv, re, json, struct

DUMP_PATH = r"C:\Program Files (x86)\Steam\steamapps\common\Village in the Shade\Mods\TextDump\dump_unique.txt"
TABLE_DIR = r"C:\Users\Supakiat\Desktop\Mover\QuickBMS\ตารางแปล"
MAPPING_JSON = r"C:\Users\Supakiat\Desktop\Mover\out\Mapping.json"
SKILLTREE_DAT = r"C:\Users\Supakiat\Desktop\Mover\QuickBMS\Extracted_Data_v109ต้นฉบับ\data\database\skilltree.dat"
OUTPUT_TRANSLATION = r"C:\Program Files (x86)\Steam\steamapps\common\Village in the Shade\Mods\TextDump\translation.txt"

# 1. Load Mapping.json
print(f"Loading Mapping.json from: {MAPPING_JSON}")
with open(MAPPING_JSON, "r", encoding="utf-8-sig") as f:
    pua_mapping = json.load(f)

max_pua_len = max(len(k) for k in pua_mapping)

def to_pua(text):
    if not text:
        return text
    result = []
    i = 0
    n = len(text)
    while i < n:
        matched = False
        for l in range(min(max_pua_len, n - i), 0, -1):
            sub = text[i : i + l]
            if sub in pua_mapping:
                result.append(pua_mapping[sub])
                i += l
                matched = True
                break
        if not matched:
            result.append(text[i])
            i += 1
    return "".join(result)

# 2. Build Translation Dictionary (JP -> Plain TH)
jp_to_th = {}

def add_trans(jp, th):
    jp = jp.strip()
    th = th.strip()
    if not jp or not th:
        return
    if th in ['Switch', 'HAS_THAI', 'Empty', 'YES', 'NO', 'MOD_EN']:
        return
    if jp not in jp_to_th:
        jp_to_th[jp] = th

# 2.1 Skilltree.dat mapping
if os.path.exists(SKILLTREE_DAT):
    skill_csv = os.path.join(TABLE_DIR, "skilltree_ตารางคำแปลไทย_พร้อมฉีด.csv")
    if os.path.exists(skill_csv):
        with open(SKILLTREE_DAT, "rb") as f:
            s_data = f.read()
        count, _, blob_sz, _ = struct.unpack("<IIII", s_data[:16])
        blob_start = len(s_data) - blob_sz
        def read_str(off):
            r_off, s_len = struct.unpack("<II", s_data[off:off+8])
            if s_len == 0: return ""
            return s_data[blob_start + r_off : blob_start + r_off + s_len].decode("utf-8", errors="ignore").rstrip("\x00")
        with open(skill_csv, "r", encoding="utf-8-sig") as f:
            rows = list(csv.DictReader(f))
        for i in range(min(count, len(rows))):
            base = 16 + i * 232
            jp_title = read_str(base + 116)
            jp_desc = read_str(base + 164)
            th_title = rows[i].get("ชื่อเต็ม_TH", "")
            th_desc = rows[i].get("คำอธิบาย_TH", "")
            if jp_title and th_title:
                add_trans(jp_title, th_title)
            if jp_desc and th_desc:
                add_trans(jp_desc, th_desc)

# 2.2 Items
item_csv = os.path.join(TABLE_DIR, "item_ตารางคำแปลไทย_พร้อมฉีด.csv")
if os.path.exists(item_csv):
    with open(item_csv, "r", encoding="utf-8", errors="ignore") as f:
        for r in csv.reader(f):
            if len(r) >= 5 and r[2].strip() and r[4].strip():
                add_trans(r[2], r[4])
            for j_idx, t_idx in [(8, 10), (11, 13), (14, 16)]:
                if len(r) > t_idx and r[j_idx].strip() and r[t_idx].strip():
                    add_trans(r[j_idx], r[t_idx])

# 2.3 gameSetting txt
for fname in ["gameSetting_ตารางจับคู่ภาษา.txt", "gamesetting_ตารางจับคู่_ปกติ_vs_MODEN.txt"]:
    fpath = os.path.join(TABLE_DIR, fname)
    if os.path.exists(fpath):
        with open(fpath, "r", encoding="utf-8", errors="ignore") as f:
            blocks = re.split(r"-{10,}|={10,}|\[\d+\]", f.read())
            for b in blocks:
                jp_m = re.search(r"ญี่ปุ่น\s*\(JP\)\s*:\s*(.+)", b)
                th_m = re.search(r"แปลไทย\s*\(TH\)\s*:\s*(.+)", b)
                if jp_m and th_m:
                    add_trans(jp_m.group(1), th_m.group(1))

# 2.4 General CSVs
for fpath in glob.glob(os.path.join(TABLE_DIR, "*_พร้อมฉีด.csv")) + glob.glob(os.path.join(TABLE_DIR, "*_ตารางจับคู่_ปกติ_vs_MODEN.csv")):
    fname = os.path.basename(fpath)
    if "item_" in fname: continue
    try:
        with open(fpath, "r", encoding="utf-8", errors="ignore") as f:
            reader = csv.reader(f)
            header = next(reader, None)
            if not header: continue
            jp_c, th_c = -1, -1
            for i, h in enumerate(header):
                hl = h.lower()
                if hl in ["jp_orig", "jp_normal", "jp", "japanese"]: jp_c = i
                elif hl in ["th_final", "th_switch", "th", "thai", "th_normal"]: th_c = i
            if jp_c != -1 and th_c != -1:
                for row in reader:
                    if len(row) > max(jp_c, th_c):
                        add_trans(row[jp_c], row[th_c])
    except:
        pass

# 2.5 Common Technical / Display Settings Fallbacks
direct_manual = {
    "垂直同期": "การซิงค์แนวตั้ง",
    "フレームレート制限": "จำกัดเฟรมเรต",
    "バックグラウンドフレームレート制限": "จำกัดเฟรมเรตพื้นหลัง",
    "ウィンドウタイプ": "ประเภทหน้าต่าง",
    "ウィンドウ": "หน้าต่าง",
    "ガイド表示": "แสดงคำแนะนำ",
    "自動": "อัตโนมัติ",
    "設定画面へ": "ไปที่หน้าจอตั้งค่า",
    "非アクティブ時ミュート": "ปิดเสียงเมื่อไม่ได้ใช้งานหน้าต่าง",
    "IME使用": "ใช้งาน IME",
    "日本語": "ภาษาญี่ปุ่น",
    "ウィンドウ時アスペクト比率固定": "ล็อกอัตราส่วนภาพในโหมดหน้าต่าง",
    "注視・平行移動": "เพ่งมอง / เคลื่อนที่ขนาน",
    "アイテム使用": "ใช้ไอเทม",
    "アクション": "แอ็กชัน",
    "決定／インタラクション": "ตกลง / มีปฏิสัมพันธ์",
    "キャンセル／ジャンプ": "ยกเลิก / กระโดด",
    "ゲームパッド": "เกมแพด",
    "設定初期化": "รีเซ็ตการตั้งค่า",
    "注視・向き変更": "เพ่งมอง / เปลี่ยนทิศทาง",
    "メモ": "บันทึกช่วยจำ",
    "道具選択": "เลือกอุปกรณ์",
    "カメラズーム": "ซูมกล้อง",
    "詳細表示": "แสดงรายละเอียด",
    "メニュー（地図）": "เมนู (แผนที่)",
    "メニュー（手持ち道具）": "เมนู (อุปกรณ์ในมือ)",
    "ページ移動右": "เปลี่ยนหน้าไปทางขวา",
    "ページ移動左": "เปลี่ยนหน้าไปทางซ้าย",
    "副ページ移動左": "เปลี่ยนหน้าย่อยทางซ้าย",
    "副ページ移動右": "เปลี่ยนหน้าย่อยทางขวา",
    "ウィンドウ切り替え": "สลับหน้าต่าง",
    "感圧半減": "ลดแรงกดครึ่งหนึ่ง",
    "メインアクション": "แอ็กชันหลัก",
    "アクション上": "แอ็กชัน บน",
    "アクション下": "แอ็กชัน ล่าง",
    "アクション左": "แอ็กชัน ซ้าย",
    "アクション右": "แอ็กชัน ขวา",
    "ジャンプ": "กระโดด",
    "初期化": "ค่าเริ่มต้น",
    "進む": "ไปข้างหน้า",
    "戻る": "ย้อนกลับ",
    "右クリック": "คลิกขวา",
    "中クリック": "คลิกกลาง",
    "左クリック": "คลิกซ้าย",
    "マウス": "เมาส์",
    "キーボード": "คีย์บอร์ด",
    "キャンセル": "ยกเลิก",
    "インベントリ右": "กระเป๋า ขวา",
    "インベントリ左": "กระเป๋า ซ้าย",
    "インベントリ下": "กระเป๋า ล่าง",
    "インベントリ上": "กระเป๋า บน",
    "プレイヤー＆カーソル移動右": "เคลื่อนที่ & เคอร์เซอร์ขวา",
    "プレイヤー＆カーソル移動左": "เคลื่อนที่ & เคอร์เซอร์ซ้าย",
    "プレイヤー＆カーソル移動下": "เคลื่อนที่ & เคอร์เซอร์ลง",
    "プレイヤー＆カーソル移動上": "เคลื่อนที่ & เคอร์เซอร์ขึ้น",
    "詳細": "รายละเอียด",
    "回収": "เก็บกู้",
    "使う": "ใช้",
    "寝る": "เข้านอน",
    "つける": "เปิดไฟ",
    "消す": "ปิดไฟ",
    "置く": "วางลง",
    "出る": "ออกไป",
    "とじる": "ปิด",
    "拡大": "ขยาย",
    "リスト": "รายการ",
    "スタンプ": "แสตมป์",
    "早送り": "เร่งความเร็ว",
}
for k, v in direct_manual.items():
    if k not in jp_to_th:
        jp_to_th[k] = v

print(f"Total dictionary entries loaded: {len(jp_to_th)}")

# 3. Read Dumped Texts
dumped_lines = []
with open(DUMP_PATH, "r", encoding="utf-8", errors="ignore") as f:
    for line in f:
        line = line.strip()
        if not line: continue
        m = re.match(r"/\*\s*ID:\d+\s*\[\w+\]\s*\*/\s*(.*)", line)
        if m:
            dumped_lines.append(m.group(1))
        else:
            dumped_lines.append(line)

print(f"Total dumped lines to translate: {len(dumped_lines)}")

# 4. Generate translation pairs
matched_pairs = []

for text in dumped_lines:
    # Skip pure numbers or resolutions or time
    if re.match(r"^\d+$", text): continue
    if re.match(r"^\d+x\d+$", text): continue
    if re.match(r"^\d+:\d+:\d+$", text): continue

    # Recipe single item: 「...」の作り方を覚える
    m1 = re.match(r"^「(.+)」の作り方を覚える$", text)
    if m1:
        item = m1.group(1)
        th_item = jp_to_th.get(item, item)
        th_line = f"เรียนรู้วิธีสร้าง「{th_item}」"
        matched_pairs.append((text, th_line))
        continue

    # Recipe dual item: 「...」「...」の作り方を覚える
    m2 = re.match(r"^「(.+)」「(.+)」の作り方を覚える$", text)
    if m2:
        it1, it2 = m2.group(1), m2.group(2)
        th1 = jp_to_th.get(it1, it1)
        th2 = jp_to_th.get(it2, it2)
        th_line = f"เรียนรู้วิธีสร้าง「{th1}」「{th2}」"
        matched_pairs.append((text, th_line))
        continue

    if text in jp_to_th:
        matched_pairs.append((text, jp_to_th[text]))

# Remove duplicates while preserving order
seen = set()
unique_pairs = []
for jp, th in matched_pairs:
    if jp not in seen:
        seen.add(jp)
        unique_pairs.append((jp, th))

print(f"Total unique translation pairs matched: {len(unique_pairs)}")

# 5. Convert to PUA and write translation.txt
with open(OUTPUT_TRANSLATION, "w", encoding="utf-8") as f:
    for jp, th in unique_pairs:
        pua_th = to_pua(th)
        # Escape newlines
        jp_esc = jp.replace("\n", "\\n").replace("\t", "\\t")
        pua_esc = pua_th.replace("\n", "\\n").replace("\t", "\\t")
        f.write(f"{jp_esc}={pua_esc}\n")

print(f"Successfully written {len(unique_pairs)} PUA translation entries to: {OUTPUT_TRANSLATION}")
