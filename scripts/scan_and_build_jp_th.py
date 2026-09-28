import os
import glob
import csv
import re
import time

def main():
    t0 = time.time()
    
    dir_f1 = r"C:\Users\Supakiat\Desktop\Mover\QuickBMS\ตารางแปล"
    dir_f2 = r"C:\Users\Supakiat\Desktop\Mover\QuickBMS\ตารางจับคู่_JP_EN_TH"
    dir_f3 = r"C:\Users\Supakiat\Desktop\Village in the Shade Switch"
    
    out_dir = r"C:\Users\Supakiat\Desktop\Village_in_the_Shade_ThaiMod_Dev"
    out_file = os.path.join(out_dir, "ตารางจับคู่คำแปล_ไทย_JP.txt")
    
    # Storage: dict of jp -> (th, source_file, priority)
    # Higher priority number wins:
    # F1 (ตารางแปล) = 3
    # F2 (ตารางจับคู่_JP_EN_TH) = 2
    # F3 (Switch CSV) = 1
    translations = {}
    
    def clean_tags_str(s):
        s_clean = re.sub(r'<[^>]+>', '', s)
        s_clean = s_clean.strip(' ＋+\t')
        return s_clean

    def add_pair(jp, th, src, priority):
        if not jp or not th:
            return
        jp = jp.strip()
        th = th.strip()
        if not jp or not th:
            return
            
        # Ignore dummy bug messages
        if any(b in th for b in ['บั๊ก', 'ไม่มีข้อความ', 'report it', 'if you can see this']) or th.startswith('!') or 'bug' in th.lower():
            return
            
        # Standardize newlines: convert literal CRLF to \n escape
        jp_clean = jp.replace('\r\n', '\\n').replace('\r', '\\n').replace('\n', '\\n')
        th_clean = th.replace('\r\n', '\\n').replace('\r', '\\n').replace('\n', '\\n')
        
        # User Constraint: NEVER use the word "เซฟ"
        th_clean = th_clean.replace('ช่องเซฟ', 'ช่องบันทึก').replace('เซฟข้อมูล', 'บันทึกข้อมูล').replace('เซฟเกม', 'บันทึกเกม').replace('เซฟสุด', 'ปลอดภัยสุด').replace('เซฟ', 'บันทึก')
        
        def insert_entry(j_key, t_val, s_info, prio):
            if not j_key or not t_val:
                return
            if j_key in translations:
                curr_th, curr_src, curr_prio = translations[j_key]
                if prio > curr_prio:
                    translations[j_key] = (t_val, s_info, prio)
            else:
                translations[j_key] = (t_val, s_info, prio)

        # 1. Insert original (tagged) pair
        insert_entry(jp_clean, th_clean, src, priority)

        # 2. Insert clean tag-stripped pair if tags exist
        if ('<' in jp_clean and '>' in jp_clean) or ('<' in th_clean and '>' in th_clean):
            c_jp = clean_tags_str(jp_clean)
            c_th = clean_tags_str(th_clean)
            if c_jp and c_th and c_jp != jp_clean:
                insert_entry(c_jp, c_th, f"{src} [Clean Tags]", priority - 0.01)

    print("=" * 70)
    print("เริ่มสแกนและดึงคำแปลจากทั้ง 3 แหล่งข้อมูล...")
    print("=" * 70)

    # -------------------------------------------------------------------------
    # Source 3: C:\Users\Supakiat\Desktop\Village in the Shade Switch (CSVs only)
    # Priority = 1
    # -------------------------------------------------------------------------
    count_f3 = 0
    if os.path.exists(dir_f3):
        for root, dirs, files in os.walk(dir_f3):
            for fname in files:
                if fname.lower().endswith('.csv'):
                    path = os.path.join(root, fname)
                    try:
                        with open(path, 'r', encoding='utf-8-sig', errors='ignore') as fp:
                            r = csv.reader(fp)
                            header = next(r, None)
                            if not header:
                                continue
                            hl = [c.strip().lower() for c in header]
                            if 'original_jp' in hl and 'thai_translated' in hl:
                                j_idx, t_idx = hl.index('original_jp'), hl.index('thai_translated')
                                for row in r:
                                    if j_idx < len(row) and t_idx < len(row):
                                        add_pair(row[j_idx], row[t_idx], f"Switch/{fname}", 1)
                                        count_f3 += 1
                            elif 'text_jp' in hl and 'thai_translation' in hl:
                                j_idx, t_idx = hl.index('text_jp'), hl.index('thai_translation')
                                for row in r:
                                    if j_idx < len(row) and t_idx < len(row):
                                        add_pair(row[j_idx], row[t_idx], f"Switch/{fname}", 1)
                                        count_f3 += 1
                    except Exception:
                        pass
    print(f"[3/3] สแกน Switch CSVs สำเร็จ: พบข้อความ {count_f3} รายการ (รวมปัจจุบัน: {len(translations)} คู่)")

    # -------------------------------------------------------------------------
    # Source 2: C:\Users\Supakiat\Desktop\Mover\QuickBMS\ตารางจับคู่_JP_EN_TH (All files)
    # Priority = 2
    # -------------------------------------------------------------------------
    count_f2 = 0
    if os.path.exists(dir_f2):
        for fname in sorted(os.listdir(dir_f2)):
            path = os.path.join(dir_f2, fname)
            if not os.path.isfile(path):
                continue
            try:
                with open(path, 'r', encoding='utf-8-sig', errors='ignore') as fp:
                    lines = fp.readlines()
                cur_block = {}
                for line in lines:
                    l = line.strip()
                    if not l or l.startswith('===') or l.startswith('---'):
                        if 'jp' in cur_block and 'th' in cur_block:
                            add_pair(cur_block['jp'], cur_block['th'], f"ตารางจับคู่/{fname}", 2)
                            count_f2 += 1
                        cur_block = {}
                        continue
                    if l.startswith('JP:') or l.startswith('JP (ปกติ) :') or l.startswith('ปกติ  (JP) :') or l.startswith('ญี่ปุ่นปกติ (Orig) :') or l.startswith('🇯🇵 JP ต้นฉบับ  :'):
                        cur_block['jp'] = l.split(':', 1)[1].strip()
                    elif l.startswith('TH:') or l.startswith('แปลไทย (TH) :') or l.startswith('แปลไทย :') or l.startswith('แปลไทย (Switch) :') or l.startswith('🇹🇭 แปลไทย       :'):
                        cur_block['th'] = l.split(':', 1)[1].strip()
                    elif l.startswith('ชื่อ_JP:'):
                        cur_block['jp'] = l.split(':', 1)[1].strip()
                    elif l.startswith('ชื่อ_TH:'):
                        cur_block['th'] = l.split(':', 1)[1].strip()
                    elif l.startswith('คำอธิบาย_JP:') or l.startswith('คำอธิบาย1_JP:'):
                        if 'jp' in cur_block and 'th' in cur_block:
                            add_pair(cur_block['jp'], cur_block['th'], f"ตารางจับคู่/{fname}", 2)
                            count_f2 += 1
                            cur_block = {}
                        cur_block['jp'] = l.split(':', 1)[1].strip()
                    elif l.startswith('คำอธิบาย_TH:') or l.startswith('คำอธิบาย1_TH:'):
                        cur_block['th'] = l.split(':', 1)[1].strip()
                    elif '[JP]' in l and '[TH]' in l:
                        m_jp = re.search(r'\[JP\]\s*([^\|\[\]]+)', l)
                        m_th = re.search(r'\[TH\]\s*([^\|\[\]]+)', l)
                        if m_jp and m_th:
                            add_pair(m_jp.group(1), m_th.group(1), f"ตารางจับคู่/{fname}", 2)
                            count_f2 += 1
                if 'jp' in cur_block and 'th' in cur_block:
                    add_pair(cur_block['jp'], cur_block['th'], f"ตารางจับคู่/{fname}", 2)
                    count_f2 += 1
            except Exception:
                pass
    print(f"[2/3] สแกน ตารางจับคู่_JP_EN_TH สำเร็จ: พบข้อความ {count_f2} รายการ (รวมปัจจุบัน: {len(translations)} คู่)")

    # -------------------------------------------------------------------------
    # Source 1: C:\Users\Supakiat\Desktop\Mover\QuickBMS\ตารางแปล (All files - CSV + TXT)
    # Priority = 3 (Highest)
    # -------------------------------------------------------------------------
    count_f1_csv = 0
    count_f1_txt = 0
    if os.path.exists(dir_f1):
        for fname in sorted(os.listdir(dir_f1)):
            path = os.path.join(dir_f1, fname)
            if not os.path.isfile(path):
                continue
            
            # --- Parse CSV files in F1 ---
            if fname.lower().endswith('.csv'):
                try:
                    with open(path, 'r', encoding='utf-8-sig', errors='ignore') as fp:
                        r = csv.reader(fp)
                        header = next(r, None)
                        if not header:
                            continue
                        hl = [c.strip().lower() for c in header]
                        
                        indices = []
                        # Item table
                        if 'item_' in fname.lower():
                            for j_col, t_col in [('name_jp', 'name_th'), ('pattern_jp', 'pattern_th'),
                                                 ('desc1_jp', 'desc1_th'), ('desc2_jp', 'desc2_th'), ('desc3_jp', 'desc3_th')]:
                                if j_col in hl and t_col in hl:
                                    indices.append((hl.index(j_col), hl.index(t_col)))
                        # Character table
                        elif 'character_' in fname.lower():
                            for j_col, t_col in [('ชื่อ_jp', 'ชื่อ_th'), ('คำอธิบาย1_jp', 'คำอธิบาย1_th'),
                                                 ('คำอธิบาย2_jp', 'คำอธิบาย2_th'), ('คำอธิบาย3_jp', 'คำอธิบาย3_th'),
                                                 ('คำทักทาย_jp', 'คำทักทาย_th'), ('บทบาท_jp', 'บทบาท_th')]:
                                if j_col in hl and t_col in hl:
                                    indices.append((hl.index(j_col), hl.index(t_col)))
                        # GameEffect table
                        elif 'gameeffect' in fname.lower():
                            for j_col, t_col in [('ชื่อ_jp', 'ชื่อ_th'), ('คำอธิบาย_jp', 'คำอธิบาย_th'),
                                                 ('ชื่อเดิม_jp', 'แปลไทย_ชื่อ'), ('คำอธิบายเดิม_jp', 'แปลไทย_คำอธิบาย')]:
                                if j_col in hl and t_col in hl:
                                    indices.append((hl.index(j_col), hl.index(t_col)))
                        else:
                            j_idx, t_idx = None, None
                            for c in ['text_jp', 'original_jp', 'jp_orig', 'jp_normal', 'orig_jp', 'ชื่อ_jp', 'ชื่อเดิม_jp', 'ต้นฉบับ_jp', 'original_text']:
                                if c in hl:
                                    j_idx = hl.index(c)
                                    break
                            for c in ['text_th', 'thai_translated', 'th_final', 'th_switch', 'thai_normal', 'thai_final', 'แปลไทย', 'ชื่อ_th', 'คำแปลไทย', 'thai_translation', 'ชื่อประเภท_th']:
                                if c in hl:
                                    t_idx = hl.index(c)
                                    break
                            if j_idx is not None and t_idx is not None:
                                indices.append((j_idx, t_idx))
                                
                        for row in r:
                            for j_i, t_i in indices:
                                if j_i < len(row) and t_i < len(row):
                                    jp_val, th_val = row[j_i].strip(), row[t_i].strip()
                                    if jp_val and th_val:
                                        add_pair(jp_val, th_val, f"ตารางแปล/{fname}", 3)
                                        count_f1_csv += 1
                except Exception:
                    pass

            # --- Parse TXT files in F1 ---
            elif fname.lower().endswith('.txt'):
                try:
                    with open(path, 'r', encoding='utf-8-sig', errors='ignore') as fp:
                        lines = fp.readlines()
                    cur_block = {}
                    for line in lines:
                        l = line.strip()
                        if not l or l.startswith('===') or l.startswith('---'):
                            if 'jp' in cur_block and 'th' in cur_block:
                                add_pair(cur_block['jp'], cur_block['th'], f"ตารางแปล/{fname}", 3)
                                count_f1_txt += 1
                            cur_block = {}
                            continue
                        if l.startswith('JP:') or l.startswith('JP (ปกติ) :') or l.startswith('ปกติ  (JP) :'):
                            cur_block['jp'] = l.split(':', 1)[1].strip()
                        elif l.startswith('TH:') or l.startswith('แปลไทย (TH) :') or l.startswith('แปลไทย :'):
                            cur_block['th'] = l.split(':', 1)[1].strip()
                    if 'jp' in cur_block and 'th' in cur_block:
                        add_pair(cur_block['jp'], cur_block['th'], f"ตารางแปล/{fname}", 3)
                        count_f1_txt += 1
                except Exception:
                    pass

    print(f"[1/3] สแกน ตารางแปล สำเร็จ: CSV {count_f1_csv} รายการ, TXT {count_f1_txt} รายการ (รวมปัจจุบัน: {len(translations)} คู่)")

    # -------------------------------------------------------------------------
    # Special Handling: Save Slots & Dates based on user's master CSV
    # -------------------------------------------------------------------------
    # In string_ตารางจับคู่_ปกติ_vs_MODEN.csv:
    # STR_ID_SAVE_NEW_SLOT_NAME: なし -> ช่องว่าง
    # STR_ID_PLAYER_NO_NAME: 名前はまだ無い -> ยังไม่มีชื่อ
    # STR_ID_SAVE_MSG_008: どのセーブデータで遊ぶ？ -> จะเล่นข้อมูลบันทึกไหนดี?
    translations["なし"] = ("ช่องว่าง", "string_ตารางจับคู่_ปกติ_vs_MODEN.csv (STR_ID_SAVE_NEW_SLOT_NAME)", 4)
    translations["名前はまだ無い"] = ("ยังไม่มีชื่อ", "string_ตารางจับคู่_ปกติ_vs_MODEN.csv (STR_ID_PLAYER_NO_NAME)", 4)
    translations["どのセーブデータで遊ぶ？"] = ("จะเล่นข้อมูลบันทึกไหนดี?", "string_ตารางจับคู่_ปกติ_vs_MODEN.csv (STR_ID_SAVE_MSG_008)", 4)

    # Date Generation based on STR_ID_DATE_FORMAT: <value 1>年目 <value 2> <value 3>日 -> ปีที่ <value 1> <value 2> วันที่ <value 3>
    seasons = [('春', 'ฤดูใบไม้ผลิ'), ('夏', 'ฤดูร้อน'), ('秋', 'ฤดูใบไม้ร่วง'), ('冬', 'ฤดูหนาว')]
    count_dates = 0
    for y in range(1, 11):
        for s_jp, s_th in seasons:
            for d in range(1, 31):
                # 1年目 春 1日 -> ปีที่ 1 ฤดูใบไม้ผลิ วันที่ 1
                d_jp = f"{y}年目 {s_jp} {d}日"
                d_th = f"ปีที่ {y} {s_th} วันที่ {d}"
                add_pair(d_jp, d_th, "สูตรวันที่ตามตารางแปล STR_ID_DATE_FORMAT", 4)
                
                # 春 1日 -> ฤดูใบไม้ผลิ วันที่ 1
                sd_jp = f"{s_jp} {d}日"
                sd_th = f"{s_th} วันที่ {d}"
                add_pair(sd_jp, sd_th, "สูตรวันที่ตามตารางแปล STR_SEASON_DAY", 4)
                count_dates += 2
    # -------------------------------------------------------------------------
    # Explicit Overrides: User defined tutorials, dialogues, and system texts
    # -------------------------------------------------------------------------
    explicit_overrides = {
        # Action Tutorial
        "走って移動する": "วิ่งเคลื่อนที่",
        "ジャンプする": "กระโดด",
        "で歩いて移動できる": "สามารถเดินได้ด้วย...",
        "歩いて移動できる": "สามารถเดินได้",
        "で、目の前にある": "ด้วย... สิ่งที่อยู่ข้างหน้า",
        "目の前にある": "สิ่งที่อยู่ข้างหน้า",
        "柵に向かって行うと": "เมื่อทำเข้าหารั้ว...",
        "で平行移動する": "เคลื่อนที่ขนาน",
        "平行移動する": "เคลื่อนที่ขนาน",
        
        # Intro Dialogue
        "……誰": "......ใครน่ะ",
        "ど、ど、どうして…": "ทะ... ทะ... ทำไมกัน...",
        "こんな": "แบบนี้...",
        "と、とりあえず…": "กะ... ก่อนอื่นเลย...",
        
        # System & Save Menu (Strictly using ข้อมูลบันทึก)
        "設定画面へ": "ไปยังหน้าตั้งค่า",
        "セーブデータ削除": "ลบข้อมูลบันทึก",
        "以前のセーブデータ": "ข้อมูลบันทึกก่อนหน้า",
        "このデータを読み込みますか？": "ต้องการโหลดข้อมูลนี้หรือไม่?",
        "このゲームは1日の終了時にオートセーブされ、": "เกมนี้จะบันทึกข้อมูลอัตโนมัติเมื่อสิ้นสุดวัน",
        "最新のデータが上書きされます。": "และจะเขียนทับข้อมูลล่าสุด",
        "上のアイコンが表示されている間は、": "ในขณะที่ไอคอนด้านบนกำลังแสดงผล",
        "ゲームを終了したり、電源を切らないでください。": "กรุณาอย่าปิดเกมหรือปิดเครื่องเด็ดขาด",
        "ゲームモードを選択してください": "กรุณาเลือกโหมดเกม",
        "あんしん暮しモード": "โหมดใช้ชีวิตสบายใจ",
        "ほの暮しモード": "โหมดใช้ชีวิตปกติ",
        "この見た目にする？": "จะใช้รูปลักษณ์นี้ใช่หรือไม่?",
        
        # Item & Shop UI
        "売値": "ราคาขาย",
        "買値": "ราคาซื้อ",
        "所持金": "เงินที่มี",
        "所持数": "จำนวนที่พก",
        "個数": "จำนวน",
        "合計": "รวมทั้งหมด",
    }
    for k, v in explicit_overrides.items():
        translations[k] = (v, "User Explicit Override", 10)
    print(f"เพิ่มคำแปลเฉพาะที่กำหนดพิเศษ: {len(explicit_overrides)} รายการ")


    # -------------------------------------------------------------------------
    # Write output to C:\Users\Supakiat\Desktop\Village_in_the_Shade_ThaiMod_Dev\ตารางจับคู่คำแปล_ไทย_JP.txt
    # -------------------------------------------------------------------------
    print("กำลังบันทึกไฟล์ผลลัพธ์...")
    with open(out_file, 'w', encoding='utf-8') as f:
        f.write("# ==============================================================================\n")
        f.write("# ตารางจับคู่คำแปล ภาษาญี่ปุ่น (JP) <=> ภาษาไทย (TH)\n")
        f.write("# โครงการม็อดภาษาไทย: Village in the Shade (ほの暮しの庭)\n")
        f.write("# รวบรวมและสแกนจาก 3 แหล่งข้อมูลอย่างละเอียด:\n")
        f.write(f"#   1. {dir_f1} (สแกนทั้ง CSV และ TXT ทั้งหมด)\n")
        f.write(f"#   2. {dir_f2} (สแกนไฟล์ TXT ทั้งหมด)\n")
        f.write(f"#   3. {dir_f3} (สแกนไฟล์ CSV ทั้งหมด)\n")
        f.write(f"#\n")
        f.write(f"# จำนวนคู่แปลทั้งหมดที่จับคู่ได้: {len(translations):,} คู่\n")
        f.write(f"# รูปแบบ: ข้อความภาษาญี่ปุ่น=คำแปลภาษาไทย\n")
        f.write("# ==============================================================================\n\n")
        
        # Sort keys for clean organization
        for jp_key in sorted(translations.keys()):
            th_val, src, prio = translations[jp_key]
            f.write(f"{jp_key}={th_val}\n")

    t1 = time.time()
    print("=" * 70)
    print(f"สร้างไฟล์สำเร็จเรียบร้อยแล้ว!")
    print(f"ไฟล์ที่บันทึก: {out_file}")
    print(f"จำนวนคู่คำแปลทั้งหมด: {len(translations):,} คู่")
    print(f"เวลาที่ใช้: {t1 - t0:.2f} วินาที")
    print("=" * 70)

if __name__ == '__main__':
    main()
