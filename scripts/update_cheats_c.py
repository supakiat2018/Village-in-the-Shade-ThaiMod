import re

# 1. Update src/cheats.c
path_cheats = r"D:\Users\Supakiat\Desktop\Village_in_the_Shade_ThaiMod_Dev\src\cheats.c"
with open(path_cheats, "r", encoding="utf-8") as f:
    cheats_code = f.read().replace("\r\n", "\n")

# Export g_config (remove static)
cheats_code = cheats_code.replace("static CheatConfig g_config = { 0 };", "CheatConfig g_config = { 0 };")

# Add get_game_state helper
helper_func = """static inline uintptr_t get_game_state(void)
{
    if (g_global_ptr_addr && is_readable((const void*)g_global_ptr_addr, sizeof(uintptr_t))) {
        uintptr_t gi = *(uintptr_t*)g_global_ptr_addr;
        if (is_readable((const void*)gi, 0x210)) {
            uintptr_t state = *(uintptr_t*)(gi + 0x208);
            if (is_readable((const void*)state, 0x3300)) {
                return state;
            }
        }
    }
    return 0;
}
"""
if "static inline uintptr_t get_game_state(void)" not in cheats_code:
    # insert before parse_vk_key
    cheats_code = cheats_code.replace("/* Parse Virtual Key from text */", helper_func + "\n/* Parse Virtual Key from text */")

# Update load_cheats_ini defaults
old_defaults = """    /* Defaults: gameplay hacks=1, freeze_time=0, infinite_money=0 */
    g_config.active = 1;
    g_config.god_mode = 1;
    g_config.infinite_items = 1;
    g_config.no_materials_crafting = 1;
    g_config.no_materials_cooking = 1;
    g_config.no_materials_smithing = 1;
    g_config.no_materials_building = 1;
    g_config.no_materials_dyeing = 1;
    g_config.submit_any_item = 1;
    g_config.noclip = 0;
    g_config.infinite_stamina = 1;
    g_config.freeze_time = 0;
    g_config.infinite_money = 0;

    /* Default Hotkeys */
    g_config.enable_hotkeys = 1;
    g_config.vk_noclip = VK_F3;
    strcpy(g_config.str_noclip, "F3");"""

new_defaults = """    /* Defaults: Settings, Cheats, and Hotkeys */
    g_config.active = 1;

    /* [Settings] Engine and hook defaults */
    g_config.enable_proportional_font = 1;
    g_config.enable_thai_keyboard = 1;
    g_config.enable_custom_textures = 1;
    g_config.use_english_textures = 0;

    /* [Cheats] Gameplay hacks defaults */
    g_config.god_mode = 0;
    g_config.infinite_items = 0;
    g_config.no_materials_crafting = 0;
    g_config.no_materials_cooking = 0;
    g_config.no_materials_smithing = 0;
    g_config.no_materials_building = 0;
    g_config.no_materials_dyeing = 0;
    g_config.submit_any_item = 0;
    g_config.noclip = 0;
    g_config.infinite_stamina = 0;
    g_config.freeze_time = 0;
    g_config.infinite_money = 0;

    /* [Hotkeys] Default Hotkeys */
    g_config.enable_hotkeys = 1;
    g_config.vk_noclip = VK_F3;
    strcpy(g_config.str_noclip, "F3");
    g_config.vk_freeze_time = VK_F2;
    strcpy(g_config.str_freeze_time, "F2");"""

assert old_defaults in cheats_code, "old_defaults not found"
cheats_code = cheats_code.replace(old_defaults, new_defaults)

# Update load_cheats_ini parsing
old_parsing = """        if (_stricmp(key, "god_mode") == 0) g_config.god_mode = ival;
        else if (_stricmp(key, "infinite_items") == 0) g_config.infinite_items = ival;
        else if (_stricmp(key, "no_materials_crafting") == 0) g_config.no_materials_crafting = ival;
        else if (_stricmp(key, "no_materials_cooking") == 0) g_config.no_materials_cooking = ival;
        else if (_stricmp(key, "no_materials_smithing") == 0) g_config.no_materials_smithing = ival;
        else if (_stricmp(key, "no_materials_building") == 0) g_config.no_materials_building = ival;
        else if (_stricmp(key, "no_materials_dyeing") == 0) g_config.no_materials_dyeing = ival;
        else if (_stricmp(key, "submit_any_item") == 0) g_config.submit_any_item = ival;
        else if (_stricmp(key, "noclip") == 0) g_config.noclip = ival;
        else if (_stricmp(key, "infinite_stamina") == 0) g_config.infinite_stamina = ival;
        else if (_stricmp(key, "freeze_time") == 0) g_config.freeze_time = ival;
        else if (_stricmp(key, "infinite_money") == 0) g_config.infinite_money = ival;

        /* Hotkey settings */
        else if (_stricmp(key, "enable_hotkeys") == 0) g_config.enable_hotkeys = ival;
        else if (_stricmp(key, "hotkey_noclip") == 0) {
            g_config.vk_noclip = parse_vk_key(val);
            strncpy(g_config.str_noclip, val, sizeof(g_config.str_noclip) - 1);
        }"""

new_parsing = """        /* [Settings] Engine toggles */
        if (_stricmp(key, "enable_proportional_font") == 0) g_config.enable_proportional_font = ival;
        else if (_stricmp(key, "enable_thai_keyboard") == 0) g_config.enable_thai_keyboard = ival;
        else if (_stricmp(key, "enable_custom_textures") == 0) g_config.enable_custom_textures = ival;
        else if (_stricmp(key, "use_english_textures") == 0) g_config.use_english_textures = ival;

        /* [Cheats] Gameplay hacks */
        else if (_stricmp(key, "god_mode") == 0) g_config.god_mode = ival;
        else if (_stricmp(key, "infinite_items") == 0) g_config.infinite_items = ival;
        else if (_stricmp(key, "no_materials_crafting") == 0) g_config.no_materials_crafting = ival;
        else if (_stricmp(key, "no_materials_cooking") == 0) g_config.no_materials_cooking = ival;
        else if (_stricmp(key, "no_materials_smithing") == 0) g_config.no_materials_smithing = ival;
        else if (_stricmp(key, "no_materials_building") == 0) g_config.no_materials_building = ival;
        else if (_stricmp(key, "no_materials_dyeing") == 0) g_config.no_materials_dyeing = ival;
        else if (_stricmp(key, "submit_any_item") == 0) g_config.submit_any_item = ival;
        else if (_stricmp(key, "noclip") == 0) g_config.noclip = ival;
        else if (_stricmp(key, "infinite_stamina") == 0) g_config.infinite_stamina = ival;
        else if (_stricmp(key, "freeze_time") == 0) g_config.freeze_time = ival;
        else if (_stricmp(key, "infinite_money") == 0) g_config.infinite_money = ival;

        /* [Hotkeys] Settings */
        else if (_stricmp(key, "enable_hotkeys") == 0) g_config.enable_hotkeys = ival;
        else if (_stricmp(key, "hotkey_noclip") == 0) {
            g_config.vk_noclip = parse_vk_key(val);
            strncpy(g_config.str_noclip, val, sizeof(g_config.str_noclip) - 1);
        }
        else if (_stricmp(key, "hotkey_freeze_time") == 0) {
            g_config.vk_freeze_time = parse_vk_key(val);
            strncpy(g_config.str_freeze_time, val, sizeof(g_config.str_freeze_time) - 1);
        }"""

assert old_parsing in cheats_code, "old_parsing not found"
cheats_code = cheats_code.replace(old_parsing, new_parsing)

# Update hotkey_thread_proc for F2 and Continuous Freeze Time
old_hotkey_proc = """        /* 1. Check NoClip Hotkey (Toggle) */
        if (g_config.enable_hotkeys && g_config.vk_noclip > 0 && (GetAsyncKeyState(g_config.vk_noclip) & 1)) {
            g_config.noclip = !g_config.noclip;
            if (g_config.noclip) {
                apply_patch(&g_patches[8]);
                MessageBeep(MB_OK);
                cheat_log("[Cheats] [HOTKEY %s] Noclip TOGGLED: ON (Walk Through Walls)", g_config.str_noclip);
            } else {
                restore_patch(&g_patches[8]);
                MessageBeep(MB_ICONASTERISK);
                cheat_log("[Cheats] [HOTKEY %s] Noclip TOGGLED: OFF (Normal Collision)", g_config.str_noclip);
            }
        }"""

new_hotkey_proc = """        /* 1. Check NoClip Hotkey (Toggle) */
        if (g_config.enable_hotkeys && g_config.vk_noclip > 0 && (GetAsyncKeyState(g_config.vk_noclip) & 1)) {
            g_config.noclip = !g_config.noclip;
            if (g_config.noclip) {
                apply_patch(&g_patches[8]);
                MessageBeep(MB_OK);
                cheat_log("[Cheats] [HOTKEY %s] Noclip TOGGLED: ON (Walk Through Walls)", g_config.str_noclip);
            } else {
                restore_patch(&g_patches[8]);
                MessageBeep(MB_ICONASTERISK);
                cheat_log("[Cheats] [HOTKEY %s] Noclip TOGGLED: OFF (Normal Collision)", g_config.str_noclip);
            }
        }

        /* 2. Check Freeze Time Hotkey (Toggle) */
        if (g_config.enable_hotkeys && g_config.vk_freeze_time > 0 && (GetAsyncKeyState(g_config.vk_freeze_time) & 1)) {
            g_config.freeze_time = !g_config.freeze_time;
            if (g_config.freeze_time) {
                uintptr_t state = get_game_state();
                if (state) {
                    g_frozen_time = *(int64_t*)(state + 0x3270);
                }
                MessageBeep(MB_OK);
                cheat_log("[Cheats] [HOTKEY %s] Freeze Time TOGGLED: ON (Time Locked at %lld)", g_config.str_freeze_time, (long long)g_frozen_time);
            } else {
                g_frozen_time = 0;
                MessageBeep(MB_ICONASTERISK);
                cheat_log("[Cheats] [HOTKEY %s] Freeze Time TOGGLED: OFF (Time Resumed)", g_config.str_freeze_time);
            }
        }

        /* 3. Continuous Time Freeze Lock (maintains exact time without tick advancing) */
        if (g_config.active && g_config.freeze_time) {
            uintptr_t state = get_game_state();
            if (state) {
                int64_t* pTime = (int64_t*)(state + 0x3270);
                if (g_frozen_time <= 0) {
                    g_frozen_time = *pTime;
                } else {
                    *pTime = g_frozen_time;
                }
            }
        } else if (!g_config.freeze_time) {
            g_frozen_time = 0;
        }"""

assert old_hotkey_proc in cheats_code, "old_hotkey_proc not found"
cheats_code = cheats_code.replace(old_hotkey_proc, new_hotkey_proc)

with open(path_cheats, "w", encoding="utf-8") as f:
    f.write(cheats_code)
print("Updated src/cheats.c successfully!")
