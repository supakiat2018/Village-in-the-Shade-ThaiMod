@echo off
chcp 65001 >nul
echo =======================================================================
echo  กำลังแปลงภาพ minimap_onsen (*.png) ใน onsen_textures_original เป็น NLTX
echo =======================================================================
python "%~dp0tools\convert_onsen_to_nltx.py"
echo.
pause
