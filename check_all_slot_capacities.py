import os

# Read v130_toc_dump.txt
with open(r"D:\Users\Supakiat\Desktop\Village_in_the_Shade_ThaiMod_Dev\scratch\v130_toc_dump.txt", "r", encoding="utf-8") as f:
    toc_lines = f.readlines()

toc_entries = []
for line in toc_lines:
    if line.startswith("TOC["):
        idx = int(line.split("]")[0].split("[")[1].strip())
        name = line.split(":")[1].split("(")[0].strip()
        base_name = os.path.splitext(name)[0]
        dim_str = line.split("(")[1].split(")")[0]
        w, h = [int(x.strip()) for x in dim_str.split("x")]
        rel_off = int(line.split("rel_off=")[1].split()[0], 16)
        sz = int(line.split("sz=")[1].strip())
        toc_entries.append({
            "idx": idx,
            "name": base_name,
            "w": w,
            "h": h,
            "rel_off": rel_off,
            "sz": sz
        })

# Compute slot capacity for each TOC entry: next_rel_off - curr_rel_off
for i in range(len(toc_entries) - 1):
    toc_entries[i]["slot_cap"] = toc_entries[i+1]["rel_off"] - toc_entries[i]["rel_off"]
toc_entries[-1]["slot_cap"] = 999999999

toc_by_idx = {e["idx"]: e for e in toc_entries}

# Now inspect our 71 mapped textures
import build_perfect_table
mapped = build_perfect_table.mapped_entries

tex_dir = r"C:\Program Files (x86)\Steam\steamapps\common\Village in the Shade\Mods\TextDump\textures"

print(f"{'Idx':<4} {'Texture Name':<35} {'Dim':<12} {'Mod Size':<10} {'Slot Cap':<10} {'Status'}")
print("-" * 85)

overflows = []
for idx, orig_file, alt_file, w, h, rel_off in sorted(mapped, key=lambda x: x[0]):
    entry = toc_by_idx[idx]
    slot_cap = entry["slot_cap"]
    # Check size of mod file
    p1 = os.path.join(tex_dir, alt_file)
    p2 = os.path.join(tex_dir, orig_file)
    file_size = 0
    actual_file = None
    if os.path.exists(p1):
        file_size = os.path.getsize(p1)
        actual_file = alt_file
    elif os.path.exists(p2):
        file_size = os.path.getsize(p2)
        actual_file = orig_file
    
    status = "OK"
    if file_size > slot_cap:
        status = f"OVERFLOW by {file_size - slot_cap} B!"
        overflows.append((idx, orig_file, file_size, slot_cap))
    
    print(f"{idx:3d}  {orig_file:<35} {w}x{h:<7} {file_size:8d} B {slot_cap:8d} B  {status}")

print("\n" + "=" * 85)
print(f"Total textures checked: {len(mapped)}")
print(f"Total overflows found: {len(overflows)}")
for idx, name, fsz, cap in overflows:
    print(f"  [OVERFLOW] TOC[{idx:3d}] {name}: file={fsz} B > slot={cap} B (diff: {fsz - cap} B)")
