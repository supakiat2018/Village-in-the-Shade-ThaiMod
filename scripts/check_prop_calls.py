import struct
import capstone

exe_path = r"C:\Program Files (x86)\Steam\steamapps\common\Village in the Shade\village.exe"
with open(exe_path, "rb") as f:
    data = f.read()

md = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_64)

# Disassemble putStrProp: RVA 0x9AB910 (FileOffset 0x9AAD10)
foff = 0x9AAD10
code = data[foff : foff + 0x870] # to 0x9AC180

calls_to_putstr = []
for ins in md.disasm(code, 0x1409AB910):
    if ins.mnemonic in ("call", "jmp"):
        if "9ac18" in ins.op_str.lower():
            calls_to_putstr.append(f"0x{ins.address:X}: {ins.mnemonic} {ins.op_str}")

print(f"Calls/Jumps to putStr from putStrProp: {len(calls_to_putstr)}")
for c in calls_to_putstr:
    print("  ", c)
