import os
import shutil

orig_exe = r"C:\Program Files (x86)\Steam\steamapps\common\Village in the Shade\village.exe"
with open(orig_exe, "rb") as f:
    exe_data = bytearray(f.read())

# Patches for Proportional / Compact Text Spacing ONLY:
patches = [
    # Point 1: putStr entry -> jmp putStrProp
    (0x9AB580, bytes.fromhex("e98bf7ffff"), "putStr -> jmp putStrProp"),
    # Point 2: conditional call in 0x96AC62 -> nop nop (always call putStrProp)
    (0x96A062, bytes.fromhex("9090"), "Force call putStrProp"),
    # Point 3: dispatcher jne -> jmp putStrProp; nop
    (0x9ABE4E, bytes.fromhex("e9bdeeffff90"), "Dispatcher -> jmp putStrProp"),
    # Point 4: putStrAlign conditional -> jmp proportional; nop
    (0x9AC041, bytes.fromhex("e9a001000090"), "putStrAlign -> jmp Proportional"),
]

for offset, patch_bytes, desc in patches:
    orig_bytes = exe_data[offset : offset + len(patch_bytes)]
    exe_data[offset : offset + len(patch_bytes)] = patch_bytes
    print(f"Applied: {desc} at 0x{offset:X} ({orig_bytes.hex()} -> {patch_bytes.hex()})")

# Output paths
out_paths = [
    r"C:\Program Files (x86)\Steam\steamapps\common\Village in the Shade\village_ตัวชิดกัน.exe",
    r"C:\Users\Administrator\Desktop\village_ตัวชิดกัน.exe",
    r"D:\Users\Supakiat\Desktop\Village_in_the_Shade_ThaiMod_Dev\village_ตัวชิดกัน.exe"
]

for out_path in out_paths:
    with open(out_path, "wb") as f:
        f.write(exe_data)
    print(f"Saved: {out_path} ({len(exe_data):,} bytes)")

print("\nSUCCESS: All compact-spacing patched executables created!")
