import os, sys, glob, csv, re
from collections import OrderedDict

dev_dir = r'D:\Users\Supakiat\Desktop\Village_in_the_Shade_ThaiMod_Dev'
base_csv_dir = os.path.join(dev_dir, 'Village_PC_v130_Database_CSVs1')
out_path = os.path.join(dev_dir, 'translation.txt')

# 1. Load PUA map from pua_mapping.h
pua_map = {}
pua_header_path = os.path.join(dev_dir, 'src', 'pua_mapping.h')
if os.path.exists(pua_header_path):
    with open(pua_header_path, 'r', encoding='utf-8') as f:
        for line in f:
            m = re.search(r'\{\s*L"([^"]+)",\s*L\'\\u([0-9A-Fa-f]{4})\'\s*\}', line)
            if m:
                key_raw = m.group(1)
                val_code = int(m.group(2), 16)
                key = key_raw.encode().decode('unicode_escape')
                val = chr(val_code)
                pua_map[key] = val

_sorted_pua_keys = sorted(pua_map.keys(), key=lambda k: -len(k)) if pua_map else []

def to_pua(text):
    if not text or not _sorted_pua_keys:
        return text
    res = text
    for k in _sorted_pua_keys:
        res = res.replace(k, pua_map[k])
    return res

def clean_str(s):
    if not s: return ''
    s = s.strip()
    s = s.replace('\r\n', r'\n').replace('\n', r'\n').replace('\r', r'\n')
    return s

def clean_trans(trans, orig):
    if not trans: return ''
    # Auto-correct typo
    trans = re.sub(r'คะ\.\.\.\s*คุณ', 'คุ... คุณ', trans)
    # Strip <cmd> from trans if orig had no <cmd>
    if '<cmd' not in orig.lower() and '<cmd' in trans.lower():
        trans = re.sub(r'<cmd[^>]*>', '', trans, flags=re.IGNORECASE)
    trans = re.sub(r'[ \t]+', ' ', trans).strip()
    return trans

def is_valid_phrase_key(k):
    if not k: return False
    k = k.strip()
    if not k: return False
    has_meaningful_char = any(
        c.isalnum() or '\u3040' <= c <= '\u9fff' or '\u0e00' <= c <= '\u0e7f'
        for c in k
    )
    if not has_meaningful_char: return False
    if len(k) <= 1 and ord(k) < 0x3000: return False
    return True

CATEGORIES_ORDER = [
    'talk',                 # NPC dialogues
    'reminiscence',         # Memory / story flashbacks
    'lostbook',             # Ancient lore books
    'letter',               # Letters from villagers
    'quest',                # Quests & tasks
    'creature',             # Animals & bugs
    'crops',                # Farm crops
    'livestock',            # Livestock animals
    'itemtype',             # Item categories
    'item',                 # Items & equipment
    'bundle',               # Bundles
    'bundlegroup',          # Bundle groups
    'whistle',              # Whistle calls
    'facility',             # Facilities
    'facilityrelease',      # Facility releases
    'construction',         # Construction blueprints
    'skilltree',            # Skill trees
    'tip',                  # Game tips
    'trophy',               # Achievements / trophies
    'updatetext',           # Patch / update notes
    'action',               # Player actions
    'cmd',                  # Commands
    'logtext',              # Notification logs
    'gameeffect',           # Effects
    'character',            # NPC names and roles
    'bgm',                  # Music track titles
    'intangeble',           # Intangible assets / flags
    'gamesetting',          # In-game settings
    'framework_cmd',        # Framework commands
    'vkey',                 # Virtual keys
    'framework_vkey',       # Framework keys
    'framework_vkeycategory', # Key categories
    'framework_string',     # Framework strings
    'string',               # Core database strings
]

# Verified dialogue / system overrides
SPECIAL_OVERRIDES = OrderedDict([
    # Stutter typo
    ('K-Kisuke! This is bad!', to_pua('คุ... คุณคิสึเกะ! แย่แล้วค่ะ!')),
    ('คะ... คุณคิสึเกะ! แย่แล้วค่ะ!', to_pua('คุ... คุณคิสึเกะ! แย่แล้วค่ะ!')),
    ('คะ... คุณคิสึเกะ!', to_pua('คุ... คุณคิสึเกะ!')),
    ('キ、キスケさん！', to_pua('คุ... คุณคิสึเกะ!')),

    # UI Equipment bar tip
    ('Move the inventory bar cursor left and right', to_pua('เลื่อนเคอร์เซอร์แถบอุปกรณ์ (ซ้าย/ขวา)')),

    # Save slots & Seasons
    ('Spring', to_pua('ฤดูใบไม้ผลิ')),
    ('Summer', to_pua('ฤดูร้อน')),
    ('Autumn', to_pua('ฤดูใบไม้ร่วง')),
    ('Winter', to_pua('ฤดูหนาว')),
    ('Fall', to_pua('ฤดูใบไม้ร่วง')),
    ('Year <value 1> - <value 2> <value 3>', to_pua('ปีที่ <value 1> <value 2> วันที่ <value 3>')),
    ('<value 1>年目 <value 2> <value 3>日', to_pua('ปีที่ <value 1> <value 2> วันที่ <value 3>')),

    # Rin dialogue 16604 / 15360: Full sentence
    ("Now, at last, you've made something precious.", to_pua('เท่านี้เธอก็มีสิ่งล้ำค่า<br>เป็นของตัวเองแล้วนะ')),
    ("Okay, I'll show you what to do next. Come with me.", to_pua('เอาล่ะเดี๋ยวฉันจะบอกว่า<br>ต้องทำอะไรต่อตามฉันมานี่สิ')),

    # Rin altar dialogue box
    ('...you must give a proper offering to the <strong>god who lives<br>at the bottom of this hole</strong>.',
     to_pua('เธอจำเป็นจะต้องมอบ<br>เครื่องเซ่นไหว้แด่<strong>ท่านเทพเจ้า</strong><br><strong>ที่สถิตอยู่ก้นหลุมลึกแห่งนี้</strong>')),
    ('Here. This is the altar where we make offerings<br>to the god of this land...',
     to_pua('ที่นี่แหละคือแท่นบูชา<br>สำหรับถวายเครื่องเซ่น<br>แด่เทพเจ้าประจำผืนดินแห่งนี้...')),
    ("An offering is meaningless unless it's something<br>precious... You understand what I'm getting at,<br>don't you?",
     to_pua('เครื่องเซ่นไหว้ถ้าไม่ใช่ของล้ำค่า<br>ก็ไม่มีความหมายใดๆ...<br>...คงเข้าใจแล้วใช่ไหม<br>ว่าฉันหมายถึงอะไร?')),
    ("In order to give thanks for making it safely through the<br>previous year, and to ask permission for you to continue<br>living in this village...",
     to_pua('เพื่อเป็นการขอบคุณที่ช่วยให้พวกเรา<br>ผ่านพ้นปีที่แล้วมาได้อย่างปลอดภัย...<br>และเพื่อขอขมา<br>และขออนุญาตให้เธอสามารถ<br>อาศัยอยู่ในหมู่บ้านแห่งนี้ต่อไปได้...')),
])

def add_pair(pairs_dict, orig, trans):
    if not orig or not trans or orig == trans: return
    pairs_dict[orig] = trans
    orig_trim = orig.rstrip('、,。.!?！？')
    if orig_trim and orig_trim != orig and orig_trim not in pairs_dict:
        pairs_dict[orig_trim] = trans

    if '<cmd' in orig.lower():
        orig_parts = re.split(r'<cmd[^>]*>', orig, flags=re.IGNORECASE)
        trans_parts = re.split(r'<cmd[^>]*>', trans, flags=re.IGNORECASE)
        if len(orig_parts) == len(trans_parts) and len(orig_parts) > 1:
            for op, tp in zip(orig_parts, trans_parts):
                op_c = op.strip()
                tp_c = tp.strip()
                if len(op_c) >= 2 and tp_c:
                    if op not in pairs_dict: pairs_dict[op] = tp
                    if op_c not in pairs_dict: pairs_dict[op_c] = tp_c
                    op_t = op_c.rstrip('、,。.!?！？')
                    if op_t and op_t != op_c and op_t not in pairs_dict:
                        pairs_dict[op_t] = tp_c

def main():
    print(f'Starting rebuild of {out_path}...')
    en_master_pairs = OrderedDict()
    jp_master_pairs = OrderedDict()

    # Apply special overrides first
    for k, v in SPECIAL_OVERRIDES.items():
        en_master_pairs[k] = v

    # 1. PROCESS EN CSV FIRST (Primary authority for English game)
    for cat in CATEGORIES_ORDER:
        cat_dir = os.path.join(base_csv_dir, cat)
        if not os.path.isdir(cat_dir): continue
        en_csv = os.path.join(cat_dir, f'{cat}_แปลจาก_EN.csv')
        if not os.path.exists(en_csv): continue

        print(f'Processing EN: {cat}...')
        with open(en_csv, 'r', encoding='utf-8-sig', errors='replace') as fp:
            reader = csv.reader(fp)
            try: header = next(reader)
            except: header = []

            en_cols = []
            for i, h in enumerate(header):
                if h.endswith('_EN') or h in ['ต้นฉบับ_EN', 'บทสนทนา_EN', 'ข้อความ_EN', 'กริยา_EN']:
                    base = h.replace('_EN', '')
                    pua_col = base + '_PUA'
                    th_col = base + '_TH'
                    if h in ['ต้นฉบับ_EN', 'บทสนทนา_EN']:
                        pua_col = 'Thai_PUA'; th_col = 'คำแปลไทย'
                    elif h == 'ข้อความ_EN':
                        pua_col = 'ข้อความ_PUA'; th_col = 'ข้อความ_TH'
                    elif h == 'กริยา_EN':
                        pua_col = 'กริยา_PUA'; th_col = 'กริยา_TH'
                    p_idx = header.index(pua_col) if pua_col in header else -1
                    t_idx = header.index(th_col) if th_col in header else -1
                    en_cols.append((i, p_idx, t_idx))

            rows = list(reader)

            # A. Process individual rows
            for row in rows:
                for o_idx, p_idx, t_idx in en_cols:
                    if o_idx < len(row):
                        orig = clean_str(row[o_idx])
                        if not is_valid_phrase_key(orig): continue
                        trans = ''
                        if p_idx >= 0 and p_idx < len(row) and row[p_idx].strip():
                            trans = clean_str(row[p_idx])
                        elif t_idx >= 0 and t_idx < len(row) and row[t_idx].strip():
                            trans = to_pua(clean_str(row[t_idx]))
                        trans = clean_trans(trans, orig)
                        add_pair(en_master_pairs, orig, trans)

            # B. Reconstruct multi-line dialogue boxes with <br>
            if cat in ['talk', 'reminiscence', 'letter', 'lostbook', 'quest', 'tip']:
                current_key = None
                box_en = []
                box_pua = []
                for row in rows:
                    key = row[2] if len(row) > 2 else ''
                    en = clean_str(row[3]) if len(row) > 3 else ''
                    pua = clean_str(row[5]) if len(row) > 5 else ''
                    if not pua and len(row) > 4 and row[4].strip():
                        pua = to_pua(clean_str(row[4]))

                    if key != current_key or (not en and not pua):
                        if len(box_en) > 1:
                            joined_en = '<br>'.join(box_en)
                            joined_pua = '<br>'.join(box_pua)
                            add_pair(en_master_pairs, joined_en, joined_pua)
                        box_en = []
                        box_pua = []
                        current_key = key
                        if not en and not pua:
                            continue

                    if en:
                        box_en.append(en)
                        box_pua.append(pua if pua else en)

                if len(box_en) > 1:
                    joined_en = '<br>'.join(box_en)
                    joined_pua = '<br>'.join(box_pua)
                    add_pair(en_master_pairs, joined_en, joined_pua)

    # 2. PROCESS JP CSV (for Japanese text fallback)
    for cat in CATEGORIES_ORDER:
        cat_dir = os.path.join(base_csv_dir, cat)
        if not os.path.isdir(cat_dir): continue
        jp_csv = os.path.join(cat_dir, f'{cat}_แปลจาก_JP.csv')
        if not os.path.exists(jp_csv): continue

        with open(jp_csv, 'r', encoding='utf-8-sig', errors='replace') as fp:
            reader = csv.reader(fp)
            try: header = next(reader)
            except: header = []

            jp_cols = []
            for i, h in enumerate(header):
                if h.endswith('_JP') or h in ['ต้นฉบับ_JP', 'บทสนทนา_JP', 'ข้อความ_JP', 'กริยา_JP']:
                    base = h.replace('_JP', '')
                    pua_col = base + '_PUA'
                    th_col = base + '_TH'
                    if h in ['ต้นฉบับ_JP', 'บทสนทนา_JP']:
                        pua_col = 'Thai_PUA'; th_col = 'คำแปลไทย'
                    elif h == 'ข้อความ_JP':
                        pua_col = 'ข้อความ_PUA'; th_col = 'ข้อความ_TH'
                    elif h == 'กริยา_JP':
                        pua_col = 'กริยา_PUA'; th_col = 'กริยา_TH'
                    p_idx = header.index(pua_col) if pua_col in header else -1
                    t_idx = header.index(th_col) if th_col in header else -1
                    jp_cols.append((i, p_idx, t_idx))

            rows = list(reader)
            for row in rows:
                for o_idx, p_idx, t_idx in jp_cols:
                    if o_idx < len(row):
                        orig = clean_str(row[o_idx])
                        if not is_valid_phrase_key(orig): continue
                        trans = ''
                        if p_idx >= 0 and p_idx < len(row) and row[p_idx].strip():
                            trans = clean_str(row[p_idx])
                        elif t_idx >= 0 and t_idx < len(row) and row[t_idx].strip():
                            trans = to_pua(clean_str(row[t_idx]))
                        trans = clean_trans(trans, orig)
                        add_pair(jp_master_pairs, orig, trans)

            # Reconstruct multi-line dialogue boxes with <br> for JP (using EN boundary or sentence transition)
            if cat in ['talk', 'reminiscence', 'letter', 'lostbook', 'quest', 'tip']:
                current_key = None
                box_jp = []
                box_pua = []
                for row in rows:
                    key = row[2] if len(row) > 2 else ''
                    jp = clean_str(row[3]) if len(row) > 3 else ''
                    pua = clean_str(row[5]) if len(row) > 5 else ''
                    en = clean_str(row[6]) if len(row) > 6 else ''
                    if not pua and len(row) > 4 and row[4].strip():
                        pua = to_pua(clean_str(row[4]))

                    if key != current_key or (en and box_jp) or (not jp and not pua):
                        if len(box_jp) > 1:
                            joined_jp = '<br>'.join(box_jp)
                            joined_pua = '<br>'.join(box_pua)
                            add_pair(jp_master_pairs, joined_jp, joined_pua)
                        box_jp = []
                        box_pua = []
                        current_key = key
                        if not jp and not pua:
                            continue

                    if jp:
                        box_jp.append(jp)
                        box_pua.append(pua if pua else jp)

                if len(box_jp) > 1:
                    joined_jp = '<br>'.join(box_jp)
                    joined_pua = '<br>'.join(box_pua)
                    add_pair(jp_master_pairs, joined_jp, joined_pua)

    # Re-apply special overrides to guarantee they are never overwritten
    for k, v in SPECIAL_OVERRIDES.items():
        en_master_pairs[k] = v

    print(f'Writing unified translation.txt...')
    print(f'Total English entries: {len(en_master_pairs)}')
    print(f'Total Japanese entries: {len(jp_master_pairs)}')

    with open(out_path, 'w', encoding='utf-8') as out_f:
        out_f.write('# ==============================================================================\n')
        out_f.write('# Village in the Shade - Reconstructed Translation Database (v1.30 Master Build)\n')
        out_f.write('# Fully reconstructed dialogue boxes with <br> support and English precedence\n')
        out_f.write('# ==============================================================================\n\n')

        out_f.write('# --- ENGLISH MASTER TRANSLATIONS & MULTI-LINE BOXES ---\n')
        for orig, trans in en_master_pairs.items():
            out_f.write(f'{orig}={trans}\n')

        out_f.write('\n# --- JAPANESE MASTER TRANSLATIONS & MULTI-LINE BOXES ---\n')
        for orig, trans in jp_master_pairs.items():
            if orig not in en_master_pairs:
                out_f.write(f'{orig}={trans}\n')

    print(f'Done! Successfully generated {out_path}')

if __name__ == '__main__':
    main()
