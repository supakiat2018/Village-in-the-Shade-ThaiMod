with open(r"D:\Users\Supakiat\Desktop\Village-in-the-Shade-Trainer\trainer.py", "r", encoding="utf-8", errors="ignore") as f:
    lines = f.readlines()

for i in range(215, 345):
    print(f"{i+1}: {lines[i].rstrip()}")
