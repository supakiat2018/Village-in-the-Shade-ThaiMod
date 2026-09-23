# Village in the Shade (ほのぐらしの庭) - ม็อดภาษาไทย (Thai Localization Mod)

ม็อดแปลภาษาไทยสมบูรณ์แบบสำหรับเกม **Village in the Shade (ほのぐらしの庭)** เวอร์ชัน PC Steam  
พัฒนาด้วยระบบ C In-Memory Text Hooking, Virtual File System (VFS) และระบบฟอนต์ภาษาไทย PUA สระไม่ลอย

---

## 🌟 ฟีเจอร์เด่นของม็อด (Features)

- ✅ **แปลภาษาไทยสมบูรณ์:** ครอบคลุมบทสนทนา, เควสต์, ป้ายร้านค้า, เมนู และไอเทมกว่า **47,950 บรรทัด**
- ✅ **ระบบฟอนต์ PUA วรรณยุกต์ไม่ลอย:** ตัวอักษรคมชัด ไม่ซ้อนทับ อ่านง่าย สบายตา
- ✅ **ภาพอินเตอร์เฟซแปลไทย 70 ภาพ:** ป้ายร้าน, เมนู, แผนที่, ป้ายประกาศ และ UI หลักทั้งหมด
- ✅ **ทำงานในหน่วยความจำ RAM:** ไม่แก้ไขไฟล์ `.exe` หรือไฟล์ `.dat` ของแท้จาก Steam ปลอดภัย 100%
- ✅ **ระบบตรวจจับคำตกหล่นอัตโนมัติ (Missing Text Auto-Logger):** ดักจับคำแปลที่ยังขาดเพื่อพัฒนาต่อได้ง่าย

---

## 📂 โครงสร้างโปรเจกต์ (Repository Contents)

```
Village-in-the-Shade-ThaiMod/
├── src/                    # ซอร์สโค้ดภาษา C ทั้งหมด (text_dump.c, MinHook, AddrSig)
├── build.bat               # สคริปต์คอมไพล์ซอร์สโค้ด (คอมไพล์ด้วย zig cc)
├── tools/                  # เครื่องมือสร้างและแปลงตารางคำแปล
├── steam_api64.dll         # ตัวโหลดปลั๊กอิน (Proxy Loader)
├── Mods/                   # โฟลเดอร์ม็อดสำหรับนำไปวางในเกม
│    ├── Fonts/font.dat     # คอนฟิกฟอนต์ไทย
│    └── TextDump/
│         ├── text_dump.dll       # ปลั๊กอินหลัก
│         ├── translation.txt     # คลังคำแปลภาษาไทย 47,950 รายการ
│         ├── title_white.nltx    # ภาพไตเติลภาษาไทย
│         ├── ui_1000_title01.nltx
│         ├── DUMP_SYSTEM_GUIDE.md# คู่มือระบบดัมพ์
│         ├── PLUGIN_STRUCTURE.md # คู่มือโครงสร้างระบบ
│         └── textures/           # ภาพแปลไทยทั้ง 70 รายการ (.nltx)
└── README.md
```

---

## 🎮 วิธีติดตั้งสำหรับผู้เล่น (How to Install)

1. ดาวน์โหลดไฟล์ม็อดจากหน้า [Releases](https://github.com/supakiat2018/Village-in-the-Shade-ThaiMod/releases)
2. นำไฟล์ `steam_api64.dll` และโฟลเดอร์ `Mods` ไปวางในโฟลเดอร์เกม:
   ```
   C:\Program Files (x86)\Steam\steamapps\common\Village in the Shade\
   ```
   *(อย่าลืมเปลี่ยนชื่อไฟล์ `steam_api64.dll` ตัวเดิมของเกมเป็น `steam_api64_org.dll` ก่อนวาง)*
3. เปิดเข้าเกมผ่าน Steam ตามปกติ ตัวเกมจะกลายเป็นภาษาไทยทันที

---

## 💻 วิธีการคอมไพล์จากซอร์สโค้ด (Build from Source)

เปิด Command Prompt หรือ PowerShell แล้วรัน:
```cmd
build.bat
```
หรือใช้คำสั่ง:
```cmd
zig cc -shared -O2 -s src\text_dump.c src\addrsig.c src\minhook-master\src\buffer.c src\minhook-master\src\hook.c src\minhook-master\src\trampoline.c src\minhook-master\src\hde\hde64.c -o Mods\TextDump\text_dump.dll -lkernel32 -luser32
```

---

## 📜 เครดิต (Credits)
- **ผู้พัฒนาและแปลภาษาไทย:** supakiat2018
- **เครื่องมือ Hooking:** MinHook Library
