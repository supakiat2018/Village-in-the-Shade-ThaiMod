import glob, csv, os, re

csv_files = glob.glob(r"D:\Users\Supakiat\Desktop\Village_in_the_Shade_ThaiMod_Dev\*_extracted.csv")
jp_map = {}

for cf in csv_files:
    fname = os.path.basename(cf)
    with open(cf, "r", encoding="utf-8", errors="ignore") as f:
        reader = csv.DictReader(f)
        for row in reader:
            jp = (row.get("text_jp") or "").strip()
            th = (row.get("text_th_pua") or row.get("text_th") or "").strip()
            if jp and th and re.search(r"[\u3040-\u30ff\u4e00-\u9faf]", jp):
                if jp not in jp_map:
                    jp_map[jp] = {}
                jp_map[jp][fname] = th

real_conflicts = {}
for jp, sources in jp_map.items():
    unique_th = set(sources.values())
    if len(unique_th) > 1:
        real_conflicts[jp] = sources

print(f"Total Unique Japanese strings in CSVs: {len(jp_map)}")
print(f"Conflicting Japanese strings across CSVs: {len(real_conflicts)}")

print("\n--- Actual Japanese Translation Conflicts (Sample 20) ---")
for jp, sources in list(real_conflicts.items())[:20]:
    print(f"\nJP: \"{jp}\"")
    for src, th in sources.items():
        print(f"   [{src}]: {th}")
