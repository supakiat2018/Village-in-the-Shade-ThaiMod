# คู่มือการสร้างและเปลี่ยนระบบคีย์บอร์ดในเกมเป็นภาษาไทย (Keyboard Thai Mod Architecture)

เอกสารนี้อธิบายโครงสร้างและขั้นตอนการดัดแปลงระบบคีย์บอร์ดพิมพ์ชื่อ (Virtual Keyboard / On-Screen Keyboard) ของเกม **Village in the Shade (v1.20)** ให้สามารถแสดงผลและพิมพ์เป็น **ภาษาไทยมาตรฐาน (Standard UTF-8 Thai)** ได้อย่างสมบูรณ์

---

## 1. ที่มาและปัญหาเดิม (Background & Challenges)

1. **ปัญหาฟอนต์และ PUA:**
   - ก่อนหน้านี้เคยมีความพยายามนำฟอนต์แบบ PUA (Private Use Area) มาใช้ แต่ส่งผลให้สระและวรรณยุกต์แสดงผลไม่ถูกต้อง และชื่อที่บันทึกลง Save Game กลายเป็นรหัสพิเศษ
   - ความจริงตัวเกมมีระบบเรนเดอร์ข้อความ UTF-8 ที่รองรับภาษาไทยมาตรฐานอยู่แล้ว หากใช้ฟอนต์อย่าง `Lora-Bold.ttf`
2. **ระบบพิมพ์ชื่อเดิมของตัวเกม:**
   - ตัวเกมไม่ได้ใช้การรับ Input คีย์บอร์ดคอมพิวเตอร์โดยตรง แต่ใช้ **On-Screen Virtual Keyboard UI**
   - แป้นพิมพ์แบ่งการทำงานออกเป็น **2 ชั้น (2 Independent Layers)**:
     - **ชั้นที่ 1 (Logic & Data):** ตารางข้อความในตัว `village.exe` ว่าเมื่อคลิกปุ่มนี้จะส่ง String อะไรเข้าตัวแปรชื่อ (Input Buffer)
     - **ชั้นที่ 2 (Visual Display):** ภาพ Spritesheet ตัวอักษรบนหน้าปุ่มที่ถูกดึงมาจากไฟล์ `resident_lang_jp.fad`

หากแก้เพียงภาพ ปุ่มก็จะยังคงพิมพ์ภาษาญี่ปุ่นลงไปในชื่อตัวละคร หรือหากแก้เพียงตัวโปรแกรม แต่ไม่แก้ภาพ ผู้เล่นก็จะมองไม่เห็นตัวอักษรไทยบนแป้นพิมพ์ ดังนั้นจึงต้องแก้ไขทั้งสองชั้นให้สอดคล้องกัน

---

## 2. ชั้นที่ 1: การแพตช์ระบบประมวลผลการพิมพ์ใน RAM (`village.exe`)

### 2.1 การวิเคราะห์ Assembly
ใน `village.exe` (Steam v1.20) คลาสที่จัดการหน้าต่างพิมพ์ชื่อคือ `CTask_Menu_StringInput` (RVA `0x403290` ถึง `0x405500`):
- แป้นพิมพ์มี 2 หน้าหลัก (Page 1 เดิมคือ Hiragana, Page 2 เดิมคือ Katakana)
- แต่ละหน้ามีปุ่มทั้งหมด **91 ปุ่ม** (13 แถว แถวละ 7 ปุ่ม) รวมเป็น **182 ปุ่ม**
- ใน Memory ของ `village.exe` จะมีคำสั่ง `memcpy` หรือ `mov` เขียน String สั้นๆ (ขนาดไม่เกิน 4 ไบต์: ตัวอักษร UTF-8 1-3 ไบต์ + `\0`) ลงใน Object ของปุ่มแต่ละปุ่ม

### 2.2 การสร้างตารางแป้นพิมพ์ภาษาไทย
เราพัฒนาสคริปต์ [`scripts/build_keyboard_v120_patch.py`](scripts/build_keyboard_v120_patch.py) และสร้าง Header [`src/keyboard_v120_patch.h`](src/keyboard_v120_patch.h):
- **หน้า 1 (Consonants / พยัญชนะ):**
  - แถวที่ 1-7: พยัญชนะ ก ถึง ฮ ทั้งหมด 44 ตัว
  - แถวที่ 8-13: ตัวเลขไทย (๐-๙) และเครื่องหมายทั่วไป
- **หน้า 2 (Vowels & Tone Marks / สระและวรรณยุกต์):**
  - สระหน้า สระหลัง สระบน สระล่าง (ะ, า, ิ, ี, ึ, ื, ุ, ู, เ, แ, โ, ใ, ไ, ฯลฯ)
  - วรรณยุกต์ (่, ้, ๊, ๋) และไม้ทัณฑฆาต (์)
  - ตัวเลขเลขอารบิก (0-9) และสัญลักษณ์

### 2.3 การแพตช์ Memory แบบ Dynamic Pattern Scanning (รองรับทุกเวอร์ชัน)
เดิมทีตัวแพตช์ใช้ RVA แบบตายตัว (Hardcoded RVA สำหรับ v1.20) แต่เมื่อนำไปตรวจสอบกับเวอร์ชันอื่น (เช่น `village.exe` เวอร์ชันเก่า) พบว่าตำแหน่ง RVA ใน `.rdata` มีการเลื่อนไปตามขนาดโค้ดของแต่ละ Build
เราจึงพัฒนาฟังก์ชัน `patch_virtual_keyboard_in_memory()` ใน [`src/keyboard_v120_patch.h`](src/keyboard_v120_patch.h) ให้ใช้ระบบ **Dynamic Signature / Pattern Scanning**:
1. สแกนหา Anchor Pattern ที่เป็นเอกลักษณ์เฉพาะของตารางแป้นพิมพ์ คือลำดับไบต์ `"あ\0" + "い\0" + "う\0"` (`\xE3\x81\x82\x00\xE3\x81\x84\x00\xE3\x81\x86\x00`) ภายใน Section `.rdata` ใน RAM ของตัวเกม
2. เมื่อพบตำแหน่ง Anchor จะคำนวณตำแหน่งของปุ่มทั้ง 182 ปุ่มด้วย Relative Offset ทันที (เนื่องจากระยะห่างระหว่างปุ่มในตารางเหมือนกัน 100% ในทุกเวอร์ชัน)
3. หากสแกนไม่พบ จะมีระบบ Fallback ไปใช้ค่าเริ่มต้นของ Steam v1.20 อัตโนมัติ
4. ปลดสิทธิ์ Memory ด้วย `VirtualProtect` และเขียนทับไบต์ UTF-8 ของภาษาไทยลงไปใน RAM

ผลลัพธ์: ทำให้ตัวม็อดรองรับการพิมพ์ภาษาไทยได้บน `village.exe` **ทุกเวอร์ชัน** โดยไม่ต้องคอมไพล์ใหม่เมื่อเกมอัปเดต!

---

## 3. ชั้นที่ 2: การดัดแปลงและแปลงภาพแป้นพิมพ์ (`resident_lang_jp.fad`)

### 3.1 การค้นหาภาพ Spritesheet
- ตัวเกมเก็บ UI Asset ทั้งหมดไว้ในไฟล์ `data/fairy_1_00.dat` ภายใน Container ชื่อ `resident_lang_jp.fad` (Offset `0x425B9400`, ขนาดประมาณ 247 MB)
- เราใช้สคริปต์ [`scripts/extract_all_resident_lang_jp.py`](scripts/extract_all_resident_lang_jp.py) แตก Texture ทั้งหมด 404 รูปออกมาที่โฟลเดอร์ `คียบอด/`
- ตรวจพบว่าไฟล์ **`tex_113_1024x2048.png`** (ขนาด 1024x2048 พิกเซล) คือ Spritesheet ของตัวอักษรบนปุ่มคีย์บอร์ดทั้งหมด:
  - พิกัด `Y < 755`: ตัวอักษรญี่ปุ่น 182 ช่อง (13 แถว x 14 คอลัมน์)
  - พิกัด `Y >= 755`: ตัวอักษรละติน (A-Z, a-z) และสัญลักษณ์พิเศษ

### 3.2 การตัดต่อและเรนเดอร์ตัวอักษรไทย
ใช้สคริปต์ [`scripts/generate_thai_keyboard_texture.py`](scripts/generate_thai_keyboard_texture.py):
1. สำรองภาพเดิมไว้ที่ `คียบอด/tex_113_1024x2048_backup.png`
2. ลบตัวอักษรญี่ปุ่นเดิมในพื้นที่ `Y < 755` โดยถมสีโปร่งใส `(0, 0, 0, 0)` ให้พื้นหลังคงความใส 100%
3. ใช้ฟอนต์ `Lora-Bold.ttf` ขนาด 32pt สี `#D2D2D2` (RGB: 210, 210, 210) วาดตัวอักษรไทยลงตรงกึ่งกลางของแต่ละช่องปุ่ม (คำนวณจาก Bounding Box ของตัวอักษรเดิมอย่างแม่นยำ)
4. คงตัวอักษรละตินและสัญลักษณ์พิเศษด้านล่างไว้เหมือนเดิม

### 3.3 การแพ็กเป็นไฟล์ `.nltx`
ใช้สคริปต์ [`scripts/pack_thai_keyboard_texture.py`](scripts/pack_thai_keyboard_texture.py):
1. รัน `texconv.exe -f BC7_UNORM -m 1` แปลง PNG เป็น DirectDraw Surface (BC7 Block Compression)
2. บีบอัดข้อมูล BC7 ด้วย **LZ4 (High Compression)** พร้อมใส่ Header `YKCMP_V1` Type 9
3. ใส่ Header มาตรฐาน `NMPLTEX1` (128 ไบต์):
   - Format: `0x66` (BC7)
   - Width / Height: 1024 / 2048
   - บีบอัดเหลือเพียง 71,272 ไบต์

---

## 4. ชั้นที่ 3: ระบบ VFS Redirection สำหรับเชื่อมภาพเข้าสู่เกม

ในไฟล์ [`src/text_dump.c`](src/text_dump.c) มีระบบ VFS Interception ของ Hook `ReadFile`:
1. **การจับคู่ TOC Index:**
   - เมื่อวิเคราะห์โครงสร้าง TOC ของ `resident_lang_jp.fad` พบว่า `tex_113` อยู่ที่ **TOC Index 110** (Offset สัมพัทธ์ `0x04AF98B0`)
2. **การลงทะเบียนใน `g_fad_mapping_defs`:**
   ```c
   { 110, "ui_keyboard_font.nltx", "ui_keyboard_font_thai.nltx", 1024, 2048 },
   ```
3. **การส่งต่อข้อมูลแบบ Dynamic:**
   - เมื่อเกมส่งคำสั่งอ่านข้อมูลที่ Offset ของ TOC 110 ตัว Hook ใน `text_dump.dll` จะขยายขนาด TOC Size ใน RAM อัตโนมัติ และสลับนำเนื้อหาของ `ui_keyboard_font.nltx` ส่งกลับไปให้ Game Engine แทนข้อมูลเดิมในแผ่นไฟล์ `.dat`

---

## 5. การคอมไพล์และติดตั้ง (Build & Deployment)

1. คอมไพล์ด้วย Zig CC:
   ```cmd
   zig cc -shared -O2 -s src\text_dump.c src\addrsig.c src\cheats.c src\minhook-master\src\buffer.c src\minhook-master\src\hook.c src\minhook-master\src\trampoline.c src\minhook-master\src\hde\hde64.c -o bin\text_dump.dll -lkernel32 -luser32 -lgdi32
   ```
2. คัดลอกไฟล์ที่ติดตั้งไปยังตัวเกม Steam:
   - DLL: `Steam\steamapps\common\Village in the Shade\Mods\TextDump\text_dump.dll`
   - Textures: `Steam\steamapps\common\Village in the Shade\Mods\TextDump\textures\ui_keyboard_font.nltx`
