import os
import glob
import re
import sys

# Import PUA converter
sys.path.insert(0, r'C:\Users\Supakiat\Desktop\Mover\out')
import csv_to_pua_gui
mapping = csv_to_pua_gui.load_mapping(r'C:\Users\Supakiat\Desktop\Mover\out\Mapping.json')
max_len = max(len(k) for k in mapping)

missing_file = r'C:\Program Files (x86)\Steam\steamapps\common\Village in the Shade\Mods\TextDump\dump_missing.txt'
trans_file = r'C:\Program Files (x86)\Steam\steamapps\common\Village in the Shade\Mods\TextDump\translation.txt'
dev_pua_file = r'C:\Users\Supakiat\Desktop\Village_in_the_Shade_ThaiMod_Dev\translation_PUA.txt'

dir_03 = r'C:\Users\Supakiat\Desktop\คลังคำแปล_Village_in_the_Shade\03_ผลลัพธ์_JP_TH'
dir_02 = r'C:\Users\Supakiat\Desktop\คลังคำแปล_Village_in_the_Shade\02_Switch'
dir_01 = r'C:\Users\Supakiat\Desktop\คลังคำแปล_Village_in_the_Shade\01_PC'

manual_added_file = r'C:\Users\Supakiat\Desktop\คลังคำแปล_Village_in_the_Shade\คำแปลที่ไม่มีในคลัง_ต้องแปลเพิ่ม.txt'
dev_manual_added_file = r'C:\Users\Supakiat\Desktop\Village_in_the_Shade_ThaiMod_Dev\คำแปลที่ไม่มีในคลัง_ต้องแปลเพิ่ม.txt'

# 1. Read existing translation.txt to avoid overwriting or duplicating
existing_keys = set()
existing_lines = []
with open(trans_file, 'r', encoding='utf-8', errors='ignore') as f:
    for line in f:
        existing_lines.append(line)
        raw = line.strip()
        if not raw or raw.startswith('#') or '=' not in raw:
            continue
        k, v = raw.split('=', 1)
        k_clean = k.strip()
        if k_clean.startswith('[') and ']' in k_clean:
            end_idx = k_clean.find(']')
            k_clean = k_clean[end_idx+1:].strip()
        if '[SCALE:' in k_clean:
            k_clean = k_clean[:k_clean.find('[SCALE:')].strip()
        existing_keys.add(k_clean)

print(f'Existing keys in translation.txt: {len(existing_keys)}')

# 2. Extract captured keys
captured_keys = []
seen = set()
with open(missing_file, 'r', encoding='utf-8', errors='ignore') as f:
    for line in f:
        line = line.strip()
        if not line: continue
        idx = line.find('] ')
        if idx != -1:
            raw_text = line[idx+2:].strip()
            if raw_text and raw_text not in seen and raw_text not in existing_keys:
                seen.add(raw_text)
                captured_keys.append(raw_text)

print(f'New captured keys to process: {len(captured_keys)}')

# 3. Load databases
# Priority order: 03 -> 02 -> 01
db = {}
# Priority list of files in 03
priority_files = [
    'gameSetting_จับคู่คำแปล_JP_TH.txt',
    'string_จับคู่คำแปล_JP_TH.txt',
    'framework_vkey_จับคู่คำแปล_JP_TH.txt',
    'framework_cmd_จับคู่คำแปล_JP_TH.txt',
    'cmd_จับคู่คำแปล_JP_TH.txt',
    'action_จับคู่คำแปล_JP_TH.txt',
    'item_จับคู่คำแปล_JP_TH.txt',
    'letter_จับคู่คำแปล_JP_TH.txt',
    'quest_จับคู่คำแปล_JP_TH.txt',
    'tips_จับคู่คำแปล_JP_TH.txt',
    'talk_จับคู่คำแปล_JP_TH.txt',
    'construction_จับคู่คำแปล_JP_TH.txt',
    'crops_จับคู่คำแปล_JP_TH.txt',
    'facility_จับคู่คำแปล_JP_TH.txt',
    'creature_จับคู่คำแปล_JP_TH.txt',
    'character_จับคู่คำแปล_JP_TH.txt',
    'intangeble_จับคู่คำแปล_JP_TH.txt',
]

for p in priority_files:
    p_path = os.path.join(dir_03, p)
    if os.path.exists(p_path):
        with open(p_path, 'r', encoding='utf-8', errors='ignore') as fp:
            for line in fp:
                line = line.strip()
                if not line or line.startswith('#') or '=' not in line: continue
                k, v = line.split('=', 1)
                k = k.strip()
                v = v.strip()
                if k and v and k not in db:
                    db[k] = (v, p, '03')

for d, tag in [(dir_03, '03'), (dir_02, '02'), (dir_01, '01')]:
    for f in glob.glob(os.path.join(d, '*.txt')):
        bname = os.path.basename(f)
        with open(f, 'r', encoding='utf-8', errors='ignore') as fp:
            for line in fp:
                line = line.strip()
                if not line or line.startswith('#') or '=' not in line: continue
                k, v = line.split('=', 1)
                k = k.strip()
                v = v.strip()
                if k and v and k not in db:
                    db[k] = (v, bname, tag)

print(f'Total database entries: {len(db):,}')

# 4. Manual / Deduced Dictionary for dynamic and parsed strings
manual_dict = {}
# Load from external tracking file
for m_path in [manual_added_file, dev_manual_added_file]:
    if os.path.exists(m_path):
        with open(m_path, 'r', encoding='utf-8') as fp:
            for line in fp:
                line = line.rstrip('\r\n')
                if not line or line.startswith('#') or '=' not in line:
                    continue
                k, v = line.split('=', 1)
                k = k.strip()
                if k and v:
                    manual_dict[k] = (v, 'คำแปลที่ไม่มีในคลัง_ต้องแปลเพิ่ม.txt')
        break

print(f'Loaded {len(manual_dict)} manual translations from คำแปลที่ไม่มีในคลัง_ต้องแปลเพิ่ม.txt')


# Birthday regex: 誕生日 <season> <day>日
season_map = {
    '春': 'ฤดูใบไม้ผลิ',
    '夏': 'ฤดูร้อน',
    '秋': 'ฤดูใบไม้ร่วง',
    '冬': 'ฤดูหนาว'
}

def translate_key(k):
    if k in manual_dict:
        return manual_dict[k]
    
    # Check save slot date: e.g. 1年目 秋 21日　深夜 or 1年目 秋 21日
    m_save = re.match(r'^(\d+)年目\s+(春|夏|秋|冬)\s+(\d+)日(\s*[\u3000\s]+深夜)?$', k)
    if m_save:
        year = m_save.group(1)
        season = season_map.get(m_save.group(2), m_save.group(2))
        day = m_save.group(3)
        extra = ' ยามดึก' if m_save.group(4) else ''
        return (f'ปีที่ {year} {season} วันที่ {day}{extra}', 'Switch-savedate')

    # Check season day: e.g. 夏 24日
    m_day = re.match(r'^(春|夏|秋|冬)\s+(\d+)日$', k)
    if m_day:
        season = season_map.get(m_day.group(1), m_day.group(1))
        day = m_day.group(2)
        return (f'{season} วันที่ {day}', 'Switch-seasonday')

    # Check birthday pattern
    m = re.match(r'^誕生日\s+(春|夏|秋|冬)\s+(\d+)日$', k)
    if m:
        season = season_map.get(m.group(1), m.group(1))
        day = m.group(2)
        return (f'วันเกิด: {season} วันที่ {day}', 'Switch-birthday')
    
    # Direct match in Switch/PC db
    if k in db:
        return (db[k][0], f'{db[k][2]}_{db[k][1]}')
    
    return None

# Process captured keys
new_entries = []
typewriter_skipped = 0
not_found_manual = []

# Detect typewriter fragments to skip polluting the translation table
for k in captured_keys:
    res = translate_key(k)
    if res:
        th, src = res
        new_entries.append((k, th, src))
    else:
        # Check if it is a typewriter fragment (substring of an existing key, or substring of another captured key)
        is_frag = False
        for ex in existing_keys:
            if k in ex and len(ex) > len(k):
                is_frag = True
                break
        if not is_frag:
            for other in captured_keys:
                if k in other and len(other) > len(k):
                    is_frag = True
                    break
        if is_frag:
            typewriter_skipped += 1
        else:
            not_found_manual.append(k)

print(f'\nResults of Translation Mapping:')
print(f'Successfully translated: {len(new_entries)} keys')
print(f'Typewriter animation fragments safely skipped: {typewriter_skipped} keys')
print(f'Remaining unmatched keys: {len(not_found_manual)} keys')

# If there are genuinely unmatched keys (not fragments), log them to the tracking file for review
if not_found_manual:
    print(f'Logging {len(not_found_manual)} unmapped keys to คำแปลที่ไม่มีในคลัง_ต้องแปลเพิ่ม.txt...')
    try:
        with open(manual_added_file, 'a', encoding='utf-8') as f:
            f.write('\n# ------------------------------------------------------------------------------\n')
            f.write('# [รอแปลเพิ่ม: ดักจับได้จากเกมล่าสุด แต่ยังไม่มีคำแปลในระบบ]\n')
            f.write('# ------------------------------------------------------------------------------\n')
            for k in not_found_manual:
                f.write(f'{k}=\n')
        import shutil
        shutil.copy2(manual_added_file, dev_manual_added_file)
        print('Successfully updated manual translation tracking files.')
    except Exception as e:
        print(f'Error logging unmatched keys: {e}')

# 5. Format and convert new entries to PUA
if new_entries:
    added_lines = []
    added_lines.append('\n# ==============================================================================\n')
    added_lines.append('# Newly Captured Texts (Auto-matched from Switch / PC / Standards / Manual)\n')
    added_lines.append('# ==============================================================================\n')

    for k, th, src in new_entries:
        th_clean = re.sub(r'</?br/?>', '', th, flags=re.IGNORECASE)
        th_pua = csv_to_pua_gui.convert_text_to_pua(th_clean, mapping, max_len)
        added_lines.append(f'{k}={th_pua}\n')

    # 6. Write back to translation.txt and translation_PUA.txt
    final_lines = existing_lines + added_lines

    with open(trans_file, 'w', encoding='utf-8') as f:
        f.writelines(final_lines)

    with open(dev_pua_file, 'w', encoding='utf-8') as f:
        f.writelines(final_lines)

    print(f'\nSuccessfully wrote {len(new_entries)} new translations to translation.txt and translation_PUA.txt!')
else:
    print('\nNo new translations to write to translation.txt.')

# 7. Clear dump_missing.txt
with open(missing_file, 'w', encoding='utf-8') as f:
    pass
print('dump_missing.txt has been cleared and reset for the next gameplay session.')
