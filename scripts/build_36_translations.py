import os
import csv
import re
import glob
import shutil

CSV_ROOT = r"C:\Users\Administrator\Downloads\Village_PC_v130_Database_CSVs1"
MOD_DIR = r"C:\Users\Administrator\Desktop\Village in the Shade Mod"
STEAM_DIR = r"C:\Program Files (x86)\Steam\steamapps\common\Village in the Shade"

DEV_DIR = r"D:\Users\Supakiat\Desktop\Village_in_the_Shade_ThaiMod_Dev"

OUT_DIRS = [
    os.path.join(STEAM_DIR, "Mods", "translations"),
    os.path.join(MOD_DIR, "Mods", "translations"),
    os.path.join(MOD_DIR, "translations"),
    os.path.join(DEV_DIR, "Mods", "translations"),
    os.path.join(DEV_DIR, "translations"),
]

for d in OUT_DIRS:
    os.makedirs(d, exist_ok=True)

# Words that should NEVER be translated as dialogue choices in talk.txt
# because they collide with system UI buttons and toggles
TALK_BLACKLIST = {
    "なし", "あり", "Yes", "No", "Off", "On", "Empty", "None",
    "Close", "Normal", "Back", "OK", "Cancel", "はい", "いいえ"
}

def clean_existing_files():
    """Remove old *.txt in all translations folders to ensure fresh alphabetical priority."""
    for d in OUT_DIRS:
        if os.path.exists(d):
            for f in glob.glob(os.path.join(d, "*.txt")):
                try:
                    os.remove(f)
                except Exception as e:
                    print(f"Warning: could not remove {f}: {e}")

def clean_text(s):
    if not s:
        return ""
    s = s.replace("\x00", "")
    return s.strip()

def esc(s):
    s = clean_text(s)
    return s.replace("\r\n", "\n").replace("\r", "\n").replace("\n", "\\n")

def read_csv(rel_path):
    full_path = os.path.join(CSV_ROOT, rel_path)
    if not os.path.exists(full_path):
        return [], []
    with open(full_path, "r", encoding="utf-8-sig", errors="ignore") as f:
        reader = csv.reader(f)
        rows = list(reader)
    if not rows:
        return [], []
    return rows[0], rows[1:]

STYLE_TAG_RE = re.compile(r'</?(?:strong|b|speed(?:\s+[^>]*)?|color(?:\s+[^>]*)?|font(?:\s+[^>]*)?|size(?:\s+[^>]*)?)>', re.IGNORECASE)

def strip_style_tags(text):
    return STYLE_TAG_RE.sub('', text)

def extract_all_tag_slices(o, t):
    pairs = []
    o_tokens = [x.strip() for x in STYLE_TAG_RE.split(o) if x.strip()]
    t_tokens = [x.strip() for x in STYLE_TAG_RE.split(t) if x.strip()]
    if len(o_tokens) == len(t_tokens) and len(o_tokens) > 1:
        for o_tok, t_tok in zip(o_tokens, t_tokens):
            if o_tok and t_tok and o_tok != t_tok:
                # DANGEROUS: Short tokens (< 4 chars) or single ASCII characters hijack keystrokes (e.g. 'e', 'd', 'L')
                if len(o_tok) < 4:
                    continue
                pairs.append((o_tok, t_tok))
    return pairs

CMD_ATTR_RE = re.compile(r'<cmd\s+([A-Za-z0-9_]+)[^>]*>', re.IGNORECASE)

def join_thai_parts(parts):
    res = ''
    for p in parts:
        p = p.strip()
        if not p: continue
        if not res:
            res = p
        else:
            if res.endswith('<br>') or p.startswith('<br>'):
                res = res + p
            elif res.endswith(' ') or res.endswith('...') or res.endswith('…'):
                res = res + p
            elif res.endswith('!') or res.endswith('?') or res.endswith(','):
                res = res + ' ' + p
            else:
                res = res + ' ' + p
    return res

def extract_talk_pairs_en(r_en):
    pairs = []
    curr_key = None
    curr_en = ''
    curr_th_list = []
    
    for r in r_en:
        if len(r) < 5: continue
        key = r[2].strip()
        en = r[3].strip()
        th = r[4].strip()
        
        if key != curr_key:
            if curr_en and curr_th_list:
                pairs.append((curr_en, join_thai_parts(curr_th_list)))
            curr_key = key
            curr_en = en
            curr_th_list = [th] if th else []
        else:
            if not en and th:
                curr_th_list.append(th)
            elif en:
                if curr_en and curr_th_list:
                    pairs.append((curr_en, join_thai_parts(curr_th_list)))
                curr_en = en
                curr_th_list = [th] if th else []

    if curr_en and curr_th_list:
        pairs.append((curr_en, join_thai_parts(curr_th_list)))
    return pairs

def save_category_file(filename, title, pairs_en, pairs_jp, is_item_or_desc=False, filter_blacklist=False):
    seen = set()
    content_lines = []

    content_lines.append(f"# ============================================================================\n")
    content_lines.append(f"# {title}\n")
    content_lines.append(f"# ============================================================================\n\n")

    content_lines.append(f"# --- [ENGLISH] ---\n")
    for raw_o, raw_t in pairs_en:
        o = clean_text(raw_o)
        t = clean_text(raw_t)
        if not o or not t or o in seen:
            continue
        # Failsafe: Never allow single ASCII letters/digits or whitespace to become translation keys
        if len(o) == 1 and (o.isascii() and (o.isalnum() or o in ' \t\r\n.,;:!?-')):
            continue
        if len(o) <= 2 and o.isascii() and filename not in ("41_string.txt", "42_gamesetting.txt", "34_framework_string.txt", "27_vkey.txt"):
            continue
        if filter_blacklist:
            if o in TALK_BLACKLIST:
                continue
            if len(o) <= 2 and o.isascii():
                continue
        seen.add(o)
        content_lines.append(f"{esc(o)}={esc(t)}\n")
        # Preserve exact raw whitespace if different from stripped
        if raw_o != o and raw_o not in seen:
            seen.add(raw_o)
            content_lines.append(f"{esc(raw_o)}={esc(raw_t)}\n")
        # Fallback for style tags stripped by engine
        o_clean = strip_style_tags(o)
        if o_clean != o and o_clean and o_clean not in seen:
            t_clean = strip_style_tags(t)
            seen.add(o_clean)
            content_lines.append(f"{esc(o_clean)}={esc(t_clean)}\n")
        # Fallback for tag slices (when engine splits at tags)
        for o_slice, t_slice in extract_all_tag_slices(o, t):
            if o_slice not in seen:
                if filter_blacklist and o_slice in TALK_BLACKLIST:
                    continue
                seen.add(o_slice)
                content_lines.append(f"{esc(o_slice)}={esc(t_slice)}\n")
        # Fallback for cmd tags with attribute stripping (e.g. <cmd CMD_NAME -offsetY -5> -> <cmd CMD_NAME>)
        if '<cmd' in o.lower():
            o_cmd = CMD_ATTR_RE.sub(r'<cmd \1>', o)
            if o_cmd != o and o_cmd not in seen:
                t_cmd = CMD_ATTR_RE.sub(r'<cmd \1>', t) if '<cmd' in t.lower() else t
                seen.add(o_cmd)
                content_lines.append(f"{esc(o_cmd)}={esc(t_cmd)}\n")
            orig_parts = re.split(r'<cmd[^>]*>', o, flags=re.IGNORECASE)
            trans_parts = re.split(r'<cmd[^>]*>', t, flags=re.IGNORECASE)
            if len(orig_parts) == len(trans_parts) and len(orig_parts) > 1:
                for op, tp in zip(orig_parts, trans_parts):
                    op_c = op.strip()
                    tp_c = tp.strip()
                    if len(op_c) >= 4 and tp_c and op_c not in seen:
                        if filter_blacklist and op_c in TALK_BLACKLIST:
                            continue
                        seen.add(op_c)
                        content_lines.append(f"{esc(op_c)}={esc(tp_c)}\n")
        if is_item_or_desc:
            if not o.endswith("<br>"):
                v_br = o + "<br>"
                if v_br not in seen:
                    seen.add(v_br)
                    content_lines.append(f"{esc(v_br)}={esc(t)}\n")
            if o.endswith("。") or o.endswith("."):
                v_no_dot = o[:-1].strip()
                if v_no_dot and v_no_dot not in seen:
                    seen.add(v_no_dot)
                    content_lines.append(f"{esc(v_no_dot)}={esc(t)}\n")
                v_no_dot_br = v_no_dot + "<br>"
                if v_no_dot_br not in seen:
                    seen.add(v_no_dot_br)
                    content_lines.append(f"{esc(v_no_dot_br)}={esc(t)}\n")

    content_lines.append(f"\n# --- [JAPANESE] ---\n")
    for raw_o, raw_t in pairs_jp:
        o = clean_text(raw_o)
        t = clean_text(raw_t)
        if not o or not t or o in seen:
            continue
        # Failsafe: Never allow single ASCII letters/digits or whitespace to become translation keys
        if len(o) == 1 and (o.isascii() and (o.isalnum() or o in ' \t\r\n.,;:!?-')):
            continue
        if len(o) <= 2 and o.isascii() and filename not in ("41_string.txt", "42_gamesetting.txt", "34_framework_string.txt", "27_vkey.txt"):
            continue
        if filter_blacklist:
            if o in TALK_BLACKLIST:
                continue
            if len(o) <= 2 and o.isascii():
                continue
        seen.add(o)
        content_lines.append(f"{esc(o)}={esc(t)}\n")
        # Preserve exact raw whitespace if different from stripped
        if raw_o != o and raw_o not in seen:
            seen.add(raw_o)
            content_lines.append(f"{esc(raw_o)}={esc(raw_t)}\n")
        # Fallback for style tags stripped by engine
        o_clean = strip_style_tags(o)
        if o_clean != o and o_clean and o_clean not in seen:
            t_clean = strip_style_tags(t)
            seen.add(o_clean)
            content_lines.append(f"{esc(o_clean)}={esc(t_clean)}\n")
        # Fallback for tag slices (when engine splits at tags)
        for o_slice, t_slice in extract_all_tag_slices(o, t):
            if o_slice not in seen:
                if filter_blacklist and o_slice in TALK_BLACKLIST:
                    continue
                seen.add(o_slice)
                content_lines.append(f"{esc(o_slice)}={esc(t_slice)}\n")
        # Fallback for cmd tags with attribute stripping (e.g. <cmd CMD_NAME -offsetY -5> -> <cmd CMD_NAME>)
        if '<cmd' in o.lower():
            o_cmd = CMD_ATTR_RE.sub(r'<cmd \1>', o)
            if o_cmd != o and o_cmd not in seen:
                t_cmd = CMD_ATTR_RE.sub(r'<cmd \1>', t) if '<cmd' in t.lower() else t
                seen.add(o_cmd)
                content_lines.append(f"{esc(o_cmd)}={esc(t_cmd)}\n")
            orig_parts = re.split(r'<cmd[^>]*>', o, flags=re.IGNORECASE)
            trans_parts = re.split(r'<cmd[^>]*>', t, flags=re.IGNORECASE)
            if len(orig_parts) == len(trans_parts) and len(orig_parts) > 1:
                for op, tp in zip(orig_parts, trans_parts):
                    op_c = op.strip()
                    tp_c = tp.strip()
                    if len(op_c) >= 4 and tp_c and op_c not in seen:
                        if filter_blacklist and op_c in TALK_BLACKLIST:
                            continue
                        seen.add(op_c)
                        content_lines.append(f"{esc(op_c)}={esc(tp_c)}\n")
        if is_item_or_desc:
            if not o.endswith("<br>"):
                v_br = o + "<br>"
                if v_br not in seen:
                    seen.add(v_br)
                    content_lines.append(f"{esc(v_br)}={esc(t)}\n")
            if o.endswith("。") or o.endswith("."):
                v_no_dot = o[:-1].strip()
                if v_no_dot and v_no_dot not in seen:
                    seen.add(v_no_dot)
                    content_lines.append(f"{esc(v_no_dot)}={esc(t)}\n")
                v_no_dot_br = v_no_dot + "<br>"
                if v_no_dot_br not in seen:
                    seen.add(v_no_dot_br)
                    content_lines.append(f"{esc(v_no_dot_br)}={esc(t)}\n")

    # Write to all output dirs
    for d in OUT_DIRS:
        dest = os.path.join(d, filename)
        with open(dest, "w", encoding="utf-8", newline="\n") as f:
            f.writelines(content_lines)

    print(f"  [OK] {filename} ({len(seen):,} รายการ)")
    return len(seen)

def main():
    print("=" * 70)
    print("สร้างไฟล์คำแปลแยกหมวดหมู่ (Update-Proof Modular Translations)")
    print("จัดลำดับความสำคัญ: บทสนทนา -> สิ่งปลูกสร้าง/ไอเทม -> เมนู -> ตั้งค่า/วันเวลา")
    print("=" * 70)

    clean_existing_files()
    total_all = 0

    # -------------------------------------------------------------------------
    # Group 1: เนื้อเรื่องและบทสนทนา (Dialogue & Story) - โหลดก่อนสุด Priority ต่ำสุด
    # -------------------------------------------------------------------------
    # 01. Talk (Dialogue)
    _, r_en = read_csv(r"talk\talk_แปลจาก_EN.csv")
    _, r_jp = read_csv(r"talk\talk_แปลจาก_JP.csv")
    p_en = extract_talk_pairs_en(r_en)
    p_jp = [(r[3], r[4]) for r in r_jp if len(r) > 4]
    p_en.extend([
        ("Now, at last, you've made something precious.", "เท่านี้เธอก็มีสิ่งล้ำค่า<br>เป็นของตัวเองแล้วนะ"),
        ("Here, <player>. Your pay for those veggies.", "เอ้า <player> นี่คือค่าตอบแทน<br>สำหรับผักพวกนั้น"),
        ("K-Kisuke! This is bad!", "คุ... คุณคิสึเกะ! แย่แล้วค่ะ!"),
        ("Good morning, <player>. Here...take a look at this!", "อรุณสวัสดิ์ <player>! นี่... ลองดูนี่สิ!"),
        ("I should answer the door...", "ต้องไปเปิดประตูแล้วสิ..."),
        ("I should answer the do", "ต้องไปเปิดประตูแล้วสิ..."),
        ("I knew you were no ordinary child.", "ก็อย่างที่คิดไว้ คุณน่ะ ไม่ใช่เด็กธรรมดาเลยนะ"),
        ("I knew you were no ord", "ก็อย่างที่คิดไว้ คุณน่ะ ไม่ใช่เด็กธรรมดาเลยนะ"),
        ("Someone's here to see me.", "เหมือนมีใครกำลังเรียก"),
    ])
    total_all += save_category_file("01_talk.txt", "01. บทสนทนาและเนื้อเรื่อง (Dialogue - talk)", p_en, p_jp, filter_blacklist=True)

    # 02. Tip
    _, r_en = read_csv(r"tip\tip_แปลจาก_EN.csv")
    _, r_jp = read_csv(r"tip\tip_แปลจาก_JP.csv")
    p_en = [(r[4], r[5]) for r in r_en if len(r) > 5]
    p_jp = [(r[4], r[5]) for r in r_jp if len(r) > 5]
    p_en.extend([
        ("Press <cmd CMD_INTERACTION_HARVEST> to harvest matured crops in front of you.", "กด<cmd CMD_INTERACTION_HARVEST>เก็บเกี่ยว"),
        ("Hold <cmd CMD_INTERACTION_HARVEST> in front of a crop to continuously harvest", "กด<cmd CMD_INTERACTION_HARVEST>ค้างไว้ตรงหน้าพืชผลเพื่อเก็บเกี่ยว"),
        ("Press", "กด"),
        ("Hold", "กด"),
        ("to harvest matured crops in front of you.", "เพื่อเก็บเกี่ยวพืชผลที่โตเต็มที่ตรงหน้า"),
        ("to harvest matured crops in front of you", "เพื่อเก็บเกี่ยวพืชผลที่โตเต็มที่ตรงหน้า"),
        ("in front of a crop to continuously harvest", "ค้างไว้ตรงหน้าพืชผลเพื่อเก็บเกี่ยวอย่างต่อเนื่อง"),
        ("crops of the same type.", "พืชผลชนิดเดียวกันอย่างต่อเนื่อง"),
        ("Persistent Harvesting", "เก็บเกี่ยวต่อเนื่อง"),
        ("Harvesting", "เก็บเกี่ยวพืชผล"),
        ("Move the inventory bar cursor left and right", "เลื่อนเคอร์เซอร์แถบอุปกรณ์ (ซ้าย/ขวา)"),
    ])
    total_all += save_category_file("02_tip.txt", "02. คำแนะนำและทริคการเล่น (Tips)", p_en, p_jp)

    # 03. Quest
    _, r_en = read_csv(r"quest\quest_แปลจาก_EN.csv")
    _, r_jp = read_csv(r"quest\quest_แปลจาก_JP.csv")
    p_en = [(r[4], r[5]) for r in r_en if len(r) > 5]
    p_jp = [(r[4], r[5]) for r in r_jp if len(r) > 5]
    p_en.extend([
        ("Take care of the vegetables", "ดูแลพืชผักที่ปลูกเอาไว้ให้ดี"),
        ("Take care of the vegetables you planted", "ดูแลพืชผักที่ปลูกเอาไว้ให้ดี"),
    ])
    total_all += save_category_file("03_quest.txt", "03. ภารกิจและเควสต์ (Quests)", p_en, p_jp)

    # 04. LostBook
    _, r_en = read_csv(r"lostbook\lostbook_แปลจาก_EN.csv")
    _, r_jp = read_csv(r"lostbook\lostbook_แปลจาก_JP.csv")
    p_en = [(r[4], r[5]) for r in r_en if len(r) > 5]
    p_jp = [(r[4], r[5]) for r in r_jp if len(r) > 5]
    total_all += save_category_file("04_lostbook.txt", "04. สมุดที่สาบสูญ (Lost Books)", p_en, p_jp)

    # 05. Reminiscence
    _, r_en = read_csv(r"reminiscence\reminiscence_แปลจาก_EN.csv")
    _, r_jp = read_csv(r"reminiscence\reminiscence_แปลจาก_JP.csv")
    p_en = [(r[4], r[5]) for r in r_en if len(r) > 5]
    p_jp = [(r[4], r[5]) for r in r_jp if len(r) > 5]
    total_all += save_category_file("05_reminiscence.txt", "05. ความทรงจำ (Reminiscence)", p_en, p_jp)

    # 06. Letter
    _, r_en = read_csv(r"letter\letter_แปลจาก_EN.csv")
    _, r_jp = read_csv(r"letter\letter_แปลจาก_JP.csv")
    p_en = [(r[4], r[5]) for r in r_en if len(r) > 5]
    p_jp = [(r[4], r[5]) for r in r_jp if len(r) > 5]
    total_all += save_category_file("06_letter.txt", "06. จดหมาย (Letters)", p_en, p_jp)

    # -------------------------------------------------------------------------
    # Group 2: ไอเทม สิ่งปลูกสร้าง สถานที่ สิ่งมีชีวิต และผังสกิล (Entities)
    # -------------------------------------------------------------------------
    # 10. Item
    _, r_en = read_csv(r"item\item_แปลจาก_EN.csv")
    _, r_jp = read_csv(r"item\item_แปลจาก_JP.csv")
    p_en = []
    for r in r_en:
        if len(r) > 10:
            p_en.extend([(r[3], r[7]), (r[4], r[8]), (r[5], r[9]), (r[6], r[10])])
    p_jp = []
    for r in r_jp:
        if len(r) > 10:
            p_jp.extend([(r[3], r[7]), (r[4], r[8]), (r[5], r[9]), (r[6], r[10])])
    total_all += save_category_file("10_item.txt", "10. ไอเทมและคำอธิบาย (Items & Descriptions)", p_en, p_jp, is_item_or_desc=True)

    # 11. Crops
    _, r_en = read_csv(r"crops\crops_แปลจาก_EN.csv")
    _, r_jp = read_csv(r"crops\crops_แปลจาก_JP.csv")
    p_en = [(r[3], r[4]) for r in r_en if len(r) > 4]
    p_jp = [(r[3], r[4]) for r in r_jp if len(r) > 4]
    total_all += save_category_file("11_crops.txt", "11. พืชผล (Crops)", p_en, p_jp)

    # 12. Construction
    _, r_en = read_csv(r"construction\construction_แปลจาก_EN.csv")
    _, r_jp = read_csv(r"construction\construction_แปลจาก_JP.csv")
    p_en = []
    for r in r_en:
        if len(r) > 10:
            p_en.extend([(r[3], r[7]), (r[4], r[8]), (r[5], r[9]), (r[6], r[10])])
    p_jp = []
    for r in r_jp:
        if len(r) > 10:
            p_jp.extend([(r[3], r[7]), (r[4], r[8]), (r[5], r[9]), (r[6], r[10])])
    total_all += save_category_file("12_construction.txt", "12. สิ่งปลูกสร้าง (Construction)", p_en, p_jp, is_item_or_desc=True)

    # 13. Facility
    _, r_en = read_csv(r"facility\facility_แปลจาก_EN.csv")
    _, r_jp = read_csv(r"facility\facility_แปลจาก_JP.csv")
    p_en = [(r[2], r[3]) for r in r_en if len(r) > 3] + [(r[5], r[6]) for r in r_en if len(r) > 6 and r[5].strip()]
    p_jp = [(r[2], r[3]) for r in r_jp if len(r) > 3] + [(r[5], r[6]) for r in r_jp if len(r) > 6 and r[5].strip()]
    total_all += save_category_file("13_facility.txt", "13. สถานที่และสิ่งอำนวยความสะดวก (Facilities)", p_en, p_jp)

    # 14. FacilityRelease
    _, r_en = read_csv(r"facilityrelease\facilityrelease_แปลจาก_EN.csv")
    _, r_jp = read_csv(r"facilityrelease\facilityrelease_แปลจาก_JP.csv")
    p_en = [(r[4], r[5]) for r in r_en if len(r) > 5]
    p_jp = [(r[4], r[5]) for r in r_jp if len(r) > 5]
    total_all += save_category_file("14_facilityrelease.txt", "14. การปลดล็อกสถานที่ (Facility Release)", p_en, p_jp)

    # 15. Creature
    _, r_en = read_csv(r"creature\creature_แปลจาก_EN.csv")
    _, r_jp = read_csv(r"creature\creature_แปลจาก_JP.csv")
    p_en = [(r[3], r[4]) for r in r_en if len(r) > 4]
    p_jp = [(r[3], r[4]) for r in r_jp if len(r) > 4]
    total_all += save_category_file("15_creature.txt", "15. สิ่งมีชีวิตและสัตว์ป่า (Creatures)", p_en, p_jp)

    # 16. Livestock
    _, r_en = read_csv(r"livestock\livestock_แปลจาก_EN.csv")
    _, r_jp = read_csv(r"livestock\livestock_แปลจาก_JP.csv")
    p_en = [(r[3], r[4]) for r in r_en if len(r) > 4]
    p_jp = [(r[3], r[4]) for r in r_jp if len(r) > 4]
    total_all += save_category_file("16_livestock.txt", "16. ปศุสัตว์ (Livestock)", p_en, p_jp)

    # 17. ItemType
    _, r_en = read_csv(r"itemtype\itemtype_แปลจาก_EN.csv")
    _, r_jp = read_csv(r"itemtype\itemtype_แปลจาก_JP.csv")
    p_en = [(r[3], r[4]) for r in r_en if len(r) > 4]
    p_jp = [(r[3], r[4]) for r in r_jp if len(r) > 4]
    total_all += save_category_file("17_itemtype.txt", "17. หมวดหมู่ไอเทม (Item Types)", p_en, p_jp)

    # 18. Bundle
    _, r_en = read_csv(r"bundle\bundle_แปลจาก_EN.csv")
    _, r_jp = read_csv(r"bundle\bundle_แปลจาก_JP.csv")
    p_en = [(r[3], r[4]) for r in r_en if len(r) > 4]
    p_jp = [(r[3], r[4]) for r in r_jp if len(r) > 4]
    total_all += save_category_file("18_bundle.txt", "18. ชุดสินค้าและแพ็กเกจ (Bundles)", p_en, p_jp)

    # 19. BundleGroup
    _, r_en = read_csv(r"bundlegroup\bundlegroup_แปลจาก_EN.csv")
    _, r_jp = read_csv(r"bundlegroup\bundlegroup_แปลจาก_JP.csv")
    p_en = [(r[4], r[5]) for r in r_en if len(r) > 5]
    p_jp = [(r[5], r[6]) for r in r_jp if len(r) > 6]
    total_all += save_category_file("19_bundlegroup.txt", "19. กลุ่มสินค้า (Bundle Groups)", p_en, p_jp)

    # 20. SkillTree
    _, r_en = read_csv(r"skilltree\skilltree_แปลจาก_EN.csv")
    _, r_jp = read_csv(r"skilltree\skilltree_แปลจาก_JP.csv")
    p_en = [(r[3], r[6]) for r in r_en if len(r) > 7] + [(r[4], r[7]) for r in r_en if len(r) > 7]
    p_jp = [(r[3], r[6]) for r in r_jp if len(r) > 8] + [(r[4], r[7]) for r in r_jp if len(r) > 8] + [(r[5], r[8]) for r in r_jp if len(r) > 8]
    total_all += save_category_file("20_skilltree.txt", "20. ผังสกิล (Skill Tree)", p_en, p_jp)

    # 21. Trophy
    _, r_en = read_csv(r"trophy\trophy_แปลจาก_EN.csv")
    _, r_jp = read_csv(r"trophy\trophy_แปลจาก_JP.csv")
    p_en = [(r[3], r[5]) for r in r_en if len(r) > 6] + [(r[4], r[6]) for r in r_en if len(r) > 6]
    p_jp = [(r[3], r[5]) for r in r_jp if len(r) > 6] + [(r[4], r[6]) for r in r_jp if len(r) > 6]
    total_all += save_category_file("21_trophy.txt", "21. ถ้วยรางวัลและความสำเร็จ (Trophies)", p_en, p_jp)

    # 22. Intangible
    _, r_en = read_csv(r"intangeble\intangeble_แปลจาก_EN.csv")
    _, r_jp = read_csv(r"intangeble\intangeble_แปลจาก_JP.csv")
    p_en = [(r[4], r[5]) for r in r_en if len(r) > 5 and r[4].strip() and r[5].strip()]
    p_jp = [(r[4], r[5]) for r in r_jp if len(r) > 5 and r[4].strip() and r[5].strip()]
    total_all += save_category_file("22_intangeble.txt", "22. ทักษะติดตัว (Intangible)", p_en, p_jp)

    # 23. GameEffect
    _, r_en = read_csv(r"gameeffect\gameeffect_แปลจาก_EN.csv")
    _, r_jp = read_csv(r"gameeffect\gameeffect_แปลจาก_JP.csv")
    p_en = [(r[3], r[4]) for r in r_en if len(r) > 4 and r[3].strip() and r[3].strip() != "N/A" and r[4].strip()]
    p_jp = []
    for r in r_jp:
        if len(r) > 6:
            if r[3].strip() and r[5].strip():
                p_jp.append((r[3], r[5]))
            if r[4].strip() and r[6].strip():
                p_jp.append((r[4], r[6]))
    total_all += save_category_file("23_gameeffect.txt", "23. เอฟเฟกต์ในเกม (Game Effects)", p_en, p_jp)

    # -------------------------------------------------------------------------
    # Group 3: ตัวละคร ท่าทาง ข้อความระบบ และเฟรมเวิร์ก (Characters & Frameworks)
    # -------------------------------------------------------------------------
    # 24. Character
    _, r_en = read_csv(r"character\character_แปลจาก_EN.csv")
    _, r_jp = read_csv(r"character\character_แปลจาก_JP.csv")
    p_en = []
    for r in r_en:
        if len(r) > 15:
            if r[3] and r[10]: p_en.append((r[3], r[10]))  # ชื่อ
            if r[4] and r[11]: p_en.append((r[4], r[11]))  # บทบาท
            if r[5] and (r[12] or r[13] or r[14]):
                desc_comb = '<br>'.join([x for x in [r[12], r[13], r[14]] if x])
                p_en.append((r[5], desc_comb))              # คำอธิบายรวม
            if r[6] and r[12]: p_en.append((r[6], r[12]))  # คำอธิบาย 1
            if r[7] and r[13]: p_en.append((r[7], r[13]))  # คำอธิบาย 2
            if r[8] and r[14]: p_en.append((r[8], r[14]))  # คำอธิบาย 3
            if r[9] and r[15]: p_en.append((r[9], r[15]))  # คำทักทาย
    p_jp = []
    for r in r_jp:
        if len(r) > 14:
            if r[3] and r[9]: p_jp.append((r[3], r[9]))    # ชื่อ
            if r[4] and r[10]: p_jp.append((r[4], r[10]))  # บทบาท
            if r[5] and r[11]: p_jp.append((r[5], r[11]))  # คำอธิบาย 1
            if r[6] and r[12]: p_jp.append((r[6], r[12]))  # คำอธิบาย 2
            if r[7] and r[13]: p_jp.append((r[7], r[13]))  # คำอธิบาย 3
            if r[8] and r[14]: p_jp.append((r[8], r[14]))  # คำทักทาย
    total_all += save_category_file("24_character.txt", "24. ตัวละครและบทบาท (Characters)", p_en, p_jp)

    # 25. Action
    _, r_en = read_csv(r"action\action_แปลจาก_EN.csv")
    _, r_jp = read_csv(r"action\action_แปลจาก_JP.csv")
    p_en = [(r[3], r[5]) for r in r_en if len(r) > 6] + [(r[4], r[6]) for r in r_en if len(r) > 6]
    p_jp = [(r[3], r[5]) for r in r_jp if len(r) > 6] + [(r[4], r[6]) for r in r_jp if len(r) > 6]
    total_all += save_category_file("25_action.txt", "25. ท่าทางและการกระทำ (Actions)", p_en, p_jp)

    # 26. TalkNameplate
    _, r_en = read_csv(r"talknameplate\talknameplate_แปลจาก_EN.csv")
    _, r_jp = read_csv(r"talknameplate\talknameplate_แปลจาก_JP.csv")
    p_en = [(r[4], r[5]) for r in r_en if len(r) > 5]
    p_jp = [(r[4], r[5]) for r in r_jp if len(r) > 5]
    total_all += save_category_file("26_talknameplate.txt", "26. ป้ายชื่อผู้พูด (Talk Nameplates)", p_en, p_jp)

    # 27. VKey
    _, r_en = read_csv(r"vkey\vkey_แปลจาก_EN.csv")
    _, r_jp = read_csv(r"vkey\vkey_แปลจาก_JP.csv")
    p_en = [(r[4], r[5]) for r in r_en if len(r) > 5]
    p_jp = [(r[4], r[5]) for r in r_jp if len(r) > 5]
    total_all += save_category_file("27_vkey.txt", "27. ปุ่มควบคุม (Virtual Keys)", p_en, p_jp)

    # 28. Whistle
    _, r_en = read_csv(r"whistle\whistle_แปลจาก_EN.csv")
    _, r_jp = read_csv(r"whistle\whistle_แปลจาก_JP.csv")
    p_en = [(r[4], r[5]) for r in r_en if len(r) > 5]
    p_jp = [(r[4], r[5]) for r in r_jp if len(r) > 5]
    total_all += save_category_file("28_whistle.txt", "28. นกหวีด (Whistle)", p_en, p_jp)

    # 29. BGM
    _, r_en = read_csv(r"bgm\bgm_แปลจาก_EN.csv")
    _, r_jp = read_csv(r"bgm\bgm_แปลจาก_JP.csv")
    p_en = [(r[4], r[5]) for r in r_en if len(r) > 5]
    p_jp = [(r[4], r[5]) for r in r_jp if len(r) > 5]
    total_all += save_category_file("29_bgm.txt", "29. เพลงประกอบ (BGM)", p_en, p_jp)

    # 30. MultilineText
    _, r_en = read_csv(r"multilinetext\multilinetext_แปลจาก_EN.csv")
    _, r_jp = read_csv(r"multilinetext\multilinetext_แปลจาก_JP.csv")
    p_en = [(r[3], r[4]) for r in r_en if len(r) > 4]
    p_jp = [(r[3], r[4]) for r in r_jp if len(r) > 4]
    total_all += save_category_file("30_multilinetext.txt", "30. ข้อความหลายบรรทัด (Multiline Text)", p_en, p_jp)

    # 31. UpdateText
    _, r_en = read_csv(r"updatetext\updatetext_แปลจาก_EN.csv")
    _, r_jp = read_csv(r"updatetext\updatetext_แปลจาก_JP.csv")
    p_en = [(r[3], r[4]) for r in r_en if len(r) > 4]
    p_jp = [(r[3], r[4]) for r in r_jp if len(r) > 4]

    # Additional Update 1.20 content from game data (Japanese & English)
    v120_jp = [
        ("【1.20アップデート】", "【อัปเดต 1.20】"),
        ("『家具と家畜のバリエーション』", "『ความหลากหลายของเฟอร์นิเจอร์และปศุสัตว์』"),
        ("『農地拡張』『家具のカタログ』などの要素を追加しました。", "เพิ่มระบบ เช่น 『ขยายพื้นที่เพาะปลูก』 『แคตตาล็อกเฟอร์นิเจอร์』 เป็นต้น"),
        ("なお、機能の解放イベントには発生条件があります。", "ทั้งนี้ อีเวนต์ปลดล็อกฟังก์ชันจะมีเงื่อนไขการเกิดอยู่"),
        ("詳細は以下をご確認ください。", "โปรดตรวจสอบรายละเอียดด้านล่าง"),
        ("・家具『キャンプシリーズ』の追加", "・เพิ่มเฟอร์นิเจอร์ 『ซีรีส์แคมป์ปิ้ง』"),
        ("　　発生条件：キジの狩猟免許を取得している", "　　เงื่อนไขการเกิด: ได้รับใบอนุญาตล่าไก่ฟ้าแล้ว"),
        ("・家畜『ウコッケイ』『カモ』の追加", "・เพิ่มปศุสัตว์ 『ไก่ซิลกี้』 และ 『เป็ด』"),
        ("　　発生条件：1年目秋以降に到達したことがある", "　　เงื่อนไขการเกิด: เคยเล่นถึงฤดูใบไม้ร่วงปีที่ 1 ขึ้นไป"),
        ("・家畜『ふさふさのウシ』『まだらヤギ』の追加", "・เพิ่มปศุสัตว์ 『วัวขนฟู』 และ 『แพะลายด่าง』"),
        ("　　発生条件：ヤギを購入したことがある", "　　เงื่อนไขการเกิด: เคยซื้อแพะมาก่อน"),
        ("・『農地拡張』機能追加", "・เพิ่มฟังก์ชัน 『ขยายพื้นที่เพาะปลูก』"),
        ("　　（ほの暮しモード）発生条件：トバリから祠修復の依頼を受けており、追加の農地を全て購入している", "　　（โหมดปกติ）เงื่อนไขการเกิด: ได้รับคำขอซ่อมศาลเจ้าจากโทบาริ และซื้อพื้นที่เพาะปลูกเพิ่มเติมครบทั้งหมดแล้ว"),
        ("　　（あんしん暮しモード）発生条件：ナゴが村に住んでおり、追加の農地を全て購入している", "　　（โหมดชีวิตแสนสบายใจ）เงื่อนไขการเกิด: นาโงะอาศัยอยู่ในหมู่บ้าน และซื้อพื้นที่เพาะปลูกเพิ่มเติมครบทั้งหมดแล้ว"),
        ("・家具『家具のカタログ』の追加", "・เพิ่มเฟอร์นิเจอร์ 『แคตตาล็อกเฟอร์นิเจอร์』"),
        ("　　発生条件：1年目秋以降に到達したことがあり、家具を雑貨店か露天商で購入したことがある", "　　เงื่อนไขการเกิด: เคยเล่นถึงฤดูใบไม้ร่วงปีที่ 1 ขึ้นไป และเคยซื้อเฟอร์นิเจอร์จากร้านขายของชำหรือพ่อค้าเร่"),
        ("※一部のイベントはメインシナリオの一部区間と、雷雨の日にはイベントが発生しません", "※อีเวนต์บางส่วนจะไม่เกิดขึ้นในบางช่วงของเนื้อเรื่องหลัก และในวันที่มีพายุฝนฟ้าคะนอง"),
    ]
    v120_en = [
        ("[1.20 Update]", "【อัปเดต 1.20】"),
        ("New Furniture and Livestock", "『ความหลากหลายของเฟอร์นิเจอร์และปศุสัตว์』"),
        ("Additional farmland expansion and furniture catalog added.", "เพิ่มระบบ เช่น 『ขยายพื้นที่เพาะปลูก』 『แคตตาล็อกเฟอร์นิเจอร์』 เป็นต้น"),
        ("Please note that these new items and animals require certain prerequisites to be met in order to unlock.", "ทั้งนี้ อีเวนต์ปลดล็อกฟังก์ชันและสัตว์ใหม่จะมีเงื่อนไขการเกิดอยู่"),
        ("See below for details.", "โปรดตรวจสอบรายละเอียดด้านล่าง"),
        ("- New Furniture: Camping Series", "・เพิ่มเฟอร์นิเจอร์ 『ซีรีส์แคมป์ปิ้ง』"),
        ("     Prerequisite:", "     เงื่อนไขการเกิด:"),
        ("     Obtain the Pheasant Hunting Permit", "     ได้รับใบอนุญาตล่าไก่ฟ้าแล้ว"),
        ("- New Livestock: Silkie Chickens and Mallards", "・เพิ่มปศุสัตว์ 『ไก่ซิลกี้』 และ 『เป็ด』"),
        ("     Prerequisite: ", "     เงื่อนไขการเกิด:"),
        ("     Reach Autumn of the 1st year", "     เคยเล่นถึงฤดูใบไม้ร่วงปีที่ 1 ขึ้นไป"),
        ("- New Livestock: Fluffy Cows and Spotted Goats", "・เพิ่มปศุสัตว์ 『วัวขนฟู』 และ 『แพะลายด่าง』"),
        ("     Prerequisite: ", "     เงื่อนไขการเกิด:"),
        ("     Have purchased at least one goat", "     เคยซื้อแพะมาก่อน"),
        ("- Additional Farmland Expansion Option", "・เพิ่มฟังก์ชัน 『ขยายพื้นที่เพาะปลูก』"),
        ("     Village in the Shade Mode Prerequisite:", "     เงื่อนไขการเกิดในโหมดปกติ (Village in the Shade):"),
        ("     Tobari has given her request to restore the hokora and all additional farmland has been purchased.", "     ได้รับคำขอซ่อมศาลเจ้าจากโทบาริ และซื้อพื้นที่เพาะปลูกเพิ่มเติมครบทั้งหมดแล้ว"),
        ("     Village in the Sunshine Mode Prerequisite: ", "     เงื่อนไขการเกิดในโหมดชีวิตแสนสบายใจ (Village in the Sunshine):"),
        ("     Nago has taken up residence in the village and all additional farmland has been purchased.", "     นาโงะอาศัยอยู่ในหมู่บ้าน และซื้อพื้นที่เพาะปลูกเพิ่มเติมครบทั้งหมดแล้ว"),
        ("- New Item: Furniture Catalog", "・เพิ่มเฟอร์นิเจอร์ 『แคตตาล็อกเฟอร์นิเจอร์』"),
        ("     Prerequisite: ", "     เงื่อนไขการเกิด:"),
        ("     Reach Autumn of the 1st year and purchase at least one piece of furniture from either the General", "     เคยเล่นถึงฤดูใบไม้ร่วงปีที่ 1 ขึ้นไป และเคยซื้อเฟอร์นิเจอร์"),
        ("     Store or Chinana's stall.", "     จากร้านขายของชำหรือแผงค้าของชินานะ"),
        ("*The events that unlock these new features will not trigger during certain sections of the main story ", "*อีเวนต์ปลดล็อกฟังก์ชันใหม่เหล่านี้จะไม่เกิดขึ้นในบางช่วงของเนื้อเรื่องหลัก "),
        ("or on days with thunderstorms.", "หรือในวันที่มีพายุฝนฟ้าคะนอง"),
    ]
    p_jp.extend(v120_jp)
    p_en.extend(v120_en)
    total_all += save_category_file("31_updatetext.txt", "31. ข้อความอัปเดต (Update Text)", p_en, p_jp)

    # 32. LogText
    _, r_en = read_csv(r"logtext\logtext_แปลจาก_EN.csv")
    _, r_jp = read_csv(r"logtext\logtext_แปลจาก_JP.csv")
    p_en = [(r[3], r[4]) for r in r_en if len(r) > 4]
    p_jp = [(r[3], r[4]) for r in r_jp if len(r) > 4]
    total_all += save_category_file("32_logtext.txt", "32. ข้อความบันทึกระบบ (Log Text)", p_en, p_jp)

    # 33. Framework CMD
    _, r_en = read_csv(r"framework_cmd\framework_cmd_แปลจาก_EN.csv")
    _, r_jp = read_csv(r"framework_cmd\framework_cmd_แปลจาก_JP.csv")
    p_en = [(r[3], r[4]) for r in r_en if len(r) > 4]
    p_jp = [(r[3], r[4]) for r in r_jp if len(r) > 4]
    total_all += save_category_file("33_framework_cmd.txt", "33. คำสั่งเฟรมเวิร์ก (Framework CMD)", p_en, p_jp)

    # 34. Framework String
    _, r_en = read_csv(r"framework_string\framework_string_แปลจาก_EN.csv")
    _, r_jp = read_csv(r"framework_string\framework_string_แปลจาก_JP.csv")
    p_en = [(r[4], r[5]) for r in r_en if len(r) > 5]
    p_jp = [(r[4], r[5]) for r in r_jp if len(r) > 5]
    total_all += save_category_file("34_framework_string.txt", "34. ข้อความเฟรมเวิร์ก (Framework String)", p_en, p_jp)

    # 35. Framework VKey
    _, r_en = read_csv(r"framework_vkey\framework_vkey_แปลจาก_EN.csv")
    _, r_jp = read_csv(r"framework_vkey\framework_vkey_แปลจาก_JP.csv")
    p_en = [(r[4], r[5]) for r in r_en if len(r) > 5]
    p_jp = [(r[4], r[5]) for r in r_jp if len(r) > 5]
    total_all += save_category_file("35_framework_vkey.txt", "35. ปุ่มเฟรมเวิร์ก (Framework VKey)", p_en, p_jp)

    # 36. Framework VKeyCategory
    _, r_en = read_csv(r"framework_vkeycategory\framework_vkeycategory_แปลจาก_EN.csv")
    _, r_jp = read_csv(r"framework_vkeycategory\framework_vkeycategory_แปลจาก_JP.csv")
    p_en = [(r[4], r[5]) for r in r_en if len(r) > 5]
    p_jp = [(r[4], r[5]) for r in r_jp if len(r) > 5]
    total_all += save_category_file("36_framework_vkeycategory.txt", "36. หมวดหมู่ปุ่ม (VKey Categories)", p_en, p_jp)

    # -------------------------------------------------------------------------
    # Group 4: เมนู คำสั่ง ข้อความ UI ตั้งค่าเกม และระบบวันเวลา (Core UI & Controls)
    # โหลดหลังสุด -> Priority สูงสุด ชนะข้อความซ้ำจากกลุ่มอื่น 100%!
    # -------------------------------------------------------------------------
    # 40. CMD
    _, r_en = read_csv(r"cmd\cmd_แปลจาก_EN.csv")
    _, r_jp = read_csv(r"cmd\cmd_แปลจาก_JP.csv")
    p_en = [(r[3], r[4]) for r in r_en if len(r) > 4]
    p_jp = [(r[3], r[4]) for r in r_jp if len(r) > 4]
    total_all += save_category_file("40_cmd.txt", "40. เมนูและคำสั่ง (CMD)", p_en, p_jp)

    # 41. String (System UI Strings)
    _, r_en = read_csv(r"string\string_แปลจาก_EN.csv")
    _, r_jp = read_csv(r"string\string_แปลจาก_JP.csv")
    p_en = [(r[4], r[5]) for r in r_en if len(r) > 5]
    p_jp = [(r[4], r[5]) for r in r_jp if len(r) > 5]
    
    # Specific fix for Empty Save Slot: Ensure 'Empty' and 'なし' mean 'ช่องว่าง' in general UI
    p_en = [(o, "ช่องว่าง" if o in ("Empty", "なし") else t) for o, t in p_en]
    p_jp = [(o, "ช่องว่าง" if o in ("Empty", "なし") else t) for o, t in p_jp]
    p_en.append(("Empty", "ช่องว่าง"))
    p_jp.append(("なし", "ช่องว่าง"))
    total_all += save_category_file("41_string.txt", "41. ข้อความ UI ระบบ (Strings)", p_en, p_jp)

    # 42. GameSetting (Settings Menu - Must WIN over general strings so toggles show [ปิด] [เปิด])
    _, r_en = read_csv(r"gamesetting\gamesetting_แปลจาก_EN.csv")
    _, r_jp = read_csv(r"gamesetting\gamesetting_แปลจาก_JP.csv")
    p_en = [(r[3], r[4]) for r in r_en if len(r) > 4]
    p_jp = [(r[3], r[4]) for r in r_jp if len(r) > 4]
    
    # Explicit button toggles for Settings Menu (Update-Proof Priority)
    p_en.extend([
        ("Off", "ปิด"),
        ("On", "เปิด"),
        ("[Off]", "ปิด"),
        ("[On]", "เปิด"),
        ("[None]", "ปิด"),
    ])
    p_jp.extend([
        ("なし", "ปิด"),
        ("あり", "เปิด"),
    ])
    total_all += save_category_file("42_gamesetting.txt", "42. การตั้งค่าเกม (Game Settings - Priority Toggles)", p_en, p_jp)

    # 43. System Date & Seasons (Date Templates & Season Names - Loaded Last)
    date_en = [
        ("Year <value 1> - <value 2> <value 3>", "ปี <value 1> <value 2> วัน <value 3>"),
        ("Spring", "ฤดูใบไม้ผลิ"),
        ("Summer", "ฤดูร้อน"),
        ("Autumn", "ฤดูใบไม้ร่วง"),
        ("Winter", "ฤดูหนาว"),
        ("Fall", "ฤดูใบไม้ร่วง"),
    ]
    date_jp = [
        ("<value 1>年目 <value 2> <value 3>日", "ปี <value 1> <value 2> วัน <value 3>"),
        ("春", "ฤดูใบไม้ผลิ"),
        ("夏", "ฤดูร้อน"),
        ("秋", "ฤดูใบไม้ร่วง"),
        ("冬", "ฤดูหนาว"),
    ]
    total_all += save_category_file("43_system_date.txt", "43. ระบบวันเวลาและฤดูกาล (Date & Seasons)", date_en, date_jp)

    print("=" * 70)
    print(f"สร้างเสร็จสิ้นครบทั้ง 37 ไฟล์! รวมคำแปลทั้งหมด {total_all:,} รายการ")
    print("=" * 70)

if __name__ == "__main__":
    main()
