@echo off
chcp 65001 >nul
title ติดตั้งม็อดภาษาไทย (มีคีย์บอร์ดไทย - ไม่มีสูตร)
set "GAME_ROOT=C:\Program Files (x86)\Steam\steamapps\common\Village in the Shade"

if not exist "%GAME_ROOT%\village.exe" (
    echo [ERROR] ไม่พบโฟลเดอร์เกมที่: %GAME_ROOT%
    pause
    exit /b 1
)

echo กำลังติดตั้งม็อดภาษาไทย (ชุดมีคีย์บอร์ดไทย)...
copy /y "%~dp0winmm.dll" "%GAME_ROOT%\winmm.dll" >nul
if not exist "%GAME_ROOT%\Mods\TextDump" mkdir "%GAME_ROOT%\Mods\TextDump"
copy /y "%~dp0Mods\TextDump\text_dump.dll" "%GAME_ROOT%\Mods\TextDump\text_dump.dll" >nul

echo.
echo [SUCCESS] ติดตั้งเรียบร้อยแล้ว! สามารถเปิดเกมเล่นได้ทันทีครับ
echo.
pause
