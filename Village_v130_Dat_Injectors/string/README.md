# เอกสารบันทึกโครงสร้างไฟล์ string.dat สูตรปลอดภัย (Safe Date/Season Edition)

> **สถานะ:** ใช้งานจริงในม็อดภาษาไทย (Active Deployment)  
> **ไฟล์เป้าหมาย:** `C:\Program Files (x86)\Steam\steamapps\common\Village in the Shade\Mods\dat_ja\string.dat`  
> **ขนาดไฟล์:** `133,446 ไบต์` (133 KB)  
> **จำนวนข้อความทั้งหมด:** 408 แถว  

---

## 1. ที่มาและหลักการความปลอดภัยต่อเอนจินเกม (Engine Safety)

ในเอนจินเกม *Village in the Shade* ฟังก์ชันการจัดการระบบปฏิทิน วันที่ ฤดูกาล และการตรวจสอบชื่อไฟล์เซฟของระบบ จะมีการเรียกอ่าน String Identifier โดยตรง หากมีการเปลี่ยนตำแหน่งโทเค็น `<value>` หรือเปลี่ยนข้อความตัวระบุของระบบเซฟ/วันที่ ตัวเอนจินเกมจะทำงานผิดพลาดและเกิดอาการแคลช (Crash) ขณะโหลดเซฟหรือเปลี่ยนวัน

**สูตรปลอดภัย (Safe Date/Season Edition):**
- **คงข้อความต้นฉบับภาษาญี่ปุ่น (JP) แท้เดิม 100% จำนวน 66 แถว** ในส่วนที่เกี่ยวข้องกับระบบเวลา วันที่ ฤดูกาล และคีย์เซฟระบบ เพื่อให้เอนจินอ่านค่าได้ถูกต้องตามสเปกเดิม 100% ไม่หลุดหรือเด้งออกจากเกม
- **แปลภาษาไทยสมบูรณ์แบบจำนวน 342 แถวที่เหลือ** ครอบคลุม UI เมนู ปุ่มกดยืนยัน หน้าต่างเซฟ/โหลด สารานุกรม และข้อความระบบทั้งหมด

---

## 2. รายละเอียดข้อความคงต้นฉบับแท้เดิม (JP) ทั้งหมด 66 แถว

### 2.1 ฟอร์แมตวันที่และเวลา (Date & Time Format)
- `STR_ID_DATE_FORMAT` $\rightarrow$ `<value 1>年目 <value 2> <value 3>日`  
  *(คงรูปแบบ token เพื่อให้เอนจินประมวลผล ปี/ฤดู/วัน ได้เป๊ะโดยไม่เลื่อนตำแหน่ง)*
- `STR_ID_DATE_LATENIGHT` $\rightarrow$ `　深夜` *(ช่วงเวลากลางดึก)*
- `STR_ID_DATE_SPRING_SEASON` $\rightarrow$ `春の月`
- `STR_ID_DATE_SUMMER_SEASON` $\rightarrow$ `夏の月`
- `STR_ID_DATE_AUTUMN_SEASON` $\rightarrow$ `秋の月`
- `STR_ID_DATE_WINTER_SEASON` $\rightarrow$ `冬の月`

### 2.2 ฤดูกาลทั้ง 4 (4 Seasons)
- `STR_ID_SEASON_SPRING` $\rightarrow$ `春`
- `STR_ID_SEASON_SUMMER` $\rightarrow$ `夏`
- `STR_ID_SEASON_AUTUMN` $\rightarrow$ `秋`
- `STR_ID_SEASON_WINTER` $\rightarrow$ `冬`

### 2.3 วันในสัปดาห์ (Days of Week)
- `STR_ID_WEEK_MONDAY` $\rightarrow$ `月` (จันทร์)
- `STR_ID_WEEK_TUESDAY` $\rightarrow$ `火` (อังคาร)
- `STR_ID_WEEK_WEDNESDAY` $\rightarrow$ `水` (พุธ)
- `STR_ID_WEEK_THURSDAY` $\rightarrow$ `木` (พฤหัสบดี)
- `STR_ID_WEEK_FRIDAY` $\rightarrow$ `金` (ศุกร์)
- `STR_ID_WEEK_SATURDAY` $\rightarrow$ `<c blue>土</c>` (เสาร์ - กำกับโค้ดสีน้ำเงิน)
- `STR_ID_WEEK_SUNDAY` $\rightarrow$ `<c red>日</c>` (อาทิตย์ - กำกับโค้ดสีแดง)

### 2.4 คีย์ระบบระบุไฟล์เซฟ (Save System Identifiers)
- `STR_ID_SAVE_FILE_NAME` $\rightarrow$ `save<value 1>`
- `STR_ID_SAVE_FILE_LIST_DISP_NAME` $\rightarrow$ `save<value 1>`
- `STR_ID_SAVE_FILE_NAME_BASE` $\rightarrow$ `save`
- `STR_ID_SYSTEM_SAVE_FILE_NAME` $\rightarrow$ `.systemsave`
- ตัวแปรระบุ slot และ path เช็คสถานะไฟล์เซฟดั้งเดิมทั้งหมด

---

## 3. รายละเอียดข้อความแปลภาษาไทยครบถ้วน (342 แถวที่เหลือ)

- **ปุ่มยืนยันระบบ:** `ใช่`, `ไม่`, `ไม่ใช่`
- **หน้าต่างจัดการเซฟ:**
  - `ต้องการบันทึกข้อมูลหรือไม่?`
  - `ต้องการโหลดข้อมูลบันทึกนี้หรือไม่?`
  - `ข้อมูลบันทึก Village in the Shade`
  - `บันทึกข้อมูลเรียบร้อยแล้ว`
  - `โหลดข้อมูลเรียบร้อยแล้ว`
- **เมนูและตัวเลือก:** ตัวเลือกกราฟิก, เสียง, การควบคุม, ปุ่มลัด, ภาษา
- **สารานุกรมและระบบช่วยเหลือ:** คู่มือการทำฟาร์ม, สารานุกรมไอเทม, ปลา, แมลง, พืชผล
- **ข้อความระบบอื่นๆ:** คำเตือนการเล่น, คำอธิบายฟังก์ชัน, ป๊อปอัปแจ้งเตือนทั้งหมด

---

## 4. โครงสร้างไฟล์และขนาดเปรียบเทียบ

| รายการ | รายละเอียด |
| :--- | :--- |
| **Path ติดตั้งในเกม** | `Village in the Shade\Mods\dat_ja\string.dat` |
| **ขนาดไฟล์** | `133,446 ไบต์` |
| **จำนวนแถวปลอดภัย (JP)** | 66 แถว |
| **จำนวนแถวแปลไทย (TH)** | 342 แถว |
| **รวมทั้งหมด** | 408 แถว |
| **ผลการทดสอบ** | เปิดเกม กดโหลดเซฟ ข้ามวัน เปลี่ยนฤดู **ไม่เด้ง ไม่แคลช 100%** |
