@echo off
chcp 65001 >nul
title Village in the Shade - Mod Build Tool

echo ========================================================
echo  Building Village in the Shade Thai Mod (text_dump.dll)
echo ========================================================
echo.

where zig >nul 2>nul
if %ERRORLEVEL% neq 0 (
    echo [ERROR] ไม่พบ Zig Compiler ในเครื่อง!
    echo กรุณาติดตั้ง Zig หรือเพิ่ม path ของ zig.exe ใน Environment Variables
    echo.
    pause
    exit /b 1
)

echo [1/2] กำลังคอมไพล์ซอร์สโค้ดภาษา C ด้วย Zig CC...
zig cc -shared -O2 -s ^
    src\text_dump.c ^
    src\addrsig.c ^
    src\minhook-master\src\buffer.c ^
    src\minhook-master\src\hook.c ^
    src\minhook-master\src\trampoline.c ^
    src\minhook-master\src\hde\hde64.c ^
    -o bin\text_dump.dll ^
    -lkernel32 -luser32 -lgdi32

if %ERRORLEVEL% equ 0 (
    echo.
    echo [SUCCESS] คอมไพล์สำเร็จเรียบร้อย!
    echo ไฟล์ปลายทาง: bin\text_dump.dll
    echo.
    echo ต้องการก๊อปปี้ไปติดตั้งในโฟลเดอร์เกมทันทีหรือไม่? (Y/N)
    set /p INSTALL_CHOICE="เลือก (Y/N): "
    if /i "%INSTALL_CHOICE%"=="Y" (
        set "GAME_MOD_DIR=C:\Program Files (x86)\Steam\steamapps\common\Village in the Shade\Mods\TextDump"
        if exist "%GAME_MOD_DIR%" (
            copy /y bin\text_dump.dll "%GAME_MOD_DIR%\text_dump.dll" >nul
            echo [INSTALLED] ติดตั้ง text_dump.dll ลงในโฟลเดอร์เกมเรียบร้อยแล้ว!
        ) else (
            echo [WARNING] ไม่พบโฟลเดอร์ Mods\TextDump ในเกม กรุณาก๊อปปี้ด้วยตนเอง
        )
    )
) else (
    echo.
    echo [ERROR] คอมไพล์ไม่ผ่าน กรุณาตรวจสอบข้อความ Error ด้านบน
)

echo.
pause
