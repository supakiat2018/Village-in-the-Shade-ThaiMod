import re

ct120_path = r"D:\Users\Supakiat\Desktop\Village-in-the-Shade-Trainer\Village in the Shade1.20.CT"
ct130_path = r"D:\Users\Supakiat\Desktop\Village-in-the-Shade-Trainer\Village in the Shade1.30.CT"

with open(ct120_path, "r", encoding="utf-8") as f:
    ct_data = f.read()

# Replace header and base pointer
ct130_data = ct_data.replace("Game v1.20", "Game v1.30")
ct130_data = ct130_data.replace('"village.exe"+10FCBB0', '"village.exe"+111CC90')
ct130_data = ct130_data.replace('"village.exe"+10fcbb0', '"village.exe"+111CC90')

with open(ct130_path, "w", encoding="utf-8") as f:
    f.write(ct130_data)

print("Created Village in the Shade1.30.CT successfully!")

# Copy to Desktop as well
with open(r"C:\Users\Administrator\Desktop\Village in the Shade1.30.CT", "w", encoding="utf-8") as f:
    f.write(ct130_data)
print("Copied to Desktop successfully!")
