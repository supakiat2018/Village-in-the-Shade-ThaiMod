# กฎเหล็กตำแหน่งไฟล์ Config ของม็อด: settings.ini และ cheats.ini

> **กฎถาวร (Permanent Architectural Rule):**  
> ไฟล์ตั้งค่าการทำงานของม็อดทั้งหมด **ต้องอยู่ในโฟลเดอร์ `Mods\` เท่านั้น!**  
> **ห้ามนำไฟล์ `settings.ini` หรือ `cheats.ini` ออกมาวางไว้ที่โฟลเดอร์เกมหลัก (Root ข้าง `village.exe`) เด็ดขาด!**

---

## 1. ตำแหน่งไฟล์ที่ถูกต้อง (Standard Structure)

```text
📁 Village in the Shade/ (โฟลเดอร์เกมหลัก)
 ├── village.exe                       (ตัวเกมแท้ของ Steam)
 ├── winmm.dll                         (ตัวโหลดม็อด Proxy DLL)
 └── 📁 Mods/                          (โฟลเดอร์ม็อดหลัก)
      ├── settings.ini                 <-- [ตำแหน่งจริง] ตั้งค่าม็อดภาษาไทย, ฟอนต์, คีย์บอร์ด
      ├── cheats.ini                   <-- [ตำแหน่งจริง] ตั้งค่าสูตรโกง, ปุ่มลัด, Speedhack
      ├── 📁 dat_ja/                   (Database ภาษาไทยสำหรับโหมด JP)
      ├── 📁 dat_en/                   (Database ภาษาไทยสำหรับโหมด EN)
      ├── 📁 TextDump/                 (text_dump.dll และ Textures)
      └── 📁 translations/             (41_string.txt ข้อความระบบ)
```

---

## 2. ลำดับความสำคัญในการอ่านของโค้ด DLL (Priority 1)

โค้ด C ของม็อดทั้งใน `src/cheats.c` และ `src/text_dump.c` กำหนดให้อ่านค่าจาก:
1. **อันดับ 1 (Primary):** `Mods\settings.ini` และ `Mods\cheats.ini`
2. **อันดับ 2 (Fallback เท่านั้น):** หากไม่มีใน `Mods\` จึงจะไปมองหาที่ Root

**ข้อควรระวัง:** หากมีไฟล์ `settings.ini` หรือ `cheats.ini` ตกค้างอยู่ที่โฟลเดอร์นอก (Root) ตัวสคริปต์ `deploy` และโค้ดจะทำการลบไฟล์ตกค้างข้างนอกทิ้งทันที เพื่อป้องกันการสับสนว่าต้องแก้ไขไฟล์ไหน

---

## 3. สรุปความรับผิดชอบของแต่ละไฟล์

| ชื่อไฟล์ | ตำแหน่งที่ถูกต้อง | หน้าที่การทำงาน |
| :--- | :--- | :--- |
| **`settings.ini`** | `Mods\settings.ini` | ควบคุมสวิตช์ม็อดหลัก (`enable_thai_mod`), การจัดช่องไฟฟอนต์ (`enable_proportional_font`), แป้นพิมพ์เสมือนไทย (`enable_thai_keyboard`), มินิแมพไทย (`enable_thai_minimap`), และการบังคับฐานข้อมูล JP |
| **`cheats.ini`** | `Mods\cheats.ini` | ควบคุมระบบสูตรโกง (ไอเทมไม่ลด, เลือดไม่ลด, ปลดล็อกความเร็ว Speedhack F4/F5/F6, ล็อกเวลา F3) |

---

## 4. บันทึกคำเตือนสำหรับระบบและ Agent (Antigravity Instruction)

> [!CAUTION]
> **ห้ามสร้างหรือก๊อปปี้ไฟล์ `settings.ini` และ `cheats.ini` ออกมาที่ root game directory (`Village in the Shade\`) โดยเด็ดขาด!**  
> ไฟล์ทั้งสองต้องมีอยู่เพียงชุดเดียวในโฟลเดอร์ `Mods\` เท่านั้น!  
> เมื่อทำการบิลด์ (Build) หรือแจกจ่าย (Package ZIP) ให้เก็บไว้ใน `Mods\` เสมอ
