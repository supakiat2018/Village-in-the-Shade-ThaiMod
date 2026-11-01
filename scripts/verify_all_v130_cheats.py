import struct

exe_path = r"C:\Program Files (x86)\Steam\steamapps\common\Village in the Shade\village.exe.bak"

with open(exe_path, "rb") as f:
    exe_data = f.read()

rva_to_file = lambda rva: rva - 0x1000 + 0x400

v130_cheats = [
    {
        "id": "god_mode",
        "rva": 0x13DA80,
        "orig": bytes.fromhex("40 53 48"),
        "patch": bytes.fromhex("B0 01 C3")
    },
    {
        "id": "noclip",
        "rva": 0x6DBCF0,
        "orig": bytes.fromhex("40 53 48 83 EC 30"),
        "patch": bytes.fromhex("31 C0 C3 90 90 90")
    },
    {
        "id": "infinite_items",
        "rva": 0x1560E0,
        "orig": bytes.fromhex("48 89 5C 24 08 48"),
        "patch": bytes.fromhex("B8 01 00 00 00 C3")
    },
    {
        "id": "crafting_free",
        "rva": 0x38A760,
        "orig": bytes.fromhex("48 89 5C"),
        "patch": bytes.fromhex("B0 01 C3")
    },
    {
        "id": "cooking_free",
        "rva": 0x384320,
        "orig": bytes.fromhex("48 89 5C"),
        "patch": bytes.fromhex("B0 01 C3")
    },
    {
        "id": "smithing_free",
        "rva": 0x345E60,
        "orig": bytes.fromhex("48 89 5C"),
        "patch": bytes.fromhex("B0 01 C3")
    },
    {
        "id": "building_free",
        "rva": 0x37D340,
        "orig": bytes.fromhex("48 89 5C"),
        "patch": bytes.fromhex("B0 01 C3")
    },
    {
        "id": "dyeing_free",
        "rva": 0x39EA80,
        "orig": bytes.fromhex("48 89 5C"),
        "patch": bytes.fromhex("B0 01 C3")
    },
    {
        "id": "submit_any_item",
        "rva": 0x356264,
        "orig": bytes.fromhex("0F 84 BA 03 00 00"),
        "patch": bytes.fromhex("90 90 90 90 90 90")
    }
]

print("=== VERIFYING v1.30 CHEAT SITES ===")
all_ok = True
for c in v130_cheats:
    foff = rva_to_file(c["rva"])
    actual = exe_data[foff : foff + len(c["orig"])]
    ok = (actual == c["orig"])
    print(f"[{'OK' if ok else 'FAIL'}] {c['id']:<18} RVA 0x{c['rva']:X} (File 0x{foff:X}): Expected {c['orig'].hex(' ')} -> Actual {actual.hex(' ')}")
    if not ok:
        all_ok = False

print("\nAll patch sites verified:", all_ok)
