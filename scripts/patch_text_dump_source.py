with open(r"D:\Users\Supakiat\Desktop\Village_in_the_Shade_ThaiMod_Dev\src\text_dump.c", "r", encoding="utf-8") as f:
    content = f.read()

# 1. Update includes
old_inc = """#include "cheats.h"
#include "keyboard_v120_patch.h" """
# let's be flexible with whitespace
import re
content = re.sub(
    r'#include\s+"cheats\.h"\s*\r?\n\s*#include\s+"keyboard_v120_patch\.h"',
    '''#ifdef ENABLE_CHEATS\n#include "cheats.h"\n#endif\n\n#ifdef ENABLE_THAI_KEYBOARD\n#include "keyboard_v130_patch.h"\n#endif''',
    content
)

# 2. Update keyboard texture redirection
content = re.sub(
    r'\{\s*110,\s*"ui_keyboard_font\.nltx",\s*"ui_keyboard_font_thai\.nltx",\s*1024,\s*2048\s*\},',
    '''#ifdef ENABLE_THAI_KEYBOARD\n    { 110, "ui_keyboard_font.nltx", "ui_keyboard_font_thai.nltx", 1024, 2048 },\n#else\n    { 110, "ui_keyboard_font.nltx", "ui_keyboard_font.nltx", 1024, 2048 },\n#endif''',
    content
)

# 3. Update keyboard patch call
content = re.sub(
    r'/\*\s*6\.\s*Patch In-Game Virtual Keyboard[^\n]*\*/\s*\r?\n\s*patch_virtual_keyboard_in_memory\([^)]*\);',
    '''#ifdef ENABLE_THAI_KEYBOARD\n    /* 6. Patch In-Game Virtual Keyboard string table in memory (Thai Unicode Layout v1.30) */\n    patch_virtual_keyboard_v130(base, log_msg);\n#else\n    log_msg("[KEYBOARD] Original Keyboard retained (Thai Virtual Keyboard disabled).");\n#endif''',
    content
)

# 4. Wrap cheats_init
content = re.sub(
    r'/\*\s*Initialize in-memory cheats system[^\n]*\*/\s*\r?\n\s*cheats_init\([^)]*\);',
    '''#ifdef ENABLE_CHEATS\n    /* Initialize in-memory cheats system (monitors cheats.ini) */\n    cheats_init(g_game_dir_w, g_mod_dir_w, log_msg);\n#endif''',
    content
)

# 5. Wrap cheats_tick
content = re.sub(
    r'\bcheats_tick\(\);',
    '''#ifdef ENABLE_CHEATS\n        cheats_tick();\n#endif''',
    content
)

# 6. Wrap cheats_cleanup
content = re.sub(
    r'\bcheats_cleanup\(\);',
    '''#ifdef ENABLE_CHEATS\n        cheats_cleanup();\n#endif''',
    content
)

with open(r"D:\Users\Supakiat\Desktop\Village_in_the_Shade_ThaiMod_Dev\src\text_dump.c", "w", encoding="utf-8") as f:
    f.write(content)

print("Updated text_dump.c successfully!")
