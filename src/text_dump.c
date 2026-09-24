#include <windows.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <stdint.h>
#include <time.h>
#include <ctype.h>
#include "minhook-master/include/MinHook.h"
#include "addrsig.h"

static HINSTANCE g_hinst = NULL;
static char g_mod_dir[MAX_PATH] = { 0 };
static char g_game_dir[MAX_PATH] = { 0 };
static wchar_t g_mod_dir_w[MAX_PATH] = { 0 };
static wchar_t g_game_dir_w[MAX_PATH] = { 0 };

static char g_log_path[MAX_PATH] = { 0 };
static char g_dump_unique_path[MAX_PATH] = { 0 };
static char g_dump_log_path[MAX_PATH] = { 0 };
static char g_session_dump_unique_path[MAX_PATH] = { 0 };
static char g_session_dump_log_path[MAX_PATH] = { 0 };
static char g_dump_missing_path[MAX_PATH] = { 0 };
static char g_session_dump_missing_path[MAX_PATH] = { 0 };
static char g_file_access_log[MAX_PATH] = { 0 };
static char g_tags_log_path[MAX_PATH] = { 0 };

static wchar_t g_log_path_w[MAX_PATH] = { 0 };
static wchar_t g_dump_unique_path_w[MAX_PATH] = { 0 };
static wchar_t g_dump_log_path_w[MAX_PATH] = { 0 };
static wchar_t g_session_dump_unique_path_w[MAX_PATH] = { 0 };
static wchar_t g_session_dump_log_path_w[MAX_PATH] = { 0 };
static wchar_t g_dump_missing_path_w[MAX_PATH] = { 0 };
static wchar_t g_session_dump_missing_path_w[MAX_PATH] = { 0 };
static wchar_t g_file_access_log_w[MAX_PATH] = { 0 };
static wchar_t g_tags_log_path_w[MAX_PATH] = { 0 };

static CRITICAL_SECTION g_cs;
static FILE* g_flog = NULL;
static FILE* g_funique = NULL;
static FILE* g_funique_latest = NULL;
static FILE* g_fraw = NULL;
static FILE* g_fraw_latest = NULL;
static FILE* g_fmissing = NULL;
static FILE* g_fmissing_latest = NULL;
static FILE* g_faccess = NULL;
static FILE* g_ftags = NULL;

static int g_unique_count = 0;
static uint64_t g_total_calls = 0;

/* ==================================================================
 * Logging Functions
 * ================================================================== */
static void log_file_access(const char* fmt, ...)
{
    char buf[1024];
    va_list ap;
    SYSTEMTIME st;
    GetLocalTime(&st);

    va_start(ap, fmt);
    vsnprintf(buf, sizeof(buf), fmt, ap);
    va_end(ap);

    EnterCriticalSection(&g_cs);
    if (!g_faccess) {
        g_faccess = _wfopen(g_file_access_log_w, L"a+");
    }
    if (g_faccess) {
        fprintf(g_faccess, "[%02d:%02d:%02d.%03d] %s\n",
                st.wHour, st.wMinute, st.wSecond, st.wMilliseconds, buf);
        fflush(g_faccess);
    }
    LeaveCriticalSection(&g_cs);
}

static void log_msg(const char* fmt, ...)
{
    char buf[1024];
    va_list ap;
    SYSTEMTIME st;
    GetLocalTime(&st);

    va_start(ap, fmt);
    vsnprintf(buf, sizeof(buf), fmt, ap);
    va_end(ap);

    EnterCriticalSection(&g_cs);
    if (!g_flog) {
        g_flog = _wfopen(g_log_path_w, L"a+");
    }
    if (g_flog) {
        fprintf(g_flog, "[%02d:%02d:%02d.%03d] %s\n",
                st.wHour, st.wMinute, st.wSecond, st.wMilliseconds, buf);
        fflush(g_flog);
    }
    LeaveCriticalSection(&g_cs);
}

/* ==================================================================
 * String Hash Set for Text Deduplication
 * ================================================================== */
#define HASH_TABLE_SIZE 65536
typedef struct HashNode {
    uint32_t hash;
    char* str;
    struct HashNode* next;
} HashNode;

static HashNode* g_hash_table[HASH_TABLE_SIZE] = { 0 };

static uint32_t hash_str(const char* str)
{
    uint32_t h = 2166136261u;
    while (*str) {
        h ^= (uint8_t)*str++;
        h *= 16777619u;
    }
    return h;
}

static BOOL is_seen_or_insert(const char* str)
{
    uint32_t h = hash_str(str);
    uint32_t bucket = h % HASH_TABLE_SIZE;
    HashNode* node = g_hash_table[bucket];
    while (node) {
        if (node->hash == h && strcmp(node->str, str) == 0) {
            return TRUE;
        }
        node = node->next;
    }

    HashNode* new_node = (HashNode*)malloc(sizeof(HashNode));
    if (new_node) {
        new_node->hash = h;
        new_node->str = _strdup(str);
        new_node->next = g_hash_table[bucket];
        g_hash_table[bucket] = new_node;
    }
    return FALSE;
}

static HashNode* g_missing_hash_table[HASH_TABLE_SIZE] = { 0 };
static int g_missing_count = 0;

static BOOL is_missing_seen_or_insert(const char* str)
{
    uint32_t h = hash_str(str);
    uint32_t bucket = h % HASH_TABLE_SIZE;
    HashNode* node = g_missing_hash_table[bucket];
    while (node) {
        if (node->hash == h && strcmp(node->str, str) == 0) {
            return TRUE;
        }
        node = node->next;
    }

    HashNode* new_node = (HashNode*)malloc(sizeof(HashNode));
    if (new_node) {
        new_node->hash = h;
        new_node->str = _strdup(str);
        new_node->next = g_missing_hash_table[bucket];
        g_missing_hash_table[bucket] = new_node;
    }
    return FALSE;
}

static BOOL is_safe_str(const char* s, int max_len)
{
    if (!s || (uintptr_t)s < 0x10000) return FALSE;
    if (s[0] == '\0') return FALSE;
    int len = 0;
    int printable = 0;
    while (len < max_len && s[len] != '\0') {
        unsigned char c = (unsigned char)s[len];
        if (c >= 0x20 || c >= 0x80) {
            printable++;
        }
        len++;
    }
    return (len > 0 && printable > 0);
}

static void process_captured_text(const char* str, const char* source)
{
    if (!is_safe_str(str, 8192)) return;

    EnterCriticalSection(&g_cs);
    g_total_calls++;

    if (!g_fraw) {
        g_fraw = _wfopen(g_session_dump_log_path_w, L"w");
        g_fraw_latest = _wfopen(g_dump_log_path_w, L"w");
    }
    if (g_fraw || g_fraw_latest) {
        SYSTEMTIME st;
        GetLocalTime(&st);
        if (g_fraw) {
            fprintf(g_fraw, "[%02d:%02d:%02d] [%s] %s\n",
                    st.wHour, st.wMinute, st.wSecond, source, str);
            fflush(g_fraw);
        }
        if (g_fraw_latest) {
            fprintf(g_fraw_latest, "[%02d:%02d:%02d] [%s] %s\n",
                    st.wHour, st.wMinute, st.wSecond, source, str);
            fflush(g_fraw_latest);
        }
    }

    if (!is_seen_or_insert(str)) {
        g_unique_count++;
        if (!g_funique) {
            g_funique = _wfopen(g_session_dump_unique_path_w, L"w");
            g_funique_latest = _wfopen(g_dump_unique_path_w, L"w");
        }
        if (g_funique) {
            fprintf(g_funique, "/* ID:%05d [%s] */ %s\n", g_unique_count, source, str);
            fflush(g_funique);
        }
        if (g_funique_latest) {
            fprintf(g_funique_latest, "/* ID:%05d [%s] */ %s\n", g_unique_count, source, str);
            fflush(g_funique_latest);
        }
    }

    if (strchr(str, '<') != NULL && strchr(str, '>') != NULL) {
        if (!g_ftags) {
            g_ftags = _wfopen(g_tags_log_path_w, L"a+");
        }
        if (g_ftags) {
            SYSTEMTIME st;
            GetLocalTime(&st);
            fprintf(g_ftags, "[%02d:%02d:%02d] [%s] %s\n",
                    st.wHour, st.wMinute, st.wSecond, source, str);
            fflush(g_ftags);
        }
    }

    LeaveCriticalSection(&g_cs);
}

/* ==================================================================
 * Missing Japanese Text Detection & Logging
 * ================================================================== */
static BOOL has_japanese_utf8(const char* s)
{
    if (!s) return FALSE;
    const unsigned char* p = (const unsigned char*)s;
    while (*p) {
        if (*p == 0xE3) {
            unsigned char b1 = *(p + 1);
            unsigned char b2 = b1 ? *(p + 2) : 0;
            if (b1 != 0 && b2 != 0) {
                /* Japanese punctuation (e.g. 、 。 「 」 『 』) U+3001..U+303F */
                if (b1 == 0x80 && b2 >= 0x81 && b2 <= 0xBF) return TRUE;
                /* Hiragana U+3040..U+309F */
                if (b1 == 0x81 && b2 >= 0x80 && b2 <= 0xBF) return TRUE;
                if (b1 == 0x82 && b2 >= 0x80 && b2 <= 0x9F) return TRUE;
                /* Katakana U+30A0..U+30FF */
                if (b1 == 0x82 && b2 >= 0xA0 && b2 <= 0xBF) return TRUE;
                if (b1 == 0x83 && b2 >= 0x80 && b2 <= 0xBF) return TRUE;
                /* Katakana Phonetic Extensions U+31F0..U+31FF */
                if (b1 == 0x87 && b2 >= 0xB0 && b2 <= 0xBF) return TRUE;
                p += 3;
                continue;
            }
        } else if (*p >= 0xE4 && *p <= 0xE9) {
            unsigned char b1 = *(p + 1);
            unsigned char b2 = b1 ? *(p + 2) : 0;
            if (b1 != 0 && b2 != 0) {
                /* CJK Unified Ideographs (Kanji) U+4E00..U+9FFF */
                if (*p == 0xE4) {
                    if (b1 >= 0xB8 && b1 <= 0xBF && b2 >= 0x80 && b2 <= 0xBF) return TRUE;
                } else {
                    if (b1 >= 0x80 && b1 <= 0xBF && b2 >= 0x80 && b2 <= 0xBF) return TRUE;
                }
                p += 3;
                continue;
            }
        } else if (*p == 0xEF) {
            unsigned char b1 = *(p + 1);
            unsigned char b2 = b1 ? *(p + 2) : 0;
            if (b1 != 0 && b2 != 0) {
                /* Fullwidth & Halfwidth Forms U+FF00..U+FFEF (excludes PUA 0xEF 0x80..0xA3) */
                if (b1 >= 0xBC && b1 <= 0xBF && b2 >= 0x80 && b2 <= 0xBF) return TRUE;
                p += 3;
                continue;
            }
        }
        p++;
    }
    return FALSE;
}

static void escape_string_for_dump(char* dest, size_t dest_sz, const char* src)
{
    char* d = dest;
    char* end = dest + dest_sz - 3;
    while (*src && d < end) {
        if (*src == '\n') {
            *d++ = '\\';
            *d++ = 'n';
        } else if (*src == '\r') {
            /* ignore CR */
        } else if (*src == '\t') {
            *d++ = '\\';
            *d++ = 't';
        } else {
            *d++ = *src;
        }
        src++;
    }
    *d = '\0';
}

static void log_missing_text(const char* str, const char* source)
{
    if (!is_safe_str(str, 8192)) return;

    EnterCriticalSection(&g_cs);
    if (!is_missing_seen_or_insert(str)) {
        g_missing_count++;
        if (!g_fmissing) {
            g_fmissing = _wfopen(g_session_dump_missing_path_w, L"a+");
        }
        if (!g_fmissing_latest) {
            g_fmissing_latest = _wfopen(g_dump_missing_path_w, L"a+");
        }
        char escaped[8192];
        escape_string_for_dump(escaped, sizeof(escaped), str);

        if (g_fmissing) {
            fprintf(g_fmissing, "// [MISSING:%05d %s]\n%s=\n\n", g_missing_count, source, escaped);
            fflush(g_fmissing);
        }
        if (g_fmissing_latest) {
            fprintf(g_fmissing_latest, "// [MISSING:%05d %s]\n%s=\n\n", g_missing_count, source, escaped);
            fflush(g_fmissing_latest);
        }
        log_msg("[MISSING TEXT] Found untranslated Japanese text (count=%d, src=%s): %s", g_missing_count, source, escaped);
    }
    LeaveCriticalSection(&g_cs);
}

/* ==================================================================
 * Virtual File System (VFS / File Redirection)
 * ================================================================== */
#pragma pack(push, 1)
typedef struct {
    char magic[8];
    uint32_t count;
    uint32_t unk;
    uint64_t str_off;
    uint64_t str_len;
    uint64_t toc_off;
    uint64_t pad;
} FAFULLFS_Header;

typedef struct {
    uint64_t hash;
    uint64_t name_off;
    uint64_t unk1;
    uint64_t size;
    uint64_t offset;
    uint64_t unk2;
} FAFULLFS_TocEntry;
#pragma pack(pop)

typedef struct {
    uint64_t offset;
    uint64_t size;
    char name[128];
    int archive_id; /* 1 = data.dat, 2 = misc_1_00.dat */
} VfsEntry;

#define MAX_VFS_ENTRIES 16384
static VfsEntry g_vfs[MAX_VFS_ENTRIES];
static int g_vfs_count = 0;

static uint64_t g_toc_off_dat = 0;
static uint64_t g_toc_off_misc = 0;
static uint32_t g_count_dat = 0;
static uint32_t g_count_misc = 0;

static int load_archive_toc_w(const wchar_t* path_w, int archive_id)
{
    FILE* f = _wfopen(path_w, L"rb");
    if (!f) {
        log_msg("[VFS] Failed to open archive: %ls", path_w);
        return 0;
    }

    FAFULLFS_Header hdr;
    if (fread(&hdr, 1, sizeof(hdr), f) != sizeof(hdr)) {
        fclose(f);
        return 0;
    }

    if (memcmp(hdr.magic, "FAFULLFS", 8) != 0) {
        fclose(f);
        return 0;
    }

    if (archive_id == 1) {
        g_toc_off_dat = hdr.toc_off;
        g_count_dat = hdr.count;
    } else if (archive_id == 2) {
        g_toc_off_misc = hdr.toc_off;
        g_count_misc = hdr.count;
    }

    FAFULLFS_TocEntry* tocs = (FAFULLFS_TocEntry*)malloc(hdr.count * sizeof(FAFULLFS_TocEntry));
    char* str_table = (char*)malloc(hdr.str_len);
    if (!tocs || !str_table) {
        if (tocs) free(tocs);
        if (str_table) free(str_table);
        fclose(f);
        return 0;
    }

    _fseeki64(f, (int64_t)hdr.toc_off, SEEK_SET);
    fread(tocs, sizeof(FAFULLFS_TocEntry), hdr.count, f);

    _fseeki64(f, (int64_t)hdr.str_off, SEEK_SET);
    fread(str_table, 1, hdr.str_len, f);
    fclose(f);

    int loaded = 0;
    for (uint32_t i = 0; i < hdr.count && g_vfs_count < MAX_VFS_ENTRIES; i++) {
        uint64_t n_off = tocs[i].name_off;
        if (n_off < hdr.str_len) {
            VfsEntry* v = &g_vfs[g_vfs_count++];
            v->offset = tocs[i].offset;
            v->size = tocs[i].size;
            v->archive_id = archive_id;
            strncpy(v->name, str_table + n_off, sizeof(v->name) - 1);
            v->name[sizeof(v->name) - 1] = '\0';
            loaded++;
        }
    }

    free(tocs);
    free(str_table);
    log_msg("[VFS] Indexed %ls: %d files (TOC off=0x%llX)", path_w, loaded, (unsigned long long)hdr.toc_off);
    return loaded;
}

static BOOL file_exists_and_size_w(const wchar_t* path_w, long* out_size)
{
    WIN32_FILE_ATTRIBUTE_DATA fad;
    if (GetFileAttributesExW(path_w, GetFileExInfoStandard, &fad)) {
        if (!(fad.dwFileAttributes & FILE_ATTRIBUTE_DIRECTORY)) {
            if (out_size) {
                *out_size = (long)fad.nFileSizeLow;
            }
            return TRUE;
        }
    }
    return FALSE;
}

static const char* get_basename(const char* path)
{
    const char* slash = strrchr(path, '/');
    if (!slash) slash = strrchr(path, '\\');
    return slash ? (slash + 1) : path;
}

/* Search for override file in Mods directory structures */
static BOOL find_override_file_w(const char* vfs_name, wchar_t* out_path_w, size_t out_max, long* out_size)
{
    const char* base_name = get_basename(vfs_name);
    wchar_t base_name_w[MAX_PATH];
    MultiByteToWideChar(CP_UTF8, 0, base_name, -1, base_name_w, MAX_PATH);

    char win_vfs_name[MAX_PATH];
    strncpy(win_vfs_name, vfs_name, sizeof(win_vfs_name) - 1);
    win_vfs_name[sizeof(win_vfs_name) - 1] = '\0';
    for (int k = 0; win_vfs_name[k]; k++) {
        if (win_vfs_name[k] == '/') win_vfs_name[k] = '\\';
    }
    wchar_t win_vfs_name_w[MAX_PATH];
    MultiByteToWideChar(CP_UTF8, 0, win_vfs_name, -1, win_vfs_name_w, MAX_PATH);

    wchar_t candidate[MAX_PATH];

    /* 1. Mods\TextDump\<basename> */
    swprintf(candidate, MAX_PATH, L"%ls\\%ls", g_mod_dir_w, base_name_w);
    if (file_exists_and_size_w(candidate, out_size)) {
        wcsncpy(out_path_w, candidate, out_max - 1);
        out_path_w[out_max - 1] = L'\0';
        return TRUE;
    }

    /* 1b. Mods\TextDump\textures\<basename> */
    swprintf(candidate, MAX_PATH, L"%ls\\textures\\%ls", g_mod_dir_w, base_name_w);
    if (file_exists_and_size_w(candidate, out_size)) {
        wcsncpy(out_path_w, candidate, out_max - 1);
        out_path_w[out_max - 1] = L'\0';
        return TRUE;
    }

    /* 1c. Mods\TextDump\title_elements\<basename> */
    swprintf(candidate, MAX_PATH, L"%ls\\title_elements\\%ls", g_mod_dir_w, base_name_w);
    if (file_exists_and_size_w(candidate, out_size)) {
        wcsncpy(out_path_w, candidate, out_max - 1);
        out_path_w[out_max - 1] = L'\0';
        return TRUE;
    }

    /* 2. Mods\Fonts\<basename> */
    swprintf(candidate, MAX_PATH, L"%ls\\..\\Fonts\\%ls", g_mod_dir_w, base_name_w);
    if (file_exists_and_size_w(candidate, out_size)) {
        wcsncpy(out_path_w, candidate, out_max - 1);
        out_path_w[out_max - 1] = L'\0';
        return TRUE;
    }

    /* 2b. Mods\Textures\<basename> */
    swprintf(candidate, MAX_PATH, L"%ls\\..\\Textures\\%ls", g_mod_dir_w, base_name_w);
    if (file_exists_and_size_w(candidate, out_size)) {
        wcsncpy(out_path_w, candidate, out_max - 1);
        out_path_w[out_max - 1] = L'\0';
        return TRUE;
    }

    /* 2c. Mods\TextDump\fonts\<basename> */
    swprintf(candidate, MAX_PATH, L"%ls\\fonts\\%ls", g_mod_dir_w, base_name_w);
    if (file_exists_and_size_w(candidate, out_size)) {
        wcsncpy(out_path_w, candidate, out_max - 1);
        out_path_w[out_max - 1] = L'\0';
        return TRUE;
    }

    /* 2d. Mods\<basename> */
    swprintf(candidate, MAX_PATH, L"%ls\\..\\%ls", g_mod_dir_w, base_name_w);
    if (file_exists_and_size_w(candidate, out_size)) {
        wcsncpy(out_path_w, candidate, out_max - 1);
        out_path_w[out_max - 1] = L'\0';
        return TRUE;
    }

    /* 3. Mods\TextDump\<vfs_name> (e.g. Mods\TextDump\data\database\talk.dat) */
    swprintf(candidate, MAX_PATH, L"%ls\\%ls", g_mod_dir_w, win_vfs_name_w);
    if (file_exists_and_size_w(candidate, out_size)) {
        wcsncpy(out_path_w, candidate, out_max - 1);
        out_path_w[out_max - 1] = L'\0';
        return TRUE;
    }

    /* 4. Mods\<vfs_name> (e.g. Mods\data\database\talk.dat) */
    swprintf(candidate, MAX_PATH, L"%ls\\..\\%ls", g_mod_dir_w, win_vfs_name_w);
    if (file_exists_and_size_w(candidate, out_size)) {
        wcsncpy(out_path_w, candidate, out_max - 1);
        out_path_w[out_max - 1] = L'\0';
        return TRUE;
    }

    return FALSE;
}

/* Fast lookup from offset to VfsEntry */
static VfsEntry* lookup_vfs_by_offset(int archive_id, uint64_t offset)
{
    for (int i = 0; i < g_vfs_count; i++) {
        if (g_vfs[i].archive_id == archive_id && g_vfs[i].offset == offset) {
            return &g_vfs[i];
        }
    }
    return NULL;
}

/* ==================================================================
 * FAD Container Dynamic Resolution & Sub-File Mapping
 * ================================================================== */
typedef struct {
    int toc_index;
    const char* filename;
    const char* alt_filename;
    uint16_t width;
    uint16_t height;
} FadMappingDef;

static const FadMappingDef g_fad_mapping_defs[] = {
    {   0, "ui_0020_カレンダー.nltx", "ui_0020_カレンダー_thai.nltx", 1024, 1024 },
    {  10, "ui_0070_buttonicon_text.nltx", "ui_0070_buttonicon_text_thai.nltx", 512, 256 },
    {  22, "ui_1070_メッセージポップアップtext0.nltx", "ui_1070_メッセージポップアップtext0_thai.nltx", 512, 128 },
    {  23, "04_掟の張り紙A.nltx", "04_掟の張り紙A_thai.nltx", 2200, 1300 },
    {  26, "ui_2030_詳細ポップアップ.nltx", "ui_2030_詳細ポップアップ_thai.nltx", 512, 512 },
    {  27, "ui_1153_ウィンドウ.nltx", "ui_1153_ウィンドウ_thai.nltx", 1024, 1024 },
    {  34, "ui_0010_itemcategory.nltx", "ui_0010_itemcategory_thai.nltx", 512, 1024 },
    {  36, "ui_5090_掲示板.nltx", "ui_5090_掲示板_thai.nltx", 2048, 2048 },
    {  38, "ui_9000_01.nltx", "ui_9000_01_thai.nltx", 1024, 2048 },
    {  40, "ui_0060_Charaname24pxB.nltx", "ui_0060_Charaname24pxB_thai.nltx", 1024, 512 },
    {  47, "ui_0010_nameplate.nltx", "ui_0010_nameplate_thai.nltx", 512, 512 },
    {  49, "ui_9000_02.nltx", "ui_9000_02_thai.nltx", 1024, 2048 },
    {  51, "ui_0010_itemcategory03.nltx", "ui_0010_itemcategory03_thai.nltx", 256, 512 },
    {  94, "タイトル白.nltx", "title_white.nltx", 2048, 1280 },
    { 101, "名前_steam版_04.nltx", "名前_steam版_04_thai.nltx", 1024, 2048 },
    { 105, "ui_5080_00.nltx", "ui_5080_00_thai.nltx", 2048, 2048 },
    { 112, "ui_5100_bandolPU01.nltx", "ui_5100_bandolPU01_thai.nltx", 256, 256 },
    { 117, "ui_1170_投げ銭_text.nltx", "ui_1170_投げ銭_text_thai.nltx", 256, 128 },
    { 119, "ui_0120_汎用テキスト01.nltx", "ui_0120_汎用テキスト01_thai.nltx", 512, 256 },
    { 120, "ui_5010_チラシ01.nltx", "ui_5010_チラシ01_thai.nltx", 1024, 1024 },
    { 121, "ui_5010_チラシ02.nltx", "ui_5010_チラシ02_thai.nltx", 1024, 1024 },
    { 122, "ui_5010_チラシ03.nltx", "ui_5010_チラシ03_thai.nltx", 1024, 1024 },
    { 123, "ui_5010_チラシ04.nltx", "ui_5010_チラシ04_thai.nltx", 1024, 1024 },
    { 124, "ui_5010_チラシ05.nltx", "ui_5010_チラシ05_thai.nltx", 1024, 1024 },
    { 125, "ui_5010_チラシ06.nltx", "ui_5010_チラシ06_thai.nltx", 1024, 1024 },
    { 126, "ui_5010_チラシ07.nltx", "ui_5010_チラシ07_thai.nltx", 1024, 1024 },
    { 127, "ui_5010_チラシ08.nltx", "ui_5010_チラシ08_thai.nltx", 1024, 1024 },
    { 128, "ui_5010_チラシ09.nltx", "ui_5010_チラシ09_thai.nltx", 1024, 1024 },
    { 129, "ui_5010_チラシ10.nltx", "ui_5010_チラシ10_thai.nltx", 1024, 1024 },
    { 130, "ui_5010_チラシ11.nltx", "ui_5010_チラシ11_thai.nltx", 1024, 1024 },
    { 131, "ui_5010_チラシ12.nltx", "ui_5010_チラシ12_thai.nltx", 1024, 1024 },
    { 132, "ui_5010_チラシ13.nltx", "ui_5010_チラシ13_thai.nltx", 1024, 1024 },
    { 133, "ui_5010_チラシ14.nltx", "ui_5010_チラシ14_thai.nltx", 1024, 1024 },
    { 134, "ui_5010_チラシ15.nltx", "ui_5010_チラシ15_thai.nltx", 1024, 1024 },
    { 135, "ui_5010_チラシ16.nltx", "ui_5010_チラシ16_thai.nltx", 1024, 1024 },
    { 136, "ui_5010_チラシ17.nltx", "ui_5010_チラシ17_thai.nltx", 1024, 1024 },
    { 137, "ui_5010_チラシ18.nltx", "ui_5010_チラシ18_thai.nltx", 1024, 1024 },
    { 138, "ui_5010_チラシ19.nltx", "ui_5010_チラシ19_thai.nltx", 1024, 1024 },
    { 139, "ui_5010_チラシ20.nltx", "ui_5010_チラシ20_thai.nltx", 1024, 1024 },
    { 140, "ui_5010_チラシ30.nltx", "ui_5010_チラシ30_thai.nltx", 1024, 1024 },
    { 141, "ui_5010_チラシ31.nltx", "ui_5010_チラシ31_thai.nltx", 1024, 1024 },
    { 142, "ui_5010_チラシ32.nltx", "ui_5010_チラシ32_thai.nltx", 1024, 1024 },
    { 143, "ui_5010_チラシ33.nltx", "ui_5010_チラシ33_thai.nltx", 1024, 1024 },
    { 144, "ui_5010_チラシ34.nltx", "ui_5010_チラシ34_thai.nltx", 1024, 1024 },
    { 145, "ui_5010_チラシ35.nltx", "ui_5010_チラシ35_thai.nltx", 1024, 1024 },
    { 146, "ui_5010_チラシ36.nltx", "ui_5010_チラシ36_thai.nltx", 1024, 1024 },
    { 168, "鐘.nltx", "鐘_thai.nltx", 2200, 1300 },
    { 171, "ui_3440_00.nltx", "ui_3440_00_thai.nltx", 4096, 2048 },
    { 187, "ui_5010_項目02.nltx", "ui_5010_項目02_thai.nltx", 256, 1024 },
    { 189, "ui_5060_家畜一覧_01.nltx", "ui_5060_家畜一覧_01_thai.nltx", 2048, 2048 },
    { 191, "ui_0010_itemcategory2.nltx", "ui_0010_itemcategory2_thai.nltx", 1024, 256 },
    { 195, "ui_2220_post03.nltx", "ui_2220_post03_thai.nltx", 512, 1024 },
    { 196, "ui_2220_post01.nltx", "ui_2220_post01_thai.nltx", 2048, 2048 },
    { 199, "ui_0990_初回起動時ポエム.nltx", "ui_0990_初回起動時ポエム_thai.nltx", 1024, 512 },
    { 205, "ui_1000_title01.nltx", "ui_1000_タイトル01.nltx", 2048, 512 },
    { 206, "ui_0990_localize_00.nltx", "ui_0990_localize_00_thai.nltx", 1024, 512 },
    { 207, "ui_1000_02.nltx", "ui_1000_02_thai.nltx", 2048, 256 },
    { 218, "ui_2100_00.nltx", "ui_2100_00_thai.nltx", 256, 256 },
    { 226, "ene_3020_1_02.nltx", "ene_3020_1_02_thai.nltx", 512, 256 },
    { 231, "bg_8080_00_tex.nltx", "bg_8080_00_tex_thai.nltx", 512, 256 },
    { 232, "bg_8080_04_tex.nltx", "bg_8080_04_tex_thai.nltx", 1024, 2048 },
    { 233, "bg_8080_01_tex.nltx", "bg_8080_01_tex_thai.nltx", 2048, 256 },
    { 313, "ui_2210_日リザルト02.nltx", "ui_2210_日リザルト02_thai.nltx", 1024, 256 },
    { 318, "ui_0030_汎用アイコン_はんこ.nltx", "ui_0030_汎用アイコン_はんこ_thai.nltx", 1024, 512 },
    { 341, "ui_2020_コックピット_text.nltx", "ui_2020_コックピット_text_thai.nltx", 512, 256 },
    { 342, "ui_3030_家具配置01.nltx", "ui_3030_家具配置01_thai.nltx", 2048, 512 },
};

typedef struct {
    uint64_t offset;          /* Offset in fairy_1_00.dat */
    const char* filename;      /* Canonical filename, e.g. "ui_1000_title01.nltx" */
    const char* alt_filename;  /* Alt filename, e.g. "ui_1000_title01_thai.nltx" */
    uint16_t width;
    uint16_t height;
    BOOL has_fad_descriptor;  /* TRUE if offset is at 32-byte FAD descriptor */
} FadSubFile;

#define MAX_FAD_RUNTIME_SUBFILES 256
static FadSubFile g_fad_runtime_subfiles[MAX_FAD_RUNTIME_SUBFILES];
static int g_fad_runtime_count = 0;
static uint64_t g_fad_base_offset = 0;
static BOOL g_fad_resolved = FALSE;

static void resolve_dynamic_fad_offsets_w(const wchar_t* fairy_path_w)
{
    if (g_fad_resolved) return;

    uint64_t resident_lang_jp_offset = 0;
    for (int i = 0; i < g_vfs_count; i++) {
        if (g_vfs[i].archive_id == 4 && strstr(g_vfs[i].name, "resident_lang_jp.fad") != NULL) {
            resident_lang_jp_offset = g_vfs[i].offset;
            break;
        }
    }

    FILE* f = _wfopen(fairy_path_w, L"rb");
    if (!f) {
        log_msg("[FAD RESOLVER] Cannot open fairy_1_00.dat: %ls", fairy_path_w);
        return;
    }

    if (resident_lang_jp_offset == 0) {
        FAFULLFS_Header hdr;
        if (fread(&hdr, 1, sizeof(hdr), f) == sizeof(hdr) && memcmp(hdr.magic, "FAFULLFS", 8) == 0) {
            FAFULLFS_TocEntry* tocs = (FAFULLFS_TocEntry*)malloc(hdr.count * sizeof(FAFULLFS_TocEntry));
            char* str_table = (char*)malloc(hdr.str_len);
            if (tocs && str_table) {
                _fseeki64(f, (int64_t)hdr.toc_off, SEEK_SET);
                fread(tocs, sizeof(FAFULLFS_TocEntry), hdr.count, f);

                _fseeki64(f, (int64_t)hdr.str_off, SEEK_SET);
                fread(str_table, 1, hdr.str_len, f);

                for (uint32_t i = 0; i < hdr.count; i++) {
                    uint64_t n_off = tocs[i].name_off;
                    if (n_off < hdr.str_len) {
                        const char* name = str_table + n_off;
                        if (strstr(name, "resident_lang_jp.fad") != NULL) {
                            resident_lang_jp_offset = tocs[i].offset;
                            break;
                        }
                    }
                }
            }
            if (tocs) free(tocs);
            if (str_table) free(str_table);
        }
    }

    if (resident_lang_jp_offset == 0) {
        log_msg("[FAD RESOLVER] resident_lang_jp.fad not found in %ls TOC", fairy_path_w);
        fclose(f);
        return;
    }

    g_fad_base_offset = resident_lang_jp_offset;
    log_msg("[FAD RESOLVER] Detected resident_lang_jp.fad base offset: 0x%llX", (unsigned long long)g_fad_base_offset);

    /* Read FAD TOC (16 KB header) */
    uint8_t fad_hdr[0x4000];
    _fseeki64(f, (int64_t)g_fad_base_offset, SEEK_SET);
    size_t nread = fread(fad_hdr, 1, sizeof(fad_hdr), f);
    fclose(f);

    if (nread < 0x4000) {
        log_msg("[FAD RESOLVER] Failed to read FAD header (read %zu bytes)", nread);
        return;
    }

    EnterCriticalSection(&g_cs);
    g_fad_runtime_count = 0;
    size_t num_defs = sizeof(g_fad_mapping_defs) / sizeof(g_fad_mapping_defs[0]);

    for (size_t i = 0; i < num_defs; i++) {
        int idx = g_fad_mapping_defs[i].toc_index;
        size_t pos = 0x1018 + (size_t)idx * 32;
        if (pos + 12 > sizeof(fad_hdr)) continue;

        uint64_t entry_sz = *(uint64_t*)(fad_hdr + pos + 0);
        uint32_t rel_off = *(uint32_t*)(fad_hdr + pos + 8);
        if (entry_sz == 0 && rel_off == 0) continue;

        uint64_t desc_off = g_fad_base_offset + (uint64_t)rel_off + 32;
        uint64_t data_off = g_fad_base_offset + (uint64_t)rel_off + 64;

        if (g_fad_runtime_count + 2 <= MAX_FAD_RUNTIME_SUBFILES) {
            /* Descriptor entry */
            FadSubFile* e1 = &g_fad_runtime_subfiles[g_fad_runtime_count++];
            e1->offset = desc_off;
            e1->filename = g_fad_mapping_defs[i].filename;
            e1->alt_filename = g_fad_mapping_defs[i].alt_filename;
            e1->width = g_fad_mapping_defs[i].width;
            e1->height = g_fad_mapping_defs[i].height;
            e1->has_fad_descriptor = TRUE;

            /* Data entry */
            FadSubFile* e2 = &g_fad_runtime_subfiles[g_fad_runtime_count++];
            e2->offset = data_off;
            e2->filename = g_fad_mapping_defs[i].filename;
            e2->alt_filename = g_fad_mapping_defs[i].alt_filename;
            e2->width = g_fad_mapping_defs[i].width;
            e2->height = g_fad_mapping_defs[i].height;
            e2->has_fad_descriptor = FALSE;
        }
    }

    g_fad_resolved = TRUE;
    LeaveCriticalSection(&g_cs);

    log_msg("[FAD RESOLVER] Dynamic resolution complete: %d subfile targets mapped in RAM (base=0x%llX)!",
            g_fad_runtime_count, (unsigned long long)g_fad_base_offset);
}

static const FadSubFile* lookup_fad_subfile(uint64_t offset)
{
    for (int i = 0; i < g_fad_runtime_count; i++) {
        if (g_fad_runtime_subfiles[i].offset == offset) {
            return &g_fad_runtime_subfiles[i];
        }
    }
    return NULL;
}

/* ==================================================================
 * Hook Definitions: CreateFileW & CreateFileA for Archive Redirection
 * ================================================================== */
typedef HANDLE (WINAPI *t_CreateFileW)(
    LPCWSTR lpFileName,
    DWORD dwDesiredAccess,
    DWORD dwShareMode,
    LPSECURITY_ATTRIBUTES lpSecurityAttributes,
    DWORD dwCreationDisposition,
    DWORD dwFlagsAndAttributes,
    HANDLE hTemplateFile
);
static t_CreateFileW fp_original_CreateFileW = NULL;

typedef HANDLE (WINAPI *t_CreateFileA)(
    LPCSTR lpFileName,
    DWORD dwDesiredAccess,
    DWORD dwShareMode,
    LPSECURITY_ATTRIBUTES lpSecurityAttributes,
    DWORD dwCreationDisposition,
    DWORD dwFlagsAndAttributes,
    HANDLE hTemplateFile
);
static t_CreateFileA fp_original_CreateFileA = NULL;

static const char* get_arch_name(int id) {
    switch (id) {
        case 1: return "data.dat";
        case 2: return "misc_1_00.dat";
        case 3: return "texture_1_00.dat";
        case 4: return "fairy_1_00.dat";
        default: return "archive";
    }
}

static HANDLE WINAPI hk_CreateFileW(
    LPCWSTR lpFileName,
    DWORD dwDesiredAccess,
    DWORD dwShareMode,
    LPSECURITY_ATTRIBUTES lpSecurityAttributes,
    DWORD dwCreationDisposition,
    DWORD dwFlagsAndAttributes,
    HANDLE hTemplateFile
)
{
    if (lpFileName) {
        wchar_t lower[MAX_PATH];
        int len = 0;
        while (lpFileName[len] && len < MAX_PATH - 1) {
            lower[len] = (wchar_t)towlower(lpFileName[len]);
            len++;
        }
        lower[len] = L'\0';

        if (wcsstr(lower, L"data") || wcsstr(lower, L".dat") || wcsstr(lower, L".fad") || wcsstr(lower, L".nltx")) {
            log_file_access("[OPEN_FILE] %ls", lpFileName);
        }

        if (wcsstr(lower, L"fairy_1_00.dat")) {
            if (!g_fad_resolved) {
                resolve_dynamic_fad_offsets_w(lpFileName);
            }
        }
    }
    return fp_original_CreateFileW(
        lpFileName,
        dwDesiredAccess,
        dwShareMode,
        lpSecurityAttributes,
        dwCreationDisposition,
        dwFlagsAndAttributes,
        hTemplateFile
    );
}

static HANDLE WINAPI hk_CreateFileA(
    LPCSTR lpFileName,
    DWORD dwDesiredAccess,
    DWORD dwShareMode,
    LPSECURITY_ATTRIBUTES lpSecurityAttributes,
    DWORD dwCreationDisposition,
    DWORD dwFlagsAndAttributes,
    HANDLE hTemplateFile
)
{
    return fp_original_CreateFileA(
        lpFileName,
        dwDesiredAccess,
        dwShareMode,
        lpSecurityAttributes,
        dwCreationDisposition,
        dwFlagsAndAttributes,
        hTemplateFile
    );
}

/* ==================================================================
 * Hook Definitions: ReadFile for Virtual File System (VFS)
 * ================================================================== */
typedef BOOL (WINAPI *t_ReadFile)(
    HANDLE hFile,
    LPVOID lpBuffer,
    DWORD nNumberOfBytesToRead,
    LPDWORD lpNumberOfBytesRead,
    LPOVERLAPPED lpOverlapped
);
static t_ReadFile fp_original_ReadFile = NULL;

#define MAX_CACHED_HANDLES 128
typedef struct {
    HANDLE h;
    int type; /* 1 = data.dat, 2 = misc_1_00.dat, -1 = other */
} HandleCache;

static HandleCache g_handles[MAX_CACHED_HANDLES];
static int g_handle_count = 0;

static int identify_archive_handle(HANDLE hFile)
{
    if (hFile == INVALID_HANDLE_VALUE || hFile == NULL) return 0;

    EnterCriticalSection(&g_cs);
    for (int i = 0; i < g_handle_count; i++) {
        if (g_handles[i].h == hFile) {
            int t = g_handles[i].type;
            LeaveCriticalSection(&g_cs);
            return (t > 0) ? t : 0;
        }
    }

    int type = -1;
    wchar_t path_w[MAX_PATH] = { 0 };
    DWORD len = GetFinalPathNameByHandleW(hFile, path_w, MAX_PATH - 1, 0);
    if (len > 0) {
        wchar_t lpath[MAX_PATH];
        for (DWORD i = 0; i <= len && i < MAX_PATH; i++) {
            lpath[i] = (wchar_t)towlower(path_w[i]);
        }
        if (wcsstr(lpath, L"misc_1_00.dat")) {
            type = 2;
            log_msg("[VFS] Cached misc_1_00.dat handle: 0x%p", hFile);
        } else if (wcsstr(lpath, L"data.dat")) {
            type = 1;
            log_msg("[VFS] Cached data.dat handle: 0x%p", hFile);
        } else if (wcsstr(lpath, L"texture_1_00.dat")) {
            type = 3;
            log_msg("[VFS] Cached texture_1_00.dat handle: 0x%p", hFile);
        } else if (wcsstr(lpath, L"fairy_1_00.dat")) {
            type = 4;
            log_msg("[VFS] Cached fairy_1_00.dat handle: 0x%p", hFile);
        }
    }

    if (g_handle_count < MAX_CACHED_HANDLES) {
        g_handles[g_handle_count].h = hFile;
        g_handles[g_handle_count].type = type;
        g_handle_count++;
    }
    LeaveCriticalSection(&g_cs);
    return (type > 0) ? type : 0;
}

/* ==================================================================
 * Hook Definitions: GetOverlappedResult for Async VFS Redirection
 * ================================================================== */
typedef BOOL (WINAPI *t_GetOverlappedResult)(
    HANDLE hFile,
    LPOVERLAPPED lpOverlapped,
    LPDWORD lpNumberOfBytesTransferred,
    BOOL bWait
);
static t_GetOverlappedResult fp_original_GetOverlappedResult = NULL;

typedef struct {
    HANDLE hFile;
    LPOVERLAPPED lpOverlapped;
    LPVOID lpBuffer;
    int arch_id;
    uint64_t offset;
    DWORD bytes_requested;
    wchar_t override_path_w[MAX_PATH];
    long ext_size;
    BOOL is_fad_desc;
    uint16_t width;
    uint16_t height;
    char filename[128];
    BOOL is_texture_db_patch;
    BOOL is_font_db_patch;
    BOOL in_use;
} PendingIo;

#define MAX_PENDING_IO 64
static PendingIo g_pending_io[MAX_PENDING_IO] = { 0 };

static void add_pending_io(
    HANDLE hFile,
    LPOVERLAPPED lpOverlapped,
    LPVOID lpBuffer,
    int arch_id,
    uint64_t offset,
    DWORD bytes_requested,
    const wchar_t* override_path_w,
    long ext_size,
    BOOL is_fad_desc,
    uint16_t width,
    uint16_t height,
    const char* filename
)
{
    EnterCriticalSection(&g_cs);
    for (int i = 0; i < MAX_PENDING_IO; i++) {
        if (!g_pending_io[i].in_use) {
            g_pending_io[i].in_use = TRUE;
            g_pending_io[i].hFile = hFile;
            g_pending_io[i].lpOverlapped = lpOverlapped;
            g_pending_io[i].lpBuffer = lpBuffer;
            g_pending_io[i].arch_id = arch_id;
            g_pending_io[i].offset = offset;
            g_pending_io[i].bytes_requested = bytes_requested;
            wcsncpy(g_pending_io[i].override_path_w, override_path_w, MAX_PATH - 1);
            g_pending_io[i].override_path_w[MAX_PATH - 1] = L'\0';
            g_pending_io[i].ext_size = ext_size;
            g_pending_io[i].is_fad_desc = is_fad_desc;
            g_pending_io[i].width = width;
            g_pending_io[i].height = height;
            strncpy(g_pending_io[i].filename, filename, 127);
            g_pending_io[i].filename[127] = '\0';
            g_pending_io[i].is_texture_db_patch = (strstr(filename, "data/database/texture.dat") != NULL);
            g_pending_io[i].is_font_db_patch = (strstr(filename, "data/database/font.dat") != NULL);
            LeaveCriticalSection(&g_cs);
            return;
        }
    }
    LeaveCriticalSection(&g_cs);
    log_msg("[VFS WARN] g_pending_io table full!");
}

static BOOL find_and_remove_pending_io(LPOVERLAPPED lpOverlapped, PendingIo* out)
{
    if (!lpOverlapped) return FALSE;
    EnterCriticalSection(&g_cs);
    for (int i = 0; i < MAX_PENDING_IO; i++) {
        if (g_pending_io[i].in_use && g_pending_io[i].lpOverlapped == lpOverlapped) {
            *out = g_pending_io[i];
            g_pending_io[i].in_use = FALSE;
            LeaveCriticalSection(&g_cs);
            return TRUE;
        }
    }
    LeaveCriticalSection(&g_cs);
    return FALSE;
}

static void apply_vfs_payload(const PendingIo* pio)
{
    FILE* fext = _wfopen(pio->override_path_w, L"rb");
    if (!fext) {
        log_msg("[VFS ERROR] Could not open override file: %ls", pio->override_path_w);
        return;
    }

    if (pio->is_fad_desc) {
        /* Prepend 32-byte FAD descriptor */
        uint8_t desc[32] = { 0 };
        uint64_t nltx_size = (uint64_t)pio->ext_size;
        memcpy(desc + 0, &nltx_size, sizeof(uint64_t));
        *(uint16_t*)(desc + 8) = pio->width;
        *(uint16_t*)(desc + 10) = pio->height;
        *(uint32_t*)(desc + 16) = 0x0B010080;
        *(uint16_t*)(desc + 20) = pio->width;
        *(uint16_t*)(desc + 22) = pio->height;

        memcpy(pio->lpBuffer, desc, 32);

        DWORD body_max = (pio->bytes_requested > 32) ? (pio->bytes_requested - 32) : 0;
        DWORD to_read = (DWORD)pio->ext_size;
        if (to_read > body_max && body_max > 0) to_read = body_max;

        size_t actual_read = fread((char*)pio->lpBuffer + 32, 1, to_read, fext);
        fclose(fext);

        size_t total_written = 32 + actual_read;
        if (pio->bytes_requested > (DWORD)total_written) {
            memset((char*)pio->lpBuffer + total_written, 0, pio->bytes_requested - (DWORD)total_written);
        }

        log_msg("[VFS ASYNC SUCCESS] Applied FAD [%s] (0x%llX) -> %ls (%u NLTX + 32 desc into buffer %u)",
                pio->filename, (unsigned long long)pio->offset, pio->override_path_w,
                (unsigned int)actual_read, (unsigned int)pio->bytes_requested);
    } else {
        DWORD to_read = (DWORD)pio->ext_size;
        if (to_read > pio->bytes_requested && pio->bytes_requested > 0) {
            to_read = pio->bytes_requested;
        }
        size_t actual_read = fread(pio->lpBuffer, 1, to_read, fext);
        fclose(fext);

        if (pio->bytes_requested > (DWORD)actual_read) {
            memset((char*)pio->lpBuffer + actual_read, 0, pio->bytes_requested - (DWORD)actual_read);
        }

        log_msg("[VFS ASYNC SUCCESS] Applied VFS [%s] (0x%llX) -> %ls (read %u bytes into buffer %u)",
                pio->filename, (unsigned long long)pio->offset, pio->override_path_w,
                (unsigned int)actual_read, (unsigned int)pio->bytes_requested);
    }
}

static void patch_texture_database_in_ram(void* buffer, DWORD size)
{
    if (!buffer || size < 1024) return;

    static const struct {
        const char* target;
        size_t target_len;
        const char* replacement;
        size_t replacement_len;
    } kTextureDbPatches[] = {
        { "data/texture/fairy_ui_0070/ui_0070_buttonicon_text_JP.nltx", 58,
          "data/texture/fairy_ui_0070/ui_0070_buttonicon_text_en.nltx", 58 },
        { "data/texture/fairy_ui_5080/ui_5080_02_JP.nltx", 46,
          "data/texture/fairy_ui_5080/ui_5080_02_en.nltx", 46 },
        { "data/texture/minimap_01_spr.nltx\0\0\0\0", 35,
          "data/texture/minimap_01_spr_en.nltx\0", 35 },
        { "data/texture/minimap_01_aut.nltx\0\0\0\0", 35,
          "data/texture/minimap_01_aut_en.nltx\0", 35 },
        { "data/texture/minimap_01_sum.nltx\0\0\0\0", 35,
          "data/texture/minimap_01_sum_en.nltx\0", 35 },
        { "data/texture/minimap_01_win.nltx\0\0\0\0", 35,
          "data/texture/minimap_01_win_en.nltx\0", 35 },
        { "data/texture/minimap_11_spr.nltx\0\0\0\0", 35,
          "data/texture/minimap_11_spr_en.nltx\0", 35 },
        { "data/texture/minimap_11_aut.nltx\0\0\0\0", 35,
          "data/texture/minimap_11_aut_en.nltx\0", 35 },
        { "data/texture/minimap_11_sum.nltx\0\0\0\0", 35,
          "data/texture/minimap_11_sum_en.nltx\0", 35 },
        { "data/texture/minimap_11_win.nltx\0\0\0\0", 35,
          "data/texture/minimap_11_win_en.nltx\0", 35 },
    };

    uint8_t* p = (uint8_t*)buffer;
    size_t num_patches = sizeof(kTextureDbPatches) / sizeof(kTextureDbPatches[0]);
    int total_applied = 0;

    for (size_t i = 0; i < num_patches; i++) {
        const char* tgt = kTextureDbPatches[i].target;
        size_t tlen = kTextureDbPatches[i].target_len;
        const char* rep = kTextureDbPatches[i].replacement;
        size_t rlen = kTextureDbPatches[i].replacement_len;

        if (size >= tlen) {
            size_t max_search = size - tlen;
            for (size_t off = 0; off <= max_search; off++) {
                if (p[off] == (uint8_t)tgt[0] && memcmp(p + off, tgt, tlen) == 0) {
                    memcpy(p + off, rep, rlen);
                    total_applied++;
                    off += tlen - 1;
                }
            }
        }
    }

    log_msg("[Texture DB Patch] Applied %d texture redirections in RAM (data/database/texture.dat)!", total_applied);
}

static void patch_font_database_in_ram(void* buffer, DWORD size)
{
    if (!buffer || size < 64) return;

    uint8_t* p = (uint8_t*)buffer;
    uint32_t num_records = *(uint32_t*)(p + 0);
    uint32_t record_size = *(uint32_t*)(p + 12);

    if (num_records == 0 || num_records > 32 || record_size < 100 || record_size > 4096) {
        log_msg("[Font DB Patch WARN] Unexpected font.dat header: num_records=%u, record_size=%u",
                num_records, record_size);
        return;
    }

    /* 1. Configure Proportional spacing (flag1=1, flag2=5) across all records */
    uint32_t stride = record_size + 4;
    int patched_flags = 0;
    for (uint32_t r = 0; r < num_records; r++) {
        size_t rec_start = 16 + (size_t)r * stride;
        if (rec_start + 0x68 <= size) {
            *(uint32_t*)(p + rec_start + 0x60) = 1;
            *(uint32_t*)(p + rec_start + 0x64) = 5;
            patched_flags++;
        }
    }

    /* 2. Replace KiwiMaru with Lora in string table */
    static const struct {
        const char* target;
        size_t target_len;
        const char* replacement;
        size_t replacement_len;
    } kFontDbPatches[] = {
        /* data/misc/KiwiMaru-Medium.ttf (30 bytes with null) -> data/misc/Lora-Bold.ttf (pad to 30 bytes) */
        { "data/misc/KiwiMaru-Medium.ttf\0", 30,
          "data/misc/Lora-Bold.ttf\0\0\0\0\0\0\0", 30 },
        /* data/misc/KiwiMaru-Regular.ttf (31 bytes with null) -> data/misc/Lora-Medium.ttf (pad to 31 bytes) */
        { "data/misc/KiwiMaru-Regular.ttf\0", 31,
          "data/misc/Lora-Medium.ttf\0\0\0\0\0\0", 31 }
    };

    int replaced_strings = 0;
    for (size_t i = 0; i < sizeof(kFontDbPatches) / sizeof(kFontDbPatches[0]); i++) {
        const char* tgt = kFontDbPatches[i].target;
        size_t tlen = kFontDbPatches[i].target_len;
        const char* rep = kFontDbPatches[i].replacement;
        size_t rlen = kFontDbPatches[i].replacement_len;

        if (size >= tlen) {
            size_t max_search = size - tlen;
            for (size_t off = 0; off <= max_search; off++) {
                if (p[off] == (uint8_t)tgt[0] && memcmp(p + off, tgt, tlen) == 0) {
                    memcpy(p + off, rep, rlen);
                    replaced_strings++;
                    off += tlen - 1;
                }
            }
        }
    }

    log_msg("[Font DB Patch] Success: Configured Proportional flags (%d records) & redirected %d KiwiMaru instances to Lora in RAM!",
            patched_flags, replaced_strings);
}

static BOOL WINAPI hk_GetOverlappedResult(
    HANDLE hFile,
    LPOVERLAPPED lpOverlapped,
    LPDWORD lpNumberOfBytesTransferred,
    BOOL bWait
)
{
    BOOL res = fp_original_GetOverlappedResult(hFile, lpOverlapped, lpNumberOfBytesTransferred, bWait);
    if (!res) {
        return FALSE;
    }

    PendingIo pio;
    if (find_and_remove_pending_io(lpOverlapped, &pio)) {
        if (pio.is_texture_db_patch) {
            DWORD bytes = (lpNumberOfBytesTransferred ? *lpNumberOfBytesTransferred : pio.bytes_requested);
            patch_texture_database_in_ram(pio.lpBuffer, bytes);
        } else if (pio.is_font_db_patch) {
            DWORD bytes = (lpNumberOfBytesTransferred ? *lpNumberOfBytesTransferred : pio.bytes_requested);
            patch_font_database_in_ram(pio.lpBuffer, bytes);
        } else {
            apply_vfs_payload(&pio);
        }
    }

    return res;
}

static BOOL WINAPI hk_ReadFile(
    HANDLE hFile,
    LPVOID lpBuffer,
    DWORD nNumberOfBytesToRead,
    LPDWORD lpNumberOfBytesRead,
    LPOVERLAPPED lpOverlapped
)
{
    int arch_id = identify_archive_handle(hFile);
    if (arch_id == 0 || !lpBuffer) {
        return fp_original_ReadFile(hFile, lpBuffer, nNumberOfBytesToRead, lpNumberOfBytesRead, lpOverlapped);
    }

    uint64_t offset_log = 0;
    if (lpOverlapped) {
        offset_log = ((uint64_t)lpOverlapped->OffsetHigh << 32) | (uint64_t)lpOverlapped->Offset;
    }
    VfsEntry* v_log = lookup_vfs_by_offset(arch_id, offset_log);
    if (v_log) {
        log_file_access("[READ_ARCHIVE] %-16s Offset: 0x%08llX (%6u B) -> [%s]",
                        get_arch_name(arch_id), (unsigned long long)offset_log, nNumberOfBytesToRead, v_log->name);
    } else {
        const FadSubFile* fs_log = (arch_id == 4) ? lookup_fad_subfile(offset_log) : NULL;
        if (fs_log) {
            log_file_access("[READ_ARCHIVE] %-16s Offset: 0x%08llX (%6u B) -> [%s]",
                            get_arch_name(arch_id), (unsigned long long)offset_log, nNumberOfBytesToRead, fs_log->filename);
        } else {
            log_file_access("[READ_ARCHIVE] %-16s Offset: 0x%08llX (%6u B)",
                            get_arch_name(arch_id), (unsigned long long)offset_log, nNumberOfBytesToRead);
        }
    }

    uint64_t offset = 0;
    if (lpOverlapped) {
        offset = ((uint64_t)lpOverlapped->OffsetHigh << 32) | (uint64_t)lpOverlapped->Offset;
    } else {
        LARGE_INTEGER curr;
        LARGE_INTEGER zero = { 0 };
        if (SetFilePointerEx(hFile, zero, &curr, FILE_CURRENT)) {
            offset = curr.QuadPart;
        }
    }

    /* 1. Check if the game is reading the TOC table */
    uint64_t toc_off = (arch_id == 1) ? g_toc_off_dat : g_toc_off_misc;
    if (toc_off != 0 && offset == toc_off) {
        BOOL res = fp_original_ReadFile(hFile, lpBuffer, nNumberOfBytesToRead, lpNumberOfBytesRead, lpOverlapped);
        if (!res && GetLastError() == ERROR_IO_PENDING && lpOverlapped) {
            DWORD transferred = 0;
            if (GetOverlappedResult(hFile, lpOverlapped, &transferred, TRUE)) {
                res = TRUE;
                if (lpNumberOfBytesRead) *lpNumberOfBytesRead = transferred;
                if (lpOverlapped->hEvent) {
                    SetEvent(lpOverlapped->hEvent);
                }
            }
        }
        if (res && lpBuffer) {
            /* Patch TOC entries in RAM for any file that has a larger external override */
            FAFULLFS_TocEntry* tocs = (FAFULLFS_TocEntry*)lpBuffer;
            uint32_t count = (arch_id == 1) ? g_count_dat : g_count_misc;
            DWORD max_entries = nNumberOfBytesToRead / sizeof(FAFULLFS_TocEntry);
            if (count > max_entries) count = max_entries;

            int patched = 0;
            for (uint32_t i = 0; i < count; i++) {
                VfsEntry* v = lookup_vfs_by_offset(arch_id, tocs[i].offset);
                if (v) {
                    wchar_t override_path_w[MAX_PATH];
                    long ext_size = 0;
                    if (find_override_file_w(v->name, override_path_w, MAX_PATH, &ext_size)) {
                        if (ext_size > (long)tocs[i].size) {
                            log_msg("[VFS TOC Patch] Expanding TOC size for [%s]: %llu -> %ld bytes",
                                    v->name, (unsigned long long)tocs[i].size, ext_size);
                            tocs[i].size = (uint64_t)ext_size;
                            v->size = (uint64_t)ext_size;
                            patched++;
                        }
                    }
                }
            }
            if (patched > 0) {
                log_msg("[VFS TOC Patch] Successfully patched %d TOC entries in RAM!", patched);
            }
        }
        return res;
    }

    /* 2. Check if this is an access to a file in data.dat or misc_1_00.dat */
    if (arch_id == 1 || arch_id == 2) {
        VfsEntry* v = lookup_vfs_by_offset(arch_id, offset);
        if (v) {
            BOOL is_tex_db = (strstr(v->name, "data/database/texture.dat") != NULL);
            BOOL is_font_db = (strstr(v->name, "data/database/font.dat") != NULL);

            wchar_t override_path_w[MAX_PATH];
            long ext_size = 0;
            BOOL has_override = find_override_file_w(v->name, override_path_w, MAX_PATH, &ext_size);

            if (has_override || is_tex_db || is_font_db) {
                if (lpOverlapped) {
                    add_pending_io(
                        hFile, lpOverlapped, lpBuffer, arch_id, offset, nNumberOfBytesToRead,
                        override_path_w, ext_size, FALSE, 0, 0, v->name
                    );
                    log_msg("[VFS ASYNC QUEUED] Archive [%s] (0x%llX) -> %ls (nBytes=%u)",
                            v->name, (unsigned long long)offset, override_path_w, nNumberOfBytesToRead);
                    return fp_original_ReadFile(hFile, lpBuffer, nNumberOfBytesToRead, lpNumberOfBytesRead, lpOverlapped);
                } else {
                    BOOL res = fp_original_ReadFile(hFile, lpBuffer, nNumberOfBytesToRead, lpNumberOfBytesRead, NULL);
                    if (res && lpBuffer) {
                        if (is_tex_db) {
                            patch_texture_database_in_ram(lpBuffer, nNumberOfBytesToRead);
                        } else if (is_font_db) {
                            patch_font_database_in_ram(lpBuffer, nNumberOfBytesToRead);
                        } else if (has_override) {
                            PendingIo pio = { 0 };
                            pio.lpBuffer = lpBuffer;
                            pio.bytes_requested = nNumberOfBytesToRead;
                            wcsncpy(pio.override_path_w, override_path_w, MAX_PATH - 1);
                            pio.ext_size = ext_size;
                            pio.is_fad_desc = FALSE;
                            strncpy(pio.filename, v->name, 127);
                            apply_vfs_payload(&pio);
                        }
                    }
                    return res;
                }
            }
        }
    }

    /* 3. Check if this is an access to a file inside fairy_1_00.dat */
    if (arch_id == 4) {
        const FadSubFile* fad_entry = lookup_fad_subfile(offset);
        if (fad_entry) {
            wchar_t override_path_w[MAX_PATH];
            long ext_size = 0;
            BOOL has_override = find_override_file_w(fad_entry->filename, override_path_w, MAX_PATH, &ext_size);
            if (!has_override && fad_entry->alt_filename) {
                has_override = find_override_file_w(fad_entry->alt_filename, override_path_w, MAX_PATH, &ext_size);
            }

            if (has_override) {
                BOOL is_nltx = FALSE;
                size_t flen = strlen(fad_entry->filename);
                if (flen > 5 && strcmp(fad_entry->filename + flen - 5, ".nltx") == 0) {
                    is_nltx = TRUE;
                }

                BOOL is_fad_desc = fad_entry->has_fad_descriptor && is_nltx;

                if (lpOverlapped) {
                    add_pending_io(
                        hFile, lpOverlapped, lpBuffer, arch_id, offset, nNumberOfBytesToRead,
                        override_path_w, ext_size, is_fad_desc, fad_entry->width, fad_entry->height, fad_entry->filename
                    );
                    log_msg("[VFS ASYNC QUEUED] FAD [%s] (0x%llX) -> %ls (nBytes=%u)",
                            fad_entry->filename, (unsigned long long)offset, override_path_w, nNumberOfBytesToRead);
                    return fp_original_ReadFile(hFile, lpBuffer, nNumberOfBytesToRead, lpNumberOfBytesRead, lpOverlapped);
                } else {
                    BOOL res = fp_original_ReadFile(hFile, lpBuffer, nNumberOfBytesToRead, lpNumberOfBytesRead, NULL);
                    if (res && lpBuffer) {
                        PendingIo pio = { 0 };
                        pio.lpBuffer = lpBuffer;
                        pio.bytes_requested = nNumberOfBytesToRead;
                        wcsncpy(pio.override_path_w, override_path_w, MAX_PATH - 1);
                        pio.ext_size = ext_size;
                        pio.is_fad_desc = is_fad_desc;
                        pio.width = fad_entry->width;
                        pio.height = fad_entry->height;
                        strncpy(pio.filename, fad_entry->filename, 127);
                        apply_vfs_payload(&pio);
                    }
                    return res;
                }
            }
        }
    }

    /* Default: original ReadFile */
    return fp_original_ReadFile(hFile, lpBuffer, nNumberOfBytesToRead, lpNumberOfBytesRead, lpOverlapped);
}

/* ==================================================================
 * Hook Definitions: Text Rendering (Pure Pass-Through & Logging)
 * ================================================================== */
typedef void (*t_putStr)(void* this_ptr, const char* str);
static t_putStr fp_original_putStr = NULL;
static t_putStr fp_original_putStrProp = NULL;
static t_putStr fp_original_putStrAlign = NULL;

static void hk_putStr(void* this_ptr, const char* str)
{
    process_captured_text(str, "putStr");
    if (has_japanese_utf8(str)) {
        log_missing_text(str, "putStr");
    }
    fp_original_putStr(this_ptr, str);
}

static void hk_putStrProp(void* this_ptr, const char* str)
{
    process_captured_text(str, "putStrProp");
    if (has_japanese_utf8(str)) {
        log_missing_text(str, "putStrProp");
    }
    fp_original_putStrProp(this_ptr, str);
}

static void hk_putStrAlign(void* this_ptr, const char* str)
{
    process_captured_text(str, "putStrAlign");
    if (has_japanese_utf8(str)) {
        log_missing_text(str, "putStrAlign");
    }
    fp_original_putStrAlign(this_ptr, str);
}

/* ==================================================================
 * Signatures for village.exe
 * ================================================================== */
static const AddrSig kSigs[] = {
    {
        .name = "putStr",
        .kind = ADDRSIG_FUNC,
        .pat_hex = "488bc45553488d68d84881ec1801000080b98000000000488bd9",
        .mask_hex = "ffffffffffffffffffffffffffffffffffffffffffffffffffff",
        .off = 0
    },
    {
        .name = "putStrProp",
        .kind = ADDRSIG_FUNC,
        .pat_hex = "488bc4555657488d68d84881ec1001000080b98000000000488bf2",
        .mask_hex = "ffffffffffffffffffffffffffffffffffffffffffffffffffffff",
        .off = 0
    },
    {
        .name = "putStrAlign",
        .kind = ADDRSIG_FUNC,
        .pat_hex = "488bc4555357488d68a14881ecb00000006683792600488bf9",
        .mask_hex = "ffffffffffffffffffffffffffffffffffffffffffffffffff",
        .off = 0
    }
};

static void init_paths(void)
{
    wchar_t path_w[MAX_PATH];
    GetModuleFileNameW(g_hinst, path_w, MAX_PATH);
    wchar_t* last_slash = wcsrchr(path_w, L'\\');
    if (last_slash) {
        *last_slash = L'\0';
        wcsncpy(g_mod_dir_w, path_w, MAX_PATH - 1);
    } else {
        wcscpy(g_mod_dir_w, L".");
    }

    /* Game directory is parent of Mods: <game_root>\Mods\TextDump -> <game_root> */
    wchar_t game_root_w[MAX_PATH];
    wcsncpy(game_root_w, g_mod_dir_w, MAX_PATH - 1);
    wchar_t* s1 = wcsrchr(game_root_w, L'\\');
    if (s1) {
        *s1 = L'\0';
        wchar_t* s2 = wcsrchr(game_root_w, L'\\');
        if (s2) {
            *s2 = L'\0';
            wcsncpy(g_game_dir_w, game_root_w, MAX_PATH - 1);
        } else {
            wcscpy(g_game_dir_w, L".");
        }
    } else {
        wcscpy(g_game_dir_w, L".");
    }

    /* Convert wide paths to UTF-8 for ANSI/display logging buffers */
    WideCharToMultiByte(CP_UTF8, 0, g_mod_dir_w, -1, g_mod_dir, sizeof(g_mod_dir), NULL, NULL);
    WideCharToMultiByte(CP_UTF8, 0, g_game_dir_w, -1, g_game_dir, sizeof(g_game_dir), NULL, NULL);

    /* Construct all wide paths */
    swprintf(g_log_path_w, MAX_PATH, L"%ls\\text_dump.log", g_mod_dir_w);
    swprintf(g_dump_unique_path_w, MAX_PATH, L"%ls\\dump_unique.txt", g_mod_dir_w);
    swprintf(g_dump_log_path_w, MAX_PATH, L"%ls\\dump_log.txt", g_mod_dir_w);
    swprintf(g_tags_log_path_w, MAX_PATH, L"%ls\\tags_dump.log", g_mod_dir_w);
    swprintf(g_file_access_log_w, MAX_PATH, L"%ls\\file_access.log", g_mod_dir_w);
    swprintf(g_dump_missing_path_w, MAX_PATH, L"%ls\\dump_missing.txt", g_mod_dir_w);

    /* Session-based timestamped dumps: Mods\TextDump\dumps\dump_..._YYYYMMDD_HHMMSS.txt */
    SYSTEMTIME st;
    GetLocalTime(&st);
    wchar_t time_str_w[32];
    swprintf(time_str_w, 32, L"%04d%02d%02d_%02d%02d%02d",
             st.wYear, st.wMonth, st.wDay, st.wHour, st.wMinute, st.wSecond);

    wchar_t dumps_dir_w[MAX_PATH];
    swprintf(dumps_dir_w, MAX_PATH, L"%ls\\dumps", g_mod_dir_w);
    CreateDirectoryW(dumps_dir_w, NULL);

    swprintf(g_session_dump_unique_path_w, MAX_PATH, L"%ls\\dumps\\dump_unique_%ls.txt", g_mod_dir_w, time_str_w);
    swprintf(g_session_dump_log_path_w, MAX_PATH, L"%ls\\dumps\\dump_log_%ls.txt", g_mod_dir_w, time_str_w);
    swprintf(g_session_dump_missing_path_w, MAX_PATH, L"%ls\\dumps\\dump_missing_%ls.txt", g_mod_dir_w, time_str_w);

    /* Populate UTF-8 versions for backwards compatibility if needed */
    WideCharToMultiByte(CP_UTF8, 0, g_log_path_w, -1, g_log_path, sizeof(g_log_path), NULL, NULL);
    WideCharToMultiByte(CP_UTF8, 0, g_dump_unique_path_w, -1, g_dump_unique_path, sizeof(g_dump_unique_path), NULL, NULL);
    WideCharToMultiByte(CP_UTF8, 0, g_dump_log_path_w, -1, g_dump_log_path, sizeof(g_dump_log_path), NULL, NULL);
    WideCharToMultiByte(CP_UTF8, 0, g_tags_log_path_w, -1, g_tags_log_path, sizeof(g_tags_log_path), NULL, NULL);
    WideCharToMultiByte(CP_UTF8, 0, g_file_access_log_w, -1, g_file_access_log, sizeof(g_file_access_log), NULL, NULL);
    WideCharToMultiByte(CP_UTF8, 0, g_dump_missing_path_w, -1, g_dump_missing_path, sizeof(g_dump_missing_path), NULL, NULL);
    WideCharToMultiByte(CP_UTF8, 0, g_session_dump_unique_path_w, -1, g_session_dump_unique_path, sizeof(g_session_dump_unique_path), NULL, NULL);
    WideCharToMultiByte(CP_UTF8, 0, g_session_dump_log_path_w, -1, g_session_dump_log_path, sizeof(g_session_dump_log_path), NULL, NULL);
    WideCharToMultiByte(CP_UTF8, 0, g_session_dump_missing_path_w, -1, g_session_dump_missing_path, sizeof(g_session_dump_missing_path), NULL, NULL);

    /* Reset root dump_missing.txt so it reflects the current session */
    FILE* f_init_miss = _wfopen(g_dump_missing_path_w, L"w");
    if (f_init_miss) fclose(f_init_miss);
}

static DWORD WINAPI worker_thread(LPVOID param)
{
    (void)param;

    /* Initialize MinHook immediately */
    if (MH_Initialize() != MH_OK) {
        log_msg("FATAL: MinHook initialization failed.");
        return 0;
    }

    log_msg("==========================================================");
    log_msg("=== Village in the Shade VFS & Text Interceptor Active ===");
    log_msg("==========================================================");
    log_msg("Mod directory: %ls", g_mod_dir_w);
    log_msg("Game directory: %ls", g_game_dir_w);

    /* 1. Index Archives for Virtual File System FIRST */
    wchar_t dat_path_w[MAX_PATH];
    wchar_t misc_path_w[MAX_PATH];
    swprintf(dat_path_w, MAX_PATH, L"%ls\\data.dat", g_game_dir_w);
    swprintf(misc_path_w, MAX_PATH, L"%ls\\data\\misc_1_00.dat", g_game_dir_w);

    load_archive_toc_w(dat_path_w, 1);
    load_archive_toc_w(misc_path_w, 2);

    wchar_t tex_path_w[MAX_PATH];
    wchar_t fairy_path_w[MAX_PATH];
    swprintf(tex_path_w, MAX_PATH, L"%ls\\data\\texture_1_00.dat", g_game_dir_w);
    swprintf(fairy_path_w, MAX_PATH, L"%ls\\data\\fairy_1_00.dat", g_game_dir_w);
    load_archive_toc_w(tex_path_w, 3);
    load_archive_toc_w(fairy_path_w, 4);
    log_msg("[VFS] Total files indexed for redirection: %d", g_vfs_count);

    /* Dynamically resolve FAD sub-file offsets across all game versions */
    resolve_dynamic_fad_offsets_w(fairy_path_w);

    /* 2. Install CreateFileW & CreateFileA Archive Hooks */
    HMODULE hKernel32 = GetModuleHandleA("kernel32.dll");
    if (hKernel32) {
        FARPROC pCreateFileW = GetProcAddress(hKernel32, "CreateFileW");
        if (pCreateFileW) {
            if (MH_CreateHook((LPVOID)pCreateFileW, (LPVOID)&hk_CreateFileW, (LPVOID*)&fp_original_CreateFileW) == MH_OK) {
                if (MH_EnableHook((LPVOID)pCreateFileW) == MH_OK) {
                    log_msg("SUCCESS: Hooked CreateFileW (Archive Redirection Active)!");
                }
            }
        }

        FARPROC pCreateFileA = GetProcAddress(hKernel32, "CreateFileA");
        if (pCreateFileA) {
            if (MH_CreateHook((LPVOID)pCreateFileA, (LPVOID)&hk_CreateFileA, (LPVOID*)&fp_original_CreateFileA) == MH_OK) {
                if (MH_EnableHook((LPVOID)pCreateFileA) == MH_OK) {
                    log_msg("SUCCESS: Hooked CreateFileA (Archive Redirection Active)!");
                }
            }
        }

        /* 3. Install ReadFile VFS Hook */
        FARPROC pReadFile = GetProcAddress(hKernel32, "ReadFile");
        if (pReadFile) {
            if (MH_CreateHook((LPVOID)pReadFile, (LPVOID)&hk_ReadFile, (LPVOID*)&fp_original_ReadFile) == MH_OK) {
                if (MH_EnableHook((LPVOID)pReadFile) == MH_OK) {
                    log_msg("SUCCESS: Hooked ReadFile (VFS Redirection Active)!");
                } else {
                    log_msg("ERROR: Failed to enable ReadFile hook.");
                }
            } else {
                log_msg("ERROR: Failed to create ReadFile hook.");
            }
        }

        /* 3b. Install GetOverlappedResult Hook for Async VFS */
        FARPROC pGetOverlappedResult = GetProcAddress(hKernel32, "GetOverlappedResult");
        if (pGetOverlappedResult) {
            if (MH_CreateHook((LPVOID)pGetOverlappedResult, (LPVOID)&hk_GetOverlappedResult, (LPVOID*)&fp_original_GetOverlappedResult) == MH_OK) {
                if (MH_EnableHook((LPVOID)pGetOverlappedResult) == MH_OK) {
                    log_msg("SUCCESS: Hooked GetOverlappedResult (Async VFS Active)!");
                } else {
                    log_msg("ERROR: Failed to enable GetOverlappedResult hook.");
                }
            } else {
                log_msg("ERROR: Failed to create GetOverlappedResult hook.");
            }
        }
    }

    /* 4. Resolve & Hook Text Rendering Functions */
    uintptr_t base = (uintptr_t)GetModuleHandleA(NULL);
    log_msg("Main module base address: 0x%p", (void*)base);

    AddrRes res[sizeof(kSigs) / sizeof(kSigs[0])];
    int hits = addrsig_resolve(kSigs, (int)(sizeof(kSigs) / sizeof(kSigs[0])), base, res, log_msg);
    log_msg("Pattern scan complete: %d/%d signatures resolved", hits, (int)(sizeof(kSigs) / sizeof(kSigs[0])));

    uintptr_t addr_putStr = 0;
    uintptr_t addr_putStrProp = 0;
    uintptr_t addr_putStrAlign = 0;

    for (int i = 0; i < (int)(sizeof(kSigs) / sizeof(kSigs[0])); i++) {
        if (res[i].hit) {
            log_msg("  [HIT] %s at 0x%p (RVA: 0x%08X)", res[i].name, (void*)res[i].addr, res[i].rva);
            if (strcmp(res[i].name, "putStr") == 0) addr_putStr = res[i].addr;
            if (strcmp(res[i].name, "putStrProp") == 0) addr_putStrProp = res[i].addr;
            if (strcmp(res[i].name, "putStrAlign") == 0) addr_putStrAlign = res[i].addr;
        } else {
            log_msg("  [MISS] %s", res[i].name);
        }
    }

    if (addr_putStr) {
        if (MH_CreateHook((LPVOID)addr_putStr, (LPVOID)&hk_putStr, (LPVOID*)&fp_original_putStr) == MH_OK) {
            if (MH_EnableHook((LPVOID)addr_putStr) == MH_OK) {
                log_msg("SUCCESS: Hooked putStr successfully!");
            }
        }
    }

    if (addr_putStrProp) {
        if (MH_CreateHook((LPVOID)addr_putStrProp, (LPVOID)&hk_putStrProp, (LPVOID*)&fp_original_putStrProp) == MH_OK) {
            if (MH_EnableHook((LPVOID)addr_putStrProp) == MH_OK) {
                log_msg("SUCCESS: Hooked putStrProp successfully!");
            }
        }
    }

    if (addr_putStrAlign) {
        if (MH_CreateHook((LPVOID)addr_putStrAlign, (LPVOID)&hk_putStrAlign, (LPVOID*)&fp_original_putStrAlign) == MH_OK) {
            if (MH_EnableHook((LPVOID)addr_putStrAlign) == MH_OK) {
                log_msg("SUCCESS: Hooked putStrAlign successfully!");
            }
        }
    }

    log_msg("System ready! VFS Redirection and Text Logging are active.");

    int last_unique = 0;
    int last_missing = 0;
    while (1) {
        Sleep(1000);
        if (g_unique_count != last_unique || g_missing_count != last_missing) {
            log_msg("Status: Unique texts=%d, Missing JP=%d, Total calls=%llu",
                    g_unique_count,
                    g_missing_count,
                    (unsigned long long)g_total_calls);
            last_unique = g_unique_count;
            last_missing = g_missing_count;
        }
    }

    return 0;
}

/* Exports for steam_api64 bridge loader */
__declspec(dllexport) void mod_init(void)
{
}

__declspec(dllexport) void mod_tick(void)
{
}

BOOL WINAPI DllMain(HINSTANCE hinst, DWORD reason, LPVOID reserved)
{
    (void)reserved;
    if (reason == DLL_PROCESS_ATTACH) {
        g_hinst = hinst;
        DisableThreadLibraryCalls(hinst);
        InitializeCriticalSection(&g_cs);
        init_paths();
        HANDLE hThread = CreateThread(NULL, 0, worker_thread, NULL, 0, NULL);
        if (hThread) CloseHandle(hThread);
    } else if (reason == DLL_PROCESS_DETACH) {
        if (g_fmissing) { fclose(g_fmissing); g_fmissing = NULL; }
        if (g_fmissing_latest) { fclose(g_fmissing_latest); g_fmissing_latest = NULL; }
        if (g_funique) { fclose(g_funique); g_funique = NULL; }
        if (g_funique_latest) { fclose(g_funique_latest); g_funique_latest = NULL; }
        if (g_fraw) { fclose(g_fraw); g_fraw = NULL; }
        if (g_fraw_latest) { fclose(g_fraw_latest); g_fraw_latest = NULL; }
        if (g_ftags) { fclose(g_ftags); g_ftags = NULL; }
        if (g_faccess) { fclose(g_faccess); g_faccess = NULL; }
        if (g_flog) { fclose(g_flog); g_flog = NULL; }
        MH_Uninitialize();
        DeleteCriticalSection(&g_cs);
    }
    return TRUE;
}
