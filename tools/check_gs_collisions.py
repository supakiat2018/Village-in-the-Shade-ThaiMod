import os
import glob

source_dir = r"C:\Users\Supakiat\Desktop\คลังคำแปล_Village_in_the_Shade\01_PC"
files = glob.glob(os.path.join(source_dir, "*.txt"))

gs_file = os.path.join(source_dir, "gameSetting_จับคู่คำแปล_PC_JP_TH.txt")
gs_pairs = {}
with open(gs_file, "r", encoding="utf-8") as f:
    for line in f:
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        jp, th = line.split("=", 1)
        gs_pairs[jp.strip()] = th.strip()

print(f"gameSetting has {len(gs_pairs)} unique JP keys")

collisions = []
for fpath in files:
    fname = os.path.basename(fpath)
    if fname == "gameSetting_จับคู่คำแปล_PC_JP_TH.txt":
        continue
    with open(fpath, "r", encoding="utf-8", errors="ignore") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            jp, th = line.split("=", 1)
            jp = jp.strip()
            th = th.strip()
            if jp in gs_pairs:
                if th != gs_pairs[jp]:
                    collisions.append((jp, gs_pairs[jp], th, fname))

print(f"Total conflicting collisions with gameSetting: {len(collisions)}")
for jp, gs_th, other_th, fname in collisions:
    print(f"  Conflict on '{jp}':")
    print(f"    gameSetting: '{gs_th}'")
    print(f"    {fname}: '{other_th}'")
