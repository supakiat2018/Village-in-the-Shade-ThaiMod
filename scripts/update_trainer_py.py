import shutil

src_file = r"D:\Users\Supakiat\Desktop\Village-in-the-Shade-Trainer\trainer.py"
bak_file = r"D:\Users\Supakiat\Desktop\Village-in-the-Shade-Trainer\trainer.py.bak"

shutil.copy2(src_file, bak_file)

with open(src_file, "r", encoding="utf-8") as f:
    content = f.read()

# Add game_version and global_ptr_rva to GameMemoryManager __init__
old_init = """class GameMemoryManager:
    def __init__(self):
        self.pid = 0
        self.base_addr = 0
        self.h_process = None
        self.cheat_states = {c["id"]: False for c in CHEATS_DEF}
        self.frozen_time = None
        self.access_denied_pid = None"""

new_init = """class GameMemoryManager:
    def __init__(self):
        self.pid = 0
        self.base_addr = 0
        self.h_process = None
        self.game_version = "1.20"
        self.global_ptr_rva = 0x10FCBB0
        self.cheat_states = {c["id"]: False for c in CHEATS_DEF}
        self.frozen_time = None
        self.access_denied_pid = None"""

assert old_init in content, "old_init not found"
content = content.replace(old_init, new_init, 1)

# Add detect_game_version method and call it in attach_game
detect_method = """    def detect_game_version(self):
        # In v1.30, God Mode RVA is 0x13DA80, bytes are 40 53 48 (or B0 01 C3 if patched)
        bytes_130 = self.read_memory(self.base_addr + 0x13DA80, 3)
        if bytes_130 in (b"\\x40\\x53\\x48", b"\\xb0\\x01\\xc3"):
            self.game_version = "1.30"
            self.global_ptr_rva = 0x111CC90
            rva_map = {
                "god_mode": 0x13DA80,
                "noclip": 0x6DBCF0,
                "infinite_items": 0x1560E0,
                "crafting_free": 0x38A760,
                "cooking_free": 0x384320,
                "smithing_free": 0x345E60,
                "building_free": 0x37D340,
                "dyeing_free": 0x39EA80,
                "submit_any_item": 0x356264,
            }
        else:
            self.game_version = "1.20"
            self.global_ptr_rva = 0x10FCBB0
            rva_map = {
                "god_mode": 0x13B010,
                "noclip": 0x6C4A80,
                "infinite_items": 0x153600,
                "crafting_free": 0x375D10,
                "cooking_free": 0x36F8D0,
                "smithing_free": 0x339C00,
                "building_free": 0x3688D0,
                "dyeing_free": 0x38A030,
                "submit_any_item": 0x3413F4,
            }
        for c in CHEATS_DEF:
            if c["id"] in rva_map:
                c["rva"] = rva_map[c["id"]]

"""

attach_needle = """            # พบโปรเซสเกมที่ใช้งานได้จริง!
            self.pid = found_pid
            self.base_addr = mod_base
            self.h_process = h_proc"""

attach_replace = """            # พบโปรเซสเกมที่ใช้งานได้จริง!
            self.pid = found_pid
            self.base_addr = mod_base
            self.h_process = h_proc

            # ตรวจสอบเวอร์ชันเกมอัตโนมัติ (v1.20 หรือ v1.30)
            self.detect_game_version()"""

assert attach_needle in content, "attach_needle not found"
content = content.replace(attach_needle, attach_replace, 1)

# Insert detect_game_version above get_save_data_ptr
save_data_needle = "    def get_save_data_ptr(self):"
assert save_data_needle in content, "save_data_needle not found"
content = content.replace(save_data_needle, detect_method + save_data_needle, 1)

# Replace 0x10FCBB0 with self.global_ptr_rva
content = content.replace("self.base_addr + 0x10FCBB0", "self.base_addr + self.global_ptr_rva")

with open(src_file, "w", encoding="utf-8") as f:
    f.write(content)

print("Updated trainer.py successfully!")
