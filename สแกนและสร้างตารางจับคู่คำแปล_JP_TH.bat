@echo off
chcp 65001 > nul
title สแกนและสร้างตารางจับคู่คำแปล JP-TH

echo ======================================================================
echo    โครงการม็อดภาษาไทย: Village in the Shade (ほの暮しの庭)
echo    กำลังสแกนคำแปลจากทั้ง 3 แหล่งข้อมูล และสร้างไฟล์จับคู่คำแปล
echo ======================================================================
echo.

python "%~dp0scripts\scan_and_build_jp_th.py"
if %errorlevel% neq 0 (
    echo [ERROR] เกิดข้อผิดพลาดในการสแกนตารางคำแปล
    pause
    exit /b %errorlevel%
)

echo.
echo ======================================================================
echo    กำลังแปลงฟอนต์ PUA และติดตั้งลงใน Mods\TextDump...
echo ======================================================================
echo.

python "%~dp0scripts\build_full_translation.py"
if %errorlevel% neq 0 (
    echo [ERROR] เกิดข้อผิดพลาดในการติดตั้ง translation.txt
    pause
    exit /b %errorlevel%
)

echo.
echo [SUCCESS] ดำเนินการเสร็จสิ้นสมบูรณ์ 100%!
echo.
pause
