import os
import sys
import re
import time
from collections import defaultdict, Counter

# Set up paths
dev_dir = r'C:\Users\Supakiat\Desktop\Village_in_the_Shade_ThaiMod_Dev'
steam_trans = r'C:\Program Files (x86)\Steam\steamapps\common\Village in the Shade\Mods\TextDump\translation.txt'
dev_trans = os.path.join(dev_dir, 'translation_PUA.txt')
sw_talk = r'C:\Users\Supakiat\Desktop\คลังคำแปล_Village_in_the_Shade\02_Switch\talk_จับคู่คำแปล_Switch_JP_TH.txt'

# Load PUA converter
sys.path.insert(0, r'C:\Users\Supakiat\Desktop\Mover\out')
import csv_to_pua_gui

mapping_path = r'C:\Users\Supakiat\Desktop\Mover\out\Mapping.json'
print(f'Loading PUA mapping from {mapping_path}...')
mapping = csv_to_pua_gui.load_mapping(mapping_path)
max_len = max(len(k) for k in mapping)
print(f'PUA mapping loaded with {len(mapping):,} entries.')

# 1. Read existing translation.txt
print(f'\nReading existing translation.txt...')
existing_keys = set()
existing_lines = []

with open(steam_trans, 'r', encoding='utf-8', errors='ignore') as f:
    for line in f:
        existing_lines.append(line)
        raw = line.strip()
        if not raw or raw.startswith('#') or '=' not in raw:
            continue
        k = raw.split('=', 1)[0].strip()
        if k.startswith('[') and ']' in k:
            k = k[k.find(']')+1:].strip()
        if '[SCALE:' in k:
            k = k[:k.find('[SCALE:')].strip()
        existing_keys.add(k)

print(f'Existing unique keys in translation.txt: {len(existing_keys):,}')

# 2. Dangerous system keys to protect
dangerous_keys = {'なし', 'あり', 'うん', 'やだ'}

# 3. Read Switch talk and collect translations per key
print(f'\nReading Switch dialogue from {sw_talk}...')
key_counts = defaultdict(Counter)
total_raw_lines = 0

with open(sw_talk, 'r', encoding='utf-8', errors='ignore') as f:
    for line in f:
        if '=' in line and not line.strip().startswith('#'):
            total_raw_lines += 1
            k, v = line.strip().split('=', 1)
            k = k.strip()
            v = v.strip()
            if not k or not v:
                continue
            
            # Skip dangerous system keys and keys already in translation.txt
            if k in dangerous_keys or k in existing_keys:
                continue
            
            # Clean <br> tags immediately (no space, continuous Thai)
            v_clean = re.sub(r'</?br/?>', '', v, flags=re.IGNORECASE).strip()
            if v_clean:
                key_counts[k][v_clean] += 1

print(f'Total raw talk lines scanned: {total_raw_lines:,}')
print(f'Unique new dialogue keys to import: {len(key_counts):,}')

# 4. Pick best translation and convert to PUA
print(f'\nConverting new dialogue keys to PUA font encoding...')
t0 = time.time()
new_lines = []
new_lines.append('\n# ==============================================================================\n')
new_lines.append(f'# Switch Dialogue Batch Import (Unique keys: {len(key_counts):,})\n')
new_lines.append('# ==============================================================================\n')

count = 0
for k, counter in key_counts.items():
    # Pick the most frequently used translation
    best_v = counter.most_common(1)[0][0]
    
    # Convert to PUA
    v_pua = csv_to_pua_gui.convert_text_to_pua(best_v, mapping, max_len)
    new_lines.append(f'{k}={v_pua}\n')
    count += 1
    if count % 10000 == 0:
        print(f'  Converted {count:,}/{len(key_counts):,} keys...')

t1 = time.time()
print(f'Successfully converted {count:,} keys in {t1-t0:.2f} seconds!')

# 5. Write back to Steam translation.txt and Dev translation_PUA.txt
final_lines = existing_lines + new_lines

print(f'\nWriting to Steam translation.txt ({len(final_lines):,} total lines)...')
with open(steam_trans, 'w', encoding='utf-8') as f:
    f.writelines(final_lines)

print(f'Writing to Dev translation_PUA.txt...')
with open(dev_trans, 'w', encoding='utf-8') as f:
    f.writelines(final_lines)

print('\n=== IMPORT COMPLETE SUCCESSFULLY! ===')
print(f'Total lines written: {len(final_lines):,}')
print(f'Steam file: {steam_trans}')
print(f'Dev file  : {dev_trans}')
