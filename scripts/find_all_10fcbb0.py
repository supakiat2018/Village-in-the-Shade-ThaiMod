with open(r"D:\Users\Supakiat\Desktop\Village-in-the-Shade-Trainer\trainer.py", "r", encoding="utf-8", errors="ignore") as f:
    lines = f.readlines()

for i, line in enumerate(lines):
    if "10FCBB0" in line:
        print(f"Line {i+1}: {line.strip()}")
