"""
Village in the Shade - Save Data Tool
รองรับทั้งไฟล์เซฟของ PC (Steam) และ Nintendo Switch (Ryujinx/Switch)
รูปแบบการบีบอัด: YKCMP_V1 (LZ4 Type 8 / Type 4) + Dynamic Schema Serialization (SER)
"""

import sys
import os
import struct
import lz4.block

def decompress_ykcmp(data):
    if not data.startswith(b'YKCMP_V1'):
        raise ValueError("ไฟล์นี้ไม่ใช่ฟอร์แมต YKCMP_V1")
    
    magic, ctype, comp_size, uncomp_size = struct.unpack('<8sIII', data[:20])
    payload = data[20:comp_size]
    decomp = lz4.block.decompress(payload, uncompressed_size=uncomp_size)
    return decomp, ctype

def compress_ykcmp(decomp_data, ctype=8):
    comp_data = lz4.block.compress(decomp_data, mode='high_compression' if ctype == 8 else 'default', store_size=False)
    comp_size = len(comp_data) + 20
    uncomp_size = len(decomp_data)
    header = struct.pack('<8sIII', b'YKCMP_V1', ctype, comp_size, uncomp_size)
    return header + comp_data

def inspect_save(file_path):
    print(f"\n=======================================================")
    print(f" กำลังตรวจสอบไฟล์: {os.path.basename(file_path)}")
    print(f"=======================================================")
    
    with open(file_path, 'rb') as f:
        data = f.read()
    
    decomp, ctype = decompress_ykcmp(data)
    
    if not decomp.startswith(b'SER\x00'):
        print("[INFO] ไฟล์นี้ไม่ได้ใช้โครงสร้าง SER (อาจเป็น save.lst)")
        # ลองดึงข้อความ
        import re
        txts = re.findall(b'[a-zA-Z0-9_\u0e00-\u0e7f]{3,}', decomp)
        print("ข้อความที่พบในไฟล์:", [t.decode('utf-8', errors='ignore') for t in txts[:20]])
        return

    total_len = struct.unpack('<I', decomp[8:12])[0]
    schema_off = struct.unpack('<I', decomp[12:16])[0]
    schema_bytes = decomp[schema_off:total_len]
    schema_names = [s.decode('utf-8', errors='ignore') for s in schema_bytes.split(b'\x00') if s]

    print(f"[*] ขนาดไฟล์บีบอัดบนดิสก์ : {len(data):,} ไบต์")
    print(f"[*] ขนาดข้อมูลจริง (Payload) : {total_len:,} ไบต์ ({total_len/1024:.2f} KB)")
    print(f"[*] จำนวนตัวแปรในระบบ (Schema) : {len(schema_names):,} รายการ")

    def get_val(name):
        tag_off = schema_bytes.find(name.encode('utf-8') + b'\x00')
        if tag_off == -1: return None
        tag = struct.pack('<I', tag_off)
        idx = decomp.find(tag, 0, schema_off)
        if idx == -1: return None
        return struct.unpack('<Q', decomp[idx+8:idx+16])[0]

    h = get_val('hour_') or 0
    m = get_val('minute_') or 0
    s = get_val('second_') or 0
    print(f"[*] เวลาเล่นทั้งหมด        : {h:02d}:{m:02d}:{s:02d}")

    # ตรวจสอบเควส
    qmap_off = schema_bytes.find(b'questMap_\x00')
    if qmap_off != -1:
        q_idx = decomp.find(struct.pack('<I', qmap_off), 0, schema_off)
        if q_idx != -1:
            data_id_tag = struct.pack('<I', schema_bytes.find(b'dataID_\x00'))
            state_tag = struct.pack('<I', schema_bytes.find(b'state_\x00'))
            p = q_idx
            quests = []
            while p < schema_off:
                f_idx = decomp.find(data_id_tag, p, p + 200)
                if f_idx == -1: break
                qid = struct.unpack('<Q', decomp[f_idx+8:f_idx+16])[0]
                s_idx = decomp.find(state_tag, f_idx, f_idx + 100)
                st = struct.unpack('<I', decomp[s_idx+8:s_idx+12])[0] if s_idx != -1 else -1
                quests.append((qid, st))
                p = f_idx + 40
            
            completed = [q for q, st in quests if st == 3]
            in_prog = [q for q, st in quests if st == 2]
            not_started = [q for q, st in quests if st == 0]
            print(f"[*] เควสหลักใน questMap_   : ทั้งหมด {len(quests)} เควส")
            print(f"    - สำเร็จแล้ว (Completed): {len(completed)} เควส")
            print(f"    - ค้างอยู่/กำลังทำ (In Progress): {len(in_prog)} เควส -> {in_prog}")
            if not_started:
                print(f"    - ยังไม่ได้รับ (Not Started): {len(not_started)} เควส -> {not_started}")
        else:
            print("[*] เควสหลักใน questMap_   : 0 เควส (ยังไม่ได้เริ่มเควสใดๆ)")
    else:
        print("[*] เควสหลักใน questMap_   : 0 เควส")

def main():
    if len(sys.argv) < 2:
        print("วิธีใช้งาน:")
        print("  1. ตรวจสอบข้อมูลเซฟ:")
        print("     python save_tool.py inspect <path_to_save_file>")
        print("  2. คลายบีบอัดเป็นไฟล์ดิบ (Decompress):")
        print("     python save_tool.py unpack <path_to_save_file> [output_file]")
        print("  3. บีบอัดกลับเป็นเซฟเกม (Compress):")
        print("     python save_tool.py pack <path_to_raw_file> <output_save_file>")
        return

    cmd = sys.argv[1].lower()
    if cmd == 'inspect':
        inspect_save(sys.argv[2])
    elif cmd == 'unpack':
        src = sys.argv[2]
        dst = sys.argv[3] if len(sys.argv) > 3 else src + ".raw"
        with open(src, 'rb') as f:
            decomp, _ = decompress_ykcmp(f.read())
        with open(dst, 'wb') as f:
            f.write(decomp)
        print(f"[SUCCESS] คลายบีบอัดสำเร็จ! บันทึกที่: {dst} ({len(decomp):,} bytes)")
    elif cmd == 'pack':
        src = sys.argv[2]
        dst = sys.argv[3]
        with open(src, 'rb') as f:
            comp = compress_ykcmp(f.read())
        with open(dst, 'wb') as f:
            f.write(comp)
        print(f"[SUCCESS] บีบอัดสำเร็จ! บันทึกที่: {dst} ({len(comp):,} bytes)")

if __name__ == '__main__':
    main()
