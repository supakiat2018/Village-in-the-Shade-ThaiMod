/* cheats.c - In-memory Cheats System for Village in the Shade
 * Directly ports Cheat Engine AOB injections and memory pointer locks into C.
 * Supports hot-reloading and instant safe disable when cheats.ini is renamed or removed.
 */

#include "cheats.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

static void (*g_log)(const char* fmt, ...) = NULL;

static wchar_t g_cheats_ini_path_w[MAX_PATH] = { 0 };
static FILETIME g_last_ini_write_time = { 0 };

static CheatConfig g_config = { 0 };
static int64_t g_frozen_time = 0;
static int g_cheats_applied = 0;

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

/* 8 Assembly Injections from Village in the Shade1.10.CT */
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
        .patch_bytes = { 0xB0, 0x01, 0xC3 },
        .size = 3,
        .is_patched = 0
    },
    {
        .name = "Smithing No Materials",
        .pattern = "48 89 5C 24 08 48 89 74 24 18 48 89 7C 24 20 55 41 54 41 55 41 56 41 57 48 8D 6C 24 C9 48 81 EC C0 00 00 00 48 8B 05 ? ? ? ? 48 33 C4 48 89 45 27",
        .offset = 0,
        .addr = 0,
        .orig_bytes = { 0x48, 0x89, 0x5C },
        .patch_bytes = { 0xB0, 0x01, 0xC3 },
        .size = 3,
        .is_patched = 0
    },
    {
        .name = "Building No Materials",
        .pattern = "48 89 5C 24 08 55 56 57 41 54 41 55 41 56 41 57 48 8D 6C 24 D9 48 81 EC C0 00 00 00",
        .offset = 0,
        .addr = 0,
        .orig_bytes = { 0x48, 0x89, 0x5C },
        .patch_bytes = { 0xB0, 0x01, 0xC3 },
        .size = 3,
        .is_patched = 0
    },
    {
        .name = "Dyeing No Materials",
        .pattern = "48 89 5C 24 18 55 56 57 41 54 41 55 41 56 41 57 48 8D 6C 24 D9 48 81 EC F0 00 00 00 48 8B 05 ? ? ? ? 48 33 C4 48 89 45 17 48 8B FA",
        .offset = 0,
        .addr = 0,
        .orig_bytes = { 0x48, 0x89, 0x5C },
        .patch_bytes = { 0xB0, 0x01, 0xC3 },
        .size = 3,
        .is_patched = 0
    },
    {
        .name = "Can Submit Any Item",
        .pattern = "48 89 5C 24 18 48 89 74 24 20 55 57 41 54 41 56 41 57 48 8D AC 24 40 FF FF FF 48 81 EC C0 01 00 00 48 63 DA",
        .offset = 0x44,
        .addr = 0,
        .orig_bytes = { 0x0F, 0x84, 0xBA, 0x03, 0x00, 0x00 },
        .patch_bytes = { 0x90, 0x90, 0x90, 0x90, 0x90, 0x90 }, /* 6x NOP */
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

/* Crash-proof user-mode memory readability check via VirtualQuery */
static int is_readable(const void* ptr, size_t size)
{
    if (!ptr) return 0;
    uintptr_t u = (uintptr_t)ptr;
    if (u < 0x10000 || u >= 0x00007FFFFFFFFFFFULL) return 0;

    MEMORY_BASIC_INFORMATION mbi;
    if (VirtualQuery(ptr, &mbi, sizeof(mbi)) != sizeof(mbi)) return 0;
    if (mbi.State != MEM_COMMIT) return 0;
    if (mbi.Protect & (PAGE_NOACCESS | PAGE_GUARD)) return 0;
    return (mbi.Protect & (PAGE_READONLY | PAGE_READWRITE | PAGE_EXECUTE_READ | PAGE_EXECUTE_READWRITE)) != 0;
}

/* Parse IDA pattern string into byte and mask arrays */
static int parse_ida_pattern(const char* pattern, uint8_t* out_bytes, uint8_t* out_mask, int max_len)
{
    int len = 0;
    const char* p = pattern;
    while (*p && len < max_len) {
        while (*p == ' ') p++;
        if (!*p) break;
        if (*p == '?') {
            out_bytes[len] = 0;
            out_mask[len] = 0;
            len++;
            p++;
            if (*p == '?') p++;
        } else {
            char hex[3] = { p[0], p[1], 0 };
            out_bytes[len] = (uint8_t)strtoul(hex, NULL, 16);
            out_mask[len] = 1;
            len++;
            p += 2;
        }
    }
    return len;
}

/* Scan PE .text section for IDA pattern */
static uintptr_t scan_pattern_ida(uintptr_t base, size_t text_va, size_t text_size, const char* pattern)
{
    uint8_t pat_bytes[256];
    uint8_t pat_mask[256];
    int pat_len = parse_ida_pattern(pattern, pat_bytes, pat_mask, sizeof(pat_bytes));
    if (pat_len <= 0 || (size_t)pat_len > text_size) return 0;

    const uint8_t* blob = (const uint8_t*)(base + text_va);
    size_t limit = text_size - pat_len;

    for (size_t i = 0; i <= limit; i++) {
        size_t j = 0;
        for (; j < (size_t)pat_len; j++) {
            if (pat_mask[j] && blob[i + j] != pat_bytes[j]) break;
        }
        if (j == (size_t)pat_len) {
            return base + text_va + i;
        }
    }
    return 0;
}

/* Apply a single memory patch safely */
static void apply_patch(CheatPatch* p)
{
    if (!p->addr || p->is_patched) return;
    DWORD old_protect;
    if (VirtualProtect((LPVOID)p->addr, p->size, PAGE_EXECUTE_READWRITE, &old_protect)) {
        memcpy((void*)p->addr, p->patch_bytes, p->size);
        VirtualProtect((LPVOID)p->addr, p->size, old_protect, &old_protect);
        FlushInstructionCache(GetCurrentProcess(), (LPCVOID)p->addr, p->size);
        p->is_patched = 1;
        cheat_log("[Cheats] ENABLED: %s at 0x%p", p->name, (void*)p->addr);
    }
}

/* Restore original bytes of a single patch */
static void restore_patch(CheatPatch* p)
{
    if (!p->addr || !p->is_patched) return;
    DWORD old_protect;
    if (VirtualProtect((LPVOID)p->addr, p->size, PAGE_EXECUTE_READWRITE, &old_protect)) {
        memcpy((void*)p->addr, p->orig_bytes, p->size);
        VirtualProtect((LPVOID)p->addr, p->size, old_protect, &old_protect);
        FlushInstructionCache(GetCurrentProcess(), (LPCVOID)p->addr, p->size);
        p->is_patched = 0;
        cheat_log("[Cheats] DISABLED: %s (restored original bytes)", p->name);
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
    g_config.infinite_stamina = 1;
    g_config.freeze_time = 0;
    g_config.infinite_money = 0;

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

        int ival = atoi(val);

        if (_stricmp(key, "god_mode") == 0) g_config.god_mode = ival;
        else if (_stricmp(key, "infinite_items") == 0) g_config.infinite_items = ival;
        else if (_stricmp(key, "no_materials_crafting") == 0) g_config.no_materials_crafting = ival;
        else if (_stricmp(key, "no_materials_cooking") == 0) g_config.no_materials_cooking = ival;
        else if (_stricmp(key, "no_materials_smithing") == 0) g_config.no_materials_smithing = ival;
        else if (_stricmp(key, "no_materials_building") == 0) g_config.no_materials_building = ival;
        else if (_stricmp(key, "no_materials_dyeing") == 0) g_config.no_materials_dyeing = ival;
        else if (_stricmp(key, "submit_any_item") == 0) g_config.submit_any_item = ival;
        else if (_stricmp(key, "infinite_stamina") == 0) g_config.infinite_stamina = ival;
        else if (_stricmp(key, "freeze_time") == 0) g_config.freeze_time = ival;
        else if (_stricmp(key, "infinite_money") == 0) g_config.infinite_money = ival;
    }
    fclose(f);
}

void cheats_init(const wchar_t* game_dir_w, const wchar_t* mod_dir_w, void (*log_fn)(const char* fmt, ...))
{
    (void)game_dir_w;
    g_log = log_fn;
    swprintf(g_cheats_ini_path_w, MAX_PATH, L"%ls\\cheats.ini", mod_dir_w);

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
        /* Fallback to known static RVA for v1.10.0 */
        g_global_ptr_addr = base + 0x10DFAD0;
        cheat_log("[Cheats] Using fallback global pointer at 0x%p", (void*)g_global_ptr_addr);
    }

    cheat_log("[Cheats] Memory signatures resolved: %d/%d available.", resolved, NUM_PATCHES);
    cheat_log("[Cheats] System initialized. Cheats will activate safely when save data is active.");
}

void cheats_tick(void)
{
    /* Check if cheats.ini exists */
    WIN32_FILE_ATTRIBUTE_DATA fad;
    BOOL exists = GetFileAttributesExW(g_cheats_ini_path_w, GetFileExInfoStandard, &fad);

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

        g_cheats_applied = 1;
        cheat_log("[Cheats] Cheats are now ACTIVE in-game.");
        cheat_log("[Cheats] ========================================================");
    }

    /* Apply pointer/value locks if cheats are active and state is valid */
    if (g_config.active && state) {
        /* Infinite Stamina */
        if (g_config.infinite_stamina) {
            uintptr_t status = *(uintptr_t*)(state + 0x32B8);
            if (is_readable((const void*)status, 0x3B0)) {
                int32_t max_stamina = *(int32_t*)(status + 0x3A4);
                if (max_stamina > 0) {
                    *(int32_t*)(status + 0x398) = max_stamina;
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
    restore_all_patches();
    g_config.active = 0;
    g_cheats_applied = 0;
}
