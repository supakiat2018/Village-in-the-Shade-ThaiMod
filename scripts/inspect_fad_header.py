fairy_path = r"C:\Program Files (x86)\Steam\steamapps\common\Village in the Shade\data\fairy_1_00.dat"

with open(fairy_path, "rb") as f:
    f.seek(0x6F74F400)
    data = f.read(512)
    print("First 64 bytes hex:")
    print(data[:64].hex(" "))
    print("\nText representation:")
    print("".join(chr(b) if 32 <= b < 127 else "." for b in data[:256]))
