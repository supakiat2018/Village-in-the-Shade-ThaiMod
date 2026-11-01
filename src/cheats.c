/* cheats.c - In-memory Cheats System for Village in the Shade
 * Directly ports Cheat Engine AOB injections and memory pointer locks into C.
 * Includes In-Game NoClip Hotkey (F3).
 * Supports hot-reloading and instant safe disable when cheats.ini is renamed or removed.
 */

#include "cheats.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

static void (*g_log)(const char* fmt, ...) = NULL;

static wchar_t g_cheats_ini_path_w[MAX_PATH] = { 0 };
static wchar_t g_game_dir_w[MAX_PATH] = { 0 };
static wchar_t g_mod_dir_w[MAX_PATH] = { 0 };
static FILETIME g_last_ini_write_time = { 0 };

static CheatConfig g_config = { 0 };
static int64_t g_frozen_time = 0;
static int g_cheats_applied = 0;

/* Dedicated fast hotkey listener thread */
static HANDLE g_hHotkeyThread = NULL;
static volatile BOOL g_hotkey_running = TRUE;

/* Memory Patch definition */
typedef struct {
    const char* name;
    const char* pattern;
    int offset;                  /* Offset from pattern match to patch site */
    uintptr_t addr;              /* Resolved runtime address */
    uint8_t orig_bytes[16];      /* Original bytes saved */
    uint8_t patch_bytes[16];     /* Replacement bytes */
    size_t size;                 /* Size of patch in bytes */
    int is_patched;              /* 1 = Currently patched, 0 = Original */
} CheatPatch;

/* 12 Assembly Injections */
static CheatPatch g_patches[] = {
    {
        .name = "Items Won't Decrease",
        .pattern = "48 89 5C 24 08 48 89 74 24 10 48 89 7C 24 20 41 56 48 83 EC 20 48 63 DA 48 8B F1 45 85 C0 0F 88 ? ? ? ? 85 D2",
        .offset = 0,
        .addr = 0,
        .orig_bytes = { 0x48, 0x89, 0x5C, 0x24, 0x08, 0x48 },
        .patch_bytes = { 0xB8, 0x01, 0x00, 0x00, 0x00, 0xC3 }, /* mov eax, 1; ret */
        .size = 6,
        .is_patched = 0
    },
    {
        .name = "God Mode (Invincible)",
        .pattern = "40 53 48 83 EC 20 48 8B 05 ? ? ? ? 48 8B D9 0F 57 C9 48 8B 90 68 02 00 00 4C 8B 82 40 03 00 00",
        .offset = 0,
        .addr = 0,
        .orig_bytes = { 0x40, 0x53, 0x48 },
        .patch_bytes = { 0xB0, 0x01, 0xC3 }, /* mov al, 1; ret */
        .size = 3,
        .is_patched = 0
    },
    {
        .name = "Crafting No Materials",
        .pattern = "48 89 5C 24 18 55 56 57 41 54 41 55 41 56 41 57 48 8D 6C 24 D9 48 81 EC C0 00 00 00 48 8B 05 ? ? ? ? 48 33 C4 48 89 45 17 48 8B DA 48 89 4D 9F 48 8B 0D ? ? ? ? E8 ? ? ? ? 4C 8B D8 48 89 5D 87",
        .offset = 0,
        .addr = 0,
        .orig_bytes = { 0x48, 0x89, 0x5C },
        .patch_bytes = { 0xB0, 0x01, 0xC3 }, /* mov al, 1; ret */
        .size = 3,
        .is_patched = 0
    },
    {
        .name = "Cooking No Materials",
        .pattern = "48 89 5C 24 18 55 56 57 41 54 41 55 41 56 41 57 48 8D 6C 24 D9 48 81 EC D0 00 00 00 48 8B 05 ? ? ? ?",
        .offset = 0,
        .addr = 0,
        .orig_bytes = { 0x48, 0x89, 0x5C },
        .patch_bytes = { 0xB0, 0x01, 0xC3 }, /* mov al, 1; ret */
        .size = 3,
        .is_patched = 0
    },
    {
        .name = "Smithing No Materials",
        .pattern = "48 89 5C 24 08 48 89 74 24 18 48 89 7C 24 20 55 41 54 41 55 41 56 41 57 48 8D 6C 24 C9 48 81 EC C0 00 00 00 48 8B 05 ? ? ? ? 48 33 C4 48 89 45 27",
        .offset = 0,
        .addr = 0,
        .orig_bytes = { 0x48, 0x89, 0x5C },
        .patch_bytes = { 0xB0, 0x01, 0xC3 }, /* mov al, 1; ret */
        .size = 3,
        .is_patched = 0
    },
    {
        .name = "Building No Materials",
        .pattern = "48 89 5C 24 08 55 56 57 41 54 41 55 41 56 41 57 48 8D 6C 24 D9 48 81 EC C0 00 00 00",
        .offset = 0,
        .addr = 0,
        .orig_bytes = { 0x48, 0x89, 0x5C },
        .patch_bytes = { 0xB0, 0x01, 0xC3 }, /* mov al, 1; ret */
        .size = 3,
        .is_patched = 0
    },
    {
        .name = "Dyeing No Materials",
        .pattern = "48 89 5C 24 18 55 56 57 41 54 41 55 41 56 41 57 48 8D 6C 24 D9 48 81 EC F0 00 00 00 48 8B 05 ? ? ? ? 48 33 C4 48 89 45 17 48 8B FA",
        .offset = 0,
        .addr = 0,
        .orig_bytes = { 0x48, 0x89, 0x5C },
        .patch_bytes = { 0xB0, 0x01, 0xC3 }, /* mov al, 1; ret */
        .size = 3,
        .is_patched = 0
    },
    {
        .name = "Can Submit Any Item",
        .pattern = "48 89 5C 24 18 48 89 74 24 20 55 57 41 54 41 56 41 57 48 8D AC 24 40 FF FF FF 48 81 EC C0 01 00 00 48 63 DA",
        .offset = 0x44,
        .addr = 0,
        .orig_bytes = { 0x0F, 0x84, 0xBA, 0x03, 0x00, 0x00 }, /* 6 bytes jump if zero */
        .patch_bytes = { 0x90, 0x90, 0x90, 0x90, 0x90, 0x90 }, /* 6x NOP */
        .size = 6,
        .is_patched = 0
    },
    {
        .name = "Noclip (Walk Through Walls)",
        .pattern = "40 53 48 83 EC 30 48 8B 05 ? ? ? ? 48 33 C4 48 89 44 24 28 80 B9 4C 03 00 00 00",
        .offset = 0,
        .addr = 0,
        .orig_bytes = { 0x40, 0x53, 0x48, 0x83, 0xEC, 0x30 },
        .patch_bytes = { 0x31, 0xC0, 0xC3, 0x90, 0x90, 0x90 }, /* xor eax, eax; ret; 3x nop */
        .size = 6,
        .is_patched = 0
    }
};

#define NUM_PATCHES ((int)(sizeof(g_patches) / sizeof(g_patches[0])))

/* Global Game State Pointer resolved dynamically */
static uintptr_t g_global_ptr_addr = 0;

/* Helper logging */
static void cheat_log(const char* fmt, ...)
{
    if (!g_log) return;
    char buf[1024];
    va_list args;
    va_start(args, fmt);
    vsnprintf(buf, sizeof(buf), fmt, args);
    va_end(args);
    g_log("%s", buf);
}

/* Safe memory read verification */
static BOOL is_readable(const void* ptr, size_t size)
{
    if (!ptr || (uintptr_t)ptr < 0x10000 || (uintptr_t)ptr >= 0x7FFFFFFFFFFFULL) return FALSE;
    MEMORY_BASIC_INFORMATION mbi;
    if (VirtualQuery(ptr, &mbi, sizeof(mbi)) == 0) return FALSE;
    if (mbi.State != MEM_COMMIT) return FALSE;
    if (mbi.Protect & (PAGE_NOACCESS | PAGE_GUARD)) return FALSE;
    return TRUE;
}

/* Fast byte pattern scanner supporting '?' and IDA format */
static uintptr_t scan_pattern_ida(uintptr_t base, size_t va, size_t sz, const char* pattern)
{
    uint8_t pat_bytes[256];
    uint8_t pat_mask[256]; /* 1 = must match, 0 = wildcard */
    size_t pat_len = 0;

    const char* p = pattern;
    while (*p && pat_len < sizeof(pat_bytes)) {
        while (*p == ' ') p++;
        if (!*p) break;
        if (*p == '?') {
            pat_bytes[pat_len] = 0;
            pat_mask[pat_len] = 0;
            pat_len++;
            p++;
            if (*p == '?') p++;
        } else {
            char hex[3] = { p[0], p[1], '\0' };
            pat_bytes[pat_len] = (uint8_t)strtol(hex, NULL, 16);
            pat_mask[pat_len] = 1;
            pat_len++;
            p += 2;
        }
    }

    if (pat_len == 0) return 0;

    const uint8_t* scan_start = (const uint8_t*)(base + va);
    const uint8_t* scan_end = scan_start + sz - pat_len;

    for (const uint8_t* cur = scan_start; cur <= scan_end; cur++) {
        BOOL match = TRUE;
        for (size_t i = 0; i < pat_len; i++) {
            if (pat_mask[i] && cur[i] != pat_bytes[i]) {
                match = FALSE;
                break;
            }
        }
        if (match) {
            return (uintptr_t)cur;
        }
    }
    return 0;
}

/* Apply single patch to executable code */
static void apply_patch(CheatPatch* p)
{
    if (!p->addr || p->is_patched) return;
    DWORD old_protect;
    if (VirtualProtect((void*)p->addr, p->size, PAGE_EXECUTE_READWRITE, &old_protect)) {
        memcpy((void*)p->addr, p->patch_bytes, p->size);
        VirtualProtect((void*)p->addr, p->size, old_protect, &old_protect);
        FlushInstructionCache(GetCurrentProcess(), (void*)p->addr, p->size);
        p->is_patched = 1;
        cheat_log("[Cheats] Applied patch: %s at 0x%p", p->name, (void*)p->addr);
    }
}

/* Restore single patch to original game code */
static void restore_patch(CheatPatch* p)
{
    if (!p->addr || !p->is_patched) return;
    DWORD old_protect;
    if (VirtualProtect((void*)p->addr, p->size, PAGE_EXECUTE_READWRITE, &old_protect)) {
        memcpy((void*)p->addr, p->orig_bytes, p->size);
        VirtualProtect((void*)p->addr, p->size, old_protect, &old_protect);
        FlushInstructionCache(GetCurrentProcess(), (void*)p->addr, p->size);
        p->is_patched = 0;
        cheat_log("[Cheats] Restored patch: %s at 0x%p", p->name, (void*)p->addr);
    }
}

/* Restore all patches unconditionally */
static void restore_all_patches(void)
{
    for (int i = 0; i < NUM_PATCHES; i++) {
        if (g_patches[i].is_patched) {
            restore_patch(&g_patches[i]);
        }
    }
    g_cheats_applied = 0;
}

/* Parse Virtual Key from text */
static int parse_vk_key(const char* str)
{
    if (!str || !*str) return 0;
    while (*str == ' ' || *str == '\t') str++;

    /* F1 - F12 */
    if ((str[0] == 'F' || str[0] == 'f') && str[1] >= '1' && str[1] <= '9') {
        int num = atoi(str + 1);
        if (num >= 1 && num <= 12) {
            return VK_F1 + (num - 1);
        }
    }

    /* Numpad keys */
    if (_strnicmp(str, "NUMPAD", 6) == 0 && str[6] >= '0' && str[6] <= '9') {
        return VK_NUMPAD0 + (str[6] - '0');
    }
    if (_strnicmp(str, "NUM", 3) == 0 && str[3] >= '0' && str[3] <= '9') {
        return VK_NUMPAD0 + (str[3] - '0');
    }
    if (_stricmp(str, "NUMPAD_SUBTRACT") == 0 || _stricmp(str, "NUM-") == 0 || _stricmp(str, "SUBTRACT") == 0) {
        return VK_SUBTRACT;
    }
    if (_stricmp(str, "NUMPAD_ADD") == 0 || _stricmp(str, "NUM+") == 0 || _stricmp(str, "ADD") == 0) {
        return VK_ADD;
    }

    /* Common keys */
    if (_stricmp(str, "TAB") == 0) return VK_TAB;
    if (_stricmp(str, "SPACE") == 0) return VK_SPACE;
    if (_stricmp(str, "CAPSLOCK") == 0) return VK_CAPITAL;
    if (_stricmp(str, "TILDE") == 0 || _stricmp(str, "`") == 0 || _stricmp(str, "~") == 0) return VK_OEM_3;

    /* Single letter or digit */
    if (strlen(str) == 1) {
        char c = str[0];
        if (c >= 'a' && c <= 'z') return c - 'a' + 'A';
        if (c >= 'A' && c <= 'Z') return c;
        if (c >= '0' && c <= '9') return c;
    }

    /* Hex (0x72) or Dec */
    if (str[0] == '0' && (str[1] == 'x' || str[1] == 'X')) {
        return (int)strtol(str, NULL, 16);
    }
    return atoi(str);
}

/* Simple safe INI parser for cheats.ini */
static void load_cheats_ini(void)
{
    FILE* f = _wfopen(g_cheats_ini_path_w, L"r");
    if (!f) return;

    /* Defaults: gameplay hacks=1, freeze_time=0, infinite_money=0 */
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
    strcpy(g_config.str_noclip, "F3");

    char line[512];
    while (fgets(line, sizeof(line), f)) {
        char* p = line;
        /* Skip UTF-8 BOM if present */
        while (*p == ' ' || *p == '\t' || (unsigned char)*p == 0xEF || (unsigned char)*p == 0xBB || (unsigned char)*p == 0xBF) p++;
        if (*p == '#' || *p == ';' || *p == '[' || *p == '\0' || *p == '\r' || *p == '\n') continue;

        char* eq = strchr(p, '=');
        if (!eq) continue;
        *eq = '\0';
        char* key = p;
        char* val = eq + 1;

        /* Trim key */
        size_t klen = strlen(key);
        while (klen > 0 && (key[klen - 1] == ' ' || key[klen - 1] == '\t')) {
            key[--klen] = '\0';
        }
        if (klen == 0) continue;

        /* Trim val */
        while (*val == ' ' || *val == '\t') val++;
        size_t vlen = strlen(val);
        while (vlen > 0 && (val[vlen - 1] == ' ' || val[vlen - 1] == '\t' || val[vlen - 1] == '\r' || val[vlen - 1] == '\n')) {
            val[--vlen] = '\0';
        }

        /* Check for inline comments in value */
        char* comment = strchr(val, '#');
        if (!comment) comment = strchr(val, ';');
        if (comment) {
            *comment = '\0';
            vlen = strlen(val);
            while (vlen > 0 && (val[vlen - 1] == ' ' || val[vlen - 1] == '\t')) {
                val[--vlen] = '\0';
            }
        }

        int ival = atoi(val);

        if (_stricmp(key, "god_mode") == 0) g_config.god_mode = ival;
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
        }
    }
    fclose(f);
}

/* Fast hotkey listener thread proc */
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
}

void cheats_init(const wchar_t* game_dir_w, const wchar_t* mod_dir_w, void (*log_fn)(const char* fmt, ...))
{
    g_log = log_fn;
    if (game_dir_w) wcscpy(g_game_dir_w, game_dir_w);
    if (mod_dir_w) wcscpy(g_mod_dir_w, mod_dir_w);

    /* Prioritize root game folder (next to village.exe), fallback to mod folder */
    wchar_t root_path[MAX_PATH];
    swprintf(root_path, MAX_PATH, L"%ls\\cheats.ini", g_game_dir_w);
    if (GetFileAttributesW(root_path) != INVALID_FILE_ATTRIBUTES) {
        wcscpy(g_cheats_ini_path_w, root_path);
    } else {
        wchar_t mod_path[MAX_PATH];
        swprintf(mod_path, MAX_PATH, L"%ls\\cheats.ini", g_mod_dir_w);
        if (GetFileAttributesW(mod_path) != INVALID_FILE_ATTRIBUTES) {
            wcscpy(g_cheats_ini_path_w, mod_path);
        } else {
            wcscpy(g_cheats_ini_path_w, root_path);
        }
    }
    cheat_log("[Cheats] Active config path: %ls", g_cheats_ini_path_w);

    uintptr_t base = (uintptr_t)GetModuleHandleA(NULL);
    if (!base) return;

    /* Get PE .text section bounds */
    IMAGE_DOS_HEADER* dos = (IMAGE_DOS_HEADER*)base;
    if (dos->e_magic != IMAGE_DOS_SIGNATURE) return;
    IMAGE_NT_HEADERS* nt = (IMAGE_NT_HEADERS*)(base + dos->e_lfanew);
    if (nt->Signature != IMAGE_NT_SIGNATURE) return;

    size_t text_va = 0;
    size_t text_size = 0;
    IMAGE_SECTION_HEADER* sh = IMAGE_FIRST_SECTION(nt);
    for (WORD i = 0; i < nt->FileHeader.NumberOfSections; i++) {
        if (memcmp(sh[i].Name, ".text", 5) == 0) {
            text_va = sh[i].VirtualAddress;
            text_size = sh[i].Misc.VirtualSize ? sh[i].Misc.VirtualSize : sh[i].SizeOfRawData;
            break;
        }
    }

    if (!text_va || !text_size) {
        cheat_log("[Cheats] Could not find .text section of game binary.");
        return;
    }

    /* 1. Resolve Assembly Patch Addresses and backup original bytes */
    int resolved = 0;
    for (int i = 0; i < NUM_PATCHES; i++) {
        uintptr_t match = scan_pattern_ida(base, text_va, text_size, g_patches[i].pattern);
        if (match) {
            g_patches[i].addr = match + g_patches[i].offset;
            memcpy(g_patches[i].orig_bytes, (void*)g_patches[i].addr, g_patches[i].size);
            resolved++;
        } else {
            cheat_log("[Cheats] Warning: Pattern scan missed for '%s'", g_patches[i].name);
        }
    }

    /* 2. Resolve Global Pointer via Getter Signature */
    const char* getter_pat = "48 8B 05 ? ? ? ? 48 8B 6C 24 38 48 8B 74 24 40 49 8B 50 10 48 8B 88 08 02 00 00 48 8B 7C 24 48 48 8B 81 70 32 00 00";
    uintptr_t getter_match = scan_pattern_ida(base, text_va, text_size, getter_pat);
    if (getter_match) {
        int32_t disp = *(int32_t*)(getter_match + 3);
        g_global_ptr_addr = getter_match + 7 + disp;
        cheat_log("[Cheats] Resolved global pointer dynamically at 0x%p (RVA: 0x%X)", 
                  (void*)g_global_ptr_addr, (uint32_t)(g_global_ptr_addr - base));
    } else {
        /* Fallback to known static RVA: v1.30 = 0x111CC90, v1.20 = 0x10FCBB0, v1.10 = 0x10DFAD0 */
        if (is_readable((const void*)(base + 0x111C090), sizeof(uintptr_t)) && *(uintptr_t*)(base + 0x111C090) != 0) {
            g_global_ptr_addr = base + 0x111C090;
        } else if (is_readable((const void*)(base + 0x10FCBB0), sizeof(uintptr_t)) && *(uintptr_t*)(base + 0x10FCBB0) != 0) {
            g_global_ptr_addr = base + 0x10FCBB0;
        } else {
            g_global_ptr_addr = base + 0x10DFAD0;
        }
        cheat_log("[Cheats] Using fallback global pointer at 0x%p (RVA: 0x%X)", 
                  (void*)g_global_ptr_addr, (uint32_t)(g_global_ptr_addr - base));
    }

    cheat_log("[Cheats] Memory signatures resolved: %d/%d available.", resolved, NUM_PATCHES);

    /* Launch dedicated hotkey thread */
    if (!g_hHotkeyThread) {
        g_hotkey_running = TRUE;
        g_hHotkeyThread = CreateThread(NULL, 0, hotkey_thread_proc, NULL, 0, NULL);
        if (g_hHotkeyThread) {
            cheat_log("[Cheats] Hotkey Listener Thread active (F3=Noclip).");
        }
    }

    cheat_log("[Cheats] System initialized. Cheats will activate safely when save data is active.");
}

void cheats_tick(void)
{
    /* Check root game folder first, fallback to mod folder */
    wchar_t root_path[MAX_PATH];
    swprintf(root_path, MAX_PATH, L"%ls\\cheats.ini", g_game_dir_w);
    WIN32_FILE_ATTRIBUTE_DATA fad;
    BOOL exists = GetFileAttributesExW(root_path, GetFileExInfoStandard, &fad);
    if (exists) {
        wcscpy(g_cheats_ini_path_w, root_path);
    } else {
        wchar_t mod_path[MAX_PATH];
        swprintf(mod_path, MAX_PATH, L"%ls\\cheats.ini", g_mod_dir_w);
        exists = GetFileAttributesExW(mod_path, GetFileExInfoStandard, &fad);
        if (exists) {
            wcscpy(g_cheats_ini_path_w, mod_path);
        }
    }

    if (!exists) {
        /* File does NOT exist (or was renamed to _cheats.ini / deleted) */
        if (g_config.active || g_cheats_applied) {
            cheat_log("[Cheats] ========================================================");
            cheat_log("[Cheats] 'cheats.ini' not found or was renamed! Restoring game...");
            restore_all_patches();
            g_config.active = 0;
            g_frozen_time = 0;
            g_cheats_applied = 0;
            cheat_log("[Cheats] ALL CHEATS DEACTIVATED. Clean game memory restored.");
            cheat_log("[Cheats] ========================================================");
        }
        return;
    }

    /* Check if game save state is loaded and valid before touching memory */
    uintptr_t state = 0;
    if (g_global_ptr_addr && is_readable((const void*)g_global_ptr_addr, sizeof(uintptr_t))) {
        uintptr_t gi = *(uintptr_t*)g_global_ptr_addr;
        if (is_readable((const void*)gi, 0x210)) {
            state = *(uintptr_t*)(gi + 0x208);
            if (!is_readable((const void*)state, 0x3300)) {
                state = 0;
            }
        }
    }

    /* If the game is still on Title Screen or loading (state == 0), don't patch yet to ensure clean startup */
    if (!state) {
        if (g_cheats_applied) {
            restore_all_patches();
        }
        return;
    }

    /* File exists AND player is in-game: Check if INI was created or modified */
    if (!g_config.active || !g_cheats_applied || CompareFileTime(&g_last_ini_write_time, &fad.ftLastWriteTime) != 0) {
        g_last_ini_write_time = fad.ftLastWriteTime;
        load_cheats_ini();

        cheat_log("[Cheats] ========================================================");
        cheat_log("[Cheats] 'cheats.ini' active in-game! Applying configured cheats...");

        /* Apply or restore each patch according to config */
        if (g_config.infinite_items) apply_patch(&g_patches[0]); else restore_patch(&g_patches[0]);
        if (g_config.god_mode) apply_patch(&g_patches[1]); else restore_patch(&g_patches[1]);
        if (g_config.no_materials_crafting) apply_patch(&g_patches[2]); else restore_patch(&g_patches[2]);
        if (g_config.no_materials_cooking) apply_patch(&g_patches[3]); else restore_patch(&g_patches[3]);
        if (g_config.no_materials_smithing) apply_patch(&g_patches[4]); else restore_patch(&g_patches[4]);
        if (g_config.no_materials_building) apply_patch(&g_patches[5]); else restore_patch(&g_patches[5]);
        if (g_config.no_materials_dyeing) apply_patch(&g_patches[6]); else restore_patch(&g_patches[6]);
        if (g_config.submit_any_item) apply_patch(&g_patches[7]); else restore_patch(&g_patches[7]);
        if (g_config.noclip) apply_patch(&g_patches[8]); else restore_patch(&g_patches[8]);

        g_cheats_applied = 1;
        cheat_log("[Cheats] Cheats are now ACTIVE in-game.");
        cheat_log("[Cheats] ========================================================");
    }

    /* Apply pointer/value locks if cheats are active and state is valid */
    if (g_config.active && state) {
        /* Infinite Stamina (v1.30: Stamina 0x3A0, Stamina Max 0x3AC) */
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
        }

        /* Infinite / High Money */
        if (g_config.infinite_money) {
            int64_t* pMoney = (int64_t*)(state + 0x32A0);
            if (*pMoney < 999999) {
                *pMoney = 999999;
            }
        }

        /* Freeze Time */
        if (g_config.freeze_time) {
            int64_t* pTime = (int64_t*)(state + 0x3270);
            if (g_frozen_time <= 0) {
                g_frozen_time = *pTime;
            } else {
                *pTime = g_frozen_time;
            }
        } else {
            g_frozen_time = 0;
        }
    }
}

void cheats_cleanup(void)
{
    g_hotkey_running = FALSE;
    if (g_hHotkeyThread) {
        WaitForSingleObject(g_hHotkeyThread, 200);
        CloseHandle(g_hHotkeyThread);
        g_hHotkeyThread = NULL;
    }

    restore_all_patches();
    g_config.active = 0;
    g_cheats_applied = 0;
}
