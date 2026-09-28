import os
import glob
import json
import re
import time

def clean_tag_str(s):
    """
    Remove all <...> structural tags completely (such as <cmd ...>, <gamevalue ...>, <player>, <speed ...>, <br>, <color ...>, etc.)
    and clean up stray whitespaces and connecting symbols (+, ＋)
    """
    if not s:
        return ""
    # 1. Loop to strip nested tags as well
    c = s
    while '<' in c and '>' in c:
        c = re.sub(r'<[^>]+>', '', c)
    # 2. Strip any stray angle brackets
    c = c.replace('<', '').replace('>', '')
    # 3. Strip stray pluses, dashes, whitespace at ends
    c = c.strip(' ＋+\t\r\n-')
    # 4. Collapse multiple whitespaces
    c = re.sub(r'[ \t]+', ' ', c)
    # 5. Remove whitespace before ( or （ (tight spacing)
    c = re.sub(r'\s+([\(（])', r'\1', c)
    c = re.sub(r'([\)）])\s+', r'\1', c)
    return c.strip()

def clean_thai_underscores(text):
    """
    Remove underscore `_` from Thai translation text and ensure tight spacing
    e.g. 'NPC สำหรับเดโม_แม่ของโย' -> 'NPC สำหรับเดโมแม่ของโย'
    """
    if not text:
        return text
    t = text.replace('_', '')
    t = re.sub(r'\s+([\(（])', r'\1', t)
    t = re.sub(r'([\)）])\s+', r'\1', t)
    return t.strip()

def main():
    t0 = time.time()
    
    # -------------------------------------------------------------------------
    # Paths Definition
    # -------------------------------------------------------------------------
    src_dir = r"C:\Users\Supakiat\Desktop\คลังคำแปล_Village_in_the_Shade\03_ผลลัพธ์_JP_TH"
    mapping_path = r"C:\Users\Supakiat\Desktop\Mover\out\Mapping.json"
    dev_dir = r"C:\Users\Supakiat\Desktop\Village_in_the_Shade_ThaiMod_Dev"
    
    mod_dir = r"C:\Program Files (x86)\Steam\steamapps\common\Village in the Shade\Mods\TextDump"
    out_trans_path = os.path.join(mod_dir, "translation.txt")
    out_desktop_path = os.path.join(src_dir, "translation.txt")
    bak_trans_path = os.path.join(mod_dir, "translation.txt.bak")
    
    dev_plain_path = os.path.join(dev_dir, "ตารางจับคู่คำแปล_ไทย_JP.txt")
    dev_pua_path = os.path.join(dev_dir, "translation_PUA.txt")

    print("=" * 75)
    print("เริ่มกระบวนการสร้าง translation.txt ปลอดแท็กโครงสร้างและขีดล่าง 100%...")
    print(f"อ่านข้อมูลคำแปลจาก 35 ไฟล์ใน: {src_dir}")
    print("=" * 75)

    if not os.path.exists(src_dir):
        print(f"Error: ไม่พบโฟลเดอร์ต้นทาง {src_dir}")
        return

    if not os.path.exists(mapping_path):
        print(f"Error: ไม่พบไฟล์ตารางแปลงรหัส {mapping_path}")
        return

    # Load Mapping.json
    with open(mapping_path, "r", encoding="utf-8-sig") as f:
        mapping = json.load(f)
    max_len = max(len(k) for k in mapping.keys())

    def to_pua(text):
        if not text:
            return text
        result, i, n = [], 0, len(text)
        while i < n:
            matched = False
            for l in range(min(max_len, n - i), 0, -1):
                sub = text[i:i+l]
                if sub in mapping:
                    result.append(mapping[sub])
                    i += l
                    matched = True
                    break
            if not matched:
                result.append(text[i])
                i += 1
        return "".join(result)

    # -------------------------------------------------------------------------
    # 1. Read all entries from 35 files in 03_ผลลัพธ์_JP_TH
    # -------------------------------------------------------------------------
    files = sorted(glob.glob(os.path.join(src_dir, "*.txt")))
    files = [f for f in files if not f.endswith("translation.txt")]
    print(f"พบไฟล์คำแปลทั้งหมด: {len(files)} ไฟล์")

    translations = {} # jp_key -> (th_val, source_info, priority)

    def add_translation(jp, th, source, priority=1.0):
        if not jp or not th:
            return
        
        # Standardize newlines
        jp = jp.replace('\r\n', '\\n').replace('\r', '\\n').replace('\n', '\\n')
        th = th.replace('\r\n', '\\n').replace('\r', '\\n').replace('\n', '\\n')

        # Check existing priority
        if jp in translations:
            curr_th, curr_src, curr_prio = translations[jp]
            if priority > curr_prio:
                translations[jp] = (th, source, priority)
        else:
            translations[jp] = (th, source, priority)

    # File loading priorities
    file_priorities = {
        "gameSetting_จับคู่คำแปล_JP_TH.txt": 3.0,
        "tips_จับคู่คำแปล_JP_TH.txt": 2.5,
        "cmd_จับคู่คำแปล_JP_TH.txt": 2.5,
        "action_จับคู่คำแปล_JP_TH.txt": 2.0,
        "item_จับคู่คำแปล_JP_TH.txt": 2.0,
        "talk_จับคู่คำแปล_JP_TH.txt": 1.5,
        "string_จับคู่คำแปล_JP_TH.txt": 1.0,
    }

    count_entries_read = 0

    for fpath in files:
        fname = os.path.basename(fpath)
        base_prio = file_priorities.get(fname, 1.0)
        
        with open(fpath, "r", encoding="utf-8") as fp:
            for line in fp:
                s = line.strip()
                if not s or s.startswith("#") or "=" not in s:
                    continue
                parts = s.split("=", 1)
                jp = parts[0].strip()
                th = parts[1].strip()
                if not jp or not th:
                    continue

                # Fix corrupted keys
                jp = re.sub(r'\(EN:[^\)]+\)\s*', '', jp)
                if jp.startswith(')(') or jp.startswith(')（'):
                    jp = jp[1:]
                elif jp.startswith(')') and len(jp) > 1 and jp[1] in '（(':
                    jp = jp[1:]

                # 1. Clean all tags from both JP and TH
                clean_jp = clean_tag_str(jp)
                clean_th = clean_tag_str(th)

                # 2. Remove all `_` from Thai translation and tighten spacing
                clean_th = clean_thai_underscores(clean_th)

                if not clean_jp or not clean_th:
                    continue
                
                # Filter out pure punctuation junk lines
                if clean_jp in ['+=+', '/=/']:
                    continue

                # User Rule: translation.txt must have 0 underscores (_) and 0 tags (<>)
                clean_jp = clean_jp.replace('_', '')
                clean_th = clean_th.replace('_', '')

                # Add clean entry
                add_translation(clean_jp, clean_th, fname, base_prio)
                count_entries_read += 1

    print(f"อ่านและทำความสะอาดรายการสำเร็จ: {count_entries_read:,} รายการ")

    # -------------------------------------------------------------------------
    # 2. Explicit Overrides & Special Game Constants
    # -------------------------------------------------------------------------
    # User Rule: Settings collisions: なし = ปิด, あり = เปิด
    add_translation("なし", "ปิด", "User Rule: Settings なし=ปิด", 10.0)
    add_translation("あり", "เปิด", "User Rule: Settings あり=เปิด", 10.0)

    # Save & System Overrides
    system_overrides = {
        # Tutorial Action & Movement Clean Tags (Engine strips <cmd ...>)
        "走って移動する": "วิ่งเคลื่อนที่",
        "ジャンプする": "กระโดด",
        "で歩いて移動できる": "สามารถเดินได้ด้วย...",
        "歩いて移動できる": "สามารถเดินได้",
        "で、目の前にある": "สิ่งที่อยู่ข้างหน้า",
        "目の前にある": "สิ่งที่อยู่ข้างหน้า",
        "柵に向かって行うと": "เมื่อทำเข้าหารั้ว...",
        "で平行移動する": "เคลื่อนที่ขนาน",
        "平行移動する": "เคลื่อนที่ขนาน",
        "回転": "หมุนตัว",
        "農具を使う": "ใช้อุปกรณ์เกษตร",
        "農具を構える": "ตั้งท่าใช้อุปกรณ์การเกษตร",
        "で移動する": "เคลื่อนที่",
        "で構えを解除する": "ยกเลิกการตั้งท่า",
        "道具を渡す": "มอบอุปกรณ์",
        "で設置": "เพื่อจัดวาง",
        "で設置位置を調整できる": "สามารถปรับตำแหน่งจัดวางได้",
        "懐中電灯を点灯": "เปิดไฟฉาย",
        "歌のガイドを表示する": "แสดงแถบนำทางบทเพลง",
        "で釣りができる": "เพื่อเริ่มตกปลาได้",

        # Save Menu & Dialogue
        "名前はまだ無い": "ยังไม่มีชื่อ",
        "どのセーブデータで遊ぶ？": "จะเล่นข้อมูลบันทึกไหนดี?",
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

        # Economy & UI labels
        "売値": "ราคาขาย",
        "買値": "ราคาซื้อ",
        "所持金": "เงินที่มี",
        "所持数": "จำนวนที่พก",
        "個数": "จำนวน",
        "合計": "รวมทั้งหมด",
    }
    for k, v in system_overrides.items():
        add_translation(k, v, "Explicit System Override", 5.0)

    # Date Generation for HUD Display
    seasons = [('春', 'ฤดูใบไม้ผลิ'), ('夏', 'ฤดูร้อน'), ('秋', 'ฤดูใบไม้ร่วง'), ('冬', 'ฤดูหนาว')]
    for y in range(1, 11):
        for s_jp, s_th in seasons:
            for d in range(1, 31):
                # 1年目 春 1日 -> ปีที่ 1 ฤดูใบไม้ผลิ วันที่ 1
                add_translation(f"{y}年目 {s_jp} {d}日", f"ปีที่ {y} {s_th} วันที่ {d}", "Date HUD Formula", 4.0)
                # 春 1日 -> ฤดูใบไม้ผลิ วันที่ 1
                add_translation(f"{s_jp} {d}日", f"{s_th} วันที่ {d}", "Date HUD Formula", 4.0)

    print(f"รวมคู่คำแปลทั้งหมดในพจนานุกรม: {len(translations):,} คู่")

    # -------------------------------------------------------------------------
    # 3. Generate Plain Thai & PUA Converted Files
    # -------------------------------------------------------------------------
    print("กำลังแปลงอักษรไทยเป็นรหัสฟอนต์ PUA (ป้องกันสระลอย)...")
    
    plain_lines = []
    pua_lines = []

    for jp_key in sorted(translations.keys()):
        th_val, src_info, prio = translations[jp_key]
        
        # Plain Thai line
        plain_lines.append(f"{jp_key}={th_val}\n")
        
        # PUA Thai line
        th_pua = to_pua(th_val)
        pua_lines.append(f"{jp_key}={th_pua}\n")

    # -------------------------------------------------------------------------
    # 4. Save to Dev Directory
    # -------------------------------------------------------------------------
    with open(dev_plain_path, "w", encoding="utf-8") as f:
        f.write("# ==============================================================================\n")
        f.write("# ตารางจับคู่คำแปล ภาษาญี่ปุ่น (JP) <=> ภาษาไทย (TH) - ฉบับ Master สำหรับ PC\n")
        f.write("# อ้างอิงคำแปลจาก 35 ไฟล์ใน: คลังคำแปล_Village_in_the_Shade\\03_ผลลัพธ์_JP_TH\n")
        f.write(f"# จำนวนคู่คำแปลทั้งหมด: {len(translations):,} คู่ (ปลอดแท็กและขีดล่าง 100%)\n")
        f.write("# ==============================================================================\n\n")
        f.writelines(plain_lines)
    print(f"บันทึกไฟล์ Plain Thai เรียบร้อยที่: {dev_plain_path}")

    with open(dev_pua_path, "w", encoding="utf-8") as f:
        f.writelines(pua_lines)
    print(f"บันทึกไฟล์ PUA สำหรับ Dev เรียบร้อยที่: {dev_pua_path}")

    # -------------------------------------------------------------------------
    # 5. Backup & Install into Steam Game Mod Directory & Desktop 03
    # -------------------------------------------------------------------------
    if os.path.exists(mod_dir):
        # Write translation.txt into game
        with open(out_trans_path, "w", encoding="utf-8") as f:
            f.writelines(pua_lines)
        print(f"★ ติดตั้งลงในตัวเกม Steam สำเร็จที่: {out_trans_path}")
        print(f"★ ขนาดไฟล์ translation.txt: {os.path.getsize(out_trans_path):,} ไบต์")



    t1 = time.time()
    print("=" * 75)
    print("สร้างและติดตั้งไฟล์ translation.txt สำเร็จสมบูรณ์ 100%!")
    print(f"จำนวนคู่คำแปลทั้งหมด: {len(pua_lines):,} คู่")
    print(f"เวลาที่ใช้ทั้งหมด: {t1 - t0:.2f} วินาที")
    print("=" * 75)

if __name__ == "__main__":
    main()
