#ifndef CHEATS_H
#define CHEATS_H

#include <windows.h>
#include <stdint.h>

#ifdef __cplusplus
extern "C" {
#endif

/* Configuration for all supported cheats & engine settings */
typedef struct {
    int active;                  /* 1 if cheats.ini exists and is active */

    /* [Settings] Engine & Hook Toggles (Update-Proof Controls) */
    int enable_proportional_font;/* 1 = enable in-memory proportional font kerning hook (tight spacing) */
    int enable_thai_keyboard;    /* 1 = enable in-memory Thai virtual keyboard string table patch */
    int enable_custom_textures;  /* 1 = enable VFS texture replacement */
    int use_english_textures;    /* 1 = redirect/load English textures instead of Thai */

    /* [Cheats] Gameplay Cheats */
    int god_mode;                /* 1 = Invincible / God Mode */
    int infinite_items;          /* 1 = Items won't decrease */
    int no_materials_crafting;   /* 1 = Free Crafting */
    int no_materials_cooking;    /* 1 = Free Cooking */
    int no_materials_smithing;   /* 1 = Free Smithing */
    int no_materials_building;   /* 1 = Free Building */
    int no_materials_dyeing;     /* 1 = Free Dyeing */
    int submit_any_item;         /* 1 = Submit any item for bundles/quests */
    int noclip;                  /* 1 = Walk through walls / Noclip */
    int infinite_stamina;        /* 1 = Lock Stamina to Max (v1.30 safe 0x3A0/0x3AC) */
    int freeze_time;             /* 1 = Freeze in-game time (0x3270) */
    int infinite_money;          /* 1 = Money won't run out (>= 999,999) */

    /* [Hotkeys] In-Game Hotkeys Configuration */
    int enable_hotkeys;          /* 1 = enable hotkeys, 0 = disable */
    int vk_noclip;               /* Virtual key for NoClip toggle (default VK_F3 = 0x72) */
    char str_noclip[32];
    int vk_freeze_time;          /* Virtual key for Freeze Time toggle (default VK_F2 = 0x71) */
    char str_freeze_time[32];
} CheatConfig;

extern CheatConfig g_config;

/* Initialize cheats system: scans memory patterns and prepares hooks */
void cheats_init(const wchar_t* game_dir_w, const wchar_t* mod_dir_w, void (*log_fn)(const char* fmt, ...));

/* Called periodically to check cheats.ini toggle and apply pointer locks */
void cheats_tick(void);

/* Restore all original game bytes safely upon mod unload or disable */
void cheats_cleanup(void);

#ifdef __cplusplus
}
#endif

#endif /* CHEATS_H */
