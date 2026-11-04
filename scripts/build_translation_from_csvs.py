import os, glob, csv, re, shutil
from collections import OrderedDict

base_csv_dir = r'C:\Users\Administrator\Downloads\Village_PC_v130_Database_CSVs1'
dev_dir = r'D:\Users\Supakiat\Desktop\Village_in_the_Shade_ThaiMod_Dev'
out_path = os.path.join(dev_dir, 'translation.txt')

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

def clean_str(s):
    if not s: return ''
    s = s.strip()
    s = s.replace('\r\n', r'\n').replace('\n', r'\n').replace('\r', r'\n')
    return s

def clean_trans(trans, orig):
    if not trans: return ''
    # Auto-correct typo
    trans = re.sub(r'คะ\.\.\.\s*คุณ', 'คุ... คุณ', trans)
    # Strip unsupported styling tags from translated text
    trans = re.sub(r'</?(?:strong|b\b|c\b|color|size|half|speed|space|font)[^>]*>', '', trans, flags=re.IGNORECASE)
    # Strip <cmd> from trans if orig had no <cmd>
    if '<cmd' not in orig.lower() and '<cmd' in trans.lower():
        trans = re.sub(r'<cmd[^>]*>', '', trans, flags=re.IGNORECASE)
    trans = re.sub(r'[ \t]+', ' ', trans).strip()
    return trans

# Load PUA map
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

# Verified screenshot / gameplay corrections (Highest Priority Override)
DIALOGUE_SCREENSHOT_CORRECTIONS = OrderedDict([
    # Stutter typo
    ('K-Kisuke! This is bad!', 'คุ... คุณคิสึเกะ! แย่แล้วค่ะ!'),
    ('คะ... คุณคิสึเกะ! แย่แล้วค่ะ!', 'คุ... คุณคิสึเกะ! แย่แล้วค่ะ!'),
    ('คะ... คุณคิสึเกะ!', 'คุ... คุณคิสึเกะ!'),
    ('キ、キスケさん！', 'คุ... คุณคิสึเกะ!'),

    # UI Equipment bar tip
    ('Move the inventory bar cursor left and right', 'เลื่อนเคอร์เซอร์แถบอุปกรณ์ (ซ้าย/ขวา)'),

    # Rin dialogues
    ('Good morning, <player>. Here...take a look at this!', 'อรุณสวัสดิ์ <player>! นี่... ลองดูนี่สิ!'),
    ('Good morning, <player>. Here...take a look at this', 'อรุณสวัสดิ์ <player>! นี่... ลองดูนี่สิ'),
    ('this very opportunity? Gainful employment AND your', 'ที่ได้ทำงานหาเงิน แถมยังมี'),
    ('own house?', 'บ้านเป็นของตัวเองอีกด้วยเนี่ยนะ?'),
    ('So we have an agreement. Please accept this magnificent', 'ถ้าอย่างนั้นก็ถือว่าตกลงเรียบร้อย เชิญรับ'),
    ('house and land!', 'บ้านและที่ดินอันยอดเยี่ยมนี้ไปได้เลย!'),
    ("...why not just put a leash on <player> whenever you're", 'ทำไมถึงไม่ล่ามโซ่ <player> เอาไว้'),
    ('off them.', 'เวลาไม่อยู่ล่ะขอรับ?'),
    ("It's not \"free\" to use, it's just completely overrun with", 'ไม่ได้ "เปิดให้ใช้ตามสบาย" หรอกนะ แค่เต็มไปด้วย'),
    ('wood scraps and rocks...', 'เศษไม้และก้อนหินมากกว่า...'),
    ('works really well!', 'ได้ผลดีมากเลยนะ!'),

    # Doctor
    ('My stock of herbal medicine...might be running a', 'คลังยาสมุนไพรของฉัน... ชักจะเริ่มร่อยหรอแล้วล่ะ'),
    ('herbal medicine...', 'ยาสมุนไพร...'),

    # Village gate stranger dialogue
    ("...I'm against it. We can't", '...ฉันไม่เห็นด้วยนะ'),
    ('have some random stranger', 'จะให้คนไม่รู้หัวนอนปลายเท้า...'),
    ("livin' here...", '...มาอยู่ที่นี่ไม่ได้เด็ดขาด!'),

    # Quest / Tutorial fragments
    ('Take care of the vegetables', 'ดูแลพืชผักที่ปลูกไว้'),
    (' to strafe and', ' เคลื่อนที่ขนานและ'),
    ('to strafe and', 'เคลื่อนที่ขนานและ'),
    (' to choose where to till', ' เพื่อเลือกจุดพรวนดิน'),
    ('to choose where to till', 'เพื่อเลือกจุดพรวนดิน'),

    # Command / Verb standardizations
    ('Use', 'ใช้'),
    ('使う', 'ใช้'),
])

UI_CMD_PHRASES = OrderedDict([
    # Common command prefixes
    ('Press ', 'กด '),
    ('Press', 'กด'),
    ('Hold ', 'กดค้าง '),
    ('Hold', 'กดค้าง'),

    # Harvesting tips chunks
    (' to harvest matured crops in front of you.', ' เพื่อเก็บเกี่ยวพืชผลที่โตเต็มที่ตรงหน้า'),
    ('to harvest matured crops in front of you.', 'เพื่อเก็บเกี่ยวพืชผลที่โตเต็มที่ตรงหน้า'),
    (' to harvest matured crops in front of you', ' เพื่อเก็บเกี่ยวพืชผลที่โตเต็มที่ตรงหน้า'),
    ('to harvest matured crops in front of you', 'เพื่อเก็บเกี่ยวพืชผลที่โตเต็มที่ตรงหน้า'),
    (' in front of a crop to continuously harvest', ' ตรงหน้าพืชผลเพื่อเก็บเกี่ยวอย่างต่อเนื่อง'),
    ('in front of a crop to continuously harvest', 'ตรงหน้าพืชผลเพื่อเก็บเกี่ยวอย่างต่อเนื่อง'),
    (' in front of a crop to continuously harvest.', ' ตรงหน้าพืชผลเพื่อเก็บเกี่ยวอย่างต่อเนื่อง'),
    ('in front of a crop to continuously harvest.', 'ตรงหน้าพืชผลเพื่อเก็บเกี่ยวอย่างต่อเนื่อง'),
    ('crops of the same type.', 'พืชผลชนิดเดียวกันอย่างต่อเนื่อง'),
    ('crops of the same type', 'พืชผลชนิดเดียวกันอย่างต่อเนื่อง'),
    ('Now, go ahead and harvest them.', 'ตอนนี้ ไปเก็บเกี่ยวพืชผลได้เลย'),
    ('Now, go ahead and harvest them', 'ตอนนี้ ไปเก็บเกี่ยวพืชผลได้เลย'),
    ('ow, go ahead and harvest them.', 'ตอนนี้ ไปเก็บเกี่ยวพืชผลได้เลย'),
    ('ow, go ahead and harvest them', 'ตอนนี้ ไปเก็บเกี่ยวพืชผลได้เลย'),

    # Jumping tips chunks
    (' while moving toward a fence with', ' ขณะเคลื่อนที่เข้าหารั้วด้วย'),
    ('while moving toward a fence with', 'ขณะเคลื่อนที่เข้าหารั้วด้วย'),
    (' to jump over it.', ' เพื่อกระโดดข้ามรั้ว'),
    ('to jump over it.', 'เพื่อกระโดดข้ามรั้ว'),
    (' to jump over it', ' เพื่อกระโดดข้ามรั้ว'),
    ('to jump over it', 'เพื่อกระโดดข้ามรั้ว'),

    ('to set configurations', 'ไปที่หน้าจอตั้งค่า'),
    (' to set configurations', ' ไปที่หน้าจอตั้งค่า'),
    ('to change assignments', 'เพื่อเปลี่ยนปุ่มที่กำหนด'),
    (' to change assignments', ' เพื่อเปลี่ยนปุ่มที่กำหนด'),
    ('to reset assignments', 'เพื่อรีเซ็ตปุ่มที่กำหนด'),
    (' to reset assignments', ' เพื่อรีเซ็ตปุ่มที่กำหนด'),
    ('to proceed.', 'เพื่อไปต่อ'),
    (' to proceed.', ' เพื่อไปต่อ'),
    ('to reload.', 'เพื่อโหลดใหม่อีกครั้ง'),
    (' to reload.', ' เพื่อโหลดใหม่อีกครั้ง'),
    ('to start', 'เพื่อเริ่ม'),
    (' to start', ' เพื่อเริ่ม'),
    ('Main Actio', 'แอ็กชันหลัก'),
    ('Main Action', 'แอ็กชันหลัก'),
    ('Move the inventory bar cursor left and right', 'เลื่อนเคอร์เซอร์แถบอุปกรณ์ (ซ้าย/ขวา)'),
    ('Switch the inventory bar to another row', 'สลับแถวช่องเก็บของ'),
    ('to rotate, allowing you to change direction', 'หมุนตัวเปลี่ยนทิศทาง'),
    ('Hold  to rotate, allowing you to change direction', 'กดค้างเพื่อหมุนตัวเปลี่ยนทิศทาง'),
    ('Run with', 'วิ่งด้วย'),
    ('Run with ', 'วิ่งด้วย '),
    ('. Walk with', '. หรือเดินช้าๆ ด้วย'),
    ('. Walk with ', '. หรือเดินช้าๆ ด้วย '),
    ('Walk with', 'เดินช้าๆ ด้วย'),
    ('Walk with ', 'เดินช้าๆ ด้วย '),
    (', or', ', หรือ'),
    (', or ', ', หรือ '),
    ('Tilt', 'โยก'),
    ('Tilt ', 'โยก '),
    ('slightly, or', 'เบาๆ หรือ'),
    (' slightly, or', ' เบาๆ หรือ'),
])

def add_pair_and_cmd_chunks(pairs_dict, orig, trans):
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

print('Parsing CSV database directly from master CSVs...')
total_entries = 0
category_stats = []

with open(out_path, 'w', encoding='utf-8') as out_f:
    out_f.write('# ==============================================================================\n')
    out_f.write('# Village in the Shade - Unified Translation Database (v1.30 Master Build)\n')
    out_f.write('# Rebuilt directly from master CSVs without index guessing or legacy backups\n')
    out_f.write('# ==============================================================================\n\n')

    for idx, cat in enumerate(CATEGORIES_ORDER, start=1):
        cat_dir = os.path.join(base_csv_dir, cat)
        if not os.path.isdir(cat_dir): continue

        jp_csv = os.path.join(cat_dir, f'{cat}_แปลจาก_JP.csv')
        en_csv = os.path.join(cat_dir, f'{cat}_แปลจาก_EN.csv')

        jp_pairs = OrderedDict()
        en_pairs = OrderedDict()

        # 1. Process JP CSV
        if os.path.exists(jp_csv):
            with open(jp_csv, 'r', encoding='utf-8-sig', errors='replace') as fp:
                reader = csv.reader(fp)
                try: header = next(reader)
                except: header = []

                # Find col mappings
                jp_cols = []
                en_cols = []
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

                for row in reader:
                    # JP pairs
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
                            add_pair_and_cmd_chunks(jp_pairs, orig, trans)

                    # EN pairs from JP CSV (e.g. column บทสนทนา_EN)
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
                            add_pair_and_cmd_chunks(en_pairs, orig, trans)

        # 2. Process EN CSV
        if os.path.exists(en_csv):
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

                for row in reader:
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
                            add_pair_and_cmd_chunks(en_pairs, orig, trans)

        # Write category pairs
        category_stats.append((cat, len(jp_pairs), len(en_pairs)))
        out_f.write('# ==============================================================================\n')
        out_f.write(f'# หมวดที่ {idx:02d}: {cat.upper()} (ภาษาญี่ปุ่น {len(jp_pairs):,} รายการ | ภาษาอังกฤษ {len(en_pairs):,} รายการ)\n')
        out_f.write('# ==============================================================================\n')

        if jp_pairs:
            out_f.write(f'# --- {cat.upper()} [JP] ---\n')
            for k, v in jp_pairs.items():
                out_f.write(f'{k}={v}\n')
                total_entries += 1
            out_f.write('\n')

        if en_pairs:
            out_f.write(f'# --- {cat.upper()} [EN] ---\n')
            for k, v in en_pairs.items():
                out_f.write(f'{k}={v}\n')
                total_entries += 1
            out_f.write('\n')

    # 3. Dedicated UI & Tip phrases
    out_f.write('# ==============================================================================\n')
    out_f.write('# หมวดพิเศษ: ข้อความท่อนคำสั่ง UI และ Tips รอบแท็กปุ่ม (<cmd> Chunks)\n')
    out_f.write('# ==============================================================================\n')
    for k, v in UI_CMD_PHRASES.items():
        v_pua = to_pua(v)
        out_f.write(f'{k}={v_pua}\n')
        total_entries += 1
    out_f.write('\n')

    # 4. Verified screenshot / gameplay corrections (Highest Priority Override)
    out_f.write('# ==============================================================================\n')
    out_f.write('# หมวดพิเศษ: การปรับแก้คำแปลเฉพาะฉากจากหน้าจอจริง (Screenshot Corrections)\n')
    out_f.write('# ==============================================================================\n')
    for k, v in DIALOGUE_SCREENSHOT_CORRECTIONS.items():
        v_pua = to_pua(v)
        out_f.write(f'{k}={v_pua}\n')
        total_entries += 1
        k_trim = k.rstrip('、,。.!?！？')
        if k_trim and k_trim != k:
            out_f.write(f'{k_trim}={v_pua}\n')
            total_entries += 1
    out_f.write('\n')

print(f'Successfully built clean translation.txt with {total_entries:,} entries!')
for cat, jcnt, ecnt in category_stats:
    print(f'  {cat:22} -> JP: {jcnt:5,}, EN: {ecnt:5,}, Total: {jcnt+ecnt:5,}')

# Deploy translation.txt to Steam Game Root
steam_root_trans = r'C:\Program Files (x86)\Steam\steamapps\common\Village in the Shade\translation.txt'
if os.path.exists(os.path.dirname(steam_root_trans)):
    shutil.copy2(out_path, steam_root_trans)
    print(f'Copied translation.txt to Steam Root: {steam_root_trans}')
