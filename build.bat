@echo off
chcp 65001 >nul
title Village in the Shade - Mod Build Tool (v1.30 All Editions)

echo ========================================================
echo  Building Village in the Shade Thai Mod v1.30
echo  [Compiling 3 Editions + winmm.dll Proxy]
echo ========================================================
echo.

where zig >nul 2>nul
if %ERRORLEVEL% neq 0 (
    echo [ERROR] ไม่พบ Zig Compiler ในเครื่อง!
    echo.
    pause
    exit /b 1
)

echo [1/4] คอมไพล์เวอร์ชัน 1: มีคีย์บอร์ดไทย (182 ปุ่ม) + ไม่มีสูตรโกง...
zig cc -shared -O2 -s -m64 -DENABLE_THAI_KEYBOARD ^
    src\text_dump.c ^
    src\addrsig.c ^
    src\minhook-master\src\buffer.c ^
    src\minhook-master\src\hook.c ^
    src\minhook-master\src\trampoline.c ^
    src\minhook-master\src\hde\hde64.c ^
    -o bin\text_dump_with_kb.dll ^
    -lkernel32 -luser32 -lgdi32

echo [2/4] คอมไพล์เวอร์ชัน 2: คีย์บอร์ดดั้งเดิมของเกม + ไม่มีสูตรโกง...
zig cc -shared -O2 -s -m64 ^
    src\text_dump.c ^
    src\addrsig.c ^
    src\minhook-master\src\buffer.c ^
    src\minhook-master\src\hook.c ^
    src\minhook-master\src\trampoline.c ^
    src\minhook-master\src\hde\hde64.c ^
    -o bin\text_dump_no_kb.dll ^
    -lkernel32 -luser32 -lgdi32

echo [3/4] คอมไพล์เวอร์ชัน 3: มีคีย์บอร์ดไทย + มีระบบสูตรโกง v1.30...
zig cc -shared -O2 -s -m64 -DENABLE_THAI_KEYBOARD -DENABLE_CHEATS ^
    src\text_dump.c ^
    src\addrsig.c ^
    src\cheats.c ^
    src\minhook-master\src\buffer.c ^
    src\minhook-master\src\hook.c ^
    src\minhook-master\src\trampoline.c ^
    src\minhook-master\src\hde\hde64.c ^
    -o bin\text_dump_full.dll ^
    -lkernel32 -luser32 -lgdi32

echo [4/4] คอมไพล์ตัวเชื่อมระบบ (winmm.dll)...
zig cc -shared -O2 -s src\proxy_winmm.c src\winmm.def -o bin\winmm.dll -lkernel32

if %ERRORLEVEL% equ 0 (
    echo.
    echo [SUCCESS] คอมไพล์สำเร็จสมบูรณ์ทั้ง 3 เวอร์ชัน!
    echo เรียกสคริปต์กระจายไฟล์แพ็กเกจ...
    python scripts\deploy_all.py
) else (
    echo.
    echo [ERROR] คอมไพล์ไม่ผ่าน กรุณาตรวจสอบข้อความ Error ด้านบน
)

echo.
pause
