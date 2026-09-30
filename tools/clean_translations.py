import os
import glob
import re
import time

def main():
    t0 = time.time()
    
    pc_dir = r"C:\Users\Supakiat\Desktop\คลังคำแปล_Village_in_the_Shade\01_PC"
    game_trans = r"C:\Program Files (x86)\Steam\steamapps\common\Village in the Shade\Mods\TextDump\translation.txt"
    dev_trans = r"C:\Users\Supakiat\Desktop\Village_in_the_Shade_ThaiMod_Dev\translation.txt"
    log_removed = r"C:\Users\Supakiat\Desktop\Village_in_the_Shade_ThaiMod_Dev\translation_removed_log.txt"
    
    mod_dat_categories = {'cmd', 'gameSetting', 'letter', 'talk'}
    
    print("=" * 70)
    print(" กำลังโหลดฐานข้อมูลคำแปลจาก 01_PC เพื่อคัดแยกหมวดหมู่...")
    print("=" * 70)
    
    dat_keys = set()
    other_keys = set()
    category_counts = {}
    
    for f in sorted(glob.glob(os.path.join(pc_dir, "*.txt"))):
        bname = os.path.basename(f)
        cat = bname.split('_')[0]
        count = 0
        with open(f, 'r', encoding='utf-8') as fp:
            for line in fp:
                line = line.strip()
                if not line or line.startswith('#') or '=' not in line:
                    continue
                jp = line.split('=', 1)[0].strip()
                if not jp:
                    continue
                count += 1
                if cat in mod_dat_categories:
                    dat_keys.add(jp)
                else:
                    other_keys.add(jp)
        category_counts[cat] = count
        
    print(f"หมวดที่ทำเป็น .dat แล้ว (talk, letter, cmd, gameSetting): {len(dat_keys):,} คำ")
    print(f"หมวดอื่นๆ อีก 31 ไฟล์ (item, crops, quest, string ฯลฯ): {len(other_keys):,} คำ")
    
    overlap = dat_keys.intersection(other_keys)
    print(f"คำที่ใช้ร่วมกัน (คงไว้ใน translation.txt เพื่อความปลอดภัย): {len(overlap):,} คำ")
    
    safe_to_remove = dat_keys - other_keys
    print(f"คำที่ย้ายลง .dat ครบ 100% และปลอดภัยที่จะลบ: {len(safe_to_remove):,} คำ")
    
    print("\n" + "=" * 70)
    print(" กำลังอ่านและคัดกรอง translation.txt...")
    print("=" * 70)
    
    kept_lines = []
    removed_records = []
    seen_keys = set()
    
    with open(game_trans, 'r', encoding='utf-8') as fp:
        for line in fp:
            raw_line = line.rstrip('\r\n')
            line_str = raw_line.strip()
            
            # บรรทัดว่าง หรือ Comment ให้คงไว้
            if not line_str or line_str.startswith('#'):
                kept_lines.append(raw_line)
                continue
                
            if '=' not in line_str:
                kept_lines.append(raw_line)
                continue
                
            jp, th = line_str.split('=', 1)
            jp_clean = jp.strip()
            if '[SCALE:' in jp_clean:
                jp_clean = re.sub(r'\[SCALE:[^\]]+\]', '', jp_clean).strip()
                
            # 1. คำแปลค่าว่าง
            if th.strip() == '':
                removed_records.append(f"[EMPTY] {jp}=")
                continue
                
            # 2. คำอันตราย (เช่น で ที่แปลเป็นค่าว่าง)
            if jp_clean == 'で':
                removed_records.append(f"[HARMFUL] {jp}={th}")
                continue
                
            # 3. คำที่อยู่ใน .dat แล้ว และไม่ได้แชร์กับหมวดอื่น
            if jp_clean in safe_to_remove:
                removed_records.append(f"[IN_DAT] {jp}={th}")
                continue
                
            # 4. คีย์ซ้ำซ้อน
            if jp in seen_keys:
                removed_records.append(f"[DUPLICATE] {jp}={th}")
                continue
                
            seen_keys.add(jp)
            kept_lines.append(raw_line)
            
    print(f"จำนวนบรรทัดเดิมทั้งหมด: {len(kept_lines) + len(removed_records):,} บรรทัด")
    print(f"จำนวนบรรทัดที่ลบออก: {len(removed_records):,} บรรทัด")
    print(f"จำนวนบรรทัดที่คงไว้: {len(kept_lines):,} บรรทัด")
    
    # บันทึกไฟล์ log ของคำที่ลบออก
    with open(log_removed, 'w', encoding='utf-8') as fp:
        fp.write(f"# บันทึกรายการคำแปลที่ถูกคัดกรองออกจาก translation.txt ({len(removed_records):,} รายการ)\n")
        fp.write("# สร้างเมื่อ: " + time.strftime("%Y-%m-%d %H:%M:%S") + "\n\n")
        for rec in removed_records:
            fp.write(rec + "\n")
    print(f"\nบันทึกประวัติคำที่ลบออกไว้ที่: {log_removed}")
    
    # เขียนไฟล์ translation.txt ในเกม
    with open(game_trans, 'w', encoding='utf-8') as fp:
        for l in kept_lines:
            fp.write(l + "\n")
    print(f"อัปเดต translation.txt (เกม): {game_trans}")
    
    # เขียนไฟล์ translation.txt ใน Dev
    with open(dev_trans, 'w', encoding='utf-8') as fp:
        for l in kept_lines:
            fp.write(l + "\n")
    print(f"อัปเดต translation.txt (Dev): {dev_trans}")
    
    t1 = time.time()
    print("=" * 70)
    print(f"คัดกรองและบันทึกเสร็จสมบูรณ์ในเวลา {t1 - t0:.2f} วินาที!")
    print("=" * 70)

if __name__ == "__main__":
    main()
