with open(r"D:\Users\Supakiat\Desktop\Village-in-the-Shade-Trainer\trainer.py", "r", encoding="utf-8", errors="ignore") as f:
    text = f.read()

import re
print("Length of trainer.py:", len(text))
for line in text.splitlines()[:50]:
    print(line)
