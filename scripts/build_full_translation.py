import os
import json
import time

def main():
    t0 = time.time()
    
    dev_dir = r"C:\Users\Supakiat\Desktop\Village_in_the_Shade_ThaiMod_Dev"
    master_txt = os.path.join(dev_dir, "ตารางจับคู่คำแปล_ไทย_JP.txt")
    mapping_path = r"C:\Users\Supakiat\Desktop\Mover\out\Mapping.json"
    
    mod_dir = r"C:\Program Files (x86)\Steam\steamapps\common\Village in the Shade\Mods\TextDump"
    out_trans_path = os.path.join(mod_dir, "translation.txt")
    bak_trans_path = os.path.join(mod_dir, "translation.txt.bak")
    dev_trans_pua = os.path.join(dev_dir, "translation_PUA.txt")

    if not os.path.exists(master_txt):
        print(f"Error: ไม่พบไฟล์ตารางคำแปลหลัก {master_txt}")
        return

    # Backup existing translation.txt if not already backed up
    if os.path.exists(out_trans_path) and not os.path.exists(bak_trans_path):
        with open(out_trans_path, "rb") as f_src, open(bak_trans_path, "wb") as f_dst:
            f_dst.write(f_src.read())
        print(f"สำรองไฟล์เดิมไว้ที่: {bak_trans_path}")

    # Load Mapping.json for Thai PUA conversion
    with open(mapping_path, "r", encoding="utf-8-sig") as f:
        mapping = json.load(f)

    max_len = max(len(k) for k in mapping.keys())
    def to_pua(text):
        if not text:
            return text
        result, i, n = [], 0, len(text)
        while i < n:
            matched = False
            for l in range(min(max_len, n - i), 0, -1):
                sub = text[i:i+l]
                if sub in mapping:
                    result.append(mapping[sub])
                    i += l
                    matched = True
                    break
            if not matched:
                result.append(text[i])
                i += 1
        return "".join(result)

    print("=" * 70)
    print("เริ่มแปลงคำแปลภาษาไทยเป็นรหัสฟอนต์ PUA (สระไม่ลอย)...")
    print(f"อ่านข้อมูลจาก: {master_txt}")
    print("=" * 70)

    count = 0
    pua_lines = []
    
    with open(master_txt, "r", encoding="utf-8") as f:
        for line in f:
            line_str = line.strip()
            if not line_str or line_str.startswith("#") or "=" not in line_str:
                continue
            jp, th = line_str.split("=", 1)
            jp = jp.strip()
            th = th.strip()
            if not jp or not th:
                continue
            
            # Convert Thai translation to PUA
            th_pua = to_pua(th)
            pua_lines.append(f"{jp}={th_pua}\n")
            count += 1

    # Write to dev folder
    with open(dev_trans_pua, "w", encoding="utf-8") as f:
        f.writelines(pua_lines)
    print(f"บันทึกไฟล์ PUA สำเร็จที่: {dev_trans_pua}")

    # Write to game mod folder
    if os.path.exists(mod_dir):
        with open(out_trans_path, "w", encoding="utf-8") as f:
            f.writelines(pua_lines)
        print(f"ติดตั้งลงในม็อดเกมสำเร็จที่: {out_trans_path}")

    t1 = time.time()
    print("=" * 70)
    print(f"สร้างและติดตั้ง translation.txt สำเร็จเรียบร้อย!")
    print(f"จำนวนคู่คำแปลที่แปลงและติดตั้ง: {count:,} คู่")
    print(f"เวลาที่ใช้: {t1 - t0:.2f} วินาที")
    print("=" * 70)

if __name__ == "__main__":
    main()
