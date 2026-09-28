"""
Batch convert all 63 edited Thai PNGs to .nltx and install to Steam mod folder.
"""

import os
import sys
import glob
import struct
import shutil
import subprocess
import unicodedata
import lz4.block
from PIL import Image

def main():
    dev_root = r'C:\Users\Supakiat\Desktop\Village_in_the_Shade_ThaiMod_Dev'
    src_dir = os.path.join(dev_root, '01_ภาพที่ม็อดเดิมแก้ไข_ทั้งหมด_65ภาพ', 'แก้แล้ว')
    texconv = os.path.join(dev_root, 'texconv.exe')
    
    local_nltx_dir = os.path.join(dev_root, 'textures', 'thai_edited_nltx')
    steam_tex_dir = r'C:\Program Files (x86)\Steam\steamapps\common\Village in the Shade\Mods\TextDump\textures'
    temp_dds_dir = os.path.join(dev_root, 'temp_dds_batch')
    
    os.makedirs(local_nltx_dir, exist_ok=True)
    os.makedirs(steam_tex_dir, exist_ok=True)
    os.makedirs(temp_dds_dir, exist_ok=True)

    png_files = [f for f in os.listdir(src_dir) if f.endswith('.png') and not f.startswith('ChatGPT')]
    print(f"=== Converting {len(png_files)} Edited Images to .nltx ===")
    print(f"Source: {src_dir}")
    print(f"Destination: {steam_tex_dir}\n")

    success_count = 0
    for i, fn in enumerate(sorted(png_files)):
        src_png = os.path.join(src_dir, fn)
        base_name = os.path.splitext(fn)[0]
        base_nfc = unicodedata.normalize('NFC', base_name)
        
        im = Image.open(src_png)
        w, h = im.size

        # 1. Run texconv to get BC7 DDS
        cmd = [texconv, '-f', 'BC7_UNORM', '-m', '1', '-nologo', '-y', '-o', temp_dds_dir, src_png]
        res = subprocess.run(cmd, capture_output=True, text=True)
        if res.returncode != 0:
            print(f"[ERROR] texconv failed for {fn}: {res.stderr}")
            continue

        dds_name = os.path.splitext(fn)[0] + '.dds'
        dds_path = os.path.join(temp_dds_dir, dds_name)
        if not os.path.exists(dds_path):
            # Sometimes texconv changes filename or replaces characters
            dds_candidates = glob.glob(os.path.join(temp_dds_dir, '*.dds'))
            if dds_candidates:
                dds_path = dds_candidates[0]
            else:
                print(f"[ERROR] DDS not found for {fn}")
                continue

        with open(dds_path, 'rb') as f_dds:
            f_dds.seek(148)
            raw_bc7 = f_dds.read()

        # Clean temp DDS
        try:
            os.remove(dds_path)
        except Exception:
            pass

        # 2. Compress BC7 with LZ4 (Type 9)
        comp_data = lz4.block.compress(raw_bc7, mode='high_compression', store_size=False)
        comp_sz = len(comp_data) + 20
        uncomp_sz = len(raw_bc7)

        ykcmp_header = struct.pack('<8sIII', b'YKCMP_V1', 9, comp_sz, uncomp_sz)
        ykcmp_payload = ykcmp_header + comp_data

        # 3. Assemble complete and valid NMPLTEX1 header
        nmpl = bytearray(128)
        nmpl[0:8] = b'NMPLTEX1'
        struct.pack_into('<I', nmpl, 0x10, 0x66)       # Format: DXGI_FORMAT_BC7_UNORM (0x66)
        struct.pack_into('<I', nmpl, 0x14, 0x00800006) # Engine flags
        struct.pack_into('<I', nmpl, 0x18, w)          # Width
        struct.pack_into('<I', nmpl, 0x1C, h)          # Height
        nmpl[0x20:0x24] = b'\x04\x00\xff\xff'         # Subsurface / mip descriptors
        nmpl[0x24:0x28] = b'\x00\x01\x01\x00'         # Compression flag (0x26=1 enables YKCMP decompression!)
        struct.pack_into('<I', nmpl, 0x2C, uncomp_sz)  # Uncompressed BC7 buffer size (w * h)
        struct.pack_into('<II', nmpl, 0x30, len(ykcmp_payload), 128) # Compressed size, header size

        nltx_data = bytes(nmpl) + ykcmp_payload

        # Save to local and steam
        out_nltx_name = f"{base_nfc}.nltx"
        local_path = os.path.join(local_nltx_dir, out_nltx_name)
        steam_path = os.path.join(steam_tex_dir, out_nltx_name)

        with open(local_path, 'wb') as f_out:
            f_out.write(nltx_data)
        with open(steam_path, 'wb') as f_out:
            f_out.write(nltx_data)

        success_count += 1
        sz_kb = len(nltx_data) / 1024
        print(f"[{success_count:02d}/{len(png_files)}] Converted & Installed: {out_nltx_name:32s} ({w:4d}x{h:<4d}) -> {sz_kb:6.1f} KB")

    # Clean temp dir
    try:
        shutil.rmtree(temp_dds_dir)
    except Exception:
        pass

    # Ensure Thai title screen is active
    thai_title_src = os.path.join(dev_root, 'textures', 'ui_1000_title01_thai.nltx')
    if os.path.exists(thai_title_src):
        shutil.copy2(thai_title_src, os.path.join(steam_tex_dir, 'ui_1000_title01.nltx'))
        print("\n[OK] Verified Thai Title Screen (ui_1000_title01.nltx) is ACTIVE!")

    # 4. Update text_dump.c to prioritize _thai.nltx
    print("\n=== Updating text_dump.c Hook Priority ===")
    c_file = os.path.join(dev_root, 'src', 'text_dump.c')
    with open(c_file, 'r', encoding='utf-8') as f:
        c_code = f.read()

    # Make sure alt_filename is checked first
    old_lookup = """            BOOL found = find_override_file(fad_entry->filename, override_path, sizeof(override_path), &ext_size);
            if (!found && fad_entry->alt_filename) {
                found = find_override_file(fad_entry->alt_filename, override_path, sizeof(override_path), &ext_size);
            }"""

    new_lookup = """            BOOL found = FALSE;
            if (fad_entry->alt_filename) {
                found = find_override_file(fad_entry->alt_filename, override_path, sizeof(override_path), &ext_size);
            }
            if (!found) {
                found = find_override_file(fad_entry->filename, override_path, sizeof(override_path), &ext_size);
            }"""

    if old_lookup in c_code:
        c_code = c_code.replace(old_lookup, new_lookup)
        with open(c_file, 'w', encoding='utf-8') as f:
            f.write(c_code)
        print("[OK] Updated text_dump.c to prioritize _thai.nltx over base .nltx!")
    else:
        print("[NOTE] Lookup priority already updated or alternate pattern present.")

    # 5. Compile text_dump.dll with Zig CC
    print("\n=== Compiling text_dump.dll ===")
    build_cmd = [
        "zig", "cc", "-shared", "-O2", "-s",
        r"src\text_dump.c",
        r"src\addrsig.c",
        r"src\minhook-master\src\buffer.c",
        r"src\minhook-master\src\hook.c",
        r"src\minhook-master\src\trampoline.c",
        r"src\minhook-master\src\hde\hde64.c",
        "-o", r"bin\text_dump.dll",
        "-lkernel32", "-luser32"
    ]
    res = subprocess.run(build_cmd, cwd=dev_root, capture_output=True, text=True)
    if res.returncode == 0:
        print("[SUCCESS] Compiled bin\\text_dump.dll successfully!")
    else:
        print(f"[ERROR] Compilation failed:\n{res.stderr}")
        return

    steam_dll = r"C:\Program Files (x86)\Steam\steamapps\common\Village in the Shade\Mods\TextDump\text_dump.dll"
    shutil.copy2(os.path.join(dev_root, 'bin', 'text_dump.dll'), steam_dll)
    print(f"[INSTALLED] Installed text_dump.dll to:\n{steam_dll}")

    print(f"\n=== FINISHED! Successfully installed {success_count} edited Thai textures into the game! ===")

if __name__ == '__main__':
    main()
