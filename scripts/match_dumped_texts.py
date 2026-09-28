import os
import glob
import re

missing_file = r'C:\Program Files (x86)\Steam\steamapps\common\Village in the Shade\Mods\TextDump\dump_missing.txt'
unique_keys = []
seen = set()

with open(missing_file, 'r', encoding='utf-8', errors='ignore') as f:
    for line in f:
        line = line.strip()
        if not line:
            continue
        idx = line.find('] ')
        if idx != -1:
            raw_text = line[idx+2:].strip()
            if raw_text and raw_text not in seen:
                seen.add(raw_text)
                unique_keys.append(raw_text)

print(f'Total unique captured keys: {len(unique_keys)}')

dir_03 = r'C:\Users\Supakiat\Desktop\คลังคำแปล_Village_in_the_Shade\03_ผลลัพธ์_JP_TH'
dir_02 = r'C:\Users\Supakiat\Desktop\คลังคำแปล_Village_in_the_Shade\02_Switch'
dir_01 = r'C:\Users\Supakiat\Desktop\คลังคำแปล_Village_in_the_Shade\01_PC'

# Priority loading
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

db_switch = {}
for p in priority_files:
    p_path = os.path.join(dir_03, p)
    if os.path.exists(p_path):
        with open(p_path, 'r', encoding='utf-8', errors='ignore') as fp:
            for line in fp:
                line = line.strip()
                if not line or line.startswith('#') or '=' not in line:
                    continue
                k, v = line.split('=', 1)
                k = k.strip()
                v = v.strip()
                if k and v and k not in db_switch:
                    db_switch[k] = (v, p, '03')

for d in [dir_03, dir_02]:
    for f in glob.glob(os.path.join(d, '*.txt')):
        bname = os.path.basename(f)
        with open(f, 'r', encoding='utf-8', errors='ignore') as fp:
            for line in fp:
                line = line.strip()
                if not line or line.startswith('#') or '=' not in line:
                    continue
                k, v = line.split('=', 1)
                k = k.strip()
                v = v.strip()
                if k and v and k not in db_switch:
                    db_switch[k] = (v, bname, '02/03')

print(f'Total database keys loaded from Switch: {len(db_switch):,}')

# Check exact matches
exact_matches = {}
remaining = []
for k in unique_keys:
    if k in db_switch:
        exact_matches[k] = db_switch[k]
    else:
        remaining.append(k)

print(f'Exact matches: {len(exact_matches)}')
print(f'Remaining unmatched: {len(remaining)}')

# Analyze remaining keys
sample_remaining = remaining[:50]
for idx, r in enumerate(sample_remaining, 1):
    print(f'{idx}. {repr(r)}')
