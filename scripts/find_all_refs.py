import struct
import capstone

exe_path = r"C:\Program Files (x86)\Steam\steamapps\common\Village in the Shade\village.exe.bak"

with open(exe_path, "rb") as f:
    exe_data = f.read()

e_lfanew = struct.unpack_from("<I", exe_data, 0x3C)[0]
num_sections = struct.unpack_from("<H", exe_data, e_lfanew + 6)[0]
opt_hdr_size = struct.unpack_from("<H", exe_data, e_lfanew + 20)[0]
sec_tbl_offset = e_lfanew + 24 + opt_hdr_size
image_base = struct.unpack_from("<Q", exe_data, e_lfanew + 24 + 24)[0]

text_sec = None
for i in range(num_sections):
    sec_off = sec_tbl_offset + i * 40
    name = exe_data[sec_off:sec_off+8].rstrip(b'\x00').decode('latin1')
    vsize, vaddr, rsize, raddr = struct.unpack_from("<IIII", exe_data, sec_off + 8)
    if name == ".text":
        text_sec = (vaddr, vsize, raddr, rsize)
        break

target_ptr_va = image_base + 0x111CC90
target_ptr_rva = 0x111CC90

print(f"Searching for RIP-relative references to RVA 0x{target_ptr_rva:X}...")

text_raw = exe_data[text_sec[2] : text_sec[2] + text_sec[3]]
md = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_64)

# Find in raw bytes: any 48 8B / 48 8D etc with disp matching target_ptr_rva - (curr_rva + 7)
refs = []
for i in range(len(text_raw) - 7):
    # Check if disp32 targets target_ptr_rva
    disp = struct.unpack_from("<i", text_raw, i + 3)[0]
    curr_rva = text_sec[0] + i
    # typical 7-byte instruction (e.g. 48 8B 05 xx xx xx xx)
    if curr_rva + 7 + disp == target_ptr_rva:
        refs.append((curr_rva, i))

print(f"Found {len(refs)} references!")

for curr_rva, raw_offset in refs[:20]:
    va = image_base + curr_rva
    chunk = text_raw[raw_offset : raw_offset + 120]
    print(f"\n--- Reference at VA 0x{va:X} (RVA 0x{curr_rva:X}, File 0x{text_sec[2]+raw_offset:X}) ---")
    count = 0
    for insn in md.disasm(chunk, va):
        print(f"    0x{insn.address:X}: {insn.mnemonic:<8} {insn.op_str}")
        count += 1
        if count >= 12:
            break
