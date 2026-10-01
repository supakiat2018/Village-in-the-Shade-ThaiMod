import re

pua_map = {}
with open('src/pua_mapping.h', 'r', encoding='utf-8') as f:
    for line in f:
        # e.g. { L"\u0E01\u0E31", L'\uF000' },
        m = re.search(r'\{\s*L"([^"]+)",\s*L\'\\u([0-9A-Fa-f]{4})\'\s*\}', line)
        if m:
            key_raw = m.group(1)
            val_code = int(m.group(2), 16)
            key = key_raw.encode().decode('unicode_escape')
            val = chr(val_code)
            pua_map[key] = val

print(f'Loaded {len(pua_map)} PUA mappings.')

def to_pua(text):
    # Sort keys by length descending
    keys = sorted(pua_map.keys(), key=lambda k: -len(k))
    res = text
    for k in keys:
        res = res.replace(k, pua_map[k])
    return res

test_str = ' เพื่อตั้งค่า'
pua_str = to_pua(test_str)
print('Original:', test_str)
print('PUA     :', repr(pua_str))
for ch in pua_str:
    print(f'  U+{ord(ch):04X}: {repr(ch)}')

# Test 'to set configurations'
print('Without space:', repr(to_pua('เพื่อตั้งค่า')))
