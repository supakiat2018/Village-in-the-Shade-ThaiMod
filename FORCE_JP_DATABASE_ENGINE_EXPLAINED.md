# คัมภีร์วิศวกรรมย้อนกลับ: เทคนิค Force Japanese Database & Dialogue Slots ใน RAM
## การแก้ปัญหาเซฟอังกฤษ (Save EN) ให้กลายเป็นไทยสมบูรณ์ 100% โดยไม่แตะต้องไฟล์เซฟ

> **เป้าหมาย:** บังคับให้เอนจินเกม *Village in the Shade* รันโครงสร้างตารางข้อมูลและบทสนทนาแบบภาษาญี่ปุ่น (JP Slot) ตลอดเวลา เพื่อให้ม็อดภาษาไทยสามารถแสดงผลได้เต็มประโยค (ไม่มีการตัดคำแบบภาษาอังกฤษ) และรองรับการโหลดเซฟภาษาอังกฤษเดิมของผู้เล่นได้ 100% โดยไม่ต้องดัดแปลงไฟล์เซฟแม้แต่ไบต์เดียว
> **ตำแหน่งโค้ดในซอร์สโค้ด:** `src/text_dump.c` ฟังก์ชัน `patch_force_jp_database()`
> **ช่วงเวลาที่แพตช์:** ทำงานใน `DllMain` ตั้งแต่วินาทีแรกที่ `winmm.dll` ถูกโหลดเข้าโพรเซส (ก่อนเกมสร้างหน้าต่างแรก)

---

## 1. ที่มาและต้นตอของปัญหาในเอนจินเกม

### 1.1 ปัญหากรอบข้อความและการตัดคำภาษาอังกฤษ (Dialogue Bubble Clipping)
- ในเอนจินเกมนี้ โครงสร้างไฟล์บทสนทนา (`talk.dat`) ของโหมด **อังกฤษ (EN)** มีการตัดทอนประโยคและแบ่งวรรคตอนไม่เท่ากับโหมด **ญี่ปุ่น (JP)** 
- หากตัวเกมรันในโหมด EN ตัวเกมจะดึงตารางของ EN ซึ่งมีข้อจำกัดเรื่องความยาวตัวอักษรต่อช่อง ทำให้เกิดอาการข้อความขาดหาย เช่น `I should answer the do...`, `I knew you were no ord...`
- โหมด **ญี่ปุ่น (JP)** เป็นโครงสร้างหลักของเกม มีช่องความจุตัวอักษรและบับเบิ้ลบทสนทนาสมบูรณ์แบบที่สุด ม็อดภาษาไทยจึงถูกออกแบบมาให้แปลทับบนฐานข้อมูลภาษาญี่ปุ่น (`Mods\dat_ja\`)

### 1.2 ปัญหาการแคลช (Crash) จากการสลับภาษาผิดจังหวะ
- ก่อนหน้านี้ หากเราพยายามสั่งเปลี่ยนค่าภาษาใน RAM (`[0x1124CE0] = 0`) หลังจากเกมเปิดขึ้นมาแล้ว ตัวเกมจะเกิดอาการ **Crash (0xC0000005 Access Violation)**
- **สาเหตุแท้จริง:** ถ้าเกมเปิดมาในโหมดภาษาอังกฤษ ตัวเอนจินจะสร้างหน่วยความจำ Font Layout Buffer เฉพาะภาษาอังกฤษเท่านั้น และปล่อยช่องพอยน์เตอร์ของฟอนต์ภาษาญี่ปุ่นทิ้งไว้เป็น `NULL` พอมีคำสั่งเปลี่ยนเป็นญี่ปุ่นกลางคัน ตัววาดตัวอักษรจะอ่านข้อมูลจาก `NULL + 0x70` ทำให้เกมเด้งหลุดทันที

---

## 2. หัวใจหลักของเทคนิค: การเจาะ Assembly 3 ระดับ

### ระดับที่ 1: บูตเอนจินเข้าโหมดญี่ปุ่นตั้งแต่วินาทีแรก (DllMain)
เพื่อป้องกันไม่ให้พอยน์เตอร์ฟอนต์กลายเป็น `NULL` เราต้องทำให้ตัวเกมคิดว่าตัวเองคือเวอร์ชันภาษาญี่ปุ่นตั้งแต่ต้น:
- **RVA 0x81ABD0 (Steam Boot Language):**  
  เดิมเรียก Steam API เช็คภาษาเครื่อง $\rightarrow$ เราแพตช์เป็น `xor eax, eax; ret; nop; nop` เพื่อคืนค่า 0 (JP) ทันที
- **RVA 0x1653E9 (Engine Init Language):**  
  เดิมมีคำสั่ง `cmovg r9d, ebx` ที่จะบังคับเซ็ตภาษาเป็น 1 (อังกฤษ) ถ้าไม่ใช่เครื่องญี่ปุ่น $\rightarrow$ เราแก้เป็น `xor r9d, r9d; nop`  
  **ผลลัพธ์:** เอนจินจองหน่วยความจำฟอนต์และตารางภาษาญี่ปุ่นครบถ้วนตั้งแต่เฟรมแรก ไม่มีการแคลชเกิดขึ้นเลย

### ระดับที่ 2: ดักฟังก์ชันโหลดเซฟ (Save Loader Bypass) — หมัดเด็ดพิชิตเซฟ EN!
เมื่อผู้เล่นกดโหลดเซฟเดิมที่เป็นภาษาอังกฤษ ในไฟล์เซฟจะมีการบันทึกค่า Option ภาษา = 1 (อังกฤษ) เอาไว้
ที่ **RVA 0x14A76C** โค้ดของเกมจะมีกระบวนการตรวจสอบดังนี้:

```x86asm
; โค้ดต้นฉบับของ village.exe (ก่อนแก้):
cmp eax, [Language]     ; ตรวจว่าภาษาในเซฟตรงกับภาษาปัจจุบันไหม
je  0x14014A77F         ; 74 0B -> ถ้าตรงกัน ให้ข้ามไป
mov [Language], eax     ; ถ้าไม่ตรง: เซ็ตภาษากลับเป็น 1 (อังกฤษ) ทันที!
call 0x140101130        ; เรียกฟังก์ชันรีโหลดฐานข้อมูลทั้ง 36 ตัวเป็นภาษาอังกฤษ!
```

**วิธีแก้ที่เราใช้:**  
เปลี่ยนไบต์เงื่อนไขจาก `74 0B` (`je`) ให้กลายเป็น `EB 0B` (`jmp` กระโดดข้ามแบบไม่มีเงื่อนไข)  
**ผลลัพธ์:** เมื่อโหลดเซฟ EN ตัวเกมจะกระโดดข้ามคำสั่งเซ็ตภาษาและข้ามคำสั่งรีโหลดตารางภาษาอังกฤษไปทันที ทำให้ตัวเกม **"คงค้างอยู่ในโหมดภาษาญี่ปุ่นตลอดกาล"** แม้จะโหลดเซฟอังกฤษก็ตาม!

### ระดับที่ 3: ล็อกกิ่งก้านบทสนทนาและฐานข้อมูลใน RAM (Runtime Guards)
ดักจุดที่ฟังก์ชันต่างๆ อาจพยายามอ่านค่าภาษาซ้ำ:
- บล็อกการสลับภาษาในเมนู Option (5 จุด)
- บังคับตัวเลือก Index ของ Dialogue และ Database ให้ชี้ไปที่ Slot 0 (JP) เสมอ

---

## 3. ตารางรหัสเครื่อง (Opcode Mapping Table) สำหรับ v1.30

หากเกมมีเวอร์ชันใหม่ออกมา ให้ค้นหา Pattern ไบต์เดิม (Original Bytes) รอบๆ ฟังก์ชันเหล่านี้ แล้วแทนที่ด้วย Patch Bytes:

| ที่ | RVA (v1.30) | ชื่อจุดแพตช์ | ไบต์เดิม (Original) | ไบต์ใหม่ (Patch) | คำสั่ง Assembly ใหม่ |
| :---: | :---: | :--- | :--- | :--- | :--- |
| **1** | `0x0081ABD0` | Steam Boot Lang | `48 89 5C 24 18` | `31 C0 C3 90 90` | `xor eax, eax; ret; nop; nop` |
| **2** | `0x001653E9` | Engine Init Lang | `44 0F 4F CB` | `45 31 C9 90` | `xor r9d, r9d; nop` |
| **3** | `0x0014A772` | **Save Load Skip (หัวใจหลัก)** | `74 0B` | `EB 0B` | `jmp +0x0B` |
| **4** | `0x0044B253` | Option Lang Skip 1 | `74 22` | `EB 22` | `jmp +0x22` |
| **5** | `0x0044DCB1` | Option Lang Skip 2 | `74 0B` | `EB 0B` | `jmp +0x0B` |
| **6** | `0x00458FC1` | Option Lang Skip 3 | `74 0B` | `EB 0B` | `jmp +0x0B` |
| **7** | `0x0046DC15` | Option Lang Skip 4 | `74 26` | `EB 26` | `jmp +0x26` |
| **8** | `0x0047AF82` | Option Lang Skip 5 | `74 0B` | `EB 0B` | `jmp +0x0B` |
| **9** | `0x000FB5EC` | Dialogue Lang Guard | `8B 05 EE 96 02 01` | `31 C0 90 90 90 90` | `xor eax, eax; nop x 4` |
| **10** | `0x001001CD` | DB String Index Guard | `48 63 15 0C 4B 02 01` | `31 D2 90 90 90 90 90` | `xor edx, edx; nop x 5` |
| **11** | `0x0010120E` | Dialogue Tree Guard | `63 05 CC 3A 02 01` | `31 C0 90 90 90 90` | `xor eax, eax; nop x 4` |
| **12** | `0x01124CE0` | Global Language RAM | `01 00 00 00` | `00 00 00 00` | ตัวแปร Global Language = 0 |

---

## 4. โค้ด C อ้างอิงใน `src/text_dump.c`

```c
typedef struct {
    uint32_t rva;
    uint8_t orig[8];
    uint8_t patch[8];
    size_t size;
    const char* desc;
} JpDatabasePatchEntry;

static void patch_force_jp_database(uintptr_t base, void (*log_fn)(const char*, ...))
{
    if (!g_settings.enable_thai_mod || !g_settings.force_jp_database) return;

    const JpDatabasePatchEntry patches[] = {
        { 0x0081ABD0, { 0x48, 0x89, 0x5C, 0x24, 0x18 }, { 0x31, 0xC0, 0xC3, 0x90, 0x90 }, 5, "Steam Boot Lang -> JP" },
        { 0x001653E9, { 0x44, 0x0F, 0x4F, 0xCB },       { 0x45, 0x31, 0xC9, 0x90 },       4, "Engine Init Boot Lang -> JP" },
        { 0x0014A772, { 0x74, 0x0B },                   { 0xEB, 0x0B },                   2, "Save Load Lang Switch Skip" },
        { 0x0044B253, { 0x74, 0x22 },                   { 0xEB, 0x22 },                   2, "Option Lang Switch Skip 1" },
        { 0x0044DCB1, { 0x74, 0x0B },                   { 0xEB, 0x0B },                   2, "Option Lang Switch Skip 2" },
        { 0x00458FC1, { 0x74, 0x0B },                   { 0xEB, 0x0B },                   2, "Option Lang Switch Skip 3" },
        { 0x0046DC15, { 0x74, 0x26 },                   { 0xEB, 0x26 },                   2, "Option Lang Switch Skip 4" },
        { 0x0047AF82, { 0x74, 0x0B },                   { 0xEB, 0x0B },                   2, "Option Lang Switch Skip 5" },
        { 0x000FB5EC, { 0x8B, 0x05, 0xEE, 0x96, 0x02, 0x01 }, { 0x31, 0xC0, 0x90, 0x90, 0x90, 0x90 }, 6, "Dialogue Lang -> JP" },
        { 0x001001CD, { 0x48, 0x63, 0x15, 0x0C, 0x4B, 0x02, 0x01 }, { 0x31, 0xD2, 0x90, 0x90, 0x90, 0x90, 0x90 }, 7, "DB String Index -> JP" },
        { 0x0010120E, { 0x63, 0x05, 0xCC, 0x3A, 0x02, 0x01 }, { 0x31, 0xC0, 0x90, 0x90, 0x90, 0x90 }, 6, "Dialogue Flow Offset -> JP" }
    };

    for (size_t i = 0; i < sizeof(patches) / sizeof(patches[0]); i++) {
        uint8_t* target = (uint8_t*)(base + patches[i].rva);
        DWORD old_protect;
        if (VirtualProtect(target, patches[i].size, PAGE_EXECUTE_READWRITE, &old_protect)) {
            memcpy(target, patches[i].patch, patches[i].size);
            FlushInstructionCache(GetCurrentProcess(), target, patches[i].size);
            VirtualProtect(target, patches[i].size, old_protect, &old_protect);
        }
    }

    uint32_t* p_global_lang = (uint32_t*)(base + 0x1124CE0);
    DWORD old_protect;
    if (VirtualProtect(p_global_lang, sizeof(uint32_t), PAGE_READWRITE, &old_protect)) {
        *p_global_lang = 0;
        VirtualProtect(p_global_lang, sizeof(uint32_t), old_protect, &old_protect);
    }
}
```

---

## 5. วิธีการค้นหาจุดแพตช์เหล่านี้หากเกมอัปเดตเวอร์ชันใหม่ในอนาคต

1. **จุด Save Load Skip (ค้นหา Signature):**
   - ค้นหาไบต์: `8B ?? ?? ?? ?? 00 39 ?? ?? ?? ?? 00 74 0B`
   - จุดที่เจอจะมีคำสั่ง `cmp [Language], eax` ตามด้วย `je 0x...` ให้เปลี่ยน `74 0B` เป็น `EB 0B`
2. **จุด Engine Boot Lang:**
   - ค้นหาไบต์: `44 0F 4F CB`
   - เปลี่ยนเป็น: `45 31 C9 90`
3. **จุด Steam GetGameLanguage:**
   - ค้นหาชื่อฟังก์ชัน `SteamAPI_ISteamApps_GetCurrentGameLanguage` จากตาราง Import ของเกม แล้วดูฟังก์ชัน Wrapper รอบข้าง เปลี่ยนต้นฟังก์ชันให้ `xor eax, eax; ret`
