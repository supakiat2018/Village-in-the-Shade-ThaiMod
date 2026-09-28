import os, glob, csv

mover_dir = r"C:\Users\Supakiat\Desktop\Mover\QuickBMS\ตารางแปล"
mod_dir = r"C:\Program Files (x86)\Steam\steamapps\common\Village in the Shade\Mods\TextDump"

# 1. Read dumped unique texts
dumped = []
with open(os.path.join(mod_dir, "dump_unique.txt"), "r", encoding="utf-8", errors="ignore") as f:
    for line in f:
        if "*/" in line:
            t = line.split("*/", 1)[1].strip()
            if t and t not in dumped:
                dumped.append(t)

print(f"Total dumped unique strings to test: {len(dumped)}")

# 2. Search each dumped text in Mover CSV files
csv_files = glob.glob(os.path.join(mover_dir, "*.csv"))

found_map = {t: [] for t in dumped}

for cpath in csv_files:
    cname = os.path.basename(cpath)
    with open(cpath, "r", encoding="utf-8", errors="ignore") as f:
        reader = csv.reader(f)
        header = next(reader, [])
        for row_idx, row in enumerate(reader):
            for col_idx, cell in enumerate(row):
                cell_clean = cell.strip()
                for t in dumped:
                    if t == cell_clean:
                        found_map[t].append((cname, row_idx + 1, header[col_idx] if col_idx < len(header) else str(col_idx), cell_clean, row, header))

print("\n================ RESULTS OF EXACT MATCH SEARCH ================")
found_count = 0
not_found = []

for t in dumped:
    hits = found_map[t]
    if hits:
        found_count += 1
        cname, row_num, col_name, cell, full_row, header = hits[0]
        print(f"[FOUND] \"{t}\"")
        print(f"   -> File: {cname} (Row {row_num}, Col: {col_name})")
        th_cols = [i for i, h in enumerate(header) if "th" in h.lower() or "แปล" in h or "pua" in h.lower()]
        for idx in th_cols:
            if idx < len(full_row) and full_row[idx]:
                print(f"      {header[idx]}: {full_row[idx]}")
    else:
        not_found.append(t)

print(f"\nSummary: Found {found_count}/{len(dumped)} strings in CSVs!")
if not_found:
    print(f"Not found ({len(not_found)}): {not_found}")
