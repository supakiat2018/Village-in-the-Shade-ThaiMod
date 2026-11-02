path_textdump = r"D:\Users\Supakiat\Desktop\Village_in_the_Shade_ThaiMod_Dev\src\text_dump.c"
with open(path_textdump, "r", encoding="utf-8") as f:
    code = f.read().replace("\r\n", "\n")

# 1. Update remap_vfs_path for textures
old_vfs_tex = """    /* 1b. Mods\\TextDump\\textures\\<basename> (e.g. Mods\\TextDump\\textures\\ui_1000_title01.nltx) */
    swprintf(candidate, MAX_PATH, L"%ls\\\\textures\\\\%ls", g_mod_dir_w, base_name_w);
    if (file_exists_and_size_w(candidate, out_size)) {
        wcsncpy(out_path_w, candidate, out_max - 1);
        out_path_w[out_max - 1] = L'\\0';
        return TRUE;
    }

    /* 1c. Mods\\TextDump\\title_elements\\<basename> */
    swprintf(candidate, MAX_PATH, L"%ls\\\\title_elements\\\\%ls", g_mod_dir_w, base_name_w);
    if (file_exists_and_size_w(candidate, out_size)) {
        wcsncpy(out_path_w, candidate, out_max - 1);
        out_path_w[out_max - 1] = L'\\0';
        return TRUE;
    }"""

new_vfs_tex = """    /* 1b. Mods\\TextDump\\textures\\<basename> (UI & Minimaps) */
    if (g_config.enable_custom_textures) {
        if (g_config.use_english_textures) {
            swprintf(candidate, MAX_PATH, L"%ls\\\\textures_en\\\\%ls", g_mod_dir_w, base_name_w);
            if (file_exists_and_size_w(candidate, out_size)) {
                wcsncpy(out_path_w, candidate, out_max - 1);
                out_path_w[out_max - 1] = L'\\0';
                return TRUE;
            }
        }
        swprintf(candidate, MAX_PATH, L"%ls\\\\textures\\\\%ls", g_mod_dir_w, base_name_w);
        if (file_exists_and_size_w(candidate, out_size)) {
            wcsncpy(out_path_w, candidate, out_max - 1);
            out_path_w[out_max - 1] = L'\\0';
            return TRUE;
        }

        /* 1c. Mods\\TextDump\\title_elements\\<basename> */
        swprintf(candidate, MAX_PATH, L"%ls\\\\title_elements\\\\%ls", g_mod_dir_w, base_name_w);
        if (file_exists_and_size_w(candidate, out_size)) {
            wcsncpy(out_path_w, candidate, out_max - 1);
            out_path_w[out_max - 1] = L'\\0';
            return TRUE;
        }
    }"""

assert old_vfs_tex in code, "old_vfs_tex not found"
code = code.replace(old_vfs_tex, new_vfs_tex)

# 2. Update worker_thread
old_worker = """    /* Apply Proportional Kerning internal branch patches (Clean village.exe supported) */
    patch_proportional_kerning_v130(base, log_msg);

    #ifdef ENABLE_THAI_KEYBOARD
    /* 6. Patch In-Game Virtual Keyboard string table in memory (Thai Unicode Layout v1.30) */
    patch_virtual_keyboard_v130(base, log_msg);
#else
    log_msg("[KEYBOARD] Original Keyboard retained (Thai Virtual Keyboard disabled).");
#endif

    log_msg("System ready! Both VFS and Text Translation are active.");

    #ifdef ENABLE_CHEATS
    /* Initialize in-memory cheats system (monitors cheats.ini) */
    cheats_init(g_game_dir_w, g_mod_dir_w, log_msg);
#endif"""

new_worker = """    #ifdef ENABLE_CHEATS
    /* Initialize in-memory cheats and user settings (monitors cheats.ini) */
    cheats_init(g_game_dir_w, g_mod_dir_w, log_msg);
#endif

    /* 1. Apply Proportional Kerning internal branch patches (Respects [Settings]) */
    if (g_config.enable_proportional_font) {
        patch_proportional_kerning_v130(base, log_msg);
    } else {
        log_msg("[SETTINGS] Proportional kerning DISABLED by user configuration.");
    }

    #ifdef ENABLE_THAI_KEYBOARD
    /* 2. Patch In-Game Virtual Keyboard string table in memory (Respects [Settings]) */
    if (g_config.enable_thai_keyboard) {
        patch_virtual_keyboard_v130(base, log_msg);
    } else {
        log_msg("[SETTINGS] Thai virtual keyboard DISABLED by user configuration.");
    }
#else
    log_msg("[KEYBOARD] Original Keyboard retained (Thai Virtual Keyboard disabled).");
#endif

    log_msg("System ready! Both VFS and Text Translation are active.");"""

assert old_worker in code, "old_worker not found"
code = code.replace(old_worker, new_worker)

with open(path_textdump, "w", encoding="utf-8") as f:
    f.write(code)

print("Updated src/text_dump.c successfully!")
