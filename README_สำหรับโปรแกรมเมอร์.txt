================================================================================
Village in the Shade - Thai Mod Source Code & Architecture
================================================================================

1. โครงสร้างโปรเจกต์:
- ภาษา: C (C99 / C11)
- Compiler ที่ใช้: Zig CC (zig cc) หรือ GCC (MinGW-w64 x64)
- Library: MinHook (Hooking Engine)
- Target Engine: Wolf RPG Editor (64-bit Windows DirectX/GDI)
- Output: text_dump.dll (วางไว้ที่ Mods\TextDump\text_dump.dll)

2. การทำงานหลักของ Mod (Hooking & Translation):
- text_dump.dll จะถูกโหลดขึ้นมาพร้อมกับเกม
- Hook ฟังก์ชันแสดงผลข้อความของเกม (putStr, putStrProp, putStrAlign)
- Hook ฟังก์ชันอ่านไฟล์ของ Windows (ReadFile / GetOverlappedResult) เพื่อทำ Virtual File System (VFS)
- ทำการแทรกแซงข้อความภาษาญี่ปุ่น และแทนที่ด้วยข้อความภาษาไทยที่ผ่านการแปลงรหัส PUA (Private Use Area) เพื่อแก้ปัญหาสระลอย/วรรณยุกต์ซ้อนในเอนจินเกม

3. วิธีการคอมไพล์ (Build Command):
ดูใน build.bat หรือสั่งด้วยคำสั่ง:
zig cc -shared -O2 -s src\text_dump.c src\addrsig.c src\minhook-master\src\buffer.c src\minhook-master\src\hook.c src\minhook-master\src\trampoline.c src\minhook-master\src\hde\hde64.c -o Mods\TextDump\text_dump.dll -lkernel32 -luser32

4. ระบบโฟลเดอร์โมดูลคำแปล (modules/):
- ไฟล์คำแปลจะแยกเป็นหมวดหมู่ 35 ไฟล์ วางไว้ที่ Mods\TextDump\modules\
  เช่น 01_gamesetting.txt, 02_cmd.txt, 03_action.txt
- รูปแบบข้อมูลภายในไฟล์: [ข้อความญี่ปุ่นต้นฉบับ]=[ข้อความไทยที่แปลงรหัส PUA]
================================================================================
