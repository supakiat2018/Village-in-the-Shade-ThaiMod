import struct

fad_path = r'C:\Program Files (x86)\Steam\steamapps\common\Village in the Shade\data\fairy_1_00.dat'
fad_base = 0x42590C00
fad_size = 245855360

offsets = []
with open(fad_path, 'rb') as f:
    f.seek(fad_base)
    chunk_size = 16 * 1024 * 1024
    pos = 0
    prev_tail = b''
    while pos < fad_size:
        to_read = min(chunk_size, fad_size - pos)
        buf = prev_tail + f.read(to_read)
        idx = 0
        while True:
            idx = buf.find(b'NMPLTEX1', idx)
            if idx == -1:
                break
            abs_off = fad_base + pos - len(prev_tail) + idx
            offsets.append(abs_off)
            idx += 8
        prev_tail = buf[-64:]
        pos += to_read

targets = {
    30: ('ui_1153_ウィンドウ', 1024, 1024),
    37: ('ui_0010_itemcategory', 512, 1024),
    54: ('ui_0010_itemcategory03', 256, 512),
    194: ('ui_0010_itemcategory2', 1024, 256)
}

for idx, (name, w, h) in targets.items():
    nmpl_off = offsets[idx]
    desc_off = nmpl_off - 32
    print(f'    /* {name} ({w}x{h}) */')
    print(f'    {{ 0x{desc_off:08X}, "{name}.nltx", "{name}_thai.nltx", {w}, {h}, TRUE }},')
    print(f'    {{ 0x{nmpl_off:08X}, "{name}.nltx", "{name}_thai.nltx", {w}, {h}, FALSE }},')
