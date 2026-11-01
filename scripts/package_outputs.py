import os, shutil

BASE_DEV = r"D:\Users\Supakiat\Desktop\Village_in_the_Shade_ThaiMod_Dev"
BIN_DIR = os.path.join(BASE_DEV, "bin")
OUT_ROOT = os.path.join(BASE_DEV, "MOD_OUTPUT_V130")

v1_dir = os.path.join(OUT_ROOT, "01_เวอร์ชัน_มีคีย์บอร์ดไทย_ไม่มีสูตร")
v2_dir = os.path.join(OUT_ROOT, "02_เวอร์ชัน_ไม่มีคีย์บอร์ด_ไม่มีสูตร")

for d in [v1_dir, v2_dir]:
    os.makedirs(os.path.join(d, "Mods", "TextDump"), exist_ok=True)

# 1. Package Version 1 (With Thai Keyboard, No Cheats)
shutil.copy2(os.path.join(BIN_DIR, "text_dump_with_kb.dll"), os.path.join(v1_dir, "Mods", "TextDump", "text_dump.dll"))
shutil.copy2(os.path.join(BIN_DIR, "winmm.dll"), os.path.join(v1_dir, "winmm.dll"))

readme_v1 = """============================================================
 ม็อดภาษาไทย Village in the Shade (v1.30)
 ชุดที่ 1: [มีคีย์บอร์ดไทย 182 ปุ่ม + ไม่มีสูตรโกง 100%]
============================================================

คุณสมบัติ:
1. รองรับเกมเวอร์ชันใหม่ v1.30 เต็มระบบ
2. [มีคีย์บอร์ดไทย]: แป้นพิมพ์เสมือนในเกมเปลี่ยนเป็นภาษาไทย 182 ปุ่ม พิมพ์ไทยได้
3. [ไม่มีสูตรโกง]: ตัดระบบ Cheats ออกทั้งหมด 100% ตัวเกมสะอาด ปลอดภัย ไม่แครช
4. [รองรับฟอนต์]: โหลดฟอนต์ภาษาไทยจาก Mods\\Fonts\\ อัตโนมัติ (KiwiMaru, Lora)
5. [รองรับไฟล์ .dat]: โหลดไฟล์แปลไทยทั้งหมดจาก Mods\\TextDump\\dat\\ อัตโนมัติ
6. [รองรับภาพ Texture]: โหลดภาพไทยทั้งหมดจาก Mods\\TextDump\\textures\\ อัตโนมัติ

วิธีติดตั้ง:
- ดับเบิ้ลคลิกไฟล์ "ติดตั้งม็อดนี้ลงในเกมทันที.bat"
  หรือ ก๊อปปี้โฟลเดอร์ Mods และไฟล์ winmm.dll ไปวางทับในโฟลเดอร์เกม:
  C:\\Program Files (x86)\\Steam\\steamapps\\common\\Village in the Shade\\
"""
with open(os.path.join(v1_dir, "README_วิธีติดตั้ง.txt"), "w", encoding="utf-8") as f:
    f.write(readme_v1)

bat_v1 = """@echo off
chcp 65001 >nul
title ติดตั้งม็อดภาษาไทย (มีคีย์บอร์ดไทย - ไม่มีสูตร)
set "GAME_ROOT=C:\\Program Files (x86)\\Steam\\steamapps\\common\\Village in the Shade"

if not exist "%GAME_ROOT%\\village.exe" (
    echo [ERROR] ไม่พบโฟลเดอร์เกมที่: %GAME_ROOT%
    pause
    exit /b 1
)

echo กำลังติดตั้งม็อดภาษาไทย (ชุดมีคีย์บอร์ดไทย)...
copy /y "%~dp0winmm.dll" "%GAME_ROOT%\\winmm.dll" >nul
if not exist "%GAME_ROOT%\\Mods\\TextDump" mkdir "%GAME_ROOT%\\Mods\\TextDump"
copy /y "%~dp0Mods\\TextDump\\text_dump.dll" "%GAME_ROOT%\\Mods\\TextDump\\text_dump.dll" >nul

echo.
echo [SUCCESS] ติดตั้งเรียบร้อยแล้ว! สามารถเปิดเกมเล่นได้ทันทีครับ
echo.
pause
"""
with open(os.path.join(v1_dir, "ติดตั้งม็อดนี้ลงในเกมทันที.bat"), "w", encoding="utf-8") as f:
    f.write(bat_v1)


# 2. Package Version 2 (No Keyboard, No Cheats)
shutil.copy2(os.path.join(BIN_DIR, "text_dump_no_kb.dll"), os.path.join(v2_dir, "Mods", "TextDump", "text_dump.dll"))
shutil.copy2(os.path.join(BIN_DIR, "winmm.dll"), os.path.join(v2_dir, "winmm.dll"))

readme_v2 = """============================================================
 ม็อดภาษาไทย Village in the Shade (v1.30)
 ชุดที่ 2: [ไม่มีคีย์บอร์ดไทย (ใช้แป้นเดิมของเกม) + ไม่มีสูตรโกง 100%]
============================================================

คุณสมบัติ:
1. รองรับเกมเวอร์ชันใหม่ v1.30 เต็มระบบ
2. [ไม่แตะต้องคีย์บอร์ด]: ใช้แป้นพิมพ์เดิมของตัวเกม 100% ไม่ยุ่งกับระบบแป้นพิมพ์
3. [ไม่มีสูตรโกง]: ตัดระบบ Cheats ออกทั้งหมด 100% ตัวเกมสะอาด ปลอดภัย ไม่แครช
4. [รองรับฟอนต์]: โหลดฟอนต์ภาษาไทยจาก Mods\\Fonts\\ อัตโนมัติ (KiwiMaru, Lora)
5. [รองรับไฟล์ .dat]: โหลดไฟล์แปลไทยทั้งหมดจาก Mods\\TextDump\\dat\\ อัตโนมัติ
6. [รองรับภาพ Texture]: โหลดภาพไทยทั้งหมดจาก Mods\\TextDump\\textures\\ อัตโนมัติ

วิธีติดตั้ง:
- ดับเบิ้ลคลิกไฟล์ "ติดตั้งม็อดนี้ลงในเกมทันที.bat"
  หรือ ก๊อปปี้โฟลเดอร์ Mods และไฟล์ winmm.dll ไปวางทับในโฟลเดอร์เกม:
  C:\\Program Files (x86)\\Steam\\steamapps\\common\\Village in the Shade\\
"""
with open(os.path.join(v2_dir, "README_วิธีติดตั้ง.txt"), "w", encoding="utf-8") as f:
    f.write(readme_v2)

bat_v2 = """@echo off
chcp 65001 >nul
title ติดตั้งม็อดภาษาไทย (ไม่มีคีย์บอร์ดไทย - ไม่มีสูตร)
set "GAME_ROOT=C:\\Program Files (x86)\\Steam\\steamapps\\common\\Village in the Shade"

if not exist "%GAME_ROOT%\\village.exe" (
    echo [ERROR] ไม่พบโฟลเดอร์เกมที่: %GAME_ROOT%
    pause
    exit /b 1
)

echo กำลังติดตั้งม็อดภาษาไทย (ชุดไม่มีคีย์บอร์ดไทย)...
copy /y "%~dp0winmm.dll" "%GAME_ROOT%\\winmm.dll" >nul
if not exist "%GAME_ROOT%\\Mods\\TextDump" mkdir "%GAME_ROOT%\\Mods\\TextDump"
copy /y "%~dp0Mods\\TextDump\\text_dump.dll" "%GAME_ROOT%\\Mods\\TextDump\\text_dump.dll" >nul

echo.
echo [SUCCESS] ติดตั้งเรียบร้อยแล้ว! สามารถเปิดเกมเล่นได้ทันทีครับ
echo.
pause
"""
with open(os.path.join(v2_dir, "ติดตั้งม็อดนี้ลงในเกมทันที.bat"), "w", encoding="utf-8") as f:
    f.write(bat_v2)

print("Both versions packaged successfully into:", OUT_ROOT)
