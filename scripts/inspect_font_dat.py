import struct

p_orig = r'C:\Users\Supakiat\Desktop\Mover\QuickBMS\Extracted_Data_v109ต้นฉบับ\data\database\font.dat'
p_mod = r'C:\Program Files (x86)\Steam\steamapps\common\Village in the Shade\Mods\Fonts\font.dat'
p_v110 = r'C:\Users\Supakiat\Desktop\Mover\QuickBMS\Extracted_Data_v110\data\database\font.dat'

with open(p_orig, 'rb') as f: d_orig = f.read()
with open(p_mod, 'rb') as f: d_mod = f.read()
with open(p_v110, 'rb') as f: d_v110 = f.read()

def parse_font_db(data, name):
    num_rec, str_off, str_len, rec_sz = struct.unpack('<IIII', data[:16])
    str_tbl = data[str_off:str_off+str_len]
    print(f"=== {name} (rec_sz={rec_sz}) ===")
    for r in range(num_rec):
        r_start = 16 + r * rec_sz
        r_data = data[r_start:r_start+rec_sz]
        id_str_off = struct.unpack('<I', r_data[0:4])[0]
        id_str = str_tbl[id_str_off:].split(b'\x00')[0].decode('ascii')
        print(f"\nRecord {r}: {id_str}")
        
        # In this game engine (Framework / Database format):
        # Databases often have language slots!
        # Languages in this engine:
        # Slot 0 = JP (Japanese)
        # Slot 1 = EN (English)
        # Slot 2 = FR / DE / ES ... or SC / TC / KO ?
        # Let's inspect sub-structures inside the record!
        for off in range(0, rec_sz, 4):
            val = struct.unpack('<I', r_data[off:off+4])[0]
            if val < str_len:
                s = str_tbl[val:].split(b'\x00')[0]
                if s.endswith(b'.ttf') or s in [b'Lora', b'ResourceHanRoundedTC', b'ResourceHanRoundedK', b'LXGWWenKaiMonoTC']:
                    print(f"  +0x{off:03X} (abs 0x{r_start+off:04X}): {val} -> {s.decode('ascii')}")

parse_font_db(d_orig, "v1.09 Original (Japanese)")
parse_font_db(d_mod, "Mods font.dat (Thai Mod)")
parse_font_db(d_v110, "v1.10 Steam Original")
