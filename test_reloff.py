import struct

game_dat = r'C:\Program Files (x86)\Steam\steamapps\common\Village in the Shade\data\fairy_1_00.dat'
with open(game_dat, 'rb') as f:
    fad_base = 0x6F74F400
    for idx in [3, 12, 13, 25, 26, 43, 50, 97, 98, 113]:
        off = 0x0FC0 + idx * 32
        f.seek(fad_base + off)
        rel_off, str_off, w, h, pad, sz = struct.unpack('<IIIIQQ', f.read(32))
        
        # Read at rel_off
        f.seek(fad_base + rel_off)
        data = f.read(128)
        print(f"=== TOC[{idx:3d}] rel_off=0x{rel_off:08X} ===")
        print("Hex:", ' '.join(f'{b:02X}' for b in data[:32]))
        # print ASCII/strings in this 128 bytes
        s = ''.join(chr(b) if 32 <= b <= 126 else '.' for b in data[:64])
        print("ASCII:", s)
