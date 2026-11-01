with open(r"D:\Users\Supakiat\Desktop\Village-in-the-Shade-Trainer\trainer.py", "r", encoding="utf-8", errors="ignore") as f:
    lines = f.readlines()

for i, line in enumerate(lines):
    if "def attach_game" in line or "def get_save_data_ptr" in line:
        for j in range(i, min(len(lines), i + 35)):
            print(f"{j+1}: {lines[j].rstrip()}")
        print("="*50)
