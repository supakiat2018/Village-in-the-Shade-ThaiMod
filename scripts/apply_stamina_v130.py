import os

path = r"D:\Users\Supakiat\Desktop\Village_in_the_Shade_ThaiMod_Dev\src\cheats.c"
with open(path, "r", encoding="utf-8") as f:
    content = f.read()

# 1. Fallback RVA fix
old_fb = "base + 0x111CC90"
new_fb = "base + 0x111C090"
assert old_fb in content, f"'{old_fb}' not found"
content = content.replace(old_fb, new_fb)

# 2. Normalize newlines
content = content.replace("\r\n", "\n")

# 3. In cheats_tick
old_tick = """        /* Infinite Stamina */
        if (g_config.infinite_stamina) {
            uintptr_t status = *(uintptr_t*)(state + 0x32B8);
            if (is_readable((const void*)status, 0x3B0)) {
                int32_t max_stamina = *(int32_t*)(status + 0x3A4);
                if (max_stamina > 0) {
                    *(int32_t*)(status + 0x398) = max_stamina;
                }
            }
        }"""

new_tick = """        /* Infinite Stamina (v1.30: Stamina 0x3A0, Stamina Max 0x3AC) */
        if (g_config.infinite_stamina) {
            uintptr_t status = *(uintptr_t*)(state + 0x32B8);
            if (is_readable((const void*)status, 0x3C0)) {
                int32_t max_stamina = *(int32_t*)(status + 0x3AC);
                if (max_stamina > 0 && max_stamina <= 10000) {
                    int32_t cur = *(int32_t*)(status + 0x3A0);
                    if (cur < max_stamina) {
                        *(int32_t*)(status + 0x3A0) = max_stamina;
                    }
                }
            }
        }"""

assert old_tick in content, "old_tick not found"
content = content.replace(old_tick, new_tick)

# 4. In hotkey_thread_proc
old_proc = """/* Fast hotkey listener thread proc */
static DWORD WINAPI hotkey_thread_proc(LPVOID param)
{
    (void)param;
    while (g_hotkey_running) {
        Sleep(25); /* ~40Hz polling rate with near-zero CPU usage */

        if (!g_config.active || !g_config.enable_hotkeys) continue;

        /* 1. Check NoClip Hotkey (Toggle) */
        if (g_config.vk_noclip > 0 && (GetAsyncKeyState(g_config.vk_noclip) & 1)) {
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
    }
    return 0;
}"""

new_proc = """/* Fast hotkey listener thread proc */
static DWORD WINAPI hotkey_thread_proc(LPVOID param)
{
    (void)param;
    int stam_tick = 0;

    while (g_hotkey_running) {
        Sleep(25); /* ~40Hz polling rate with near-zero CPU usage */

        if (!g_config.active) continue;

        /* 1. Check NoClip Hotkey (Toggle) */
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

        /* 2. Safe Infinite Stamina refresh (v1.30: Stamina 0x3A0, Stamina Max 0x3AC) */
        if (g_config.infinite_stamina) {
            if (++stam_tick >= 4) { /* ~100ms interval */
                stam_tick = 0;
                if (g_global_ptr_addr && is_readable((const void*)g_global_ptr_addr, sizeof(uintptr_t))) {
                    uintptr_t gi = *(uintptr_t*)g_global_ptr_addr;
                    if (is_readable((const void*)gi, 0x210)) {
                        uintptr_t state = *(uintptr_t*)(gi + 0x208);
                        if (state && is_readable((const void*)state, 0x3300)) {
                            uintptr_t status = *(uintptr_t*)(state + 0x32B8);
                            if (status && is_readable((const void*)status, 0x3C0)) {
                                int32_t max_stamina = *(int32_t*)(status + 0x3AC);
                                if (max_stamina > 0 && max_stamina <= 10000) {
                                    int32_t cur = *(int32_t*)(status + 0x3A0);
                                    if (cur < max_stamina) {
                                        *(int32_t*)(status + 0x3A0) = max_stamina;
                                    }
                                }
                            }
                        }
                    }
                }
            }
        }
    }
    return 0;
}"""

assert old_proc in content, "old_proc not found"
content = content.replace(old_proc, new_proc)

with open(path, "w", encoding="utf-8") as f:
    f.write(content)

print("Applied v1.30 Stamina update to src/cheats.c successfully!")
