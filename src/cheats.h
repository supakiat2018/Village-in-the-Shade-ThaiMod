#ifndef CHEATS_H
#define CHEATS_H

#include <windows.h>
#include <stdint.h>

#ifdef __cplusplus
extern "C" {
#endif

/* Configuration for all supported cheats */
typedef struct {
    int active;                  /* 1 if cheats.ini exists and is active */
    int god_mode;                /* 1 = Invincible / God Mode */
    int infinite_items;          /* 1 = Items won't decrease */
    int no_materials_crafting;   /* 1 = Free Crafting */
    int no_materials_cooking;    /* 1 = Free Cooking */
    int no_materials_smithing;   /* 1 = Free Smithing */
    int no_materials_building;   /* 1 = Free Building */
    int no_materials_dyeing;     /* 1 = Free Dyeing */
    int submit_any_item;         /* 1 = Submit any item for bundles/quests */
    int infinite_stamina;        /* 1 = Lock Stamina to Max */
    int freeze_time;             /* 1 = Freeze in-game time */
    int infinite_money;          /* 1 = Money won't run out (>= 999,999) */
} CheatConfig;

/* Initialize cheats system: scans memory patterns and prepares hooks */
void cheats_init(const wchar_t* game_dir_w, const wchar_t* mod_dir_w, void (*log_fn)(const char* fmt, ...));

/* Called periodically (e.g. every 1 sec) to check cheats.ini toggle and apply pointer locks */
void cheats_tick(void);

/* Restore all original game bytes safely upon mod unload or disable */
void cheats_cleanup(void);

#ifdef __cplusplus
}
#endif

#endif /* CHEATS_H */
