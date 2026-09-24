import os

source_dir = r"C:\Users\Supakiat\Desktop\คลังคำแปล_Village_in_the_Shade\01_PC"

def load_pairs(fname):
    pairs = {}
    fpath = os.path.join(source_dir, fname)
    with open(fpath, "r", encoding="utf-8", errors="ignore") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            jp, th = line.split("=", 1)
            pairs[jp.strip()] = th.strip()
    return pairs

cmd_pairs = load_pairs("cmd_จับคู่คำแปล_PC_JP_TH.txt")
gs_pairs = load_pairs("gameSetting_จับคู่คำแปล_PC_JP_TH.txt")
str_pairs = load_pairs("string_จับคู่คำแปล_PC_JP_TH.txt")

print(f"cmd unique keys: {len(cmd_pairs)}")

# Check collisions
for name, other_pairs in [("gameSetting", gs_pairs), ("string", str_pairs)]:
    conflicts = []
    matches = []
    for k, v in cmd_pairs.items():
        if k in other_pairs:
            if other_pairs[k] == v:
                matches.append(k)
            else:
                conflicts.append((k, v, other_pairs[k]))
    print(f"\nComparing cmd vs {name}:")
    print(f"  Exact matches: {len(matches)}")
    print(f"  Conflicts: {len(conflicts)}")
    for k, cv, ov in conflicts:
        print(f"    Key '{k}': cmd='{cv}' vs {name}='{ov}'")
