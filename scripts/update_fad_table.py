import re
import sys
import os

sys.path.insert(0, r"D:\Users\Supakiat\Desktop\Village_in_the_Shade_ThaiMod_Dev")
import build_perfect_table

c_file = r"D:\Users\Supakiat\Desktop\Village_in_the_Shade_ThaiMod_Dev\src\text_dump.c"
with open(c_file, "r", encoding="utf-8") as f:
    content = f.read()

new_table_lines = ["static const FadMappingDef g_fad_mapping_defs[] = {"]
for idx, orig_file, alt_file, w, h, rel_off in sorted(build_perfect_table.mapped_entries, key=lambda x: x[0]):
    if orig_file == "ui_keyboard_font.nltx":
        new_table_lines.append("#ifdef ENABLE_THAI_KEYBOARD")
        new_table_lines.append(f'    {{ {idx:3d}, "{orig_file}", "{alt_file}", {w:4d}, {h:4d} }}, /* RelOff=0x{rel_off:08X} */')
        new_table_lines.append("#else")
        new_table_lines.append(f'    {{ {idx:3d}, "{orig_file}", "{orig_file}", {w:4d}, {h:4d} }}, /* RelOff=0x{rel_off:08X} */')
        new_table_lines.append("#endif")
    else:
        new_table_lines.append(f'    {{ {idx:3d}, "{orig_file}", "{alt_file}", {w:4d}, {h:4d} }}, /* RelOff=0x{rel_off:08X} */')
new_table_lines.append("};")
new_table_str = "\n".join(new_table_lines)

# Replace g_fad_mapping_defs
pattern = r"static const FadMappingDef g_fad_mapping_defs\[\] = \{.*?\};"
content = re.sub(pattern, new_table_str, content, flags=re.DOTALL)

# Replace loop in resolve_dynamic_fad_offsets_w
old_loop = """    for (size_t i = 0; i < num_defs; i++) {
        int idx = g_fad_mapping_defs[i].toc_index;
        size_t pos = 0x1018 + (size_t)idx * 32;
        if (pos + 12 > sizeof(fad_hdr)) continue;

        uint64_t entry_sz = *(uint64_t*)(fad_hdr + pos + 0);
        uint32_t rel_off = *(uint32_t*)(fad_hdr + pos + 8);"""

new_loop = """    for (size_t i = 0; i < num_defs; i++) {
        int idx = g_fad_mapping_defs[i].toc_index;
        size_t pos = 0x0FC0 + (size_t)idx * 32;
        if (pos + 32 > sizeof(fad_hdr)) continue;

        uint32_t rel_off = *(uint32_t*)(fad_hdr + pos + 0);
        uint64_t entry_sz = *(uint64_t*)(fad_hdr + pos + 24);"""

if old_loop in content:
    content = content.replace(old_loop, new_loop)
    print("Replaced resolve_dynamic_fad_offsets_w loop successfully!")
else:
    print("WARNING: old_loop not found!")

with open(c_file, "w", encoding="utf-8") as f:
    f.write(content)

print(f"Updated text_dump.c with {len(build_perfect_table.mapped_entries)} entries and 0x0FC0 base!")
