import os
import sys
import time

# นำเข้าโมดูล csv_to_pua_gui จาก C:\Users\Supakiat\Desktop\Mover\out
mover_out_dir = r"C:\Users\Supakiat\Desktop\Mover\out"
if mover_out_dir not in sys.path:
    sys.path.insert(0, mover_out_dir)

import csv_to_pua_gui

def main():
    t0 = time.time()
    
    dev_dir = r"C:\Users\Supakiat\Desktop\Village_in_the_Shade_ThaiMod_Dev"
    master_txt = os.path.join(dev_dir, "ตารางจับคู่คำแปล_ไทย_JP.txt")
    mapping_path = os.path.join(mover_out_dir, "Mapping.json")
    
    plugin_mod_dir = r"C:\Program Files (x86)\Steam\steamapps\common\Village in the Shade\Mods\TextDump"
    plugin_trans_path = os.path.join(plugin_mod_dir, "translation.txt")
    dev_trans_pua = os.path.join(dev_dir, "translation_PUA.txt")

    if not os.path.exists(master_txt):
        print(f"[ERROR] ไม่พบไฟล์ตารางคำแปล: {master_txt}")
        return

    print("=" * 70)
    print("เริ่มแปลงตารางคำแปลเป็นรหัส PUA ด้วย csv_to_pua_gui.py...")
    print(f"ไฟล์ต้นทาง: {master_txt}")
    print(f"ไฟล์ Mapping: {mapping_path}")
    print("=" * 70)

    # โหลด Mapping โดยใช้ฟังก์ชันของ csv_to_pua_gui
    mapping = csv_to_pua_gui.load_mapping(mapping_path)
    max_len = max(len(k) for k in mapping)
    print(f"โหลด Mapping สำเร็จ: {len(mapping):,} รายการ (ความยาวสูงสุด: {max_len})")

    # อ่านและแปลงคำแปล
    pua_lines = []
    total_count = 0

    with open(master_txt, "r", encoding="utf-8") as f_in:
        for line in f_in:
            line_str = line.strip()
            if not line_str or line_str.startswith("#") or "=" not in line_str:
                continue
            jp, th = line_str.split("=", 1)
            jp = jp.strip()
            th = th.strip()
            if not jp or not th:
                continue

            # แปลงข้อความไทยด้วยฟังก์ชัน convert_text_to_pua ของ csv_to_pua_gui
            th_pua = csv_to_pua_gui.convert_text_to_pua(th, mapping, max_len)
            pua_lines.append(f"{jp}={th_pua}\n")
            total_count += 1

    # บันทึกไฟล์ PUA ในโฟลเดอร์ Dev
    with open(dev_trans_pua, "w", encoding="utf-8") as f_out:
        f_out.writelines(pua_lines)
    print(f"บันทึกไฟล์ PUA สำเร็จที่: {dev_trans_pua}")

    # ติดตั้งใส่ในโฟลเดอร์ปลั๊กอิน Mods\TextDump\translation.txt
    if os.path.exists(plugin_mod_dir):
        with open(plugin_trans_path, "w", encoding="utf-8") as f_mod:
            f_mod.writelines(pua_lines)
        print(f"ติดตั้งใส่ในปลั๊กอินสำเร็จที่: {plugin_trans_path}")
    else:
        print(f"[WARNING] ไม่พบโฟลเดอร์ปลั๊กอิน: {plugin_mod_dir}")

    t1 = time.time()
    print("=" * 70)
    print(f"แปลงและใส่ในปลั๊กอินเสร็จสิ้นสมบูรณ์!")
    print(f"จำนวนคู่คำแปลทั้งหมด: {total_count:,} คู่")
    print(f"เวลาที่ใช้: {t1 - t0:.2f} วินาที")
    print("=" * 70)

if __name__ == "__main__":
    main()
