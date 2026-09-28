import struct

p_orig = r'C:\Users\Supakiat\Desktop\Mover\QuickBMS\Extracted_Data_v109ต้นฉบับ\data\database\font.dat'
p_v110 = r'C:\Users\Supakiat\Desktop\Mover\QuickBMS\Extracted_Data_v110\data\database\font.dat'
p_mod = r'C:\Program Files (x86)\Steam\steamapps\common\Village in the Shade\Mods\Fonts\font.dat'

def print_lang_slots(path):
    with open(path, 'rb') as f: d = f.read()
    num_rec, str_off, str_len, rec_sz = struct.unpack('<IIII', d[:16])
    str_tbl = d[str_off:str_off+str_len]
    num_langs = (rec_sz - 36) // 132
    print(f"=== {path}: num_langs={num_langs} ===")
    for r in range(5):
        r_start = 16 + r * rec_sz
        id_str_off = struct.unpack('<I', d[r_start:r_start+4])[0]
        id_str = str_tbl[id_str_off:].split(b'\x00')[0].decode('ascii')
        print(f"Record {r}: {id_str}")
        for lang_i in range(num_langs):
            l_start = r_start + 36 + lang_i * 132
            # Find ttf string
            ttf_name = ""
            for off in range(0, 132, 4):
                val = struct.unpack('<I', d[l_start+off:l_start+off+4])[0]
                if val < str_len:
                    sub = str_tbl[val:].split(b'\x00')[0]
                    if sub.endswith(b'.ttf'):
                        ttf_name = sub.decode('ascii')
                        break
            # Find spacing flags
            flag1 = struct.unpack('<I', d[l_start+0x38:l_start+0x3C])[0] # +0x60 in record (36 + 0x3C = 0x60)
            flag2 = struct.unpack('<I', d[l_start+0x3C:l_start+0x40])[0] # +0x64 in record
            print(f"  Lang {lang_i}: font={ttf_name:35s} | flag1={flag1}, flag2={flag2}")

print("=== MOD ===")
print_lang_slots(p_mod)
print("\n=== V110 ORIG ===")
print_lang_slots(p_v110)
