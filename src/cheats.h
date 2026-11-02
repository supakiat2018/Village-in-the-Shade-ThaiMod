#ifndef CHEATS_H
#define CHEATS_H

#include <windows.h>
#include <stdint.h>

#ifdef __cplusplus
extern "C" {
#endif

/* Configuration for Mod Engine Settings (settings.ini) */
typedef struct {
    int enable_proportional_font; /* 1 = enable in-memory proportional font kerning hook (tight spacing) */
    int enable_thai_keyboard;     /* 1 = enable in-memory Thai virtual keyboard string table patch */
    int enable_custom_textures;   /* 1 = enable VFS texture replacement */
    int use_english_textures;     /* 1 = redirect/load English textures instead of Thai */
    int texture_mode;             /* 0 = Original game, 1 = Thai + EN fallback, 2 = All EN */
    int enable_speedhack;         /* 1 = enable in-memory Speedhack (game speed multiplier), 0 = disable */
} ModSettings;

/* Configuration for In-Game Cheats & Hotkeys (cheats.ini) */
typedef struct {
    int active;                   /* 1 if cheats.ini exists and is active */
    int god_mode;                 /* 1 = Invincible / God Mode */
    int infinite_items;           /* 1 = Items won't decrease */
    int no_materials_crafting;    /* 1 = Free Crafting */
    int no_materials_cooking;     /* 1 = Free Cooking */
    int no_materials_smithing;    /* 1 = Free Smithing */
    int no_materials_building;    /* 1 = Free Building */
    int no_materials_dyeing;      /* 1 = Free Dyeing */
    int submit_any_item;          /* 1 = Submit any item for bundles/quests */
    int noclip;                   /* 1 = Walk through walls / Noclip */
    int infinite_stamina;         /* 1 = Lock Stamina to Max (v1.30 safe 0x3A0/0x3AC) */
    int freeze_time;              /* 1 = Freeze in-game time (0x3270) */
    int infinite_money;           /* 1 = Money won't run out (>= 999,999) */

    /* Hotkeys Configuration */
    int enable_hotkeys;           /* 1 = enable hotkeys, 0 = disable */
    int vk_noclip;                /* Virtual key for NoClip toggle (default VK_F3) */
    char str_noclip[32];
    int vk_freeze_time;           /* Virtual key for Freeze Time toggle (default VK_F2) */
    char str_freeze_time[32];

    /* Speedhack Hotkeys */
    int vk_speed_fast;            /* Virtual key for Fast Speed (default VK_F4) */
    char str_speed_fast[32];
    int vk_speed_slow;            /* Virtual key for Slow Speed (default VK_F5) */
    char str_speed_slow[32];
    int vk_speed_normal;          /* Virtual key for Normal Speed (default VK_F6) */
    char str_speed_normal[32];
    double speed_multiplier_fast; /* Multiplier for Fast (default 2.0) */
    double speed_multiplier_slow; /* Multiplier for Slow (default 0.5) */
    double current_speed;         /* Currently active speed (default 1.0) */
} CheatConfig;

extern ModSettings g_settings;
extern CheatConfig g_config;

/* Initialize mod settings from settings.ini */
void settings_init(const wchar_t* game_dir_w, const wchar_t* mod_dir_w, void (*log_fn)(const char* fmt, ...));

#ifdef ENABLE_CHEATS
/* Initialize cheats system: scans memory patterns and prepares hooks */
void cheats_init(const wchar_t* game_dir_w, const wchar_t* mod_dir_w, void (*log_fn)(const char* fmt, ...));

/* Called periodically to check cheats.ini toggle and apply pointer locks */
void cheats_tick(void);

/* Restore all original game bytes safely upon mod unload or disable */
void cheats_cleanup(void);
#else
static inline void cheats_init(const wchar_t* game_dir_w, const wchar_t* mod_dir_w, void (*log_fn)(const char* fmt, ...)) {
    (void)game_dir_w; (void)mod_dir_w; (void)log_fn;
}
static inline void cheats_tick(void) {}
static inline void cheats_cleanup(void) {}
#endif

#ifdef __cplusplus
}
#endif

#endif /* CHEATS_H */
