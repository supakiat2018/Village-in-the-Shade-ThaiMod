import os
import shutil

src_base = r"D:\Users\Supakiat\Desktop\Village_in_the_Shade_ThaiMod_Dev"
steam_game = r"C:\Program Files (x86)\Steam\steamapps\common\Village in the Shade"

pkg_desktop = r"C:\Users\Administrator\Desktop\03_เวอร์ชัน_มีคีย์บอร์ดไทย_มีสูตรโกง"
pkg_backup = r"D:\Users\Supakiat\Desktop\MOD_OUTPUT_V130\03_เวอร์ชัน_มีคีย์บอร์ดไทย_มีสูตรโกง"
pkg_desktop_backup = r"C:\Users\Administrator\Desktop\MOD_OUTPUT_V130\03_เวอร์ชัน_มีคีย์บอร์ดไทย_มีสูตรโกง"

fonts_src = os.path.join(steam_game, "Mods", "Fonts")
dat_src = os.path.join(steam_game, "Mods", "TextDump", "dat")
tex_src = os.path.join(steam_game, "Mods", "TextDump", "textures")

print("Packaging Version 3 (Thai Keyboard + Cheats System v1.30)...")

for target_dir in [pkg_desktop, pkg_backup, pkg_desktop_backup]:
    if os.path.exists(target_dir):
        shutil.rmtree(target_dir)
    os.makedirs(target_dir, exist_ok=True)
    
    # 1. winmm.dll
    shutil.copy2(os.path.join(src_base, "bin", "winmm.dll"), os.path.join(target_dir, "winmm.dll"))
    
    # 2. Mods folder structure
    mods_fonts = os.path.join(target_dir, "Mods", "Fonts")
    mods_textdump = os.path.join(target_dir, "Mods", "TextDump")
    mods_dat = os.path.join(mods_textdump, "dat")
    mods_tex = os.path.join(mods_textdump, "textures")
    
    os.makedirs(mods_fonts, exist_ok=True)
    os.makedirs(mods_dat, exist_ok=True)
    os.makedirs(mods_tex, exist_ok=True)
    
    # 3. DLL (Full build with Thai KB + Cheats)
    shutil.copy2(os.path.join(src_base, "bin", "text_dump_full.dll"), os.path.join(mods_textdump, "text_dump.dll"))
    
    # 4. cheats.ini (in Mods/TextDump and in root folder)
    shutil.copy2(os.path.join(src_base, "cheats.ini"), os.path.join(mods_textdump, "cheats.ini"))
    shutil.copy2(os.path.join(src_base, "cheats.ini"), os.path.join(target_dir, "cheats.ini"))
    
    # 5. Cheat Engine Table for v1.30
    ct_src = r"D:\Users\Supakiat\Desktop\Village-in-the-Shade-Trainer\Village in the Shade1.30.CT"
    if os.path.exists(ct_src):
        shutil.copy2(ct_src, os.path.join(target_dir, "Village in the Shade1.30.CT"))
    
    # 6. Copy Fonts
    for f in os.listdir(fonts_src):
        s = os.path.join(fonts_src, f)
        if os.path.isfile(s):
            shutil.copy2(s, os.path.join(mods_fonts, f))
        
    # 7. Copy DATs
    for f in os.listdir(dat_src):
        s = os.path.join(dat_src, f)
        if os.path.isfile(s):
            shutil.copy2(s, os.path.join(mods_dat, f))
        
    # 8. Copy Textures
    for f in os.listdir(tex_src):
        s = os.path.join(tex_src, f)
        if os.path.isfile(s):
            shutil.copy2(s, os.path.join(mods_tex, f))
        
    # 9. ติดตั้งม็อดนี้ลงในเกมทันที.bat
    bat_content = f"""@echo off
chcp 65001 >nul
title ติดตั้งม็อดภาษาไทย + สูตรโกง v1.30

echo ========================================================
echo   ติดตั้ง Village in the Shade ภาษาไทย + ระบบสูตรโกง (v1.30)
echo ========================================================
echo.

set "DEST=C:\\Program Files (x86)\\Steam\\steamapps\\common\\Village in the Shade"

if not exist "%DEST%\\village.exe" (
    echo [ERROR] ไม่พบโฟลเดอร์เกมที่:
    echo %DEST%
    echo กรุณาคัดลอกไฟล์ทั้งหมดในโฟลเดอร์นี้ไปวางในโฟลเดอร์เกมด้วยตัวเอง
    echo.
    pause
    exit /b 1
)

echo กำลังคัดลอกไฟล์ม็อดลงในโฟลเดอร์เกม...
copy /y "%~dp0winmm.dll" "%DEST%\\winmm.dll" >nul
copy /y "%~dp0cheats.ini" "%DEST%\\cheats.ini" >nul
if exist "%~dp0Village in the Shade1.30.CT" copy /y "%~dp0Village in the Shade1.30.CT" "%DEST%\\Village in the Shade1.30.CT" >nul

echo กำลังคัดลอกโฟลเดอร์ Mods...
xcopy /e /y /i "%~dp0Mods" "%DEST%\\Mods" >nul

echo.
echo ========================================================
echo   [SUCCESS] ติดตั้งสำเร็จเรียบร้อยแล้ว!
echo.
echo   * ฟังก์ชันทั้งหมดพร้อมใช้งาน:
echo     1. ภาษาไทยครบถ้วน (แปลไทย 100%% + ฟอนต์ + ภาพ UI)
echo     2. แป้นพิมพ์ภาษาไทยในเกม 182 ปุ่ม
echo     3. ระบบสูตรโกงในตัวเกม (เปิด/ปิด ได้จาก cheats.ini)
echo     4. รองรับ Cheat Engine Table (v1.30.CT) และ Trainer
echo ========================================================
echo.
pause
"""
    with open(os.path.join(target_dir, "ติดตั้งม็อดนี้ลงในเกมทันที.bat"), "w", encoding="utf-8") as bf:
        bf.write(bat_content)

    # 10. README_วิธีใช้งานและสูตรโกง.txt
    readme_content = """================================================================================
  Village in the Shade — เวอร์ชัน 3: มีคีย์บอร์ดไทย + มีสูตรโกง (Game ver. 1.30)
================================================================================

[รายละเอียดเวอร์ชันนี้]
  - ม็อดแปลภาษาไทยสมบูรณ์ (ฐานข้อมูล + ป้าย UI + ฟอนต์ภาษาไทย)
  - แป้นพิมพ์เสมือนจริงภาษาไทย (Thai Virtual Keyboard 182 ปุ่ม)
  - ระบบสูตรโกงในตัวเกม (In-Game Cheats System) อัปเดตตรงกับ v1.30 เรียบร้อยแล้ว!
  - มาพร้อมตาราง Cheat Engine Table (Village in the Shade1.30.CT) สำหรับ v1.30
  - รองรับ Trainer GUI ภาษาไทย (อัปเดตระบบตรวจสอบ v1.30 อัตโนมัติ)

--------------------------------------------------------------------------------
[วิธีติดตั้ง]
  วิธีที่ 1: ดับเบิ้ลคลิกไฟล์ "ติดตั้งม็อดนี้ลงในเกมทันที.bat"
  วิธีที่ 2: คัดลอกไฟล์ winmm.dll, cheats.ini และโฟลเดอร์ Mods ทั้งหมด
            ไปวางทับในโฟลเดอร์เกม Steam:
            C:\\Program Files (x86)\\Steam\\steamapps\\common\\Village in the Shade\\

--------------------------------------------------------------------------------
[วิธีใช้งานระบบสูตรโกงในตัวเกม (In-Game Cheats)]
  สูตรจะถูกควบคุมผ่านไฟล์ "cheats.ini" (อยู่ในโฟลเดอร์ Mods\\TextDump\\ และในโฟลเดอร์เกม):

  * เปิดใช้งานสูตรทั้งหมด: ตั้งชื่อไฟล์ว่า "cheats.ini"
  * ปิดสูตรทั้งหมดทันที: เปลี่ยนชื่อไฟล์เป็น "_cheats.ini" หรือลบออก
                       (เกมจะคืนค่าความจำกลับเป็นค่าเดิมทันทีโดยไม่ต้องรีสตาร์ทเกม!)

  * การตั้งค่าแต่ละสูตรใน cheats.ini (1 = เปิด, 0 = ปิด):
    - god_mode = 1                (อมตะ เลือดไม่ลด ไม่โดนดาเมจ)
    - infinite_items = 1          (ไอเทมไม่ลด ใช้/โยน/ปลูก จำนวนไม่ลด)
    - no_materials_crafting = 1   (สร้างของ/คราฟต์ของ ฟรี ไม่ใช้วัตถุดิบ)
    - no_materials_cooking = 1    (ทำอาหาร ฟรี ไม่ใช้วัตถุดิบ)
    - no_materials_smithing = 1   (ตีเหล็ก ฟรี ไม่ใช้วัตถุดิบ)
    - no_materials_building = 1   (สร้างบ้าน/สิ่งปลูกสร้าง ฟรี ไม่ใช้วัตถุดิบ)
    - no_materials_dyeing = 1     (ย้อมสี ฟรี ไม่ใช้วัตถุดิบ)
    - submit_any_item = 1         (ส่งของบันเดิล/เควสต์ ด้วยไอเทมอะไรก็ได้)
    - noclip = 0                  (เดินทะลุกำแพง/สิ่งกีดขวาง)
    - infinite_stamina = 1        (พลังกายเต็มตลอดเวลา)
    - freeze_time = 0             (หยุดเวลาในเกม)
    - infinite_money = 0          (เงินไม่จำกัด 999,999)

--------------------------------------------------------------------------------
[การใช้งานร่วมกับ Cheat Engine]
  หากต้องการใช้ Cheat Engine ให้เปิดไฟล์:
  "Village in the Shade1.30.CT"
  (อัปเดต Address ตัวชี้ตำแหน่งข้อมูลหลักเป็น 0x111CC90 ตรงกับ v1.30 แล้ว 100%)
================================================================================
"""
    with open(os.path.join(target_dir, "README_วิธีใช้งานและสูตรโกง.txt"), "w", encoding="utf-8") as rf:
        rf.write(readme_content)

    print(f"Packaged -> {target_dir}")

print("ALL PACKAGES DEPLOYED 100% SUCCESSFULLY!")
