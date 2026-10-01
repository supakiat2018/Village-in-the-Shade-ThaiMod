#include <windows.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <stdint.h>
#include <time.h>
#include <intrin.h>
#ifndef _ReturnAddress
#define _ReturnAddress() __builtin_return_address(0)
#endif
#include "minhook-master/include/MinHook.h"
#include "addrsig.h"
#include "cheats.h"
#include "keyboard_v120_patch.h"

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
static char g_translation_path[MAX_PATH] = { 0 };
static char g_file_access_log[MAX_PATH] = { 0 };
static char g_tags_log_path[MAX_PATH] = { 0 };
static char g_id_log_path[MAX_PATH] = { 0 };

static wchar_t g_log_path_w[MAX_PATH] = { 0 };
static wchar_t g_dump_unique_path_w[MAX_PATH] = { 0 };
static wchar_t g_dump_log_path_w[MAX_PATH] = { 0 };
static wchar_t g_session_dump_unique_path_w[MAX_PATH] = { 0 };
static wchar_t g_session_dump_log_path_w[MAX_PATH] = { 0 };
static wchar_t g_dump_missing_path_w[MAX_PATH] = { 0 };
static wchar_t g_session_dump_missing_path_w[MAX_PATH] = { 0 };
static wchar_t g_missing_latest_path_w[MAX_PATH] = { 0 };
static wchar_t g_translation_path_w[MAX_PATH] = { 0 };
static wchar_t g_file_access_log_w[MAX_PATH] = { 0 };
static wchar_t g_tags_log_path_w[MAX_PATH] = { 0 };
static wchar_t g_id_log_path_w[MAX_PATH] = { 0 };

static CRITICAL_SECTION g_cs;
static FILE* g_flog = NULL;
static FILE* g_funique = NULL;
static FILE* g_funique_latest = NULL;
static FILE* g_fraw = NULL;
static FILE* g_fraw_latest = NULL;
static FILE* g_fmissing_session = NULL;
static FILE* g_fmissing_latest = NULL;
static FILE* g_fmissing_legacy = NULL;
static FILE* g_faccess = NULL;
static FILE* g_ftags = NULL;
static FILE* g_fidlog = NULL;
static uint8_t g_logged_ids[65536 / 8] = { 0 };

static void log_id_access(uint32_t id)
{
    if (id < 65536) {
        int byte_idx = id / 8;
        int bit_idx = id % 8;
        if (g_logged_ids[byte_idx] & (1 << bit_idx)) {
            return;
        }
        g_logged_ids[byte_idx] |= (1 << bit_idx);
    }

    EnterCriticalSection(&g_cs);
    if (!g_fidlog) {
        g_fidlog = _wfopen(g_id_log_path_w, L"a+");
    }
    if (g_fidlog) {
        SYSTEMTIME st;
        GetLocalTime(&st);
        fprintf(g_fidlog, "[%02d:%02d:%02d.%03d] [ID_QUERY] String ID = %u (0x%X)\n",
                st.wHour, st.wMinute, st.wSecond, st.wMilliseconds, id, id);
        fflush(g_fidlog);
    }
    LeaveCriticalSection(&g_cs);
}

static void log_file_access(const char* fmt, ...)
{
    (void)fmt;
}

static int g_unique_count = 0;
static uint64_t g_total_calls = 0;
static uint64_t g_total_replacements = 0;
static FILETIME g_trans_filetime = { 0 };

/* ==================================================================
 * Logging Function
 * ================================================================== */
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

/* ==================================================================
 * Translation Table & Hot Reloading
 * ================================================================== */
typedef struct TransNode {
    uint32_t hash;
    char* orig;
    float scale;
    char* trans;
    struct TransNode* next;
} TransNode;

static TransNode* g_trans_table[HASH_TABLE_SIZE] = { 0 };
static int g_trans_count = 0;

static void clear_translation_table(void)
{
    for (int i = 0; i < HASH_TABLE_SIZE; i++) {
        TransNode* node = g_trans_table[i];
        while (node) {
            TransNode* next = node->next;
            free(node->orig);
            free(node->trans);
            free(node);
            node = next;
        }
        g_trans_table[i] = NULL;
    }
    g_trans_count = 0;
}

static void insert_translation_ex(const char* orig, float scale, const char* trans, BOOL allow_overwrite)
{
    if (!orig || !trans || *orig == '\0' || *trans == '\0') return;
    uint32_t h = hash_str(orig);
    uint32_t bucket = h % HASH_TABLE_SIZE;

    TransNode* node = g_trans_table[bucket];
    while (node) {
        if (node->hash == h && strcmp(node->orig, orig) == 0) {
            if (allow_overwrite) {
                free(node->trans);
                node->trans = _strdup(trans);
                node->scale = scale;
            }
            return;
        }
        node = node->next;
    }

    TransNode* new_node = (TransNode*)malloc(sizeof(TransNode));
    if (new_node) {
        new_node->hash = h;
        new_node->orig = _strdup(orig);
        new_node->scale = scale;
        new_node->trans = _strdup(trans);
        new_node->next = g_trans_table[bucket];
        g_trans_table[bucket] = new_node;
        g_trans_count++;
    }
}

static void insert_translation(const char* orig, float scale, const char* trans)
{
    insert_translation_ex(orig, scale, trans, TRUE);
}

static void trim_str(char* str)
{
    if (!str) return;
    char* p = str;
    while (*p == ' ' || *p == '\t' || *p == '\r' || *p == '\n') p++;
    if (p != str) memmove(str, p, strlen(p) + 1);
    int len = (int)strlen(str);
    while (len > 0 && (str[len - 1] == ' ' || str[len - 1] == '\t' || str[len - 1] == '\r' || str[len - 1] == '\n')) {
        str[len - 1] = '\0';
        len--;
    }
}

static BOOL replace_str(const char* src, const char* from, const char* to, char* out, size_t out_sz)
{
    if (!src || !from || !to || !out || out_sz == 0) return FALSE;
    size_t from_len = strlen(from);
    size_t to_len = strlen(to);
    if (from_len == 0) return FALSE;

    const char* p = src;
    char* d = out;
    char* end = out + out_sz - 1;

    while (*p) {
        if (strncmp(p, from, from_len) == 0) {
            if (d + to_len >= end) return FALSE;
            memcpy(d, to, to_len);
            d += to_len;
            p += from_len;
        } else {
            if (d >= end) return FALSE;
            *d++ = *p++;
        }
    }
    *d = '\0';
    return TRUE;
}

static const char* lookup_translation(const char* orig);
static const char* try_match_dynamic_template(const char* orig);

static const char* lookup_translation_ex(const char* orig, float* out_scale)
{
    if (out_scale) *out_scale = 1.0f;
    if (!orig || orig[0] == '\0' || g_trans_count == 0) return NULL;

    /* 1. Direct Exact Match in Translation Table */
    uint32_t h = hash_str(orig);
    uint32_t bucket = h % HASH_TABLE_SIZE;

    EnterCriticalSection(&g_cs);
    TransNode* node = g_trans_table[bucket];
    while (node) {
        if (node->hash == h && strcmp(node->orig, orig) == 0) {
            LeaveCriticalSection(&g_cs);
            if (out_scale) *out_scale = node->scale;
            return node->trans;
        }
        node = node->next;
    }
    LeaveCriticalSection(&g_cs);

    /* 1.5. Whitespace Fallback: if exact match failed, match trimmed version and restore original spaces */
    size_t orig_len = strlen(orig);
    const char* sp_start = orig;
    while (*sp_start == ' ' || *sp_start == '\t') sp_start++;
    const char* sp_end = orig + orig_len;
    while (sp_end > sp_start && (*(sp_end - 1) == ' ' || *(sp_end - 1) == '\t')) sp_end--;

    if (sp_start > orig || sp_end < orig + orig_len) {
        size_t trimmed_len = (size_t)(sp_end - sp_start);
        if (trimmed_len > 0 && trimmed_len < 512) {
            char trimmed[512];
            memcpy(trimmed, sp_start, trimmed_len);
            trimmed[trimmed_len] = '\0';

            uint32_t th = hash_str(trimmed);
            uint32_t tbucket = th % HASH_TABLE_SIZE;

            EnterCriticalSection(&g_cs);
            TransNode* tnode = g_trans_table[tbucket];
            while (tnode) {
                if (tnode->hash == th && strcmp(tnode->orig, trimmed) == 0) {
                    LeaveCriticalSection(&g_cs);
                    if (out_scale) *out_scale = tnode->scale;

                    static char s_ws_buf[1024];
                    size_t lead_sp = (size_t)(sp_start - orig);
                    size_t trail_sp = (size_t)((orig + orig_len) - sp_end);
                    size_t rep_len = strlen(tnode->trans);

                    if (lead_sp + rep_len + trail_sp < sizeof(s_ws_buf) - 1) {
                        memcpy(s_ws_buf, orig, lead_sp);
                        memcpy(s_ws_buf + lead_sp, tnode->trans, rep_len);
                        memcpy(s_ws_buf + lead_sp + rep_len, sp_end, trail_sp);
                        s_ws_buf[lead_sp + rep_len + trail_sp] = '\0';
                        return s_ws_buf;
                    }
                    return tnode->trans;
                }
                tnode = tnode->next;
            }
            LeaveCriticalSection(&g_cs);
        }
    }

    /* 2. Dynamic Name Confirmation: 「<name>」でよろしいですか？ or Proceed with "<name>"? */
    const char* p_name_start = NULL;
    size_t name_len = 0;
    BOOL is_confirm = FALSE;

    if (strncmp(orig, "\xe3\x80\x8c", 3) == 0) {
        const char* p_close = strstr(orig, "\xe3\x80\x8d\xe3\x81\xa7\xe3\x82\x88\xe3\x82\x8d\xe3\x81\x97\xe3\x81\x84\xe3\x81\x99\xe3\x81\x8b\xef\xbc\x9f");
        if (p_close) {
            p_name_start = orig + 3;
            name_len = p_close - p_name_start;
            is_confirm = TRUE;
        }
    } else if (strncmp(orig, "Proceed with ", 13) == 0) {
        const char* p_cur = orig + 13;
        if (*p_cur == '\"') p_cur++;
        const char* p_q = strchr(p_cur, '?');
        if (p_q) {
            const char* p_end = p_q;
            if (p_end > p_cur && *(p_end - 1) == '\"') p_end--;
            p_name_start = p_cur;
            name_len = p_end - p_name_start;
            is_confirm = TRUE;
        }
    }

    if (is_confirm && p_name_start && name_len > 0) {
        char captured_name[64] = { 0 };
        if (name_len < sizeof(captured_name)) {
            memcpy(captured_name, p_name_start, name_len);
            captured_name[name_len] = '\0';
        }

        static char name_confirm_buf[512];
        const char* templ = lookup_translation_ex("Proceed with <value 1>?", NULL);
        if (!templ) templ = lookup_translation_ex("「<value 1>」でよろしいですか？", NULL);
        if (!templ) templ = lookup_translation_ex("「」でよろしいですか？", NULL);
        if (templ && captured_name[0] != '\0') {
            if (strstr(templ, "<value 1>")) {
                if (replace_str(templ, "<value 1>", captured_name, name_confirm_buf, sizeof(name_confirm_buf))) {
                    return name_confirm_buf;
                }
            } else if (strstr(templ, "\"\"")) {
                char name_in_quotes[128];
                snprintf(name_in_quotes, sizeof(name_in_quotes), "\"%s\"", captured_name);
                if (replace_str(templ, "\"\"", name_in_quotes, name_confirm_buf, sizeof(name_confirm_buf))) {
                    return name_confirm_buf;
                }
            } else if (strstr(templ, "\xe3\x80\x8c\xe3\x80\x8d")) {
                char name_in_brackets[128];
                snprintf(name_in_brackets, sizeof(name_in_brackets), "「%s」", captured_name);
                if (replace_str(templ, "\xe3\x80\x8c\xe3\x80\x8d", name_in_brackets, name_confirm_buf, sizeof(name_confirm_buf))) {
                    return name_confirm_buf;
                }
            }
        }
    }

    /* 3. Dynamic Template Matching (<value ...> patterns: save dates, currency, items) */
    const char* dyn_match = try_match_dynamic_template(orig);
    if (dyn_match) {
        return dyn_match;
    }

    return NULL;
}

static const char* lookup_translation(const char* orig)
{
    return lookup_translation_ex(orig, NULL);
}

/* ==================================================================
 * Dynamic Template Matching (<value ...> patterns)
 * ================================================================== */
static char s_dynamic_buffers[4][1024];
static volatile LONG s_dynamic_buf_idx = 0;

static const char* try_match_dynamic_template(const char* orig)
{
    if (!orig || orig[0] == '\0') return NULL;

    size_t len = strlen(orig);
    char temp1[1024];
    char temp2[1024];

    /* 1. Full Save Game Date: "%d年目 %s %d日" with optional suffix (e.g. "　深夜" or " 深夜") */
    /* "年目 " in UTF-8: \xe5\xb9\xb4\xe7\x9b\xae\x20 (7 bytes) */
    const char* p_nen = strstr(orig, "\xe5\xb9\xb4\xe7\x9b\xae ");
    if (p_nen && p_nen > orig) {
        char* end_yr = NULL;
        long year = strtol(orig, &end_yr, 10);
        if (year > 0 && end_yr == p_nen) {
            const char* p_season = p_nen + 7; /* skip "年目 " */
            const char* p_sp = strchr(p_season, ' ');
            size_t skip_sp = 1;
            if (!p_sp) {
                p_sp = strstr(p_season, "\xe3\x80\x80");
                skip_sp = 3;
            }
            if (p_sp && p_sp > p_season) {
                char season_jp[32] = {0};
                size_t slen = (size_t)(p_sp - p_season);
                if (slen < sizeof(season_jp)) {
                    memcpy(season_jp, p_season, slen);
                    season_jp[slen] = '\0';
                    char* end_day = NULL;
                    long day = strtol(p_sp + skip_sp, &end_day, 10);
                    /* "日" in UTF-8: \xe6\x97\xa5 (3 bytes) */
                    if (day > 0 && end_day && strncmp(end_day, "\xe6\x97\xa5", 3) == 0) {
                        const char* templ = lookup_translation("<value 1>年目 <value 2> <value 3>日");
                        if (templ) {
                            const char* season_th = lookup_translation(season_jp);
                            if (!season_th) season_th = season_jp;
                            char y_buf[16], d_buf[16];
                            snprintf(y_buf, sizeof(y_buf), "%ld", year);
                            snprintf(d_buf, sizeof(d_buf), "%ld", day);

                            LONG b_idx = InterlockedIncrement(&s_dynamic_buf_idx);
                            char* buf = s_dynamic_buffers[b_idx & 3];

                            if (replace_str(templ, "<value 1>", y_buf, temp1, sizeof(temp1)) &&
                                replace_str(temp1, "<value 2>", season_th, temp2, sizeof(temp2)) &&
                                replace_str(temp2, "<value 3>", d_buf, buf, sizeof(s_dynamic_buffers[0]))) {

                                const char* p_extra = end_day + 3; /* skip "日" */
                                while (*p_extra == ' ' || *p_extra == '\t' ||
                                       ((unsigned char)p_extra[0] == 0xe3 && (unsigned char)p_extra[1] == 0x80 && (unsigned char)p_extra[2] == 0x80)) {
                                    if ((unsigned char)p_extra[0] == 0xe3) p_extra += 3;
                                    else p_extra++;
                                }
                                if (*p_extra != '\0') {
                                    const char* extra_th = lookup_translation(p_extra);
                                    if (!extra_th) extra_th = p_extra;
                                    strncat(buf, " ", sizeof(s_dynamic_buffers[0]) - strlen(buf) - 1);
                                    strncat(buf, extra_th, sizeof(s_dynamic_buffers[0]) - strlen(buf) - 1);
                                }
                                return buf;
                            }
                        }
                    }
                }
            }
        }
    }

    /* 1b. English Save Game Date: "Year %d - %s %d" with optional suffix (e.g. "Late Night" or "23Late Night") */
    if (strncmp(orig, "Year ", 5) == 0) {
        char* end_yr = NULL;
        long year = strtol(orig + 5, &end_yr, 10);
        if (year > 0 && end_yr && strncmp(end_yr, " - ", 3) == 0) {
            const char* p_season = end_yr + 3; /* skip " - " */
            const char* p_sp = strchr(p_season, ' ');
            if (p_sp && p_sp > p_season) {
                char season_en[32] = {0};
                size_t slen = (size_t)(p_sp - p_season);
                if (slen < sizeof(season_en)) {
                    memcpy(season_en, p_season, slen);
                    season_en[slen] = '\0';
                    char* end_day = NULL;
                    long day = strtol(p_sp + 1, &end_day, 10);
                    if (day > 0 && end_day) {
                        const char* templ = lookup_translation("Year <value 1> - <value 2> <value 3>");
                        if (!templ) templ = lookup_translation("<value 1>年目 <value 2> <value 3>日");
                        if (templ) {
                            const char* season_th = lookup_translation(season_en);
                            if (!season_th) season_th = season_en;
                            char y_buf[16], d_buf[16];
                            snprintf(y_buf, sizeof(y_buf), "%ld", year);
                            snprintf(d_buf, sizeof(d_buf), "%ld", day);

                            LONG b_idx = InterlockedIncrement(&s_dynamic_buf_idx);
                            char* buf = s_dynamic_buffers[b_idx & 3];

                            if (replace_str(templ, "<value 1>", y_buf, temp1, sizeof(temp1)) &&
                                replace_str(temp1, "<value 2>", season_th, temp2, sizeof(temp2)) &&
                                replace_str(temp2, "<value 3>", d_buf, buf, sizeof(s_dynamic_buffers[0]))) {

                                const char* p_extra = end_day;
                                while (*p_extra == ' ' || *p_extra == '\t') p_extra++;
                                if (*p_extra != '\0') {
                                    const char* extra_th = lookup_translation(p_extra);
                                    if (!extra_th) extra_th = p_extra;
                                    strncat(buf, " ", sizeof(s_dynamic_buffers[0]) - strlen(buf) - 1);
                                    strncat(buf, extra_th, sizeof(s_dynamic_buffers[0]) - strlen(buf) - 1);
                                }
                                return buf;
                            }
                        }
                    }
                }
            }
        }
    }

    /* 2. Short / Prefixed Dates: "[prefix] <Season> <Day>日" */
    const char* date_templ_key = NULL;
    const char* p_date_start = orig;
    if (strncmp(orig, "\xe8\xaa\x95\xe7\x94\x9f\xe6\x97\xa5 ", 10) == 0) {
        /* "誕生日 " */
        date_templ_key = "誕生日 <value 1> <value 2>日";
        p_date_start = orig + 10;
    } else if (strncmp(orig, "\xe6\x9c\x9f\xe9\x99\x90\xef\xbc\x9a", 9) == 0) {
        /* "期限：" */
        date_templ_key = "期限：<value 1> <value 2>日";
        p_date_start = orig + 9;
    } else {
        date_templ_key = "<value 1> <value 2>日";
        p_date_start = orig;
    }

    static const char* s_seasons[] = {
        "\xe6\x98\xa5", /* 春 */
        "\xe5\xa4\x8f", /* 夏 */
        "\xe7\xa7\x8b", /* 秋 */
        "\xe5\x86\xac"  /* 冬 */
    };
    for (int i = 0; i < 4; i++) {
        if (strncmp(p_date_start, s_seasons[i], 3) == 0 && (p_date_start[3] == ' ' || (unsigned char)p_date_start[3] == 0xe3)) {
            size_t s_sp = 1;
            if ((unsigned char)p_date_start[3] == 0xe3 && (unsigned char)p_date_start[4] == 0x80 && (unsigned char)p_date_start[5] == 0x80) {
                s_sp = 3;
            }
            char* end_day = NULL;
            long day = strtol(p_date_start + 3 + s_sp, &end_day, 10);
            if (day > 0 && end_day && strncmp(end_day, "\xe6\x97\xa5", 3) == 0) {
                const char* templ = lookup_translation(date_templ_key);
                if (templ) {
                    const char* season_th = lookup_translation(s_seasons[i]);
                    if (!season_th) season_th = s_seasons[i];
                    char d_buf[16];
                    snprintf(d_buf, sizeof(d_buf), "%ld", day);
                    LONG b_idx = InterlockedIncrement(&s_dynamic_buf_idx);
                    char* buf = s_dynamic_buffers[b_idx & 3];
                    if (replace_str(templ, "<value 1>", season_th, temp1, sizeof(temp1)) &&
                        replace_str(temp1, "<value 2>", d_buf, buf, sizeof(s_dynamic_buffers[0]))) {
                        return buf;
                    }
                }
            }
            break;
        }
    }

    /* 3. Harvest Season List: "収穫季節：<Season>・..." */
    /* "収穫季節：" in UTF-8: \xe5\x8f\x8e\xe7\xa9\xab\xe5\xad\xa3\xe7\xaf\x80\xef\xbc\x9a (15 bytes) */
    if (strncmp(orig, "\xe5\x8f\x8e\xe7\xa9\xab\xe5\xad\xa3\xe7\xaf\x80\xef\xbc\x9a", 15) == 0) {
        const char* p_cur = orig + 15;
        char s1[32] = {0}, s2[32] = {0}, s3[32] = {0};
        int season_count = 0;
        /* Tokenize by "・" (\xe3\x83\xbb, 3 bytes) */
        while (*p_cur && season_count < 3) {
            const char* p_dot = strstr(p_cur, "\xe3\x83\xbb");
            size_t seg_len = p_dot ? (size_t)(p_dot - p_cur) : strlen(p_cur);
            if (season_count == 0 && seg_len < sizeof(s1)) {
                memcpy(s1, p_cur, seg_len); s1[seg_len] = '\0';
            } else if (season_count == 1 && seg_len < sizeof(s2)) {
                memcpy(s2, p_cur, seg_len); s2[seg_len] = '\0';
            } else if (season_count == 2 && seg_len < sizeof(s3)) {
                memcpy(s3, p_cur, seg_len); s3[seg_len] = '\0';
            }
            season_count++;
            if (!p_dot) break;
            p_cur = p_dot + 3;
        }
        if (season_count == 1) {
            const char* templ = lookup_translation("収穫季節：<value 1>");
            if (templ) {
                const char* th1 = lookup_translation(s1);
                if (!th1) th1 = s1;
                LONG b_idx = InterlockedIncrement(&s_dynamic_buf_idx);
                char* buf = s_dynamic_buffers[b_idx & 3];
                if (replace_str(templ, "<value 1>", th1, buf, sizeof(s_dynamic_buffers[0]))) return buf;
            }
        } else if (season_count == 2) {
            const char* templ = lookup_translation("収穫季節：<value 1>・<value 2>");
            if (templ) {
                const char* th1 = lookup_translation(s1); if (!th1) th1 = s1;
                const char* th2 = lookup_translation(s2); if (!th2) th2 = s2;
                LONG b_idx = InterlockedIncrement(&s_dynamic_buf_idx);
                char* buf = s_dynamic_buffers[b_idx & 3];
                if (replace_str(templ, "<value 1>", th1, temp1, sizeof(temp1)) &&
                    replace_str(temp1, "<value 2>", th2, buf, sizeof(s_dynamic_buffers[0]))) return buf;
            }
        } else if (season_count == 3) {
            const char* templ = lookup_translation("収穫季節：<value 1>・<value 2>・<value 3>");
            if (templ) {
                const char* th1 = lookup_translation(s1); if (!th1) th1 = s1;
                const char* th2 = lookup_translation(s2); if (!th2) th2 = s2;
                const char* th3 = lookup_translation(s3); if (!th3) th3 = s3;
                LONG b_idx = InterlockedIncrement(&s_dynamic_buf_idx);
                char* buf = s_dynamic_buffers[b_idx & 3];
                if (replace_str(templ, "<value 1>", th1, temp1, sizeof(temp1)) &&
                    replace_str(temp1, "<value 2>", th2, temp2, sizeof(temp2)) &&
                    replace_str(temp2, "<value 3>", th3, buf, sizeof(s_dynamic_buffers[0]))) return buf;
            }
        }
    }

    /* 4. Number + 円 (\xe5\x86\x86, 3 bytes) */
    if (len > 3 && memcmp(orig + len - 3, "\xe5\x86\x86", 3) == 0) {
        char* endptr = NULL;
        long val = strtol(orig, &endptr, 10);
        if (endptr == orig + len - 3 && val >= 0) {
            const char* templ = lookup_translation("<value 1>円");
            if (templ) {
                char v_buf[32];
                snprintf(v_buf, sizeof(v_buf), "%ld", val);
                LONG b_idx = InterlockedIncrement(&s_dynamic_buf_idx);
                char* buf = s_dynamic_buffers[b_idx & 3];
                if (replace_str(templ, "<value 1>", v_buf, buf, sizeof(s_dynamic_buffers[0]))) return buf;
            }
        }
    }

    /* 5. Number + 個 (\xe5\x80\x8b, 3 bytes) */
    if (len > 3 && memcmp(orig + len - 3, "\xe5\x80\x8b", 3) == 0) {
        char* endptr = NULL;
        long val = strtol(orig, &endptr, 10);
        if (endptr == orig + len - 3 && val >= 0) {
            const char* templ = lookup_translation("<value 1>個");
            if (templ) {
                char v_buf[32];
                snprintf(v_buf, sizeof(v_buf), "%ld", val);
                LONG b_idx = InterlockedIncrement(&s_dynamic_buf_idx);
                char* buf = s_dynamic_buffers[b_idx & 3];
                if (replace_str(templ, "<value 1>", v_buf, buf, sizeof(s_dynamic_buffers[0]))) return buf;
            }
        }
    }

    /* 6. 地下<number>階 (\xe5\x9c\xb0\xe4\xb8\x8b, 6 bytes ... \xe9\x9a\x8e, 3 bytes) */
    if (len > 9 && memcmp(orig, "\xe5\x9c\xb0\xe4\xb8\x8b", 6) == 0 && memcmp(orig + len - 3, "\xe9\x9a\x8e", 3) == 0) {
        char* endptr = NULL;
        long val = strtol(orig + 6, &endptr, 10);
        if (endptr == orig + len - 3 && val >= 0) {
            const char* templ = lookup_translation("地下<value 1>階");
            if (templ) {
                char v_buf[32];
                snprintf(v_buf, sizeof(v_buf), "%ld", val);
                LONG b_idx = InterlockedIncrement(&s_dynamic_buf_idx);
                char* buf = s_dynamic_buffers[b_idx & 3];
                if (replace_str(templ, "<value 1>", v_buf, buf, sizeof(s_dynamic_buffers[0]))) return buf;
            }
        }
    }

    /* 7. 家畜小屋<number> (\xe5\xae\xb6\xe7\x95\x9c\xe5\xb0\x8f\xe5\xb1\x8b, 12 bytes) */
    if (len > 12 && memcmp(orig, "\xe5\xae\xb6\xe7\x95\x9c\xe5\xb0\x8f\xe5\xb1\x8b", 12) == 0) {
        char* endptr = NULL;
        long val = strtol(orig + 12, &endptr, 10);
        if (endptr == orig + len && val >= 0) {
            const char* templ = lookup_translation("家畜小屋<value 1>");
            if (templ) {
                char v_buf[32];
                snprintf(v_buf, sizeof(v_buf), "%ld", val);
                LONG b_idx = InterlockedIncrement(&s_dynamic_buf_idx);
                char* buf = s_dynamic_buffers[b_idx & 3];
                if (replace_str(templ, "<value 1>", v_buf, buf, sizeof(s_dynamic_buffers[0]))) return buf;
            }
        }
    }

    /* 8. 鶏小屋<number> (\xe9\xb8\xa1\xe5\xb0\x8f\xe5\xb1\x8b, 9 bytes) */
    if (len > 9 && memcmp(orig, "\xe9\xb8\xa1\xe5\xb0\x8f\xe5\xb1\x8b", 9) == 0) {
        char* endptr = NULL;
        long val = strtol(orig + 9, &endptr, 10);
        if (endptr == orig + len && val >= 0) {
            const char* templ = lookup_translation("鶏小屋<value 1>");
            if (templ) {
                char v_buf[32];
                snprintf(v_buf, sizeof(v_buf), "%ld", val);
                LONG b_idx = InterlockedIncrement(&s_dynamic_buf_idx);
                char* buf = s_dynamic_buffers[b_idx & 3];
                if (replace_str(templ, "<value 1>", v_buf, buf, sizeof(s_dynamic_buffers[0]))) return buf;
            }
        }
    }

    /* 9. <number>日後まで (\xe6\x97\xa5\xe5\xbe\x8c\xe3\x81\xbe\xe3\x81\xa7, 12 bytes) */
    if (len > 12 && memcmp(orig + len - 12, "\xe6\x97\xa5\xe5\xbe\x8c\xe3\x81\xbe\xe3\x81\xa7", 12) == 0) {
        char* endptr = NULL;
        long val = strtol(orig, &endptr, 10);
        if (endptr == orig + len - 12 && val >= 0) {
            const char* templ = lookup_translation("<value 1>日後まで");
            if (templ) {
                char v_buf[32];
                snprintf(v_buf, sizeof(v_buf), "%ld", val);
                LONG b_idx = InterlockedIncrement(&s_dynamic_buf_idx);
                char* buf = s_dynamic_buffers[b_idx & 3];
                if (replace_str(templ, "<value 1>", v_buf, buf, sizeof(s_dynamic_buffers[0]))) return buf;
            }
        }
    }

    /* 10. String templates with suffix: "<item><suffix>" */
    struct SuffixRule {
        const char* suffix_jp;
        size_t suffix_len;
        const char* templ_key;
        int is_bracketed;
    };
    static const struct SuffixRule s_suffix_rules[] = {
        { "\xe3\x80\x8d\xe3\x82\x92\xe4\xbd\x9c\xe6\x88\x90\xe3\x81\x97\xe3\x81\xbe\xe3\x81\x99\xe3\x81\x8b\xef\xbc\x9f", 27, "「<value 1>」を作成しますか？", 1 },
        { "\xe3\x82\x92\xe6\x89\x8b\xe3\x81\xab\xe5\x85\xa5\xe3\x82\x8c\xe3\x81\x9f", 18, "<value 1>を手に入れた", 0 },
        { "\xe3\x82\x92\xe3\x82\x82\xe3\x82\x89\xe3\x81\xa3\xe3\x81\x9f", 15, "<value 1>をもらった", 0 },
        { "\xe3\x81\x8c\xe8\xb6\xb3\xe3\x82\x8a\xe3\x81\xaa\xe3\x81\x84\xe2\x80\xa6\xe2\x80\xa6", 21, "<value 1>が足りない……", 0 },
        { "\xe3\x82\x92\xe6\x8f\x90\xe5\x87\xba\xe3\x81\x97\xe3\x81\x9f", 15, "<value 1>を提出した", 0 },
        { "\xe3\x82\x92\xe3\x83\xa1\xe3\x83\xa2\xe3\x81\x97\xe3\x81\x9f", 15, "<value 1>をメモした", 0 },
        { "\xe3\x82\x92\xe5\x90\xb9\xe3\x81\x84\xe3\x81\x9f", 12, "<value 1>を吹いた", 0 },
        { "\xe3\x81\xa8\xe3\x81\xae\xe4\xbb\xb2\xe3\x81\x8c\xe6\xb7\xb1\xe3\x81\xbe\xe3\x81\xa3\xe3\x81\x9f\xef\xbc\x81", 27, "<value 1>との仲が深まった！", 0 },
        { "\xe3\x81\xae\xe8\xaa\x95\xe7\x94\x9f\xe6\x97\xa5", 12, "<value 1>の誕生日", 0 },
        { "\xe3\x81\xae\xe3\x81\xaa\xe3\x81\xa4\xe3\x81\x8d\xe5\xba\xa6\xe3\x81\x8c\xe4\xb8\x8a\xe3\x81\x8c\xe3\x81\xa3\xe3\x81\x9f\xef\xbc\x81", 33, "<value 1>のなつき度が上がった！", 0 },
        { "\xe3\x81\xae\xe5\x93\x81\xe8\xb3\xaa\xe3\x81\x8c\xe4\xb8\x8a\xe3\x81\x8c\xe3\x81\xa3\xe3\x81\x9f\xef\xbc\x81", 27, "<value 1>の品質が上がった！", 0 },
        { "\xe3\x81\xae\xe3\x82\xbb\xe3\x83\xbc\xe3\x83\x96\xe3\x83\x87\xe3\x83\xbc\xe3\x82\xbf\xe3\x82\x92\xe5\x89\x8a\xe9\x99\xa4\xe3\x81\x97\xe3\x81\xbe\xe3\x81\x99\xe3\x80\x82", 42, "<value 1>のセーブデータを削除します。", 0 }
    };
    for (size_t i = 0; i < sizeof(s_suffix_rules) / sizeof(s_suffix_rules[0]); i++) {
        const struct SuffixRule* r = &s_suffix_rules[i];
        if (r->is_bracketed) {
            if (len > 3 + r->suffix_len && memcmp(orig, "\xe3\x80\x8c", 3) == 0 &&
                memcmp(orig + len - r->suffix_len, r->suffix_jp, r->suffix_len) == 0) {
                size_t item_len = len - 3 - r->suffix_len;
                if (item_len > 0 && item_len < 128) {
                    char item_jp[128];
                    memcpy(item_jp, orig + 3, item_len);
                    item_jp[item_len] = '\0';
                    const char* item_th = lookup_translation(item_jp);
                    if (!item_th) item_th = item_jp;
                    const char* templ = lookup_translation(r->templ_key);
                    if (templ) {
                        LONG b_idx = InterlockedIncrement(&s_dynamic_buf_idx);
                        char* buf = s_dynamic_buffers[b_idx & 3];
                        if (replace_str(templ, "<value 1>", item_th, buf, sizeof(s_dynamic_buffers[0]))) return buf;
                    }
                }
            }
        } else {
            if (len > r->suffix_len && memcmp(orig + len - r->suffix_len, r->suffix_jp, r->suffix_len) == 0) {
                size_t item_len = len - r->suffix_len;
                if (item_len > 0 && item_len < 128) {
                    char item_jp[128];
                    memcpy(item_jp, orig, item_len);
                    item_jp[item_len] = '\0';
                    const char* item_th = lookup_translation(item_jp);
                    if (!item_th) item_th = item_jp;
                    const char* templ = lookup_translation(r->templ_key);
                    if (templ) {
                        LONG b_idx = InterlockedIncrement(&s_dynamic_buf_idx);
                        char* buf = s_dynamic_buffers[b_idx & 3];
                        if (replace_str(templ, "<value 1>", item_th, buf, sizeof(s_dynamic_buffers[0]))) return buf;
                    }
                }
            }
        }
    }

    /* 11. Dynamic <gamevalue> Matching */
    /* Pattern A: NPC Count (...<digits>人...) -> <gamevalue GAME_VALUE_STORY_01_NPC_TALK_COUNT> */
    const char* p_nin = strstr(orig, "\xe4\xba\xba"); /* "人" */
    if (p_nin && p_nin > orig) {
        const char* p_digit_start = p_nin - 1;
        while (p_digit_start >= orig && *p_digit_start >= '0' && *p_digit_start <= '9') {
            p_digit_start--;
        }
        p_digit_start++;
        if (p_digit_start < p_nin) {
            char num_str[16] = { 0 };
            size_t nlen = (size_t)(p_nin - p_digit_start);
            if (nlen < sizeof(num_str)) {
                memcpy(num_str, p_digit_start, nlen);
                num_str[nlen] = '\0';

                char gv_templ_key[1024] = { 0 };
                size_t pfx_len = (size_t)(p_digit_start - orig);
                if (pfx_len + 45 + strlen(p_nin) < sizeof(gv_templ_key)) {
                    memcpy(gv_templ_key, orig, pfx_len);
                    strcpy(gv_templ_key + pfx_len, "<gamevalue GAME_VALUE_STORY_01_NPC_TALK_COUNT>");
                    strcat(gv_templ_key, p_nin);

                    const char* templ = lookup_translation(gv_templ_key);
                    if (templ) {
                        LONG b_idx = InterlockedIncrement(&s_dynamic_buf_idx);
                        char* buf = s_dynamic_buffers[b_idx & 3];
                        if (replace_str(templ, "<gamevalue GAME_VALUE_STORY_01_NPC_TALK_COUNT>", num_str, buf, sizeof(s_dynamic_buffers[0]))) {
                            return buf;
                        }
                    }
                }
            }
        }
    }

    /* Pattern B: Talk Num (...<digits>日... or ...<digits>円...) -> <gamevalue GAME_VALUE_TALK_NUM> */
    const char* p_target = strstr(orig, "\xe6\x97\xa5"); /* "日" */
    if (!p_target) p_target = strstr(orig, "\xe5\x86\x86\xe3\x82\x92\xe6\xb8\xa1\xe3\x81\x95\xe3\x82\x8c\xe3\x81\x9f"); /* "円を渡された" */
    if (p_target && p_target > orig) {
        const char* p_digit_start = p_target - 1;
        while (p_digit_start >= orig && *p_digit_start >= '0' && *p_digit_start <= '9') {
            p_digit_start--;
        }
        p_digit_start++;
        if (p_digit_start < p_target) {
            char num_str[16] = { 0 };
            size_t nlen = (size_t)(p_target - p_digit_start);
            if (nlen < sizeof(num_str)) {
                memcpy(num_str, p_digit_start, nlen);
                num_str[nlen] = '\0';

                char gv_templ_key[1024] = { 0 };
                size_t pfx_len = (size_t)(p_digit_start - orig);
                if (pfx_len + 35 + strlen(p_target) < sizeof(gv_templ_key)) {
                    memcpy(gv_templ_key, orig, pfx_len);
                    strcpy(gv_templ_key + pfx_len, "<gamevalue GAME_VALUE_TALK_NUM>");
                    strcat(gv_templ_key, p_target);

                    const char* templ = lookup_translation(gv_templ_key);
                    if (templ) {
                        LONG b_idx = InterlockedIncrement(&s_dynamic_buf_idx);
                        char* buf = s_dynamic_buffers[b_idx & 3];
                        if (replace_str(templ, "<gamevalue GAME_VALUE_TALK_NUM>", num_str, buf, sizeof(s_dynamic_buffers[0]))) {
                            return buf;
                        }
                    }
                }
            }
        }
    }

    /* 12. Dynamic <tmpstr> Quest Item Matching */
    struct TmpstrRule {
        const char* pfx;
        size_t pfx_len;
        const char* sfx;
        size_t sfx_len;
        const char* templ_key;
    };
    static const struct TmpstrRule s_tmpstr_rules[] = {
        { "\xe3\x81\x93\xe3\x82\x8c\xe3\x81\x8b\xe3\x82\x89\xe3\x82\x82", 15, "\xe3\x81\xae\xe7\x94\x9f\xe7\x94\xa3\xe3\x81\xab\xe5\x8a\xb1\xe3\x82\x93\xe3\x81\xa7\xe3\x81\x8f\xe3\x82\x8c", 27, "\xe3\x81\x93\xe3\x82\x8c\xe3\x81\x8b\xe3\x82\x89\xe3\x82\x82<tmpstr>\xe3\x81\xae\xe7\x94\x9f\xe7\x94\xa3\xe3\x81\xab\xe5\x8a\xb1\xe3\x82\x93\xe3\x81\xa7\xe3\x81\x8f\xe3\x82\x8c" },
        { "\xe3\x81\x93\xe3\x82\x8c\xe3\x81\x8b\xe3\x82\x89\xe3\x82\x82", 15, "\xe3\x82\x92\xe8\x82\xb2\xe3\x81\xa6\xe3\x81\xa6\xe3\x81\x8f\xe3\x82\x8c", 18, "\xe3\x81\x93\xe3\x82\x8c\xe3\x81\x8b\xe3\x82\x89\xe3\x82\x82<tmpstr>\xe3\x82\x92\xe8\x82\xb2\xe3\x81\xa6\xe3\x81\xa6\xe3\x81\x8f\xe3\x82\x8c" },
        { "\xe3\x82\x82\xe3\x81\x97\xe3\x81\x8b\xe3\x81\x97\xe3\x81\xaa\xe3\x81\x8f\xe3\x81\xa6\xe3\x82\x82", 24, "\xe3\x81\xa7\xe3\x81\x99\xe3\x83\x8d\xef\xbc\x9f", 12, "\xe3\x82\x82\xe3\x81\x97\xe3\x81\x8b\xe3\x81\x97\xe3\x81\xaa\xe3\x81\x8f\xe3\x81\xa6\xe3\x82\x82<tmpstr>\xe3\x81\xa7\xe3\x81\x99\xe3\x83\x8d\xef\xbc\x9f" },
        { "\xe4\xbb\x8a\xe3\x80\x81", 6, "\xe3\x82\x92\xe6\x8e\xa2\xe3\x81\x97\xe3\x81\xa6\xe3\x82\x8b\xe3\x82\x93\xe3\x81\xa0\xe3\x81\x91\xe3\x81\xa9", 27, "\xe4\xbb\x8a\xe3\x80\x81<tmpstr>\xe3\x82\x92\xe6\x8e\xa2\xe3\x81\x97\xe3\x81\xa6\xe3\x82\x8b\xe3\x82\x93\xe3\x81\xa0\xe3\x81\x91\xe3\x81\xa9" },
        { "\xe3\x81\x82\xe3\x81\xae\xe3\x81\xad\xe3\x80\x81", 12, "\xe3\x81\xa3\xe3\x81\xa6\xe6\x8c\x81\xe3\x81\xa3\xe3\x81\xa6\xe3\x82\x8b\xef\xbc\x9f", 21, "\xe3\x81\x82\xe3\x81\xae\xe3\x81\xad\xe3\x80\x81<tmpstr>\xe3\x81\xa3\xe3\x81\xa6\xe6\x8c\x81\xe3\x81\xa3\xe3\x81\xa6\xe3\x82\x8b\xef\xbc\x9f" },
        { "\xe5\xae\x9f\xe3\x81\xaf", 6, "\xe3\x81\x8c\xe6\xac\xb2\xe3\x81\x97\xe3\x81\x84\xe3\x82\x93\xe3\x81\xa0\xe3\x81\x91\xe3\x81\xa9", 24, "\xe5\xae\x9f\xe3\x81\xaf<tmpstr>\xe3\x81\x8c\xe6\xac\xb2\xe3\x81\x97\xe3\x81\x84\xe3\x82\x93\xe3\x81\xa0\xe3\x81\x91\xe3\x81\xa9" },
        { "", 0, "\xe3\x82\x92\xe6\x8c\x81\xe3\x81\xa3\xe3\x81\xa6\xe3\x81\x8d\xe3\x81\xa6\xe3\x81\x8f\xe3\x82\x8c\xe3\x81\x9f\xe3\x82\x93\xe3\x81\xa7\xe3\x81\x99\xe3\x81\x8b\xef\xbc\x9f", 42, "<tmpstr>\xe3\x82\x92\xe6\x8c\x81\xe3\x81\xa3\xe3\x81\xa6\xe3\x81\x8d\xe3\x81\xa6\xe3\x81\x8f\xe3\x82\x8c\xe3\x81\x9f\xe3\x82\x93\xe3\x81\xa7\xe3\x81\x99\xe3\x81\x8b\xef\xbc\x9f" },
        { "", 0, "\xe3\x82\x92\xe6\x8c\x81\xe3\x81\xa3\xe3\x81\xa6\xe3\x81\x8d\xe3\x81\xa6\xe3\x81\x8f\xe3\x82\x8c\xe3\x81\x9f\xe3\x81\xae\xe3\x81\x8b\xe3\x81\x84\xef\xbc\x9f", 39, "<tmpstr>\xe3\x82\x92\xe6\x8c\x81\xe3\x81\xa3\xe3\x81\xa6\xe3\x81\x8d\xe3\x81\xa6\xe3\x81\x8f\xe3\x82\x8c\xe3\x81\x9f\xe3\x81\xae\xe3\x81\x8b\xe3\x81\x84\xef\xbc\x9f" },
        { "", 0, "\xe3\x82\x92\xe6\x8c\x81\xe3\x81\xa3\xe3\x81\xa6\xe3\x81\x8d\xe3\x81\xa6\xe3\x81\x8f\xe3\x82\x8c\xe3\x81\x9f\xe3\x82\x93\xe3\x82\xb9\xe3\x81\x8b\xef\xbc\x9f", 39, "<tmpstr>\xe3\x82\x92\xe6\x8c\x81\xe3\x81\xa3\xe3\x81\xa6\xe3\x81\x8d\xe3\x81\xa6\xe3\x81\x8f\xe3\x82\x8c\xe3\x81\x9f\xe3\x82\x93\xe3\x82\xb9\xe3\x81\x8b\xef\xbc\x9f" },
        { "", 0, "\xe3\x82\x92\xe3\x81\x8a\xe6\x8c\x81\xe3\x81\xa1\xe3\x81\xa7\xe3\x81\xaf\xe3\x81\xaa\xe3\x81\x84\xe3\x81\xa7\xe3\x81\x99\xe3\x81\x8b\xef\xbc\x9f", 36, "<tmpstr>\xe3\x82\x92\xe3\x81\x8a\xe6\x8c\x81\xe3\x81\xa1\xe3\x81\xa7\xe3\x81\xaf\xe3\x81\xaa\xe3\x81\x84\xe3\x81\xa7\xe3\x81\x99\xe3\x81\x8b\xef\xbc\x9f" },
        { "", 0, "\xe3\x82\x92\xe6\x8c\x81\xe3\x81\xa3\xe3\x81\xa6\xe3\x81\x8d\xe3\x81\xa6\xe3\x81\x8f\xe3\x82\x8c\xe3\x81\x9f\xe3\x81\xae\xe3\x81\x8b\xef\xbc\x9f", 36, "<tmpstr>\xe3\x82\x92\xe6\x8c\x81\xe3\x81\xa3\xe3\x81\xa6\xe3\x81\x8d\xe3\x81\xa6\xe3\x81\x8f\xe3\x82\x8c\xe3\x81\x9f\xe3\x81\xae\xe3\x81\x8b\xef\xbc\x9f" },
        { "", 0, "\xe3\x81\x8c\xe3\x81\xbb\xe3\x81\x97\xe3\x81\x8f\xe3\x81\xa6\xe6\x8e\xa2\xe3\x81\x97\xe3\x81\xa6\xe3\x82\x8b\xe3\x82\x93\xe3\x81\xa0", 33, "<tmpstr>\xe3\x81\x8c\xe3\x81\xbb\xe3\x81\x97\xe3\x81\x8f\xe3\x81\xa6\xe6\x8e\xa2\xe3\x81\x97\xe3\x81\xa6\xe3\x82\x8b\xe3\x82\x93\xe3\x81\xa0" },
        { "", 0, "\xe3\x81\xa3\xe3\x81\xa6\xe3\x80\x81\xe4\xbd\x99\xe3\x81\xa3\xe3\x81\xa6\xe3\x81\x9f\xe3\x82\x8a\xe3\x81\x97\xe3\x81\xbe\xe3\x81\x99\xef\xbc\x9f", 36, "<tmpstr>\xe3\x81\xa3\xe3\x81\xa6\xe3\x80\x81\xe4\xbd\x99\xe3\x81\xa3\xe3\x81\xa6\xe3\x81\x9f\xe3\x82\x8a\xe3\x81\x97\xe3\x81\xbe\xe3\x81\x99\xef\xbc\x9f" },
        { "", 0, "\xe3\x82\x92\xe6\x8c\x81\xe3\x81\xa3\xe3\x81\xa6\xe3\x81\x8d\xe3\x81\xa6\xe3\x81\x8f\xe3\x82\x8c\xe3\x81\x9f\xe3\x81\xae\xef\xbc\x9f", 33, "<tmpstr>\xe3\x82\x92\xe6\x8c\x81\xe3\x81\xa3\xe3\x81\xa6\xe3\x81\x8d\xe3\x81\xa6\xe3\x81\x8f\xe3\x82\x8c\xe3\x81\x9f\xe3\x81\xae\xef\xbc\x9f" },
        { "\xe3\x81\x8a\xe3\x80\x81\xe3\x81\x9d\xe3\x82\x8c\xe3\x81\xa3\xe3\x81\xa6", 18, "\xef\xbc\x9f", 3, "\xe3\x81\x8a\xe3\x80\x81\xe3\x81\x9d\xe3\x82\x8c\xe3\x81\xa3\xe3\x81\xa6<tmpstr>\xef\xbc\x9f" },
        { "\xe3\x81\xb2\xe3\x82\x87\xe3\x81\xa3\xe3\x81\xa8\xe3\x81\x97\xe3\x81\xa6\xe3\x80\x81", 21, "", 0, "\xe3\x81\xb2\xe3\x82\x87\xe3\x81\xa3\xe3\x81\xa8\xe3\x81\x97\xe3\x81\xa6\xe3\x80\x81<tmpstr>" },
        { "", 0, "\xe3\x81\x8c\xe5\xbf\x85\xe8\xa6\x81\xe3\x81\xaa\xe3\x82\x93\xe3\x81\xa0\xe3\x81\x8c\xe2\x80\xa6\xe2\x80\xa6", 27, "<tmpstr>\xe3\x81\x8c\xe5\xbf\x85\xe8\xa6\x81\xe3\x81\xaa\xe3\x82\x93\xe3\x81\xa0\xe3\x81\x8c\xe2\x80\xa6\xe2\x80\xa6" },
        { "", 0, "\xe3\x82\x92\xe6\x8c\x81\xe3\x81\xa3\xe3\x81\xa6\xe3\x81\x8d\xe3\x81\x9f\xe3\x81\xae\xe3\x81\xad", 24, "<tmpstr>\xe3\x82\x92\xe6\x8c\x81\xe3\x81\xa3\xe3\x81\xa6\xe3\x81\x8d\xe3\x81\x9f\xe3\x81\xae\xe3\x81\xad" },
        { "", 0, "\xe3\x82\x92\xe6\x8c\x81\xe3\x81\xa3\xe3\x81\xa6\xe3\x81\xaa\xe3\x81\x84\xe3\x81\x8b\xef\xbc\x9f", 24, "<tmpstr>\xe3\x82\x92\xe6\x8c\x81\xe3\x81\xa3\xe3\x81\xa6\xe3\x81\xaa\xe3\x81\x84\xe3\x81\x8b\xef\xbc\x9f" },
        { "\xe3\x83\xaf\xe3\x82\xb7\xe3\x81\xaf\xe4\xbb\x8a\xe3\x80\x81", 18, "\xe3\x81\x8c", 3, "\xe3\x83\xaf\xe3\x82\xb7\xe3\x81\xaf\xe4\xbb\x8a\xe3\x80\x81<tmpstr>\xe3\x81\x8c" },
        { "\xe3\x83\xaf\xe3\x82\xbf\xe3\x82\xb7\xe3\x81\xaf\xe4\xbb\x8a\xe3\x80\x81", 21, "\xe3\x81\x8c", 3, "\xe3\x83\xaf\xe3\x82\xbf\xe3\x82\xb7\xe3\x81\xaf\xe4\xbb\x8a\xe3\x80\x81<tmpstr>\xe3\x81\x8c" },
        { "", 0, "\xe3\x81\x8c\xe5\xbf\x85\xe8\xa6\x81\xe3\x81\xaa\xe3\x82\x93\xe3\x81\xa0\xe3\x81\x91\xe3\x81\xa9", 24, "<tmpstr>\xe3\x81\x8c\xe5\xbf\x85\xe8\xa6\x81\xe3\x81\xaa\xe3\x82\x93\xe3\x81\xa0\xe3\x81\x91\xe3\x81\xa9" },
        { "\xe3\x81\x93\xe3\x82\x8c\xe3\x81\x8c", 9, "\xe3\x81\x8b\xe2\x80\xa6\xe2\x80\xa6", 9, "\xe3\x81\x93\xe3\x82\x8c\xe3\x81\x8c<tmpstr>\xe3\x81\x8b\xe2\x80\xa6\xe2\x80\xa6" },
        { "\xe3\x81\x9d\xe3\x82\x8c\xe3\x81\xaf", 9, "\xe3\x81\x8b\xef\xbc\x9f", 6, "\xe3\x81\x9d\xe3\x82\x8c\xe3\x81\xaf<tmpstr>\xe3\x81\x8b\xef\xbc\x9f" },
        { "", 0, "\xe3\x82\x92\xe6\x8c\x81\xe3\x81\xa3\xe3\x81\xa6\xe3\x81\xaa\xe3\x81\x84\xef\xbc\x9f", 21, "<tmpstr>\xe3\x82\x92\xe6\x8c\x81\xe3\x81\xa3\xe3\x81\xa6\xe3\x81\xaa\xe3\x81\x84\xef\xbc\x9f" },
        { "\xe3\x81\xbe\xe3\x81\x95\xe3\x81\x8b", 9, "\xe3\x82\x92", 3, "\xe3\x81\xbe\xe3\x81\x95\xe3\x81\x8b<tmpstr>\xe3\x82\x92" },
        { "\xe3\x81\x95\xe3\x81\x99\xe3\x81\x8c", 9, "\xe3\x81\xa0", 3, "\xe3\x81\x95\xe3\x81\x99\xe3\x81\x8c<tmpstr>\xe3\x81\xa0" },
        { "", 0, "\xe3\x81\x8c\xe5\xbf\x85\xe8\xa6\x81\xe3\x81\xa7\xe3\x81\x95", 15, "<tmpstr>\xe3\x81\x8c\xe5\xbf\x85\xe8\xa6\x81\xe3\x81\xa7\xe3\x81\x95" },
        { "", 0, "\xe3\x81\xaa\xe3\x82\x93\xe3\x81\xa0\xe3\x81\x91\xe3\x81\xa9", 15, "<tmpstr>\xe3\x81\xaa\xe3\x82\x93\xe3\x81\xa0\xe3\x81\x91\xe3\x81\xa9" },
        { "\xe3\x81\x9d\xe3\x82\x8c\xe3\x81\xaf", 9, "", 0, "\xe3\x81\x9d\xe3\x82\x8c\xe3\x81\xaf<tmpstr>" },
        { "", 0, "\xe3\x81\xa0\xe3\x81\xad\xef\xbc\x81", 9, "<tmpstr>\xe3\x81\xa0\xe3\x81\xad\xef\xbc\x81" },
        { "", 0, "\xe3\x80\x81", 3, "<tmpstr>\xe3\x80\x81" }
    };
    for (size_t i = 0; i < sizeof(s_tmpstr_rules) / sizeof(s_tmpstr_rules[0]); i++) {
        const struct TmpstrRule* r = &s_tmpstr_rules[i];
        if (len > r->pfx_len + r->sfx_len) {
            if ((r->pfx_len == 0 || memcmp(orig, r->pfx, r->pfx_len) == 0) &&
                (r->sfx_len == 0 || memcmp(orig + len - r->sfx_len, r->sfx, r->sfx_len) == 0)) {
                size_t item_len = len - r->pfx_len - r->sfx_len;
                if (item_len > 0 && item_len < 128) {
                    char item_jp[128];
                    memcpy(item_jp, orig + r->pfx_len, item_len);
                    item_jp[item_len] = '\0';
                    const char* item_th = lookup_translation(item_jp);
                    if (!item_th) item_th = item_jp;
                    const char* templ = lookup_translation(r->templ_key);
                    if (templ) {
                        LONG b_idx = InterlockedIncrement(&s_dynamic_buf_idx);
                        char* buf = s_dynamic_buffers[b_idx & 3];
                        if (replace_str(templ, "<tmpstr>", item_th, buf, sizeof(s_dynamic_buffers[0]))) {
                            return buf;
                        }
                    }
                }
            }
        }
    }

    /* 15. Dynamic Bulletin Board Delivery Quest: "<item> <count>個の納品" */
    /* "個の納品" in UTF-8: \xe5\x80\x8b\xe3\x81\xae\xe7\xb4\x8d\xe5\x93\x81 (15 bytes) */
    if (len > 18 && memcmp(orig + len - 15, "\xe5\x80\x8b\xe3\x81\xae\xe7\xb4\x8d\xe5\x93\x81", 15) == 0) {
        const char* p_ko = orig + len - 15;
        const char* p_d = p_ko - 1;
        while (p_d >= orig && *p_d >= '0' && *p_d <= '9') {
            p_d--;
        }
        if (p_d < p_ko - 1 && p_d > orig && (*p_d == ' ' || (p_d >= orig + 2 && (unsigned char)p_d[-2] == 0xe3 && (unsigned char)p_d[-1] == 0x80 && (unsigned char)p_d[0] == 0x80))) {
            const char* item_end = (*p_d == ' ') ? p_d : (p_d - 2);
            size_t item_len = (size_t)(item_end - orig);
            size_t cnt_len = (size_t)(p_ko - (p_d + 1));
            if (item_len > 0 && item_len < 128 && cnt_len > 0 && cnt_len < 16) {
                char item_jp[128];
                memcpy(item_jp, orig, item_len);
                item_jp[item_len] = '\0';
                char cnt_str[16];
                memcpy(cnt_str, p_d + 1, cnt_len);
                cnt_str[cnt_len] = '\0';

                const char* item_th = lookup_translation(item_jp);
                if (!item_th) item_th = item_jp;

                const char* templ = lookup_translation("<value 1> <value 2>個の納品");
                if (templ) {
                    LONG b_idx = InterlockedIncrement(&s_dynamic_buf_idx);
                    char* buf = s_dynamic_buffers[b_idx & 3];
                    if (replace_str(templ, "<value 1>", item_th, temp1, sizeof(temp1)) &&
                        replace_str(temp1, "<value 2>", cnt_str, buf, sizeof(s_dynamic_buffers[0]))) {
                        return buf;
                    }
                }
            }
        }
    }

    /* 16. Dynamic Bulletin Board Headers: 依頼人： / 物品： / 個数： / 一言： */
    /* "依頼人：" in UTF-8: \xe4\xbe\x9d\xe9\xa0\xbc\xe4\xba\xba\xef\xbc\x9a (12 bytes) */
    if (len > 12 && memcmp(orig, "\xe4\xbe\x9d\xe9\xa0\xbc\xe4\xba\xba\xef\xbc\x9a", 12) == 0) {
        const char* val_jp = orig + 12;
        const char* val_th = lookup_translation(val_jp);
        if (!val_th) val_th = val_jp;
        const char* templ = lookup_translation("依頼人：<value 1>");
        if (templ) {
            LONG b_idx = InterlockedIncrement(&s_dynamic_buf_idx);
            char* buf = s_dynamic_buffers[b_idx & 3];
            if (replace_str(templ, "<value 1>", val_th, buf, sizeof(s_dynamic_buffers[0]))) return buf;
        }
    }
    /* "物品：" in UTF-8: \xe7\x89\xa9\xe5\x93\x81\xef\xbc\x9a (9 bytes) */
    if (len > 9 && memcmp(orig, "\xe7\x89\xa9\xe5\x93\x81\xef\xbc\x9a", 9) == 0) {
        const char* val_jp = orig + 9;
        const char* val_th = lookup_translation(val_jp);
        if (!val_th) val_th = val_jp;
        const char* templ = lookup_translation("物品：<value 1>");
        if (templ) {
            LONG b_idx = InterlockedIncrement(&s_dynamic_buf_idx);
            char* buf = s_dynamic_buffers[b_idx & 3];
            if (replace_str(templ, "<value 1>", val_th, buf, sizeof(s_dynamic_buffers[0]))) return buf;
        }
    }
    /* "個数：" in UTF-8: \xe5\x80\x8b\xe6\x95\xb0\xef\xbc\x9a (9 bytes) ... ends with "個" (\xe5\x80\x8b, 3 bytes) */
    if (len > 12 && memcmp(orig, "\xe5\x80\x8b\xe6\x95\xb0\xef\xbc\x9a", 9) == 0 &&
        memcmp(orig + len - 3, "\xe5\x80\x8b", 3) == 0) {
        size_t nlen = len - 12;
        if (nlen > 0 && nlen < 16) {
            char num_str[16];
            memcpy(num_str, orig + 9, nlen);
            num_str[nlen] = '\0';
            const char* templ = lookup_translation("個数：<value 1>個");
            if (templ) {
                LONG b_idx = InterlockedIncrement(&s_dynamic_buf_idx);
                char* buf = s_dynamic_buffers[b_idx & 3];
                if (replace_str(templ, "<value 1>", num_str, buf, sizeof(s_dynamic_buffers[0]))) return buf;
            }
        }
    }
    /* "一言：" in UTF-8: \xe4\xb8\x80\xe8\xa8\x80\xef\xbc\x9a (9 bytes) */
    if (len > 9 && memcmp(orig, "\xe4\xb8\x80\xe8\xa8\x80\xef\xbc\x9a", 9) == 0) {
        const char* val_jp = orig + 9;
        const char* val_th = lookup_translation(val_jp);
        if (!val_th) val_th = val_jp;
        const char* templ = lookup_translation("一言：<value 1>");
        if (templ) {
            LONG b_idx = InterlockedIncrement(&s_dynamic_buf_idx);
            char* buf = s_dynamic_buffers[b_idx & 3];
            if (replace_str(templ, "<value 1>", val_th, buf, sizeof(s_dynamic_buffers[0]))) return buf;
        }
    }

    /* 17. Dynamic Quest Tracker HUD: "<item>を<count>個<npc>へ届けよう" */
    /* "へ届けよう" in UTF-8: \xe3\x81\xb8\xe5\xb1\x8a\xe3\x81\x91\xe3\x82\x88\xe3\x81\x86 (15 bytes) */
    if (len > 24 && memcmp(orig + len - 15, "\xe3\x81\xb8\xe5\xb1\x8a\xe3\x81\x91\xe3\x82\x88\xe3\x81\x86", 15) == 0) {
        /* Find "を" (\xe3\x82\x92, 3 bytes) and "個" (\xe5\x80\x8b, 3 bytes) */
        const char* p_wo = strstr(orig, "\xe3\x82\x92");
        if (p_wo && p_wo > orig) {
            const char* p_ko = strstr(p_wo + 3, "\xe5\x80\x8b");
            if (p_ko && p_ko > p_wo + 3) {
                size_t item_len = (size_t)(p_wo - orig);
                size_t cnt_len = (size_t)(p_ko - (p_wo + 3));
                size_t npc_len = (size_t)((orig + len - 15) - (p_ko + 3));
                if (item_len > 0 && item_len < 128 && cnt_len > 0 && cnt_len < 16 && npc_len > 0 && npc_len < 64) {
                    char item_jp[128], cnt_str[16], npc_jp[64];
                    memcpy(item_jp, orig, item_len); item_jp[item_len] = '\0';
                    memcpy(cnt_str, p_wo + 3, cnt_len); cnt_str[cnt_len] = '\0';
                    memcpy(npc_jp, p_ko + 3, npc_len); npc_jp[npc_len] = '\0';

                    const char* item_th = lookup_translation(item_jp); if (!item_th) item_th = item_jp;
                    const char* npc_th = lookup_translation(npc_jp); if (!npc_th) npc_th = npc_jp;

                    const char* templ = lookup_translation("<value 1>を<value 2>個<value 3>へ届けよう");
                    if (templ) {
                        LONG b_idx = InterlockedIncrement(&s_dynamic_buf_idx);
                        char* buf = s_dynamic_buffers[b_idx & 3];
                        if (replace_str(templ, "<value 1>", item_th, temp1, sizeof(temp1)) &&
                            replace_str(temp1, "<value 2>", cnt_str, temp2, sizeof(temp2)) &&
                            replace_str(temp2, "<value 3>", npc_th, buf, sizeof(s_dynamic_buffers[0]))) {
                            return buf;
                        }
                    }
                }
            }
        }
    }

    return NULL;
}

static void unescape_string(char* dest, const char* src)
{
    while (*src) {
        if (*src == '\\' && *(src + 1) == 'n') {
            *dest++ = '\n';
            src += 2;
        } else if (*src == '\\' && *(src + 1) == 't') {
            *dest++ = '\t';
            src += 2;
        } else if (*src == '\\' && *(src + 1) == '\\') {
            *dest++ = '\\';
            src += 2;
        } else {
            *dest++ = *src++;
        }
    }
    *dest = '\0';
}

static void strip_br_tags(char* str)
{
    char* src = str;
    char* dst = str;
    while (*src) {
        if (_strnicmp(src, "<br/>", 5) == 0) {
            src += 5;
        } else if (_strnicmp(src, "</br>", 5) == 0) {
            src += 5;
        } else if (_strnicmp(src, "<br>", 4) == 0) {
            src += 4;
        } else {
            *dst++ = *src++;
        }
    }
    *dst = '\0';
}

static int parse_and_insert_translation_file(const wchar_t* path_w)
{
    FILE* f = _wfopen(path_w, L"rb");
    if (!f) return 0;

    char line[16384];
    int loaded = 0;

    /* Skip UTF-8 BOM if present */
    int b0 = fgetc(f), b1 = fgetc(f), b2 = fgetc(f);
    if (!(b0 == 0xEF && b1 == 0xBB && b2 == 0xBF)) {
        rewind(f);
    }

    while (fgets(line, sizeof(line), f)) {
        if (line[0] == '\r' || line[0] == '\n' || line[0] == '\0') continue;

        /* Check comments */
        char* p = line;
        while (*p == ' ' || *p == '\t') p++;
        if (*p == '#' || *p == ';' || (p[0] == '/' && p[1] == '/')) continue;

        char* sep = strchr(line, '=');
        if (!sep) continue;

        *sep = '\0';
        char* orig_raw = line;
        char* trans_raw = sep + 1;

        int len = (int)strlen(trans_raw);
        while (len > 0 && (trans_raw[len - 1] == '\r' || trans_raw[len - 1] == '\n')) {
            trans_raw[len - 1] = '\0';
            len--;
        }

        if (strlen(orig_raw) == 0) continue;

        char orig[16384];
        char trans[16384];
        unescape_string(orig, orig_raw);
        unescape_string(trans, trans_raw);

        strip_br_tags(trans);

        float scale = 1.0f;

        /* Extract [SCALE:...] factor */
        char* sc_tag = strstr(orig, "[SCALE:");
        if (sc_tag) {
            char* tag_end = strchr(sc_tag, ']');
            if (tag_end) {
                float sc = (float)atof(sc_tag + 7);
                if (sc > 0.05f && sc < 10.0f) {
                    scale = sc;
                }
                memmove(sc_tag, tag_end + 1, strlen(tag_end + 1) + 1);
            }
        }

        if (orig[0] == '\0') continue;

        insert_translation(orig, scale, trans);
        loaded++;
    }

    fclose(f);
    return loaded;
}

static void load_translation_file(void)
{
    EnterCriticalSection(&g_cs);
    clear_translation_table();
    int loaded = 0;

    /* 1. Load primary translation.txt */
    loaded += parse_and_insert_translation_file(g_translation_path_w);

    /* 2. Load modular translations from translations\ folder if it exists */
    wchar_t trans_pattern_w[MAX_PATH];
    swprintf(trans_pattern_w, MAX_PATH, L"%ls\\translations\\*.txt", g_mod_dir_w);
    WIN32_FIND_DATAW ffd;
    HANDLE hFind = FindFirstFileW(trans_pattern_w, &ffd);
    if (hFind != INVALID_HANDLE_VALUE) {
        do {
            if (!(ffd.dwFileAttributes & FILE_ATTRIBUTE_DIRECTORY)) {
                wchar_t sub_path_w[MAX_PATH];
                swprintf(sub_path_w, MAX_PATH, L"%ls\\translations\\%ls", g_mod_dir_w, ffd.cFileName);
                loaded += parse_and_insert_translation_file(sub_path_w);
            }
        } while (FindNextFileW(hFind, &ffd));
        FindClose(hFind);
    }

    WIN32_FILE_ATTRIBUTE_DATA fad;
    if (GetFileAttributesExW(g_translation_path_w, GetFileExInfoStandard, &fad)) {
        g_trans_filetime = fad.ftLastWriteTime;
    }

    LeaveCriticalSection(&g_cs);
    log_msg("Loaded %d translation entries (translation.txt and translations folder)", loaded);
}

static void check_hot_reload_translation(void)
{
    WIN32_FILE_ATTRIBUTE_DATA fad;
    if (GetFileAttributesExW(g_translation_path_w, GetFileExInfoStandard, &fad)) {
        if (CompareFileTime(&fad.ftLastWriteTime, &g_trans_filetime) != 0) {
            log_msg("translation.txt changed on disk, hot-reloading...");
            load_translation_file();
        }
    }
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
    (void)source;
    if (!is_safe_str(str, 8192)) return;

    EnterCriticalSection(&g_cs);
    g_total_calls++;
    LeaveCriticalSection(&g_cs);
}

/* ==================================================================
 * Missing Text Detection (Japanese & English) & Logging
 * ================================================================== */
static BOOL has_thai_utf8(const char* s)
{
    if (!s) return FALSE;
    const unsigned char* p = (const unsigned char*)s;
    while (*p) {
        /* Standard Thai Unicode block U+0E00..U+0E7F: 0xE0 0xB8..0xB9 0x80..0xBF */
        if (*p == 0xE0 && (*(p + 1) == 0xB8 || *(p + 1) == 0xB9)) {
            return TRUE;
        }
        /* Thai PUA characters (Private Use Area U+F000..U+F8FF): 0xEF 0x80..0xA3 0x80..0xBF */
        if (*p == 0xEF && (*(p + 1) >= 0x80 && *(p + 1) <= 0xA3)) {
            return TRUE;
        }
        p++;
    }
    return FALSE;
}

static BOOL has_japanese_content(const char* s)
{
    if (!s) return FALSE;
    const unsigned char* p = (const unsigned char*)s;
    while (*p) {
        if (*p == 0xE3) {
            unsigned char b1 = *(p + 1);
            unsigned char b2 = *(p + 2);
            if (b1 != 0 && b2 != 0) {
                /* Hiragana U+3040..U+309F */
                if (b1 == 0x81 && b2 >= 0x80 && b2 <= 0xBF) return TRUE;
                if (b1 == 0x82 && b2 >= 0x80 && b2 <= 0x9F) return TRUE;
                /* Katakana U+30A0..U+30FF */
                if (b1 == 0x82 && b2 >= 0xA0 && b2 <= 0xBF) return TRUE;
                if (b1 == 0x83 && b2 >= 0x80 && b2 <= 0xBF) return TRUE;
                /* Katakana Phonetic Extensions U+31F0..U+31FF */
                if (b1 == 0x87 && b2 >= 0xB0 && b2 <= 0xBF) return TRUE;
                p += 2;
            }
        } else if (*p >= 0xE4 && *p <= 0xE9) {
            unsigned char b1 = *(p + 1);
            unsigned char b2 = *(p + 2);
            if (b1 != 0 && b2 != 0) {
                /* CJK Unified Ideographs (Kanji) U+4E00..U+9FFF */
                if (*p == 0xE4) {
                    if (b1 >= 0xB8 && b1 <= 0xBF && b2 >= 0x80 && b2 <= 0xBF) return TRUE;
                } else {
                    if (b1 >= 0x80 && b1 <= 0xBF && b2 >= 0x80 && b2 <= 0xBF) return TRUE;
                }
                p += 2;
            }
        }
        p++;
    }
    return FALSE;
}

static BOOL has_english_content(const char* s)
{
    if (!s) return FALSE;
    const unsigned char* p = (const unsigned char*)s;
    int letter_streak = 0;
    BOOL in_tag = FALSE;

    while (*p) {
        if (*p == '<') {
            in_tag = TRUE;
            p++;
            continue;
        }
        if (in_tag) {
            if (*p == '>') {
                in_tag = FALSE;
            }
            p++;
            continue;
        }

        /* Check for ASCII Latin letters A-Z, a-z */
        if ((*p >= 'A' && *p <= 'Z') || (*p >= 'a' && *p <= 'z')) {
            letter_streak++;
            if (letter_streak >= 2) {
                return TRUE; /* Word with at least 2 letters */
            }
        } else {
            letter_streak = 0;
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

static void write_utf8_bom(FILE* f)
{
    if (!f) return;
    fseek(f, 0, SEEK_END);
    if (ftell(f) == 0) {
        const unsigned char bom[3] = { 0xEF, 0xBB, 0xBF };
        fwrite(bom, 1, 3, f);
    }
}

static void log_missing_text(const char* str, const char* source, const char* lang_tag)
{
    (void)source;
    if (!is_safe_str(str, 8192)) return;

    EnterCriticalSection(&g_cs);
    if (!is_missing_seen_or_insert(str)) {
        g_missing_count++;

        /* 1. Open session file: missing/missing_YYYY-MM-DD_HH-MM-SS.txt */
        if (!g_fmissing_session && g_session_dump_missing_path_w[0]) {
            g_fmissing_session = _wfopen(g_session_dump_missing_path_w, L"a+");
            if (g_fmissing_session) write_utf8_bom(g_fmissing_session);
        }

        /* 2. Open latest file: missing/missing_latest.txt */
        static BOOL s_latest_opened = FALSE;
        if (!s_latest_opened && g_missing_latest_path_w[0]) {
            g_fmissing_latest = _wfopen(g_missing_latest_path_w, L"w");
            if (g_fmissing_latest) write_utf8_bom(g_fmissing_latest);
            s_latest_opened = TRUE;
        } else if (!g_fmissing_latest && g_missing_latest_path_w[0]) {
            g_fmissing_latest = _wfopen(g_missing_latest_path_w, L"a+");
            if (g_fmissing_latest) write_utf8_bom(g_fmissing_latest);
        }

        /* 3. Open legacy cumulative file: dump_missing.txt */
        if (!g_fmissing_legacy && g_dump_missing_path_w[0]) {
            g_fmissing_legacy = _wfopen(g_dump_missing_path_w, L"a+");
            if (g_fmissing_legacy) write_utf8_bom(g_fmissing_legacy);
        }

        char escaped[8192];
        escape_string_for_dump(escaped, sizeof(escaped), str);

        SYSTEMTIME st;
        GetLocalTime(&st);

        if (g_fmissing_session) {
            fprintf(g_fmissing_session, "[%04d-%02d-%02d %02d:%02d:%02d] [%s] %s\n",
                    st.wYear, st.wMonth, st.wDay,
                    st.wHour, st.wMinute, st.wSecond,
                    lang_tag, escaped);
            fflush(g_fmissing_session);
        }

        if (g_fmissing_latest) {
            fprintf(g_fmissing_latest, "[%04d-%02d-%02d %02d:%02d:%02d] [%s] %s\n",
                    st.wYear, st.wMonth, st.wDay,
                    st.wHour, st.wMinute, st.wSecond,
                    lang_tag, escaped);
            fflush(g_fmissing_latest);
        }

        if (g_fmissing_legacy) {
            fprintf(g_fmissing_legacy, "[%04d-%02d-%02d %02d:%02d:%02d] [%s] %s\n",
                    st.wYear, st.wMonth, st.wDay,
                    st.wHour, st.wMinute, st.wSecond,
                    lang_tag, escaped);
            fflush(g_fmissing_legacy);
        }

        log_msg("[MISSING TEXT] [%s] [%04d-%02d-%02d %02d:%02d:%02d] %s",
                lang_tag,
                st.wYear, st.wMonth, st.wDay,
                st.wHour, st.wMinute, st.wSecond,
                escaped);
    }
    LeaveCriticalSection(&g_cs);
}

static void check_and_log_missing(const char* str, const char* source)
{
    if (!str || !*str) return;

    /* Rule 1: Exclude already-translated Thai text (standard Thai or Thai PUA) */
    if (has_thai_utf8(str)) {
        return;
    }

    /* Rule 2: Check for Japanese text (Hiragana, Katakana, Kanji) */
    if (has_japanese_content(str)) {
        log_missing_text(str, source, "JP");
        return;
    }

    /* Rule 3: Check for English text (>=2 ASCII letters outside tags) */
    if (has_english_content(str)) {
        log_missing_text(str, source, "EN");
        return;
    }
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

static HANDLE g_hDataDat = INVALID_HANDLE_VALUE;
static HANDLE g_hMiscDat = INVALID_HANDLE_VALUE;
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

    /* 1. Mods\TextDump\<basename> (e.g. Mods\TextDump\font.dat) */
    swprintf(candidate, MAX_PATH, L"%ls\\%ls", g_mod_dir_w, base_name_w);
    if (file_exists_and_size_w(candidate, out_size)) {
        wcsncpy(out_path_w, candidate, out_max - 1);
        out_path_w[out_max - 1] = L'\0';
        return TRUE;
    }

    /* 1b. Mods\TextDump\textures\<basename> (e.g. Mods\TextDump\textures\ui_1000_title01.nltx) */
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

    /* 1d. Mods\TextDump\dat\<basename> */
    swprintf(candidate, MAX_PATH, L"%ls\\dat\\%ls", g_mod_dir_w, base_name_w);
    if (file_exists_and_size_w(candidate, out_size)) {
        wcsncpy(out_path_w, candidate, out_max - 1);
        out_path_w[out_max - 1] = L'\0';
        return TRUE;
    }

    /* 1e. Mods\TextDump\data\<basename> */
    swprintf(candidate, MAX_PATH, L"%ls\\data\\%ls", g_mod_dir_w, base_name_w);
    if (file_exists_and_size_w(candidate, out_size)) {
        wcsncpy(out_path_w, candidate, out_max - 1);
        out_path_w[out_max - 1] = L'\0';
        return TRUE;
    }

    /* 1f. Mods\TextDump\database\<basename> */
    swprintf(candidate, MAX_PATH, L"%ls\\database\\%ls", g_mod_dir_w, base_name_w);
    if (file_exists_and_size_w(candidate, out_size)) {
        wcsncpy(out_path_w, candidate, out_max - 1);
        out_path_w[out_max - 1] = L'\0';
        return TRUE;
    }

    /* 2. Mods\Fonts\<basename> (e.g. Mods\Fonts\font.dat or Mods\Fonts\KiwiMaru-Regular.ttf) */
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

    /* 2d. Mods\<basename> (e.g. Mods\font.dat, Mods\talk.dat) */
    swprintf(candidate, MAX_PATH, L"%ls\\..\\%ls", g_mod_dir_w, base_name_w);
    if (file_exists_and_size_w(candidate, out_size)) {
        wcsncpy(out_path_w, candidate, out_max - 1);
        out_path_w[out_max - 1] = L'\0';
        return TRUE;
    }

    /* 2e. Mods\database\<basename> or Mods\Database\<basename> */
    swprintf(candidate, MAX_PATH, L"%ls\\..\\database\\%ls", g_mod_dir_w, base_name_w);
    if (file_exists_and_size_w(candidate, out_size)) {
        wcsncpy(out_path_w, candidate, out_max - 1);
        out_path_w[out_max - 1] = L'\0';
        return TRUE;
    }
    swprintf(candidate, MAX_PATH, L"%ls\\..\\Database\\%ls", g_mod_dir_w, base_name_w);
    if (file_exists_and_size_w(candidate, out_size)) {
        wcsncpy(out_path_w, candidate, out_max - 1);
        out_path_w[out_max - 1] = L'\0';
        return TRUE;
    }

    /* 3. Mods\TextDump\<vfs_name> (e.g. Mods\TextDump\data\database\font.dat) */
    swprintf(candidate, MAX_PATH, L"%ls\\%ls", g_mod_dir_w, win_vfs_name_w);
    if (file_exists_and_size_w(candidate, out_size)) {
        wcsncpy(out_path_w, candidate, out_max - 1);
        out_path_w[out_max - 1] = L'\0';
        return TRUE;
    }

    /* 4. Mods\<vfs_name> (e.g. Mods\data\database\font.dat) */
    swprintf(candidate, MAX_PATH, L"%ls\\..\\%ls", g_mod_dir_w, win_vfs_name_w);
    if (file_exists_and_size_w(candidate, out_size)) {
        wcsncpy(out_path_w, candidate, out_max - 1);
        out_path_w[out_max - 1] = L'\0';
        return TRUE;
    }

    /* 5. <game_root>\script\<basename> (e.g. Village in the Shade\script\story_common.lub) */
    swprintf(candidate, MAX_PATH, L"%ls\\script\\%ls", g_game_dir_w, base_name_w);
    if (file_exists_and_size_w(candidate, out_size)) {
        wcsncpy(out_path_w, candidate, out_max - 1);
        out_path_w[out_max - 1] = L'\0';
        return TRUE;
    }

    /* 6. <game_root>\<vfs_name> */
    swprintf(candidate, MAX_PATH, L"%ls\\%ls", g_game_dir_w, win_vfs_name_w);
    if (file_exists_and_size_w(candidate, out_size)) {
        wcsncpy(out_path_w, candidate, out_max - 1);
        out_path_w[out_max - 1] = L'\0';
        return TRUE;
    }

    /* font.dat is patched dynamically in RAM to support all game versions */

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
    { 110, "ui_keyboard_font.nltx", "ui_keyboard_font_thai.nltx", 1024, 2048 },
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
    { 147, "ui_5010_チラシ37.nltx", "ui_5010_チラシ37_thai.nltx", 1024, 1024 },
    { 148, "ui_5010_チラシ38.nltx", "ui_5010_チラシ38_thai.nltx", 1024, 1024 },
    { 149, "ui_5010_チラシ39.nltx", "ui_5010_チラシ39_thai.nltx", 1024, 1024 },
    { 150, "ui_5010_チラシ40.nltx", "ui_5010_チラシ40_thai.nltx", 1024, 1024 },
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

    /* 1b. Check if the game is reading the FAD Header/TOC for resident_lang_jp.fad */
    if (arch_id == 4 && g_fad_base_offset != 0 && offset == g_fad_base_offset && nNumberOfBytesToRead >= 0x4000) {
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
            int patched = 0;
            size_t fad_sub_count = (size_t)g_fad_runtime_count;
            for (size_t i = 0; i < fad_sub_count; i++) {
                if (!g_fad_runtime_subfiles[i].has_fad_descriptor) continue;

                wchar_t override_path_w[MAX_PATH];
                long ext_size = 0;
                BOOL found = FALSE;
                if (g_fad_runtime_subfiles[i].alt_filename) {
                    found = find_override_file_w(g_fad_runtime_subfiles[i].alt_filename, override_path_w, MAX_PATH, &ext_size);
                }
                if (!found) {
                    found = find_override_file_w(g_fad_runtime_subfiles[i].filename, override_path_w, MAX_PATH, &ext_size);
                }

                if (found && ext_size > 0) {
                    uint32_t target_rel_off = (uint32_t)(g_fad_runtime_subfiles[i].offset - g_fad_base_offset - 32);

                    /* Walk FAD entry table in lpBuffer between 0x1018 and 0x3B00 in 32-byte strides */
                    for (size_t pos = 0x1018; pos + 32 <= nNumberOfBytesToRead && pos < 0x4000; pos += 32) {
                        uint32_t entry_off = *(uint32_t*)((char*)lpBuffer + pos + 8);
                        if (entry_off == target_rel_off) {
                            uint64_t* p_sz = (uint64_t*)((char*)lpBuffer + pos + 0);
                            /* Needed entry size in table: ext_size + 64 bytes (aligned to 64 bytes) */
                            uint64_t needed_sz = ((uint64_t)ext_size + 64 + 63) & ~63ULL;
                            if (needed_sz > *p_sz) {
                                log_msg("[VFS FAD TOC Patch] Expanding size for [%s]: %llu -> %llu bytes (rel_off=0x%X at TOC+0x%X)",
                                        g_fad_runtime_subfiles[i].filename, *p_sz, needed_sz, target_rel_off, (unsigned int)pos);
                                *p_sz = needed_sz;
                                patched++;
                            }
                            break;
                        }
                    }
                }
            }
            if (patched > 0) {
                log_msg("[VFS FAD TOC Patch] Successfully patched %d / %d FAD TOC entries in RAM!",
                        patched, (int)(g_fad_runtime_count / 2));
            }
        }
        return res;
    }

    /* 2. Check if the read offset matches an indexed resource file */
    VfsEntry* entry = lookup_vfs_by_offset(arch_id, offset);
    if (entry) {
        if (strstr(entry->name, "data/database/font.dat")) {
            log_msg("[VFS DETECT] Game requested [%s] at offset 0x%llX (size=%u)",
                    entry->name, (unsigned long long)offset, nNumberOfBytesToRead);
            if (lpOverlapped) {
                add_pending_io(
                    hFile, lpOverlapped, lpBuffer, arch_id, offset, nNumberOfBytesToRead,
                    L"", 0, FALSE, 0, 0, entry->name
                );
                log_msg("[VFS ASYNC QUEUED] Font DB memory patch queued for [%s] (0x%llX, nBytes=%u)",
                        entry->name, (unsigned long long)offset, nNumberOfBytesToRead);
                return fp_original_ReadFile(hFile, lpBuffer, nNumberOfBytesToRead, lpNumberOfBytesRead, lpOverlapped);
            } else {
                BOOL res = fp_original_ReadFile(hFile, lpBuffer, nNumberOfBytesToRead, lpNumberOfBytesRead, NULL);
                if (res && lpBuffer) {
                    DWORD bytes = (lpNumberOfBytesRead ? *lpNumberOfBytesRead : nNumberOfBytesToRead);
                    patch_font_database_in_ram(lpBuffer, bytes);
                }
                return res;
            }
        }

        wchar_t override_path_w[MAX_PATH];
        long ext_size = 0;
        if (find_override_file_w(entry->name, override_path_w, MAX_PATH, &ext_size)) {
            log_msg("[VFS OVERRIDE] Target [%s] (0x%llX) -> %ls (requested=%u, ext_size=%ld)",
                    entry->name, (unsigned long long)offset, override_path_w, nNumberOfBytesToRead, ext_size);
            if (lpOverlapped) {
                add_pending_io(
                    hFile, lpOverlapped, lpBuffer, arch_id, offset, nNumberOfBytesToRead,
                    override_path_w, ext_size, FALSE, 0, 0, entry->name
                );
                log_msg("[VFS ASYNC QUEUED] [%s] (0x%llX) -> %ls (nBytes=%u)",
                        entry->name, (unsigned long long)offset, override_path_w, nNumberOfBytesToRead);
                return fp_original_ReadFile(hFile, lpBuffer, nNumberOfBytesToRead, lpNumberOfBytesRead, lpOverlapped);
            } else {
                BOOL res = fp_original_ReadFile(hFile, lpBuffer, nNumberOfBytesToRead, lpNumberOfBytesRead, NULL);
                if (res && lpBuffer) {
                    PendingIo pio = { 0 };
                    pio.lpBuffer = lpBuffer;
                    pio.bytes_requested = nNumberOfBytesToRead;
                    wcsncpy(pio.override_path_w, override_path_w, MAX_PATH - 1);
                    pio.ext_size = ext_size;
                    pio.is_fad_desc = FALSE;
                    strncpy(pio.filename, entry->name, 127);
                    apply_vfs_payload(&pio);
                }
                return res;
            }
        } else if (strstr(entry->name, "data/database/texture.dat")) {
            /* Patch texture database in memory to point to English/localized textures (as in Switch mod) */
            if (lpOverlapped) {
                add_pending_io(
                    hFile, lpOverlapped, lpBuffer, arch_id, offset, nNumberOfBytesToRead,
                    L"", 0, FALSE, 0, 0, entry->name
                );
                log_msg("[VFS ASYNC QUEUED] Texture DB memory patch queued for [%s] (0x%llX, nBytes=%u)",
                        entry->name, (unsigned long long)offset, nNumberOfBytesToRead);
                return fp_original_ReadFile(hFile, lpBuffer, nNumberOfBytesToRead, lpNumberOfBytesRead, lpOverlapped);
            } else {
                BOOL res = fp_original_ReadFile(hFile, lpBuffer, nNumberOfBytesToRead, lpNumberOfBytesRead, NULL);
                if (res && lpBuffer) {
                    DWORD bytes = (lpNumberOfBytesRead ? *lpNumberOfBytesRead : nNumberOfBytesToRead);
                    patch_texture_database_in_ram(lpBuffer, bytes);
                }
                return res;
            }
        }
    }

    /* 3. Check for FAD sub-file redirections (fairy_1_00.dat / resident_lang_jp.fad) */
    if (arch_id == 4) {
        const FadSubFile* fad_entry = lookup_fad_subfile(offset);
        if (fad_entry) {
            wchar_t override_path_w[MAX_PATH];
            long ext_size = 0;
            BOOL found = FALSE;
            if (fad_entry->alt_filename) {
                found = find_override_file_w(fad_entry->alt_filename, override_path_w, MAX_PATH, &ext_size);
            }
            if (!found) {
                found = find_override_file_w(fad_entry->filename, override_path_w, MAX_PATH, &ext_size);
            }

            if (found) {
                BOOL is_nltx = FALSE;
                FILE* ftest = _wfopen(override_path_w, L"rb");
                if (ftest) {
                    char magic[8] = { 0 };
                    size_t nread = fread(magic, 1, 8, ftest);
                    fclose(ftest);
                    is_nltx = (nread >= 8 && memcmp(magic, "NMPLTEX1", 8) == 0);
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
 * Hook Definitions: Text Rendering & Dynamic Font Scaling
 * ================================================================== */
typedef void (*t_putStr)(void* this_ptr, const char* str);
static t_putStr fp_original_putStr = NULL;
static t_putStr fp_original_putStrProp = NULL;
static t_putStr fp_original_putStrAlign = NULL;

static void call_with_auto_scale(t_putStr fn, void* this_ptr, const char* str, float scale)
{
    if (!fn) return;
    if (!this_ptr || (uintptr_t)this_ptr < 0x10000 || !str) {
        fn(this_ptr, str);
        return;
    }

    if (scale > 0.05f && scale < 0.999f) {
        float* pScaleX = (float*)((char*)this_ptr + 0x28);
        float old_scale = *pScaleX;
        if (old_scale > 0.001f && old_scale < 50.0f) {
            *pScaleX = old_scale * scale;
            fn(this_ptr, str);
            *pScaleX = old_scale;
            return;
        }
    }

    fn(this_ptr, str);
}

static void hk_putStr(void* this_ptr, const char* str)
{
    process_captured_text(str, "putStr");

    float scale = 1.0f;
    const char* rep = lookup_translation_ex(str, &scale);
    if (rep) {
        InterlockedIncrement64((volatile LONG64*)&g_total_replacements);
        str = rep;
    } else {
        check_and_log_missing(str, "putStr");
    }

    call_with_auto_scale(fp_original_putStr, this_ptr, str, scale);
}

static void hk_putStrProp(void* this_ptr, const char* str)
{
    process_captured_text(str, "putStrProp");

    float scale = 1.0f;
    const char* rep = lookup_translation_ex(str, &scale);
    if (rep) {
        InterlockedIncrement64((volatile LONG64*)&g_total_replacements);
        str = rep;
    } else {
        check_and_log_missing(str, "putStrProp");
    }

    call_with_auto_scale(fp_original_putStrProp, this_ptr, str, scale);
}

static void hk_putStrAlign(void* this_ptr, const char* str)
{
    process_captured_text(str, "putStrAlign");

    float scale = 1.0f;
    const char* rep = lookup_translation_ex(str, &scale);
    if (rep) {
        InterlockedIncrement64((volatile LONG64*)&g_total_replacements);
        str = rep;
    } else {
        check_and_log_missing(str, "putStrAlign");
    }

    call_with_auto_scale(fp_original_putStrAlign, this_ptr, str, scale);
}

/* ==================================================================
 * Hook Definitions: Database String ID Interceptor
 * ================================================================== */
typedef void* (*t_GetStringByID)(void* rcx, uint32_t string_id, void* r8);
static t_GetStringByID fp_original_GetStringByID = NULL;

static void* hk_GetStringByID(void* rcx, uint32_t string_id, void* r8)
{
    log_id_access(string_id);
    return fp_original_GetStringByID(rcx, string_id, r8);
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
    },
    {
        .name = "GetStringByID",
        .kind = ADDRSIG_FUNC,
        .pat_hex = "48895c240848897424104c89442418574883ec40",
        .mask_hex = "ffffffffffffffffffffffffffffffffffffffff",
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
    swprintf(g_translation_path_w, MAX_PATH, L"%ls\\translation.txt", g_mod_dir_w);
    swprintf(g_file_access_log_w, MAX_PATH, L"%ls\\file_access.log", g_mod_dir_w);
    swprintf(g_id_log_path_w, MAX_PATH, L"%ls\\id_dump.log", g_mod_dir_w);
    swprintf(g_dump_missing_path_w, MAX_PATH, L"%ls\\dump_missing.txt", g_mod_dir_w);

    /* Missing files directory: Mods/TextDump/missing */
    wchar_t missing_dir_w[MAX_PATH];
    swprintf(missing_dir_w, MAX_PATH, L"%ls\\missing", g_mod_dir_w);
    CreateDirectoryW(missing_dir_w, NULL);

    /* Session missing file: missing/missing_YYYY-MM-DD_HH-MM-SS.txt */
    SYSTEMTIME st;
    GetLocalTime(&st);
    swprintf(g_session_dump_missing_path_w, MAX_PATH, 
             L"%ls\\missing\\missing_%04d-%02d-%02d_%02d-%02d-%02d.txt", 
             g_mod_dir_w, st.wYear, st.wMonth, st.wDay, st.wHour, st.wMinute, st.wSecond);

    /* Latest missing file: missing/missing_latest.txt */
    swprintf(g_missing_latest_path_w, MAX_PATH, L"%ls\\missing\\missing_latest.txt", g_mod_dir_w);

    /* Populate UTF-8 versions for display/logging if needed */
    WideCharToMultiByte(CP_UTF8, 0, g_log_path_w, -1, g_log_path, sizeof(g_log_path), NULL, NULL);
    WideCharToMultiByte(CP_UTF8, 0, g_translation_path_w, -1, g_translation_path, sizeof(g_translation_path), NULL, NULL);
    WideCharToMultiByte(CP_UTF8, 0, g_dump_missing_path_w, -1, g_dump_missing_path, sizeof(g_dump_missing_path), NULL, NULL);
}

static DWORD WINAPI worker_thread(LPVOID param)
{
    (void)param;

    /* Initialize MinHook immediately - zero delay */
    if (MH_Initialize() != MH_OK) {
        log_msg("FATAL: MinHook initialization failed.");
        return 0;
    }

    log_msg("==========================================================");
    log_msg("=== Village in the Shade VFS & Translation Mod Active ===");
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

    /* 2. Install CreateFileW & CreateFileA Archive Hooks immediately */
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

    /* 4. Load translation file */
    load_translation_file();

    /* 5. Resolve & Hook Text Rendering Functions */
    uintptr_t base = (uintptr_t)GetModuleHandleA(NULL);
    log_msg("Main module base address: 0x%p", (void*)base);

    AddrRes res[sizeof(kSigs) / sizeof(kSigs[0])];
    int hits = addrsig_resolve(kSigs, (int)(sizeof(kSigs) / sizeof(kSigs[0])), base, res, log_msg);
    log_msg("Pattern scan complete: %d/%d signatures resolved", hits, (int)(sizeof(kSigs) / sizeof(kSigs[0])));

    uintptr_t addr_putStr = 0;
    uintptr_t addr_putStrProp = 0;
    uintptr_t addr_putStrAlign = 0;
    uintptr_t addr_GetStringByID = 0;

    for (int i = 0; i < (int)(sizeof(kSigs) / sizeof(kSigs[0])); i++) {
        if (res[i].hit) {
            log_msg("  [HIT] %s at 0x%p (RVA: 0x%08X)", res[i].name, (void*)res[i].addr, res[i].rva);
            if (strcmp(res[i].name, "putStr") == 0) addr_putStr = res[i].addr;
            if (strcmp(res[i].name, "putStrProp") == 0) addr_putStrProp = res[i].addr;
            if (strcmp(res[i].name, "putStrAlign") == 0) addr_putStrAlign = res[i].addr;
            if (strcmp(res[i].name, "GetStringByID") == 0) addr_GetStringByID = res[i].addr;
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

    if (addr_GetStringByID) {
        if (MH_CreateHook((LPVOID)addr_GetStringByID, (LPVOID)&hk_GetStringByID, (LPVOID*)&fp_original_GetStringByID) == MH_OK) {
            if (MH_EnableHook((LPVOID)addr_GetStringByID) == MH_OK) {
                log_msg("SUCCESS: Hooked GetStringByID (ID Database Interceptor Active)!");
            }
        }
    }

    /* 6. Patch In-Game Virtual Keyboard string table in memory (Thai Unicode Layout) */
    patch_virtual_keyboard_in_memory(base, log_msg);

    log_msg("System ready! Both VFS and Text Translation are active.");

    /* Initialize in-memory cheats system (monitors cheats.ini) */
    cheats_init(g_game_dir_w, g_mod_dir_w, log_msg);

    int last_unique = 0;
    int last_missing = 0;
    uint64_t last_rep = 0;
    while (1) {
        Sleep(1000);
        check_hot_reload_translation();
        cheats_tick();

        if (g_unique_count != last_unique || g_missing_count != last_missing || g_total_replacements != last_rep) {
            log_msg("Status: Unique texts=%d, Missing texts=%d, Replacements applied=%llu, Total calls=%llu",
                    g_unique_count,
                    g_missing_count,
                    (unsigned long long)g_total_replacements,
                    (unsigned long long)g_total_calls);
            last_unique = g_unique_count;
            last_missing = g_missing_count;
            last_rep = g_total_replacements;
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
        cheats_cleanup();
        if (g_fmissing_session) { fclose(g_fmissing_session); g_fmissing_session = NULL; }
        if (g_fmissing_latest) { fclose(g_fmissing_latest); g_fmissing_latest = NULL; }
        if (g_fmissing_legacy) { fclose(g_fmissing_legacy); g_fmissing_legacy = NULL; }
        if (g_funique) { fclose(g_funique); g_funique = NULL; }
        if (g_funique_latest) { fclose(g_funique_latest); g_funique_latest = NULL; }
        if (g_fraw) { fclose(g_fraw); g_fraw = NULL; }
        if (g_fraw_latest) { fclose(g_fraw_latest); g_fraw_latest = NULL; }
        if (g_flog) { fclose(g_flog); g_flog = NULL; }
        MH_Uninitialize();
        DeleteCriticalSection(&g_cs);
    }
    return TRUE;
}
