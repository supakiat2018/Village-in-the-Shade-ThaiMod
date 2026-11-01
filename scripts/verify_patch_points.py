import struct

exe_path = r"C:\Program Files (x86)\Steam\steamapps\common\Village in the Shade\village.exe"
with open(exe_path, "rb") as f:
    data = f.read()

# Point 1: putStr entry (RVA 0x9AC180 -> FileOffset 0x9AB580)
# Original: 48 8b c4 55 53 (mov rax, rsp; push rbp; push rbx)
# Patch:    e9 8b f7 ff ff (jmp putStrProp at 0x9AB910)
foff1 = 0x9AB580
orig1 = data[foff1:foff1+5]
print("Point 1 (putStr entry):", orig1.hex())
assert orig1 == bytes.fromhex("488bc45553"), f"Mismatch at Point 1: {orig1.hex()}"

# Point 2: conditional call in 0x96AC62 (FileOffset 0x96A062)
# Original: 74 07 (je 0x14096ac93)
# Patch:    90 90 (nop nop)
foff2 = 0x96A062
orig2 = data[foff2:foff2+2]
print("Point 2 (call putStrProp):", orig2.hex())
assert orig2 == bytes.fromhex("7407"), f"Mismatch at Point 2: {orig2.hex()}"

# Point 3: dispatcher jump (FileOffset 0x9ABE4E)
# Original: 0f 85 bc ee ff ff (jne 0x1409ab910)
# Patch:    e9 bd ee ff ff 90 (jmp 0x1409ab910; nop)
foff3 = 0x9ABE4E
orig3 = data[foff3:foff3+6]
print("Point 3 (dispatcher jne):", orig3.hex())
assert orig3 == bytes.fromhex("0f85bceeffff"), f"Mismatch at Point 3: {orig3.hex()}"

# Point 4: putStrAlign conditional (FileOffset 0x9AC041)
# Original: 0f 85 9f 01 00 00 (jne 0x1409acde6)
# Patch:    e9 a0 01 00 00 90 (jmp 0x1409acde6; nop)
foff4 = 0x9AC041
orig4 = data[foff4:foff4+6]
print("Point 4 (putStrAlign jne):", orig4.hex())
assert orig4 == bytes.fromhex("0f859f010000"), f"Mismatch at Point 4: {orig4.hex()}"

print("\nALL 4 POINTS VERIFIED AND MATCH EXACTLY!")
