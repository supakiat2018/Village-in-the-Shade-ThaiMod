import os
import sys
import re
import shutil

# 1. Setup PUA converter
sys.path.insert(0, r'C:\Users\Supakiat\Desktop\Mover\out')
import csv_to_pua_gui
mapping = csv_to_pua_gui.load_mapping(r'C:\Users\Supakiat\Desktop\Mover\out\Mapping.json')
max_len = max(len(k) for k in mapping)

# 2. File Paths
steam_trans = r'C:\Program Files (x86)\Steam\steamapps\common\Village in the Shade\Mods\TextDump\translation.txt'
dev_trans = r'C:\Users\Supakiat\Desktop\Village_in_the_Shade_ThaiMod_Dev\translation_PUA.txt'
missing_file = r'C:\Program Files (x86)\Steam\steamapps\common\Village in the Shade\Mods\TextDump\dump_missing.txt'

manual_file = r'C:\Users\Supakiat\Desktop\คลังคำแปล_Village_in_the_Shade\คำแปลที่ไม่มีในคลัง_ต้องแปลเพิ่ม.txt'
dir_02 = r'C:\Users\Supakiat\Desktop\คลังคำแปล_Village_in_the_Shade\02_Switch'
dir_01 = r'C:\Users\Supakiat\Desktop\คลังคำแปล_Village_in_the_Shade\01_PC'

backup_dir = r'C:\Users\Supakiat\Desktop\Village_in_the_Shade_ThaiMod_Dev\backup'
os.makedirs(backup_dir, exist_ok=True)

# 3. Create Backups
print('Creating backups...')
shutil.copy2(steam_trans, os.path.join(backup_dir, 'translation.txt.bak'))
shutil.copy2(dev_trans, os.path.join(backup_dir, 'translation_PUA.txt.bak'))
print('Backups created successfully.')

# 4. Read Existing translation.txt
existing_lines = []
existing_keys = set()
with open(steam_trans, 'r', encoding='utf-8', errors='ignore') as f:
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
        if k_clean:
            existing_keys.add(k_clean)

print(f'Existing keys in translation.txt: {len(existing_keys):,}')

# 5. Define System Priority Order
# Priority: UI & Commands > Items & World Data > Narrative & General Lore > Dialogue
priority_order = [
    # Tier 1: UI, Controls & Commands
    'cmd',
    'action',
    'gameSetting',
    'vkey',
    'framework_cmd',
    'framework_vkey',
    'vkeycategory',
    'framework_vkeycategory',
    # Tier 2: Items, Crafting, Entities
    'item',
    'itemcategory',
    'itemtype',
    'crops',
    'creature',
    'construction',
    'livestock',
    'facility',
    'facilityrelease',
    'character',
    'skilltree',
    'trophy',
    'bgm',
    # Tier 3: Narrative, Books, Mail, Quests, System Strings
    'quest',
    'tips',
    'letter',
    'lostbook',
    'reminiscence',
    'multilinetext',
    'string',
    'framework_string',
    'intangeble',
    'logtext',
    'whistle',
    'bundlegroup',
    'bundle',
    'talknameplate',
    # Tier 4: Dialogue
    'talk'
]

# 6. Gather all translations from 02_Switch and 01_PC
candidate_translations = {} # key -> (thai_text, source_sys, priority_index)

def process_file(file_path, sys_name, p_idx, is_pc_fallback=False):
    if not os.path.exists(file_path):
        return
    with open(file_path, 'r', encoding='utf-8', errors='ignore') as fp:
        for line in fp:
            line = line.rstrip('\r\n')
            if not line or line.startswith('#') or '=' not in line:
                continue
            k, v = line.split('=', 1)
            k = k.strip()
            v = v.rstrip('\r\n')
            if not k or not v:
                continue
            
            # If already in existing translation.txt, do not overwrite
            if k in existing_keys:
                continue
            
            # If not yet registered, or if this system has higher priority (lower p_idx)
            if k not in candidate_translations:
                candidate_translations[k] = (v, sys_name, p_idx)
            else:
                existing_p_idx = candidate_translations[k][2]
                if p_idx < existing_p_idx and not is_pc_fallback:
                    candidate_translations[k] = (v, sys_name, p_idx)

# 6.1 Process Manual Added File first (Priority 0)
if os.path.exists(manual_file):
    print(f'Loading manual translations from {os.path.basename(manual_file)}...')
    with open(manual_file, 'r', encoding='utf-8') as fp:
        for line in fp:
            line = line.rstrip('\r\n')
            if not line or line.startswith('#') or '=' not in line:
                continue
            k, v = line.split('=', 1)
            k = k.strip()
            v = v.rstrip('\r\n')
            if k and v and k not in existing_keys:
                candidate_translations[k] = (v, 'Manual_Custom', -1)

# 6.2 Process 02_Switch files in priority order
print('Loading 02_Switch files...')
for p_idx, sys_name in enumerate(priority_order):
    f_path = os.path.join(dir_02, f'{sys_name}_จับคู่คำแปล_Switch_JP_TH.txt')
    process_file(f_path, sys_name, p_idx, is_pc_fallback=False)

# Also check any other files in 02_Switch not in priority list
for f in os.listdir(dir_02):
    if not f.endswith('.txt'): continue
    sys_name = f.replace('_จับคู่คำแปล_Switch_JP_TH.txt', '')
    if sys_name not in priority_order:
        p_idx = len(priority_order) + 1
        process_file(os.path.join(dir_02, f), sys_name, p_idx, is_pc_fallback=False)

# 6.3 Process 01_PC files for Gap-Filling (PC-only keys)
print('Loading 01_PC files for PC-exclusive keys...')
for p_idx, sys_name in enumerate(priority_order):
    f_path = os.path.join(dir_01, f'{sys_name}_จับคู่คำแปล_PC_JP_TH.txt')
    process_file(f_path, sys_name, p_idx, is_pc_fallback=True)

for f in os.listdir(dir_01):
    if not f.endswith('.txt'): continue
    sys_name = f.replace('_จับคู่คำแปล_PC_JP_TH.txt', '')
    if sys_name not in priority_order:
        p_idx = len(priority_order) + 1
        process_file(os.path.join(dir_01, f), sys_name, p_idx, is_pc_fallback=True)

print(f'\nTotal unique new translations to add: {len(candidate_translations):,}')

# 7. Convert to PUA and format lines
print('Converting new translations to PUA encoding...')
added_lines = []
added_lines.append('\n# ==============================================================================\n')
added_lines.append('# MASTER MERGED TRANSLATIONS (Switch 36 Systems + PC Exclusives)\n')
added_lines.append('# ==============================================================================\n')

by_system_counts = {}
for k, (th_raw, sys_name, p_idx) in candidate_translations.items():
    by_system_counts[sys_name] = by_system_counts.get(sys_name, 0) + 1
    # Strip <br> and </br>
    th_clean = re.sub(r'</?br/?>', '', th_raw, flags=re.IGNORECASE)
    # Convert to PUA
    th_pua = csv_to_pua_gui.convert_text_to_pua(th_clean, mapping, max_len)
    added_lines.append(f'{k}={th_pua}\n')

print('\nBreakdown of new additions by system:')
for sys_name, count in sorted(by_system_counts.items(), key=lambda x: -x[1]):
    print(f'  {sys_name:25s}: {count:5d} entries')

# 8. Write to translation.txt and translation_PUA.txt
final_lines = existing_lines + added_lines

print(f'\nWriting to Steam: {steam_trans}...')
with open(steam_trans, 'w', encoding='utf-8') as f:
    f.writelines(final_lines)

print(f'Writing to Dev: {dev_trans}...')
with open(dev_trans, 'w', encoding='utf-8') as f:
    f.writelines(final_lines)

print(f'Successfully updated translation files! Total lines now: {len(final_lines):,}')

# 9. Clear dump_missing.txt
with open(missing_file, 'w', encoding='utf-8') as f:
    pass
print('dump_missing.txt has been cleared and reset for the next gameplay session.')

# 10. Self-Validation
print('\nRunning self-validation check...')
with open(steam_trans, 'r', encoding='utf-8') as f:
    lines_verify = [l.strip() for l in f if '=' in l and not l.startswith('#')]

v_keys = set()
duplicates = 0
for l in lines_verify:
    k = l.split('=', 1)[0].strip()
    if k.startswith('[') and ']' in k:
        k = k[k.find(']')+1:].strip()
    if '[SCALE:' in k:
        k = k[:k.find('[SCALE:')].strip()
    if k in v_keys:
        duplicates += 1
    v_keys.add(k)

print(f'Validation Result:')
print(f'  Total unique keys in final translation.txt: {len(v_keys):,}')
print(f'  Duplicate keys: {duplicates}')
print('Master Translation Integration completed successfully!')
