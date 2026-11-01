import os
import shutil

bin_with_kb = r'D:\Users\Supakiat\Desktop\Village_in_the_Shade_ThaiMod_Dev\bin\text_dump_with_kb.dll'
bin_no_kb   = r'D:\Users\Supakiat\Desktop\Village_in_the_Shade_ThaiMod_Dev\bin\text_dump_no_kb.dll'
bin_full    = r'D:\Users\Supakiat\Desktop\Village_in_the_Shade_ThaiMod_Dev\bin\text_dump_full.dll'
winmm_src   = r'D:\Users\Supakiat\Desktop\Village_in_the_Shade_ThaiMod_Dev\bin\winmm.dll'
cheats_ini  = r'D:\Users\Supakiat\Desktop\Village_in_the_Shade_ThaiMod_Dev\cheats.ini'
ct_130      = r'D:\Users\Supakiat\Desktop\Village-in-the-Shade-Trainer\Village in the Shade1.30.CT'
steam_game  = r'C:\Program Files (x86)\Steam\steamapps\common\Village in the Shade'

# Default deployment to active game: text_dump_with_kb.dll (clean)
steam_dll = os.path.join(steam_game, 'Mods', 'TextDump', 'text_dump.dll')
shutil.copy2(bin_with_kb, steam_dll)
print(f'Copied text_dump_with_kb.dll -> {steam_dll}')

targets = [
    r'C:\Users\Administrator\Desktop',
    r'D:\Users\Supakiat\Desktop\MOD_OUTPUT_V130',
    r'C:\Users\Administrator\Desktop\MOD_OUTPUT_V130'
]

fonts_src = os.path.join(steam_game, 'Mods', 'Fonts')
dat_src   = os.path.join(steam_game, 'Mods', 'TextDump', 'dat')
tex_src   = os.path.join(steam_game, 'Mods', 'TextDump', 'textures')

packages = [
    (1, True, False, '01_เวอร์ชัน_มีคีย์บอร์ดไทย_ไม่มีสูตร', bin_with_kb),
    (2, False, False, '02_เวอร์ชัน_ไม่มีคีย์บอร์ด_ไม่มีสูตร', bin_no_kb),
    (3, True, True, '03_เวอร์ชัน_มีคีย์บอร์ดไทย_มีสูตรโกง', bin_full),
]

for t in targets:
    for pkg_id, is_kb, has_cheats, name, src_dll in packages:
        dest_dir = os.path.join(t, name)
        mod_textdump = os.path.join(dest_dir, 'Mods', 'TextDump')
        mod_fonts    = os.path.join(dest_dir, 'Mods', 'Fonts')
        os.makedirs(mod_textdump, exist_ok=True)
        os.makedirs(mod_fonts, exist_ok=True)

        # Copy DLLs
        shutil.copy2(src_dll, os.path.join(mod_textdump, 'text_dump.dll'))
        shutil.copy2(winmm_src, os.path.join(dest_dir, 'winmm.dll'))

        # Copy Fonts
        for f in os.listdir(fonts_src):
            s_file = os.path.join(fonts_src, f)
            if os.path.isfile(s_file):
                shutil.copy2(s_file, os.path.join(mod_fonts, f))

        # Copy dat files
        dest_dat = os.path.join(mod_textdump, 'dat')
        os.makedirs(dest_dat, exist_ok=True)
        for f in os.listdir(dat_src):
            s_file = os.path.join(dat_src, f)
            if os.path.isfile(s_file):
                shutil.copy2(s_file, os.path.join(dest_dat, f))

        # Copy textures
        dest_tex = os.path.join(mod_textdump, 'textures')
        os.makedirs(dest_tex, exist_ok=True)
        for f in os.listdir(tex_src):
            s_file = os.path.join(tex_src, f)
            if os.path.isfile(s_file):
                shutil.copy2(s_file, os.path.join(dest_tex, f))

        if has_cheats:
            shutil.copy2(cheats_ini, os.path.join(mod_textdump, 'cheats.ini'))
            shutil.copy2(cheats_ini, os.path.join(dest_dir, 'cheats.ini'))
            if os.path.exists(ct_130):
                shutil.copy2(ct_130, os.path.join(dest_dir, 'Village in the Shade1.30.CT'))
            
            # Cheats README
            readme_content = f"""================================================================================
  Village in the Shade — เวอร์ชัน 3: มีคีย์บอร์ดไทย + มีสูตรโกง (Game ver. 1.30)
================================================================================

[รายละเอียดเวอร์ชันนี้]
  - ม็อดแปลภาษาไทยสมบูรณ์ (ฐานข้อมูล + ป้าย UI + ฟอนต์ภาษาไทย)
  - แป้นพิมพ์เสมือนจริงภาษาไทย (Thai Virtual Keyboard 182 ปุ่ม)
  - ระบบสูตรโกงในตัวเกม (In-Game Cheats System) อัปเดตตรงกับ v1.30 เรียบร้อยแล้ว!
  - มาพร้อมตาราง Cheat Engine Table (Village in the Shade1.30.CT) สำหรับ v1.30
  - รองรับ Trainer GUI ภาษาไทย (อัปเดตระบบตรวจสอบ v1.30 อัตโนมัติ)

วิธีติดตั้ง:
  - ดับเบิ้ลคลิกไฟล์ "ติดตั้งม็อดนี้ลงในเกมทันที.bat"
  - หรือก๊อปปี้ไฟล์ winmm.dll, cheats.ini และโฟลเดอร์ Mods ทั้งหมดไปวางในโฟลเดอร์เกม:
    C:\\Program Files (x86)\\Steam\\steamapps\\common\\Village in the Shade\\

วิธีใช้งานสูตรโกง:
  เปิด/ปิดผ่านไฟล์ cheats.ini (1 = เปิด, 0 = ปิด)
  เปลี่ยนชื่อเป็น _cheats.ini เพื่อปิดสูตรทั้งหมดทันที
================================================================================
"""
            with open(os.path.join(dest_dir, 'README_วิธีใช้งานและสูตรโกง.txt'), 'w', encoding='utf-8') as rf:
                rf.write(readme_content)

            bat_content = f"""@echo off
chcp 65001 >nul
title ติดตั้งม็อดภาษาไทย + สูตรโกง - {name}
set "GAME_ROOT=C:\\Program Files (x86)\\Steam\\steamapps\\common\\Village in the Shade"

if not exist "%GAME_ROOT%\\village.exe" (
    echo [ERROR] ไม่พบโฟลเดอร์เกมที่: %GAME_ROOT%
    pause
    exit /b 1
)

echo กำลังติดตั้ง {name}...
copy /y "%~dp0winmm.dll" "%GAME_ROOT%\\winmm.dll" >nul
copy /y "%~dp0cheats.ini" "%GAME_ROOT%\\cheats.ini" >nul
if exist "%~dp0Village in the Shade1.30.CT" copy /y "%~dp0Village in the Shade1.30.CT" "%GAME_ROOT%\\Village in the Shade1.30.CT" >nul

echo ก๊อปปี้โฟลเดอร์ Mods...
xcopy /e /y /i "%~dp0Mods" "%GAME_ROOT%\\Mods" >nul

echo.
echo [SUCCESS] ติดตั้งม็อดลงในเกมเรียบร้อยแล้ว! สามารถเปิดเกมเล่นได้ทันทีครับ
echo.
pause
"""
            with open(os.path.join(dest_dir, 'ติดตั้งม็อดนี้ลงในเกมทันที.bat'), 'w', encoding='utf-8') as bf:
                bf.write(bat_content)

        else:
            # Ensure no cheats.ini
            for cpath in [
                os.path.join(dest_dir, 'cheats.ini'),
                os.path.join(mod_textdump, 'cheats.ini')
            ]:
                if os.path.exists(cpath):
                    os.remove(cpath)

            kb_text = "[มีคีย์บอร์ดไทย 182 ปุ่ม]" if is_kb else "[ใช้คีย์บอร์ดดั้งเดิมของเกม]"
            readme_content = f"""============================================================
 ม็อดภาษาไทย Village in the Shade (v1.30)
 ชุด: {name}
 {kb_text} + [ไม่มีสูตรโกง 100%]
============================================================

คุณสมบัติ:
1. รองรับเกมเวอร์ชันใหม่ v1.30 เต็มระบบ
2. {kb_text}: {'แป้นพิมพ์เสมือนภาษาไทย 182 ปุ่ม พิมพ์ไทยได้สะดวกรวดเร็ว' if is_kb else 'แป้นพิมพ์เสมือนเดิมของเกม ไม่มีการดัดแปลง'}
3. [ไม่มีสูตรโกง]: ตัดระบบสูตรโกงออก 100% ตัวเกมสะอาด ปลอดภัย ไม่แครช
4. [รองรับฟอนต์ไทย]: ฟอนต์ KiwiMaru และ Lora ครบสมบูรณ์ใน Mods\\Fonts\\
5. [รองรับฐานข้อมูล]: ไฟล์ข้อความภาษาไทย 37 ไฟล์ใน Mods\\TextDump\\dat\\
6. [รองรับภาพ UI ไทย]: ภาพ Texture แปลไทยทั้งหมด 71 ภาพใน Mods\\TextDump\\textures\\

วิธีติดตั้ง:
- ก๊อปปี้โฟลเดอร์ Mods และไฟล์ winmm.dll ไปวางทับในโฟลเดอร์เกม:
  C:\\Program Files (x86)\\Steam\\steamapps\\common\\Village in the Shade\\
- หรือดับเบิ้ลคลิกไฟล์ "ติดตั้งม็อดนี้ลงในเกมทันที.bat"
"""
            with open(os.path.join(dest_dir, 'README_วิธีติดตั้ง.txt'), 'w', encoding='utf-8') as rf:
                rf.write(readme_content)

            bat_content = f"""@echo off
chcp 65001 >nul
title ติดตั้งม็อดภาษาไทย - {name}
set "GAME_ROOT=C:\\Program Files (x86)\\Steam\\steamapps\\common\\Village in the Shade"

if not exist "%GAME_ROOT%\\village.exe" (
    echo [ERROR] ไม่พบโฟลเดอร์เกมที่: %GAME_ROOT%
    pause
    exit /b 1
)

echo กำลังติดตั้ง {name}...
copy /y "%~dp0winmm.dll" "%GAME_ROOT%\\winmm.dll" >nul

echo ก๊อปปี้โฟลเดอร์ Mods...
xcopy /e /y /i "%~dp0Mods" "%GAME_ROOT%\\Mods" >nul

echo.
echo [SUCCESS] ติดตั้งม็อดลงในเกมเรียบร้อยแล้ว! สามารถเปิดเกมเล่นได้ทันทีครับ
echo.
pause
"""
            with open(os.path.join(dest_dir, 'ติดตั้งม็อดนี้ลงในเกมทันที.bat'), 'w', encoding='utf-8') as bf:
                bf.write(bat_content)

        print(f'Packaged -> {dest_dir}')

print('ALL 3 PACKAGES DEPLOYED 100% SUCCESSFULLY!')
