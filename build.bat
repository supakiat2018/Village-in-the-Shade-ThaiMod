@echo off
chcp 65001 >nul
title Village in the Shade - Mod Build Tool (v1.30 Unified Single Edition)

echo ========================================================
echo  Building Village in the Shade Thai Mod v1.30
echo  [Unified Single Target: text_dump.dll + winmm.dll]
echo ========================================================
echo.

where zig >nul 2>nul
if %ERRORLEVEL% neq 0 (
    echo [ERROR] ไม่พบ Zig Compiler ในเครื่อง!
    echo.
    pause
    exit /b 1
)

echo [1/2] คอมไพล์ม็อดเวอร์ชันเดียวจบ (Thai Keyboard + Cheats + Engine Guard)...
zig cc -shared -O2 -s -m64 -DENABLE_THAI_KEYBOARD -DENABLE_CHEATS ^
    src\text_dump.c ^
    src\addrsig.c ^
    src\cheats.c ^
    src\speedhack.c ^
    src\minhook-master\src\buffer.c ^
    src\minhook-master\src\hook.c ^
    src\minhook-master\src\trampoline.c ^
    src\minhook-master\src\hde\hde64.c ^
    -o bin\text_dump.dll ^
    -lkernel32 -luser32 -lgdi32 -lwinmm

if %ERRORLEVEL% neq 0 (
    echo.
    echo [ERROR] คอมไพล์ text_dump.dll ไม่ผ่าน!
    pause
    exit /b 1
)

echo [2/2] คอมไพล์ตัวเชื่อมระบบ (winmm.dll)...
zig cc -shared -O2 -s src\proxy_winmm.c src\winmm.def -o bin\winmm.dll -lkernel32

if %ERRORLEVEL% equ 0 (
    echo.
    echo [SUCCESS] คอมไพล์สำเร็จสมบูรณ์ (Single Version)!
    echo เรียกสคริปต์กระจายไฟล์แพ็กเกจ...
    py scripts\deploy_all.py
) else (
    echo.
    echo [ERROR] คอมไพล์ winmm.dll ไม่ผ่าน กรุณาตรวจสอบข้อความ Error ด้านบน
)

echo.
pause
