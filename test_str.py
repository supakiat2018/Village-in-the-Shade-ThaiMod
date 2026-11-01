import struct

game_dat = r'C:\Program Files (x86)\Steam\steamapps\common\Village in the Shade\data\fairy_1_00.dat'
with open(game_dat, 'rb') as f:
    f.seek(0x6F74F400)
    fad_hdr = f.read(0x6000)

for idx in [0, 1, 2, 3, 4, 5, 6, 7, 8, 12, 13, 25, 26, 43, 50, 97, 98, 113]:
    off = 0x0FC0 + idx * 32
    rel_off, str_off, w, h, pad, sz = struct.unpack('<IIIIQQ', fad_hdr[off:off+32])
    # Read string at str_off
    s = fad_hdr[str_off:str_off+64].split(b'\x00')[0]
    try:
        s_text = s.decode('utf-8')
    except:
        s_text = s.decode('shift-jis', errors='ignore')
    print(f"TOC[{idx:3d}]: str_off=0x{str_off:04X} -> '{s_text}', w={w}, h={h}, sz={sz}, rel_off=0x{rel_off:08X}")
