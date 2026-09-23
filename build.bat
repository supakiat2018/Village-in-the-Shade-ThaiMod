@echo off
echo Compiling text_dump.dll with zig cc...
zig cc -shared -O2 -s src\text_dump.c src\addrsig.c src\minhook-master\src\buffer.c src\minhook-master\src\hook.c src\minhook-master\src\trampoline.c src\minhook-master\src\hde\hde64.c -o Mods\TextDump\text_dump.dll -lkernel32 -luser32
if %ERRORLEVEL% EQU 0 (
    echo SUCCESS: Mods\TextDump\text_dump.dll built successfully!
) else (
    echo ERROR: Compilation failed!
)
pause
