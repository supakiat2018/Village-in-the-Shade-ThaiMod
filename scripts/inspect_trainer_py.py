with open(r"D:\Users\Supakiat\Desktop\Village-in-the-Shade-Trainer\trainer.py", "r", encoding="utf-8", errors="ignore") as f:
    lines = f.readlines()

for i, line in enumerate(lines):
    if '"rva":' in line or '0x10FCBB0' in line:
        for j in range(max(0, i-4), min(len(lines), i+12)):
            print(f"{j+1}: {lines[j].rstrip()}")
        print("="*50)
