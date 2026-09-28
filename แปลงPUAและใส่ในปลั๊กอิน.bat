@echo off
chcp 65001 > nul
title แปลงตารางคำแปลเป็น PUA ด้วย csv_to_pua_gui.py และใส่ในปลั๊กอิน

echo ======================================================================
echo    แปลงตารางจับคู่คำแปล_ไทย_JP.txt เป็นรหัส PUA 
echo    โดยใช้โมดูล C:\Users\Supakiat\Desktop\Mover\out\csv_to_pua_gui.py
echo    และติดตั้งใส่ในปลั๊กอิน Mods\TextDump
echo ======================================================================
echo.

python "%~dp0scripts\convert_to_pua_and_install.py"
if %errorlevel% neq 0 (
    echo [ERROR] เกิดข้อผิดพลาดในการแปลง PUA
    pause
    exit /b %errorlevel%
)

echo.
echo [SUCCESS] แปลงและติดตั้งใส่ในปลั๊กอินเรียบร้อยแล้ว!
echo.
pause
