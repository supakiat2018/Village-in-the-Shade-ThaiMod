import struct
import os

fairy_path = r"C:\Program Files (x86)\Steam\steamapps\common\Village in the Shade\data\fairy_1_00.dat"
tex_path = r"C:\Program Files (x86)\Steam\steamapps\common\Village in the Shade\data\texture_1_00.dat"

def scan_archive(path, label):
    with open(path, "rb") as f:
        magic = f.read(8)
        print(f"[{label}] Magic: {magic}")
        if magic != b"FAFULLFS":
            return
        count, str_len, toc_off, str_off = struct.unpack("<IIQQ", f.read(24))
        print(f"[{label}] Count: {count}, StrLen: {str_len}, TocOff: 0x{toc_off:X}, StrOff: 0x{str_off:X}")
        
        f.seek(toc_off)
        toc_data = f.read(count * 32)
        f.seek(str_off)
        str_data = f.read(str_len)
        
        entries = []
        for i in range(count):
            off, sz, name_off, unk = struct.unpack_from("<QQQQ", toc_data, i * 32)
            name_end = str_data.find(b"\x00", name_off)
            name = str_data[name_off:name_end].decode("latin1", errors="ignore")
            entries.append((name, off, sz))
            
        print(f"[{label}] Parsed {len(entries)} files!")
        # Search for .fad or ui_ or nameplate or resident
        matches = [e for e in entries if any(k in e[0].lower() for k in ["resident", "fad", "nameplate", "ui_0010", "charaname"])]
        for m in matches:
            print(f"  -> {m[0]}: Offset=0x{m[1]:X}, Size={m[2]}")
        return entries

print("Scanning archives in data/ ...")
fairy_entries = scan_archive(fairy_path, "fairy_1_00.dat")
tex_entries = scan_archive(tex_path, "texture_1_00.dat")
