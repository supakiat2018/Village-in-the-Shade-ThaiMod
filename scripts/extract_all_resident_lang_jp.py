import os
import sys
import struct
import time
import ctypes
import lz4.block
import texture2ddecoder
from PIL import Image
from concurrent.futures import ThreadPoolExecutor

fairy_path = r"C:\Program Files (x86)\Steam\steamapps\common\Village in the Shade\data\fairy_1_00.dat"
out_dir = r"C:\Users\Supakiat\Desktop\Village_in_the_Shade_ThaiMod_Dev\คียบอด"
os.makedirs(out_dir, exist_ok=True)

print("1. Locating resident_lang_jp.fad...")
with open(fairy_path, "rb") as f:
    hdr = f.read(48)
    magic, count, unk, str_off, str_len, toc_off, pad = struct.unpack("<8sIIQQQQ", hdr)
    f.seek(str_off)
    str_data = f.read(str_len)
    f.seek(toc_off)
    fad_off, fad_size = None, None
    for _ in range(count):
        entry_data = f.read(48)
        hash_val, name_off, unk1, size, offset, unk2 = struct.unpack("<QQQQQQ", entry_data)
        null_pos = str_data.find(b"\x00", name_off)
        name = str_data[name_off:null_pos].decode("utf-8", errors="ignore") if null_pos != -1 else ""
        if "resident_lang_jp" in name:
            fad_off, fad_size = offset, size
            break

print(f"   resident_lang_jp.fad at 0x{fad_off:08X} ({fad_size:,} bytes)")

print("2. Reading FAD data into memory...")
t0 = time.time()
with open(fairy_path, "rb") as f:
    f.seek(fad_off)
    fad_bytes = f.read(fad_size)
print(f"   Read in {time.time() - t0:.2f}s")

print("3. Scanning NMPLTEX1 textures...")
offsets = []
pos = 0
while True:
    idx = fad_bytes.find(b"NMPLTEX1", pos)
    if idx == -1: break
    offsets.append(idx)
    pos = idx + 8

print(f"   Found {len(offsets)} textures")

# Load C decompressor DLL
dll_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "bin", "ykcmp_fast.dll")
dll_path = os.path.abspath(dll_path)
decompress_c = None
if os.path.exists(dll_path):
    try:
        lib = ctypes.CDLL(dll_path)
        decompress_c = lib.decompress_ykcmp_type4_c
        decompress_c.argtypes = [ctypes.c_char_p, ctypes.c_uint32, ctypes.c_char_p, ctypes.c_uint32]
        decompress_c.restype = ctypes.c_int
        print(f"   Loaded fast C decompressor: {dll_path}")
    except Exception as e:
        print(f"   Failed to load C DLL: {e}")

def decompress_ykcmp_py(payload, uncomp_sz):
    dst = bytearray()
    src_idx = 0
    src_len = len(payload)
    while src_idx < src_len and len(dst) < uncomp_sz:
        b = payload[src_idx]
        src_idx += 1
        if (b & 0x80) == 0:
            length = b
            for _ in range(length):
                if src_idx < src_len and len(dst) < uncomp_sz:
                    dst.append(payload[src_idx])
                    src_idx += 1
        elif (b & 0x40) == 0:
            length = ((b >> 4) & 3) + 1
            offset = (b & 0x0F) + 1
            for _ in range(length):
                if len(dst) < uncomp_sz:
                    dst.append(dst[-offset] if offset <= len(dst) else 0)
        elif (b & 0x20) == 0:
            length = (b & 0x1F) + 2
            if src_idx < src_len:
                b1 = payload[src_idx]
                src_idx += 1
                offset = b1 + 1
                for _ in range(length):
                    if len(dst) < uncomp_sz:
                        dst.append(dst[-offset] if offset <= len(dst) else 0)
        else:
            if src_idx + 1 < src_len:
                b1 = payload[src_idx]
                b2 = payload[src_idx + 1]
                src_idx += 2
                length = (((b & 0x1F) << 4) | (b1 >> 4)) + 3
                offset = (((b1 & 0x0F) << 8) | b2) + 1
                for _ in range(length):
                    if len(dst) < uncomp_sz:
                        dst.append(dst[-offset] if offset <= len(dst) else 0)
    return bytes(dst)

def decompress_ykcmp(payload, uncomp_sz):
    if decompress_c:
        dst = bytearray(uncomp_sz)
        res = decompress_c(bytes(payload), len(payload), (ctypes.c_char * uncomp_sz).from_buffer(dst), uncomp_sz)
        return bytes(dst[:res])
    else:
        return decompress_ykcmp_py(payload, uncomp_sz)

def process_texture(item):
    idx, off = item
    try:
        w, h = struct.unpack("<II", fad_bytes[off+0x18:off+0x20])
        doff = struct.unpack("<I", fad_bytes[off+0x34:off+0x38])[0]
        yk_off = off + doff
        magic = fad_bytes[yk_off:yk_off+8]
        if magic != b"YKCMP_V1":
            return (idx, False, f"Not YKCMP ({magic})")

        ptype, comp_sz, uncomp_sz = struct.unpack("<III", fad_bytes[yk_off+8:yk_off+20])
        comp_data = fad_bytes[yk_off+20:yk_off+20+comp_sz]

        if ptype == 4:
            decomp = decompress_ykcmp(comp_data, uncomp_sz)
        elif ptype == 9:
            decomp = lz4.block.decompress(comp_data, uncompressed_size=uncomp_sz)
        else:
            return (idx, False, f"Unknown ptype {ptype}")

        decoded = texture2ddecoder.decode_bc7(decomp, w, h)
        img = Image.frombytes("RGBA", (w, h), decoded, "raw", "BGRA")
        out_fn = f"tex_{idx:03d}_{w}x{h}.png"
        out_path = os.path.join(out_dir, out_fn)
        img.save(out_path)
        return (idx, True, out_fn)
    except Exception as e:
        return (idx, False, str(e))

print(f"4. Extracting all {len(offsets)} textures in parallel...")
t_extract = time.time()
with ThreadPoolExecutor(max_workers=8) as executor:
    results = list(executor.map(process_texture, enumerate(offsets)))

success = sum(1 for r in results if r[1])
failed = len(results) - success
print(f"   Done in {time.time() - t_extract:.2f}s! Successfully extracted: {success}/{len(offsets)}, Failed: {failed}")

if failed > 0:
    for idx, ok, err in results:
        if not ok:
            print(f"   Failed index {idx:03d}: {err}")
