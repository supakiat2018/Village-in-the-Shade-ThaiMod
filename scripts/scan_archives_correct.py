import struct
import os

fairy_path = r"C:\Program Files (x86)\Steam\steamapps\common\Village in the Shade\data\fairy_1_00.dat"
tex_path = r"C:\Program Files (x86)\Steam\steamapps\common\Village in the Shade\data\texture_1_00.dat"

def scan_archive(path, label):
    with open(path, "rb") as f:
        hdr = f.read(40) # FAFULLFS_Header
        magic = hdr[:8]
        if magic != b"FAFULLFS":
            print(f"[{label}] Not FAFULLFS!")
            return []
        count = struct.unpack_from("<I", hdr, 8)[0]
        str_off = struct.unpack_from("<Q", hdr, 16)[0]
        str_len = struct.unpack_from("<Q", hdr, 24)[0]
        toc_off = struct.unpack_from("<Q", hdr, 32)[0]
        
        print(f"[{label}] Count: {count}, StrLen: {str_len}, TocOff: 0x{toc_off:X}, StrOff: 0x{str_off:X}")
        
        f.seek(toc_off)
        toc_data = f.read(count * 48)
        f.seek(str_off)
        str_data = f.read(str_len)
        
        entries = []
        for i in range(count):
            hash_val, name_off, unk1, sz, off, unk2 = struct.unpack_from("<QQQQQQ", toc_data, i * 48)
            name_end = str_data.find(b"\x00", name_off)
            name = str_data[name_off:name_end].decode("latin1", errors="ignore")
            entries.append((name, off, sz))
            
        print(f"[{label}] Parsed {len(entries)} files successfully!")
        return entries

print("Scanning archives...")
fairy_files = scan_archive(fairy_path, "fairy_1_00.dat")
for name, off, sz in fairy_files:
    if "resident" in name.lower() or "fad" in name.lower():
        print(f"  fairy -> {name}: Offset=0x{off:X}, Size={sz}")

tex_files = scan_archive(tex_path, "texture_1_00.dat")
print(f"Total texture files: {len(tex_files)}")
for name, off, sz in tex_files[:20]:
    print(f"  tex -> {name}: Offset=0x{off:X}, Size={sz}")
