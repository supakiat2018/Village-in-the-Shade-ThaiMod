#include <windows.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <stdint.h>
#include <time.h>
#include <ctype.h>
#include "minhook-master/include/MinHook.h"
#include "addrsig.h"
#include "pua_mapping.h"
#include "cheats.h"

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
static FILE* g_fmissing = NULL;
static FILE* g_fmissing_latest = NULL;
static FILE* g_faccess = NULL;
static FILE* g_ftags = NULL;
static FILE* g_fidlog = NULL;
static uint8_t g_logged_ids[65536 / 8] = { 0 };
static char g_active_player_name[64] = { 0 };
static char g_active_dog_name[64] = { 0 };
static char g_custom_thai_player_name[128] = { 0 };
static char g_custom_thai_dog_name[128] = { 0 };
static wchar_t g_custom_thai_player_name_raw_w[128] = { 0 };
static wchar_t g_custom_thai_dog_name_raw_w[128] = { 0 };
static wchar_t g_custom_names_ini_path_w[MAX_PATH] = { 0 };
static char g_custom_names_ini_path[MAX_PATH] = { 0 };

static ULONGLONG g_last_name_screen_tick = 0;
static BOOL g_is_dog_name_screen = FALSE;
static BOOL g_thai_dialog_open = FALSE;
static wchar_t g_thai_dialog_result[128] = { 0 };
static WNDPROC g_prev_edit_proc = NULL;

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
    char* cond;
    float scale;
    char* trans;
    struct TransNode* next;
} TransNode;

static TransNode* g_trans_table[HASH_TABLE_SIZE] = { 0 };
static int g_trans_count = 0;
static void clear_reassembler_table(void);

/* ==================================================================
 * Anchor-Based Context Ring Buffer (Order-Aware Anchor Tracking)
 * ================================================================== */
#define ANCHOR_HISTORY_CAP 64
#define ANCHOR_MAX_AGE_MS  1500

typedef struct {
    char str[128];
    ULONGLONG tick;
} AnchorEntry;

static AnchorEntry g_anchors[ANCHOR_HISTORY_CAP] = { 0 };
static int g_anchor_idx = 0;

static void record_recent_string(const char* s)
{
    if (!s || (uintptr_t)s < 0x10000 || s[0] == '\0') return;
    ULONGLONG now = GetTickCount64();
    EnterCriticalSection(&g_cs);

    int idx = g_anchor_idx % ANCHOR_HISTORY_CAP;
    strncpy(g_anchors[idx].str, s, sizeof(g_anchors[idx].str) - 1);
    g_anchors[idx].str[sizeof(g_anchors[idx].str) - 1] = '\0';
    g_anchors[idx].tick = now;
    g_anchor_idx++;

    LeaveCriticalSection(&g_cs);
}

static void clear_translation_table(void)
{
    clear_reassembler_table();
    for (int i = 0; i < HASH_TABLE_SIZE; i++) {
        TransNode* node = g_trans_table[i];
        while (node) {
            TransNode* next = node->next;
            free(node->orig);
            if (node->cond) free(node->cond);
            free(node->trans);
            free(node);
            node = next;
        }
        g_trans_table[i] = NULL;
    }
    g_trans_count = 0;
}

static void insert_translation_ex(const char* orig, const char* cond, float scale, const char* trans, BOOL allow_overwrite)
{
    if (!orig || !trans || *orig == '\0' || *trans == '\0') return;
    uint32_t h = hash_str(orig);
    uint32_t bucket = h % HASH_TABLE_SIZE;

    TransNode* node = g_trans_table[bucket];
    while (node) {
        if (node->hash == h && strcmp(node->orig, orig) == 0) {
            BOOL same_cond = (node->cond == NULL && cond == NULL) ||
                             (node->cond != NULL && cond != NULL && strcmp(node->cond, cond) == 0);
            if (same_cond) {
                if (allow_overwrite) {
                    free(node->trans);
                    node->trans = _strdup(trans);
                    node->scale = scale;
                }
                return;
            }
        }
        node = node->next;
    }

    TransNode* new_node = (TransNode*)malloc(sizeof(TransNode));
    if (new_node) {
        new_node->hash = h;
        new_node->orig = _strdup(orig);
        new_node->cond = cond ? _strdup(cond) : NULL;
        new_node->scale = scale;
        new_node->trans = _strdup(trans);
        new_node->next = g_trans_table[bucket];
        g_trans_table[bucket] = new_node;
        g_trans_count++;
    }
}

static void insert_translation(const char* orig, const char* cond, float scale, const char* trans)
{
    insert_translation_ex(orig, cond, scale, trans, TRUE);
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

/* ==================================================================
 * Direct Thai Input System (F2 Modal Dialog & Clipboard Paste)
 * ================================================================== */
static void load_custom_names_ini(void)
{
    if (g_custom_names_ini_path[0] == '\0') return;

    GetPrivateProfileStringA("Names", "PlayerName", "", g_custom_thai_player_name, sizeof(g_custom_thai_player_name), g_custom_names_ini_path);
    GetPrivateProfileStringA("Names", "DogName", "", g_custom_thai_dog_name, sizeof(g_custom_thai_dog_name), g_custom_names_ini_path);
    GetPrivateProfileStringA("Names", "ActivePlayerName", "", g_active_player_name, sizeof(g_active_player_name), g_custom_names_ini_path);
    GetPrivateProfileStringA("Names", "ActiveDogName", "", g_active_dog_name, sizeof(g_active_dog_name), g_custom_names_ini_path);

    GetPrivateProfileStringW(L"Names", L"PlayerNameRaw", L"", g_custom_thai_player_name_raw_w, 128, g_custom_names_ini_path_w);
    GetPrivateProfileStringW(L"Names", L"DogNameRaw", L"", g_custom_thai_dog_name_raw_w, 128, g_custom_names_ini_path_w);

    if (g_custom_thai_player_name[0] != '\0') {
        log_msg("[NAMES] Loaded custom player name from INI: %s (active: %s)",
                g_custom_thai_player_name, g_active_player_name);
    }
    if (g_custom_thai_dog_name[0] != '\0') {
        log_msg("[NAMES] Loaded custom dog name from INI: %s (active: %s)",
                g_custom_thai_dog_name, g_active_dog_name);
    }
}

static void save_custom_names_ini(void)
{
    if (g_custom_names_ini_path[0] == '\0') return;

    WritePrivateProfileStringA("Names", "PlayerName", g_custom_thai_player_name, g_custom_names_ini_path);
    WritePrivateProfileStringA("Names", "DogName", g_custom_thai_dog_name, g_custom_names_ini_path);
    WritePrivateProfileStringA("Names", "ActivePlayerName", g_active_player_name, g_custom_names_ini_path);
    WritePrivateProfileStringA("Names", "ActiveDogName", g_active_dog_name, g_custom_names_ini_path);

    WritePrivateProfileStringW(L"Names", L"PlayerNameRaw", g_custom_thai_player_name_raw_w, g_custom_names_ini_path_w);
    WritePrivateProfileStringW(L"Names", L"DogNameRaw", g_custom_thai_dog_name_raw_w, g_custom_names_ini_path_w);
}

static BOOL read_clipboard_thai_wstr(wchar_t* out_wstr, size_t max_chars)
{
    if (!out_wstr || max_chars == 0) return FALSE;
    out_wstr[0] = L'\0';
    if (!OpenClipboard(NULL)) return FALSE;
    HANDLE hData = GetClipboardData(CF_UNICODETEXT);
    if (!hData) {
        CloseClipboard();
        return FALSE;
    }
    const wchar_t* pText = (const wchar_t*)GlobalLock(hData);
    if (!pText) {
        CloseClipboard();
        return FALSE;
    }
    wcsncpy(out_wstr, pText, max_chars - 1);
    out_wstr[max_chars - 1] = L'\0';
    GlobalUnlock(hData);
    CloseClipboard();

    size_t len = wcslen(out_wstr);
    while (len > 0 && (out_wstr[len - 1] == L'\r' || out_wstr[len - 1] == L'\n' || out_wstr[len - 1] == L' ' || out_wstr[len - 1] == L'\t')) {
        out_wstr[--len] = L'\0';
    }
    wchar_t* p = out_wstr;
    while (*p == L' ' || *p == L'\t' || *p == L'\r' || *p == L'\n') p++;
    if (p != out_wstr) {
        wmemmove(out_wstr, p, wcslen(p) + 1);
    }
    return wcslen(out_wstr) > 0;
}

static void trigger_thai_name_clipboard_paste(void)
{
    wchar_t wbuf[128] = { 0 };
    if (!read_clipboard_thai_wstr(wbuf, 128)) {
        log_msg("[CLIPBOARD PASTE] Clipboard was empty or contained no text.");
        return;
    }

    char pua_buf[256] = { 0 };
    convert_thai_wstr_to_pua_utf8(wbuf, pua_buf, sizeof(pua_buf));
    if (pua_buf[0] == '\0') return;

    if (g_is_dog_name_screen) {
        strncpy(g_custom_thai_dog_name, pua_buf, sizeof(g_custom_thai_dog_name) - 1);
        wcsncpy(g_custom_thai_dog_name_raw_w, wbuf, 127);
        if (g_active_dog_name[0] == '\0') {
            strncpy(g_active_dog_name, "\xe3\x83\x9d\xe3\x83\x81", sizeof(g_active_dog_name) - 1); // "ポチ"
        }
        log_msg("[CLIPBOARD PASTE] Set dog name from clipboard: %s", g_custom_thai_dog_name);
    } else {
        strncpy(g_custom_thai_player_name, pua_buf, sizeof(g_custom_thai_player_name) - 1);
        wcsncpy(g_custom_thai_player_name_raw_w, wbuf, 127);
        if (g_active_player_name[0] == '\0') {
            strncpy(g_active_player_name, "\xe3\x82\xa2\xe3\x83\xa1", sizeof(g_active_player_name) - 1); // "アメ"
        }
        log_msg("[CLIPBOARD PASTE] Set player name from clipboard: %s", g_custom_thai_player_name);
    }
    save_custom_names_ini();
    MessageBeep(MB_OK);
}

static LRESULT CALLBACK EditSubclassProc(HWND hWnd, UINT uMsg, WPARAM wParam, LPARAM lParam)
{
    if (uMsg == WM_KEYDOWN) {
        if (wParam == VK_RETURN) {
            SendMessageW(GetParent(hWnd), WM_COMMAND, MAKEWPARAM(IDOK, BN_CLICKED), (LPARAM)hWnd);
            return 0;
        } else if (wParam == VK_ESCAPE) {
            SendMessageW(GetParent(hWnd), WM_COMMAND, MAKEWPARAM(IDCANCEL, BN_CLICKED), (LPARAM)hWnd);
            return 0;
        }
    }
    return CallWindowProcW(g_prev_edit_proc, hWnd, uMsg, wParam, lParam);
}

static LRESULT CALLBACK ThaiInputDialogProc(HWND hWnd, UINT uMsg, WPARAM wParam, LPARAM lParam)
{
    switch (uMsg) {
    case WM_COMMAND:
        if (LOWORD(wParam) == IDOK) {
            HWND hEdit = GetDlgItem(hWnd, 101);
            if (hEdit) {
                GetWindowTextW(hEdit, g_thai_dialog_result, 128);
                int len = (int)wcslen(g_thai_dialog_result);
                while (len > 0 && (g_thai_dialog_result[len - 1] == L' ' || g_thai_dialog_result[len - 1] == L'\t')) {
                    g_thai_dialog_result[--len] = L'\0';
                }
                wchar_t* p = g_thai_dialog_result;
                while (*p == L' ' || *p == L'\t') p++;
                if (p != g_thai_dialog_result) {
                    wmemmove(g_thai_dialog_result, p, wcslen(p) + 1);
                }
            }
            g_thai_dialog_open = FALSE;
            DestroyWindow(hWnd);
            return 0;
        } else if (LOWORD(wParam) == IDCANCEL) {
            g_thai_dialog_result[0] = L'\0';
            g_thai_dialog_open = FALSE;
            DestroyWindow(hWnd);
            return 0;
        }
        break;

    case WM_CLOSE:
        g_thai_dialog_result[0] = L'\0';
        g_thai_dialog_open = FALSE;
        DestroyWindow(hWnd);
        return 0;

    case WM_CTLCOLORSTATIC: {
        HDC hdcStatic = (HDC)wParam;
        SetBkMode(hdcStatic, TRANSPARENT);
        return (LRESULT)GetSysColorBrush(COLOR_BTNFACE);
    }

    default:
        break;
    }
    return DefWindowProcW(hWnd, uMsg, wParam, lParam);
}

static void show_thai_name_input_dialog(void)
{
    if (g_thai_dialog_open) return;

    HWND hGameWnd = GetActiveWindow();
    if (!hGameWnd) hGameWnd = GetForegroundWindow();

    static BOOL s_class_registered = FALSE;
    static const wchar_t CLASS_NAME[] = L"VillageThaiNameInputWndClass";

    if (!s_class_registered) {
        WNDCLASSEXW wc = { 0 };
        wc.cbSize = sizeof(WNDCLASSEXW);
        wc.style = CS_HREDRAW | CS_VREDRAW;
        wc.lpfnWndProc = ThaiInputDialogProc;
        wc.hInstance = g_hinst ? g_hinst : GetModuleHandleW(NULL);
        wc.hCursor = LoadCursor(NULL, IDC_ARROW);
        wc.hbrBackground = (HBRUSH)(COLOR_BTNFACE + 1);
        wc.lpszClassName = CLASS_NAME;
        if (!RegisterClassExW(&wc)) {
            log_msg("[DIRECT THAI INPUT] Failed to register window class.");
            return;
        }
        s_class_registered = TRUE;
    }

    int dlg_w = 480;
    int dlg_h = 245;
    int pos_x = (GetSystemMetrics(SM_CXSCREEN) - dlg_w) / 2;
    int pos_y = (GetSystemMetrics(SM_CYSCREEN) - dlg_h) / 2;

    if (hGameWnd) {
        RECT rc;
        if (GetWindowRect(hGameWnd, &rc)) {
            pos_x = rc.left + ((rc.right - rc.left) - dlg_w) / 2;
            pos_y = rc.top + ((rc.bottom - rc.top) - dlg_h) / 2;
        }
    }

    const wchar_t* title = g_is_dog_name_screen ? 
        L"ป้อนชื่อสุนัข (Dog Name Input) - Village in the Shade" : 
        L"ป้อนชื่อตัวละคร (Player Name Input) - Village in the Shade";

    HWND hDlg = CreateWindowExW(
        WS_EX_DLGMODALFRAME | WS_EX_TOPMOST,
        CLASS_NAME,
        title,
        WS_POPUP | WS_CAPTION | WS_SYSMENU,
        pos_x, pos_y, dlg_w, dlg_h,
        hGameWnd,
        NULL,
        g_hinst ? g_hinst : GetModuleHandleW(NULL),
        NULL
    );

    if (!hDlg) {
        log_msg("[DIRECT THAI INPUT] Failed to create dialog window.");
        return;
    }

    HFONT hFont = CreateFontW(
        18, 0, 0, 0, FW_NORMAL, FALSE, FALSE, FALSE,
        DEFAULT_CHARSET, OUT_DEFAULT_PRECIS, CLIP_DEFAULT_PRECIS,
        CLEARTYPE_QUALITY, DEFAULT_PITCH | FF_DONTCARE, L"Segoe UI"
    );

    const wchar_t* prompt_text = g_is_dog_name_screen ?
        L"พิมพ์ชื่อสุนัขภาษาไทยที่ต้องการ (หรือกด Ctrl+V เพื่อวาง):" :
        L"พิมพ์ชื่อตัวละครภาษาไทยที่ต้องการ (หรือกด Ctrl+V เพื่อวาง):";

    HWND hLbl = CreateWindowW(
        L"STATIC", prompt_text,
        WS_CHILD | WS_VISIBLE,
        25, 20, 420, 24,
        hDlg, NULL, NULL, NULL
    );

    HWND hEdit = CreateWindowExW(
        WS_EX_CLIENTEDGE, L"EDIT", L"",
        WS_CHILD | WS_VISIBLE | ES_AUTOHSCROLL | WS_TABSTOP,
        25, 50, 415, 28,
        hDlg, (HMENU)101, NULL, NULL
    );

    HWND hHint = CreateWindowW(
        L"STATIC",
        L"คำแนะนำ: ชื่อห้ามเว้นว่าง ให้พิมพ์ภาษาญี่ปุ่นในเกม 1 ตัว\nแล้วกด F2 เพื่อตั้งชื่อไทย จากนั้นกด ตกลง และกดยืนยันในเกมทันที",
        WS_CHILD | WS_VISIBLE,
        25, 85, 430, 40,
        hDlg, NULL, NULL, NULL
    );

    HWND hBtnOk = CreateWindowW(
        L"BUTTON", L"ตกลง (OK)",
        WS_CHILD | WS_VISIBLE | BS_DEFPUSHBUTTON | WS_TABSTOP,
        125, 140, 105, 34,
        hDlg, (HMENU)IDOK, NULL, NULL
    );

    HWND hBtnCancel = CreateWindowW(
        L"BUTTON", L"ยกเลิก (Cancel)",
        WS_CHILD | WS_VISIBLE | BS_PUSHBUTTON | WS_TABSTOP,
        250, 140, 105, 34,
        hDlg, (HMENU)IDCANCEL, NULL, NULL
    );

    if (hFont) {
        SendMessageW(hLbl, WM_SETFONT, (WPARAM)hFont, TRUE);
        SendMessageW(hEdit, WM_SETFONT, (WPARAM)hFont, TRUE);
        SendMessageW(hHint, WM_SETFONT, (WPARAM)hFont, TRUE);
        SendMessageW(hBtnOk, WM_SETFONT, (WPARAM)hFont, TRUE);
        SendMessageW(hBtnCancel, WM_SETFONT, (WPARAM)hFont, TRUE);
    }

    g_prev_edit_proc = (WNDPROC)SetWindowLongPtrW(hEdit, GWLP_WNDPROC, (LONG_PTR)EditSubclassProc);

    if (g_is_dog_name_screen && g_custom_thai_dog_name_raw_w[0] != L'\0') {
        SetWindowTextW(hEdit, g_custom_thai_dog_name_raw_w);
        SendMessageW(hEdit, EM_SETSEL, 0, -1);
    } else if (!g_is_dog_name_screen && g_custom_thai_player_name_raw_w[0] != L'\0') {
        SetWindowTextW(hEdit, g_custom_thai_player_name_raw_w);
        SendMessageW(hEdit, EM_SETSEL, 0, -1);
    }

    g_thai_dialog_result[0] = L'\0';
    g_thai_dialog_open = TRUE;

    if (hGameWnd) {
        EnableWindow(hGameWnd, FALSE);
    }

    ShowWindow(hDlg, SW_SHOW);
    SetForegroundWindow(hDlg);
    SetFocus(hEdit);

    MSG msg;
    while (g_thai_dialog_open && GetMessageW(&msg, NULL, 0, 0)) {
        if (!IsDialogMessageW(hDlg, &msg)) {
            TranslateMessage(&msg);
            DispatchMessageW(&msg);
        }
    }

    if (hGameWnd) {
        EnableWindow(hGameWnd, TRUE);
        SetForegroundWindow(hGameWnd);
    }

    if (hFont) {
        DeleteObject(hFont);
    }

    if (g_thai_dialog_result[0] != L'\0') {
        char pua_buf[256] = { 0 };
        convert_thai_wstr_to_pua_utf8(g_thai_dialog_result, pua_buf, sizeof(pua_buf));
        if (pua_buf[0] != '\0') {
            if (g_is_dog_name_screen) {
                strncpy(g_custom_thai_dog_name, pua_buf, sizeof(g_custom_thai_dog_name) - 1);
                wcsncpy(g_custom_thai_dog_name_raw_w, g_thai_dialog_result, 127);
                if (g_active_dog_name[0] == '\0') {
                    strncpy(g_active_dog_name, "\xe3\x83\x9d\xe3\x83\x81", sizeof(g_active_dog_name) - 1); // "ポチ"
                }
                log_msg("[DIRECT THAI INPUT] Set dog name: %s", g_custom_thai_dog_name);
            } else {
                strncpy(g_custom_thai_player_name, pua_buf, sizeof(g_custom_thai_player_name) - 1);
                wcsncpy(g_custom_thai_player_name_raw_w, g_thai_dialog_result, 127);
                if (g_active_player_name[0] == '\0') {
                    strncpy(g_active_player_name, "\xe3\x82\xa2\xe3\x83\xa1", sizeof(g_active_player_name) - 1); // "アメ"
                }
                log_msg("[DIRECT THAI INPUT] Set player name: %s", g_custom_thai_player_name);
            }
            save_custom_names_ini();
            MessageBeep(MB_OK);
        }
    }
}

static void check_thai_name_input_hotkeys(ULONGLONG now)
{
    if (g_thai_dialog_open) return;
    static ULONGLONG s_last_hotkey_tick = 0;
    if (now - s_last_hotkey_tick < 400) return;

    if (GetAsyncKeyState(VK_F2) & 0x8000) {
        s_last_hotkey_tick = now;
        show_thai_name_input_dialog();
    } else if ((GetAsyncKeyState(VK_CONTROL) & 0x8000) && (GetAsyncKeyState('V') & 0x8000)) {
        s_last_hotkey_tick = now;
        trigger_thai_name_clipboard_paste();
    }
}

static void update_name_screen_state_and_hotkeys(const char* str)
{
    if (!str || str[0] == '\0') return;

    if (strcmp(str, "あなたの名前") == 0 ||
        strcmp(str, "\xe3\x81\x82\xe3\x81\xaa\xe3\x81\x9f\xe3\x81\xae\xe5\x90\x8d\xe5\x89\x8d") == 0) {
        g_is_dog_name_screen = FALSE;
        g_last_name_screen_tick = GetTickCount64();
    } else if (strcmp(str, "犬の名前") == 0 ||
               strcmp(str, "\xe7\x8a\xac\xe3\x81\xae\xe5\x90\x8d\xe5\x89\x8d") == 0) {
        g_is_dog_name_screen = TRUE;
        g_last_name_screen_tick = GetTickCount64();
    } else if (strcmp(str, "ひら") == 0 || strcmp(str, "カタ") == 0 ||
               strcmp(str, "1文字消す") == 0 || strcmp(str, "決定") == 0 ||
               strcmp(str, "\xe3\x81\xb2\xe3\x82\x89") == 0 ||
               strcmp(str, "\xe3\x82\xab\xe3\x82\xbf") == 0 ||
               strcmp(str, "\x31\xe6\x96\x87\xe5\xad\x97\xe6\xb6\x88\xe3\x81\x99") == 0 ||
               strcmp(str, "\xe6\xb1\xba\xe5\xae\x9a") == 0) {
        g_last_name_screen_tick = GetTickCount64();
    }

    ULONGLONG now = GetTickCount64();
    if ((now - g_last_name_screen_tick) <= 1500) {
        check_thai_name_input_hotkeys(now);
    }
}

/* ==================================================================
 * Smart Sentence Re-assembler for Split Tagged Lines (<player>, <dog>, <strong>)
 * ================================================================== */
typedef struct {
    char* orig_prefix;
    char* orig_mid;
    char* orig_suffix;
    char* trans_prefix;
    char* trans_mid;
    char* trans_suffix;
    char* cond;
    float scale;
    int is_strong;
} ReassemblerEntry;

static ReassemblerEntry* g_reassembler_table = NULL;
static int g_reassembler_count = 0;
static int g_reassembler_capacity = 0;

static int g_active_reassembler_idx = -1;
static ULONGLONG g_active_reassembler_tick = 0;
static int g_active_reassembler_step = 0;

static void clear_reassembler_table(void)
{
    if (g_reassembler_table) {
        for (int i = 0; i < g_reassembler_count; i++) {
            if (g_reassembler_table[i].orig_prefix) free(g_reassembler_table[i].orig_prefix);
            if (g_reassembler_table[i].orig_mid) free(g_reassembler_table[i].orig_mid);
            if (g_reassembler_table[i].orig_suffix) free(g_reassembler_table[i].orig_suffix);
            if (g_reassembler_table[i].trans_prefix) free(g_reassembler_table[i].trans_prefix);
            if (g_reassembler_table[i].trans_mid) free(g_reassembler_table[i].trans_mid);
            if (g_reassembler_table[i].trans_suffix) free(g_reassembler_table[i].trans_suffix);
            if (g_reassembler_table[i].cond) free(g_reassembler_table[i].cond);
        }
        free(g_reassembler_table);
        g_reassembler_table = NULL;
    }
    g_reassembler_count = 0;
    g_reassembler_capacity = 0;
    g_active_reassembler_idx = -1;
    g_active_reassembler_step = 0;
}

static void add_reassembler_entry(const char* orig_prefix, const char* orig_mid, const char* orig_suffix,
                                  const char* trans_prefix, const char* trans_mid, const char* trans_suffix,
                                  const char* cond, float scale, int is_strong)
{
    if (g_reassembler_count >= g_reassembler_capacity) {
        int new_cap = g_reassembler_capacity == 0 ? 512 : g_reassembler_capacity * 2;
        ReassemblerEntry* new_tbl = (ReassemblerEntry*)realloc(g_reassembler_table, new_cap * sizeof(ReassemblerEntry));
        if (!new_tbl) return;
        g_reassembler_table = new_tbl;
        g_reassembler_capacity = new_cap;
    }

    ReassemblerEntry* e = &g_reassembler_table[g_reassembler_count++];
    e->orig_prefix  = _strdup(orig_prefix ? orig_prefix : "");
    e->orig_mid     = _strdup(orig_mid ? orig_mid : "");
    e->orig_suffix  = _strdup(orig_suffix ? orig_suffix : "");
    e->trans_prefix = _strdup(trans_prefix ? trans_prefix : "");
    e->trans_mid    = _strdup(trans_mid ? trans_mid : "");
    e->trans_suffix = _strdup(trans_suffix ? trans_suffix : "");
    e->cond = (cond && cond[0] != '\0') ? _strdup(cond) : NULL;
    e->scale = scale;
    e->is_strong = is_strong;
}

static BOOL check_anchor_condition(const char* cond)
{
    if (!cond || cond[0] == '\0') return TRUE;
    ULONGLONG now = GetTickCount64();
    EnterCriticalSection(&g_cs);
    int max_search = (g_anchor_idx < ANCHOR_HISTORY_CAP) ? g_anchor_idx : ANCHOR_HISTORY_CAP;
    for (int dist = 1; dist <= max_search; dist++) {
        int slot = (g_anchor_idx - dist + ANCHOR_HISTORY_CAP * 100) % ANCHOR_HISTORY_CAP;
        if (g_anchors[slot].tick > 0 && (now - g_anchors[slot].tick) <= 8000) {
            if (strstr(g_anchors[slot].str, cond) != NULL) {
                LeaveCriticalSection(&g_cs);
                return TRUE;
            }
        }
    }
    LeaveCriticalSection(&g_cs);
    return FALSE;
}

static BOOL check_recent_anchor(const char* needle, ULONGLONG max_age_ms)
{
    if (!needle || needle[0] == '\0') return FALSE;
    ULONGLONG now = GetTickCount64();
    EnterCriticalSection(&g_cs);
    int max_search = (g_anchor_idx < ANCHOR_HISTORY_CAP) ? g_anchor_idx : ANCHOR_HISTORY_CAP;
    for (int dist = 1; dist <= max_search; dist++) {
        int slot = (g_anchor_idx - dist + ANCHOR_HISTORY_CAP * 100) % ANCHOR_HISTORY_CAP;
        if (g_anchors[slot].tick > 0 && (now - g_anchors[slot].tick) <= max_age_ms) {
            if (strstr(g_anchors[slot].str, needle) != NULL) {
                LeaveCriticalSection(&g_cs);
                return TRUE;
            }
        }
    }
    LeaveCriticalSection(&g_cs);
    return FALSE;
}

static const char* lookup_reassembler(const char* orig, float* out_scale)
{
    if (!orig || orig[0] == '\0' || g_reassembler_count == 0) return NULL;
    ULONGLONG now = GetTickCount64();

    /* 1. Check if active reassembler is currently waiting for suffix */
    if (g_active_reassembler_idx >= 0 && g_active_reassembler_idx < g_reassembler_count) {
        if (now - g_active_reassembler_tick <= 3000) {
            ReassemblerEntry* e = &g_reassembler_table[g_active_reassembler_idx];

            /* Check if this is the middle token */
            BOOL is_mid = FALSE;
            if (e->is_strong) {
                if (e->orig_mid[0] != '\0' && strcmp(e->orig_mid, orig) == 0) is_mid = TRUE;
            } else {
                if (g_active_player_name[0] != '\0' && strcmp(orig, g_active_player_name) == 0) is_mid = TRUE;
                else if (strcmp(orig, "\xe3\x82\xa2\xe3\x83\xa1") == 0) is_mid = TRUE; /* "アメ" */
                else if (g_custom_thai_player_name[0] != '\0' && strcmp(orig, g_custom_thai_player_name) == 0) is_mid = TRUE;
                else if (g_active_dog_name[0] != '\0' && strcmp(orig, g_active_dog_name) == 0) is_mid = TRUE;
                else if (strcmp(orig, "\xe3\x83\x9d\xe3\x83\x81") == 0) is_mid = TRUE; /* "ポチ" */
                else if (g_custom_thai_dog_name[0] != '\0' && strcmp(orig, g_custom_thai_dog_name) == 0) is_mid = TRUE;
            }

            if (is_mid) {
                g_active_reassembler_step = 2;
                g_active_reassembler_tick = now;
                if (e->is_strong && e->trans_mid[0] != '\0') {
                    if (out_scale) *out_scale = e->scale;
                    return e->trans_mid;
                }
                if (!e->is_strong && g_custom_thai_player_name[0] != '\0') {
                    if (out_scale) *out_scale = 1.0f;
                    return g_custom_thai_player_name;
                }
            }

            /* Check if this is the suffix token (or prefix of suffix during layout measuring) */
            if (e->orig_suffix[0] != '\0') {
                if (strcmp(e->orig_suffix, orig) == 0) {
                    g_active_reassembler_idx = -1;
                    g_active_reassembler_step = 0;
                    if (out_scale) *out_scale = e->scale;
                    static const char s_empty[] = "";
                    return (e->trans_suffix && e->trans_suffix[0] != '\0') ? e->trans_suffix : s_empty;
                } else if (e->trans_suffix[0] == '\0' && strstr(e->orig_suffix, orig) != NULL) {
                    /* Suppress partial Japanese suffix during word measurement */
                    static const char s_empty[] = "";
                    return s_empty;
                }
            }
        } else {
            g_active_reassembler_idx = -1;
            g_active_reassembler_step = 0;
        }
    }

    /* 2. Check if orig is a suffix of an entry whose prefix is EMPTY */
    for (int i = 0; i < g_reassembler_count; i++) {
        ReassemblerEntry* e = &g_reassembler_table[i];
        if (e->orig_prefix[0] == '\0' && e->orig_suffix[0] != '\0') {
            if (strcmp(e->orig_suffix, orig) == 0) {
                if (e->cond && !check_anchor_condition(e->cond)) continue;
                if (out_scale) *out_scale = e->scale;
                return e->trans_suffix;
            }
        }
    }

    /* 3. Check if orig is the prefix of a Reassembler entry */
    int matched_idx = -1;
    int match_count = 0;
    for (int i = 0; i < g_reassembler_count; i++) {
        ReassemblerEntry* e = &g_reassembler_table[i];
        if (e->orig_prefix[0] != '\0' && strcmp(e->orig_prefix, orig) == 0) {
            if (e->cond) {
                if (!check_anchor_condition(e->cond)) continue;
            }
            matched_idx = i;
            match_count++;
        }
    }

    if (match_count == 1) {
        g_active_reassembler_idx = matched_idx;
        g_active_reassembler_tick = now;
        g_active_reassembler_step = 1;
        if (out_scale) *out_scale = g_reassembler_table[matched_idx].scale;
        return g_reassembler_table[matched_idx].trans_prefix;
    } else if (match_count > 1) {
        for (int i = 0; i < g_reassembler_count; i++) {
            ReassemblerEntry* e = &g_reassembler_table[i];
            if (e->orig_prefix[0] != '\0' && strcmp(e->orig_prefix, orig) == 0 && e->cond != NULL) {
                if (check_anchor_condition(e->cond)) {
                    g_active_reassembler_idx = i;
                    g_active_reassembler_tick = now;
                    g_active_reassembler_step = 1;
                    if (out_scale) *out_scale = e->scale;
                    return e->trans_prefix;
                }
            }
        }
    }

    /* 4. Check if orig is a suffix of an entry whose prefix was seen recently in anchors */
    for (int i = 0; i < g_reassembler_count; i++) {
        ReassemblerEntry* e = &g_reassembler_table[i];
        if (e->orig_suffix[0] != '\0' && strcmp(e->orig_suffix, orig) == 0) {
            if (e->orig_prefix[0] != '\0' && check_recent_anchor(e->orig_prefix, 4000)) {
                if (e->cond && !check_anchor_condition(e->cond)) continue;
                if (out_scale) *out_scale = e->scale;
                static const char s_empty[] = "";
                return (e->trans_suffix && e->trans_suffix[0] != '\0') ? e->trans_suffix : s_empty;
            }
        }
    }

    return NULL;
}

static const char* lookup_translation(const char* orig);
static const char* try_match_dynamic_template(const char* orig);

static const char* lookup_translation_ex(const char* orig, float* out_scale)
{
    if (out_scale) *out_scale = 1.0f;
    if (!orig || g_trans_count == 0) return NULL;
    update_name_screen_state_and_hotkeys(orig);

    /* 0. Smart Sentence Re-assembler for split tagged dialogue */
    const char* re_match = lookup_reassembler(orig, out_scale);
    if (re_match != NULL) {
        return re_match;
    }

    /* 0.5 Standalone Player & Dog Name Replacement (takes absolute precedence over default dictionary) */
    if (g_custom_thai_player_name[0] != '\0') {
        if ((g_active_player_name[0] != '\0' && strcmp(orig, g_active_player_name) == 0) ||
            strcmp(orig, "\xe3\x82\xa2\xe3\x83\xa1") == 0) { /* "アメ" */
            if (out_scale) *out_scale = 1.0f;
            return g_custom_thai_player_name;
        }
    }
    if (g_custom_thai_dog_name[0] != '\0') {
        if ((g_active_dog_name[0] != '\0' && strcmp(orig, g_active_dog_name) == 0) ||
            strcmp(orig, "\xe3\x83\x9d\xe3\x83\x81") == 0) { /* "ポチ" */
            if (out_scale) *out_scale = 1.0f;
            return g_custom_thai_dog_name;
        }
    }

    uint32_t h = hash_str(orig);
    uint32_t bucket = h % HASH_TABLE_SIZE;

    TransNode* best_node = NULL;
    int best_distance = 999999;
    TransNode* default_node = NULL;

    ULONGLONG now = GetTickCount64();
    EnterCriticalSection(&g_cs);

    /* 1. First pass: check anchor rules and find the CLOSEST anchor */
    TransNode* node = g_trans_table[bucket];
    while (node) {
        if (node->hash == h && strcmp(node->orig, orig) == 0) {
            if (node->cond != NULL) {
#define ANCHOR_MAX_DISTANCE ANCHOR_HISTORY_CAP
                int max_search = (g_anchor_idx < ANCHOR_MAX_DISTANCE) ? g_anchor_idx : ANCHOR_MAX_DISTANCE;
                for (int dist = 1; dist <= max_search; dist++) {
                    int slot = (g_anchor_idx - dist + ANCHOR_HISTORY_CAP * 100) % ANCHOR_HISTORY_CAP;
                    if (g_anchors[slot].tick > 0 && (now - g_anchors[slot].tick) <= ANCHOR_MAX_AGE_MS) {
                        if (strstr(g_anchors[slot].str, node->cond) != NULL) {
                            if (dist < best_distance) {
                                best_distance = dist;
                                best_node = node;
                            }
                            break; /* Found closest occurrence for this rule */
                        }
                    }
                }
            } else {
                default_node = node;
            }
        }
        node = node->next;
    }
    LeaveCriticalSection(&g_cs);

    /* Throttled debug logging for ambiguous keys (なし, うん) */
    static ULONGLONG s_last_debug_log = 0;
    if ((strcmp(orig, "なし") == 0 || strcmp(orig, "うん") == 0) && (now - s_last_debug_log > 2000)) {
        s_last_debug_log = now;
        log_msg("[ANCHOR DEBUG] lookup '%s': matched=%s (cond='%s', dist=%d)",
                orig,
                best_node ? best_node->trans : (default_node ? default_node->trans : "NULL"),
                best_node && best_node->cond ? best_node->cond : "NONE",
                best_distance);
        for (int d = 1; d <= 8 && d <= g_anchor_idx; d++) {
            int sl = (g_anchor_idx - d + ANCHOR_HISTORY_CAP * 100) % ANCHOR_HISTORY_CAP;
            log_msg("   anchor[-d=%d, age=%llums]: '%s'", d, now - g_anchors[sl].tick, g_anchors[sl].str);
        }
    }

    /* If a contextual anchor matched, return the closest one */
    if (best_node) {
        if (out_scale) *out_scale = best_node->scale;
        return best_node->trans;
    }

    /* 2. Fallback to unconditional default translation */
    if (default_node) {
        if (out_scale) *out_scale = default_node->scale;
        return default_node->trans;
    }

    /* 2.5 Standalone Player & Dog Name Replacement (menus, status, name screen) */
    if (g_custom_thai_player_name[0] != '\0' && g_active_player_name[0] != '\0' && strcmp(orig, g_active_player_name) == 0) {
        if (out_scale) *out_scale = 1.0f;
        return g_custom_thai_player_name;
    }
    if (g_custom_thai_dog_name[0] != '\0' && g_active_dog_name[0] != '\0' && strcmp(orig, g_active_dog_name) == 0) {
        if (out_scale) *out_scale = 1.0f;
        return g_custom_thai_dog_name;
    }

    /* 3. Dynamic Name Confirmation: 「<name>」でよろしいですか？ */
    if (strncmp(orig, "\xe3\x80\x8c", 3) == 0) {
        const char* p_close = strstr(orig, "\xe3\x80\x8d\xe3\x81\xa7\xe3\x82\x88\xe3\x82\x8d\xe3\x81\x97\xe3\x81\x84\xe3\x81\xa7\xe3\x81\x99\xe3\x81\x8b\xef\xbc\x9f");
        if (p_close) {
            size_t name_len = p_close - (orig + 3);
            char captured_name[64] = { 0 };
            BOOL is_dog = FALSE;
            if (name_len > 0 && name_len < sizeof(captured_name)) {
                memcpy(captured_name, orig + 3, name_len);
                captured_name[name_len] = '\0';

                /* Check if recent anchor was "犬の名前" (\xe7\x8a\xac\xe3\x81\xae\xe5\x90\x8d\xe5\x89\x8d) */
                for (int d = 1; d <= 8 && d <= g_anchor_idx; d++) {
                    int sl = (g_anchor_idx - d + ANCHOR_HISTORY_CAP * 100) % ANCHOR_HISTORY_CAP;
                    if (g_anchors[sl].tick > 0 && (now - g_anchors[sl].tick) <= 15000) {
                        if (strstr(g_anchors[sl].str, "\xe7\x8a\xac\xe3\x81\xae\xe5\x90\x8d\xe5\x89\x8d") != NULL) {
                            is_dog = TRUE;
                            break;
                        }
                    }
                }
                if (is_dog) {
                    strncpy(g_active_dog_name, captured_name, sizeof(g_active_dog_name) - 1);
                    log_msg("[DOG NAME] Captured dog name: %s", g_active_dog_name);
                    save_custom_names_ini();
                } else {
                    strncpy(g_active_player_name, captured_name, sizeof(g_active_player_name) - 1);
                    log_msg("[PLAYER NAME] Captured player name: %s", g_active_player_name);
                    save_custom_names_ini();
                }
            }
            static char name_confirm_buf[512];
            const char* templ = lookup_translation_ex("「<value 1>」でよろしいですか？", NULL);
            if (!templ) templ = lookup_translation_ex("「」でよろしいですか？", NULL);
            if (templ) {
                const char* cur_name = NULL;
                if (is_dog) {
                    if (g_custom_thai_dog_name[0] != '\0') {
                        cur_name = g_custom_thai_dog_name;
                    } else {
                        cur_name = captured_name[0] != '\0' ? captured_name : g_active_dog_name;
                    }
                } else {
                    if (g_custom_thai_player_name[0] != '\0') {
                        cur_name = g_custom_thai_player_name;
                    } else {
                        cur_name = captured_name[0] != '\0' ? captured_name : g_active_player_name;
                    }
                }
                if (strstr(templ, "<value 1>")) {
                    if (replace_str(templ, "<value 1>", cur_name, name_confirm_buf, sizeof(name_confirm_buf))) {
                        return name_confirm_buf;
                    }
                } else if (strstr(templ, "\"\"")) {
                    char name_in_quotes[128];
                    snprintf(name_in_quotes, sizeof(name_in_quotes), "\"%s\"", cur_name);
                    if (replace_str(templ, "\"\"", name_in_quotes, name_confirm_buf, sizeof(name_confirm_buf))) {
                        return name_confirm_buf;
                    }
                }
            }
        }
    }

    /* 4. Dynamic Player & Dog Name Substitution */
    if ((g_active_player_name[0] != '\0' && strstr(orig, g_active_player_name) != NULL) ||
        (g_active_dog_name[0] != '\0' && strstr(orig, g_active_dog_name) != NULL)) {
        char templ[8192];
        strncpy(templ, orig, sizeof(templ) - 1);
        templ[sizeof(templ) - 1] = '\0';
        if (g_active_player_name[0] != '\0' && strstr(templ, g_active_player_name) != NULL) {
            char temp_sub[8192];
            if (replace_str(templ, g_active_player_name, "<player>", temp_sub, sizeof(temp_sub))) {
                strncpy(templ, temp_sub, sizeof(templ) - 1);
                templ[sizeof(templ) - 1] = '\0';
            }
        }
        if (g_active_dog_name[0] != '\0' && strstr(templ, g_active_dog_name) != NULL) {
            char temp_sub[8192];
            if (replace_str(templ, g_active_dog_name, "<dog>", temp_sub, sizeof(temp_sub))) {
                strncpy(templ, temp_sub, sizeof(templ) - 1);
                templ[sizeof(templ) - 1] = '\0';
            }
        }
        const char* rep_templ = lookup_translation_ex(templ, NULL);
        if (rep_templ) {
            static char dynamic_buf[8192];
            strncpy(dynamic_buf, rep_templ, sizeof(dynamic_buf) - 1);
            dynamic_buf[sizeof(dynamic_buf) - 1] = '\0';
            const char* player_rep = (g_custom_thai_player_name[0] != '\0') ? g_custom_thai_player_name : g_active_player_name;
            const char* dog_rep = (g_custom_thai_dog_name[0] != '\0') ? g_custom_thai_dog_name : g_active_dog_name;
            if (player_rep[0] != '\0' && strstr(dynamic_buf, "<player>") != NULL) {
                char temp_sub[8192];
                if (replace_str(dynamic_buf, "<player>", player_rep, temp_sub, sizeof(temp_sub))) {
                    strncpy(dynamic_buf, temp_sub, sizeof(dynamic_buf) - 1);
                    dynamic_buf[sizeof(dynamic_buf) - 1] = '\0';
                }
            }
            if (dog_rep[0] != '\0' && strstr(dynamic_buf, "<dog>") != NULL) {
                char temp_sub[8192];
                if (replace_str(dynamic_buf, "<dog>", dog_rep, temp_sub, sizeof(temp_sub))) {
                    strncpy(dynamic_buf, temp_sub, sizeof(dynamic_buf) - 1);
                    dynamic_buf[sizeof(dynamic_buf) - 1] = '\0';
                }
            }
            return dynamic_buf;
        }
    }

    /* 5. Dynamic Template Matching (<value ...> patterns: save dates, currency, items) */
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

    /* 13. Dynamic <npcname> Matching */
    /* Pattern A: <npc>と食事の約束をしたんだった！ */
    /* "と食事の約束をしたんだった！" in UTF-8: \xe3\x81\xa8\xe9\xa3\x9f\xe4\xba\x8b\xe3\x81\xae\xe7\xb4\x84\xe6\x9d\x9f\xe3\x82\x92\xe3\x81\x97\xe3\x81\x9f\xe3\x82\x93\xe3\x81\xa0\xe3\x81\xa3\xe3\x81\x9f\xef\xbc\x81 (39 bytes) */
    static const char s_sfx_meal[] = "\xe3\x81\xa8\xe9\xa3\x9f\xe4\xba\x8b\xe3\x81\xae\xe7\xb4\x84\xe6\x9d\x9f\xe3\x82\x92\xe3\x81\x97\xe3\x81\x9f\xe3\x82\x93\xe3\x81\xa0\xe3\x81\xa3\xe3\x81\x9f\xef\xbc\x81";
    if (len > 39 && memcmp(orig + len - 39, s_sfx_meal, 39) == 0) {
        size_t nlen = len - 39;
        if (nlen > 0 && nlen < 64) {
            char npc_jp[64];
            memcpy(npc_jp, orig, nlen);
            npc_jp[nlen] = '\0';
            const char* npc_th = lookup_translation(npc_jp);
            if (!npc_th) npc_th = npc_jp;
            const char* templ = lookup_translation("<npcname>と食事の約束をしたんだった！");
            if (templ) {
                LONG b_idx = InterlockedIncrement(&s_dynamic_buf_idx);
                char* buf = s_dynamic_buffers[b_idx & 3];
                if (replace_str(templ, "<npcname>", npc_th, buf, sizeof(s_dynamic_buffers[0]))) return buf;
            }
        }
    }

    /* Pattern B: <npc>とお泊りの約束したんだった！ */
    /* "とお泊りの約束したんだった！" in UTF-8: \xe3\x81\xa8\xe3\x81\x8a\xe6\xb3\x8a\xe3\x82\x8a\xe3\x81\xae\xe7\xb4\x84\xe6\x9d\x9f\xe3\x81\x97\xe3\x81\x9f\xe3\x82\x93\xe3\x81\xa0\xe3\x81\xa3\xe3\x81\x9f\xef\xbc\x81 (42 bytes) */
    static const char s_sfx_stay[] = "\xe3\x81\xa8\xe3\x81\x8a\xe6\xb3\x8a\xe3\x82\x8a\xe3\x81\xae\xe7\xb4\x84\xe6\x9d\x9f\xe3\x81\x97\xe3\x81\x9f\xe3\x82\x93\xe3\x81\xa0\xe3\x81\xa3\xe3\x81\x9f\xef\xbc\x81";
    if (len > 42 && memcmp(orig + len - 42, s_sfx_stay, 42) == 0) {
        size_t nlen = len - 42;
        if (nlen > 0 && nlen < 64) {
            char npc_jp[64];
            memcpy(npc_jp, orig, nlen);
            npc_jp[nlen] = '\0';
            const char* npc_th = lookup_translation(npc_jp);
            if (!npc_th) npc_th = npc_jp;
            const char* templ = lookup_translation("<npcname>とお泊りの約束したんだった！");
            if (templ) {
                LONG b_idx = InterlockedIncrement(&s_dynamic_buf_idx);
                char* buf = s_dynamic_buffers[b_idx & 3];
                if (replace_str(templ, "<npcname>", npc_th, buf, sizeof(s_dynamic_buffers[0]))) return buf;
            }
        }
    }

    /* Pattern C: 今日は、<npc>と */
    /* "今日は、" in UTF-8: \xe4\xbb\x8a\xe6\x97\xa5\xe3\x81\xaf\xe3\x80\x81 (12 bytes), "と" is \xe3\x81\xa8 (3 bytes) */
    if (len > 15 && memcmp(orig, "\xe4\xbb\x8a\xe6\x97\xa5\xe3\x81\xaf\xe3\x80\x81", 12) == 0 &&
        memcmp(orig + len - 3, "\xe3\x81\xa8", 3) == 0) {
        size_t nlen = len - 15;
        if (nlen > 0 && nlen < 64) {
            char npc_jp[64];
            memcpy(npc_jp, orig + 12, nlen);
            npc_jp[nlen] = '\0';
            const char* npc_th = lookup_translation(npc_jp);
            if (!npc_th) npc_th = npc_jp;
            const char* templ = lookup_translation("今日は、<npcname>と");
            if (templ) {
                LONG b_idx = InterlockedIncrement(&s_dynamic_buf_idx);
                char* buf = s_dynamic_buffers[b_idx & 3];
                if (replace_str(templ, "<npcname>", npc_th, buf, sizeof(s_dynamic_buffers[0]))) return buf;
            }
        }
    }

    /* 14. Dynamic Dog Name Extraction & Patterns */
    /* Pattern A: この子は<dog>ってお名前なの */
    /* "この子は" in UTF-8: \xe3\x81\x93\xe3\x81\xae\xe5\xad\x90\xe3\x81\xaf (12 bytes) */
    /* "ってお名前なの" in UTF-8: \xe3\x81\xa3\xe3\x81\xa6\xe3\x81\x8a\xe5\x90\x8d\xe5\x89\x8d\xe3\x81\xaa\xe3\x81\xae (21 bytes) */
    if (len > 33 && memcmp(orig, "\xe3\x81\x93\xe3\x81\xae\xe5\xad\x90\xe3\x81\xaf", 12) == 0 &&
        memcmp(orig + len - 21, "\xe3\x81\xa3\xe3\x81\xa6\xe3\x81\x8a\xe5\x90\x8d\xe5\x89\x8d\xe3\x81\xaa\xe3\x81\xae", 21) == 0) {
        size_t dlen = len - 33;
        if (dlen > 0 && dlen < sizeof(g_active_dog_name)) {
            memcpy(g_active_dog_name, orig + 12, dlen);
            g_active_dog_name[dlen] = '\0';
            log_msg("[DOG NAME] Learned active dog name: %s", g_active_dog_name);
            const char* templ = lookup_translation("この子は<dog>ってお名前なの");
            if (templ) {
                LONG b_idx = InterlockedIncrement(&s_dynamic_buf_idx);
                char* buf = s_dynamic_buffers[b_idx & 3];
                if (replace_str(templ, "<dog>", g_active_dog_name, buf, sizeof(s_dynamic_buffers[0]))) return buf;
            }
        }
    }

    /* Pattern B: <dog>を育てることになった */
    /* "を育てることになった" in UTF-8: \xe3\x82\x92\xe8\x82\xb2\xe3\x81\xa6\xe3\x82\x8b\xe3\x81\x93\xe3\x81\xa8\xe3\x81\xab\xe3\x81\xaa\xe3\x81\xa3\xe3\x81\x9f" (33 bytes) */
    if (len > 33 && memcmp(orig + len - 33, "\xe3\x82\x92\xe8\x82\xb2\xe3\x81\xa6\xe3\x82\x8b\xe3\x81\x93\xe3\x81\xa8\xe3\x81\xab\xe3\x81\xaa\xe3\x81\xa3\xe3\x81\x9f", 33) == 0) {
        size_t dlen = len - 33;
        if (dlen > 0 && dlen < sizeof(g_active_dog_name)) {
            memcpy(g_active_dog_name, orig, dlen);
            g_active_dog_name[dlen] = '\0';
            log_msg("[DOG NAME] Learned active dog name: %s", g_active_dog_name);
            const char* templ = lookup_translation("<dog>を育てることになった");
            if (templ) {
                LONG b_idx = InterlockedIncrement(&s_dynamic_buf_idx);
                char* buf = s_dynamic_buffers[b_idx & 3];
                if (replace_str(templ, "<dog>", g_active_dog_name, buf, sizeof(s_dynamic_buffers[0]))) return buf;
            }
        }
    }

    /* Pattern C: <dog>が呼んでる…… */
    /* "が呼んでる……" in UTF-8: \xe3\x81\x8c\xe5\x91\xbc\xe3\x82\x93\xe3\x81\xa7\xe3\x82\x8b\xe2\x80\xa6\xe2\x80\xa6 (21 bytes) */
    if (len > 21 && memcmp(orig + len - 21, "\xe3\x81\x8c\xe5\x91\xbc\xe3\x82\x93\xe3\x81\xa7\xe3\x82\x8b\xe2\x80\xa6\xe2\x80\xa6", 21) == 0) {
        size_t dlen = len - 21;
        if (dlen > 0 && dlen < sizeof(g_active_dog_name)) {
            memcpy(g_active_dog_name, orig, dlen);
            g_active_dog_name[dlen] = '\0';
            log_msg("[DOG NAME] Learned active dog name: %s", g_active_dog_name);
            const char* templ = lookup_translation("<dog>が呼んでる……");
            if (templ) {
                LONG b_idx = InterlockedIncrement(&s_dynamic_buf_idx);
                char* buf = s_dynamic_buffers[b_idx & 3];
                if (replace_str(templ, "<dog>", g_active_dog_name, buf, sizeof(s_dynamic_buffers[0]))) return buf;
            }
        }
    }

    /* Pattern D: <dog>についていってみよう…… */
    /* "についていってみよう……" in UTF-8: \xe3\x81\xab\xe3\x81\xa4\xe3\x81\x84\xe3\x81\xa6\xe3\x81\x84\xe3\x81\xa3\xe3\x81\xa6\xe3\x81\xbf\xe3\x82\x88\xe3\x81\x86\xe2\x80\xa6\xe2\x80\xa6 (33 bytes) */
    if (len > 33 && memcmp(orig + len - 33, "\xe3\x81\xab\xe3\x81\xa4\xe3\x81\x84\xe3\x81\xa6\xe3\x81\x84\xe3\x81\xa3\xe3\x81\xa6\xe3\x81\xbf\xe3\x82\x88\xe3\x81\x86\xe2\x80\xa6\xe2\x80\xa6", 33) == 0) {
        size_t dlen = len - 33;
        if (dlen > 0 && dlen < sizeof(g_active_dog_name)) {
            memcpy(g_active_dog_name, orig, dlen);
            g_active_dog_name[dlen] = '\0';
            log_msg("[DOG NAME] Learned active dog name: %s", g_active_dog_name);
            const char* templ = lookup_translation("<dog>についていってみよう……");
            if (templ) {
                LONG b_idx = InterlockedIncrement(&s_dynamic_buf_idx);
                char* buf = s_dynamic_buffers[b_idx & 3];
                if (replace_str(templ, "<dog>", g_active_dog_name, buf, sizeof(s_dynamic_buffers[0]))) return buf;
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

static void strip_xml_tags(char* dst, const char* src, size_t dst_max)
{
    size_t d = 0;
    while (*src && d + 1 < dst_max) {
        if (*src == '<') {
            const char* close = strchr(src, '>');
            if (close) {
                src = close + 1;
                continue;
            }
        }
        dst[d++] = *src++;
    }
    dst[d] = '\0';
}

static void strip_dialogue_tags(char* str)
{
    char* src = str;
    char* dst = str;
    while (*src) {
        if (*src == '<') {
            if (_strnicmp(src, "<cmd", 4) != 0) {
                char* close = strchr(src, '>');
                if (close) {
                    src = close + 1;
                    continue;
                }
            }
        }
        *dst++ = *src++;
    }
    *dst = '\0';
}

static void register_reassembler_entry(const char* orig, const char* trans_with_tags, const char* cond, float scale)
{
    if (!orig || !trans_with_tags || *orig == '\0' || *trans_with_tags == '\0') return;

    /* 1. Handle <player> */
    const char* p_orig_player = strstr(orig, "<player>");
    if (p_orig_player) {
        char op[1024] = { 0 };
        char os[1024] = { 0 };
        size_t op_len = (size_t)(p_orig_player - orig);
        if (op_len < sizeof(op)) {
            memcpy(op, orig, op_len);
            op[op_len] = '\0';
        }
        strncpy(os, p_orig_player + 8, sizeof(os) - 1);

        char tp[2048] = { 0 };
        char ts[2048] = { 0 };
        const char* p_trans_player = strstr(trans_with_tags, "<player>");
        if (p_trans_player) {
            size_t tp_len = (size_t)(p_trans_player - trans_with_tags);
            if (tp_len < sizeof(tp)) {
                memcpy(tp, trans_with_tags, tp_len);
                tp[tp_len] = '\0';
            }
            strncpy(ts, p_trans_player + 8, sizeof(ts) - 1);
        } else {
            strncpy(tp, trans_with_tags, sizeof(tp) - 1);
            ts[0] = '\0';
        }
        strip_dialogue_tags(tp);
        strip_dialogue_tags(ts);

        add_reassembler_entry(op, "<player>", os, tp, "<player>", ts, cond, scale, 0);
        return;
    }

    /* 2. Handle <dog> */
    const char* p_orig_dog = strstr(orig, "<dog>");
    if (p_orig_dog) {
        char op[1024] = { 0 };
        char os[1024] = { 0 };
        size_t op_len = (size_t)(p_orig_dog - orig);
        if (op_len < sizeof(op)) {
            memcpy(op, orig, op_len);
            op[op_len] = '\0';
        }
        strncpy(os, p_orig_dog + 5, sizeof(os) - 1);

        char tp[2048] = { 0 };
        char ts[2048] = { 0 };
        const char* p_trans_dog = strstr(trans_with_tags, "<dog>");
        if (p_trans_dog) {
            size_t tp_len = (size_t)(p_trans_dog - trans_with_tags);
            if (tp_len < sizeof(tp)) {
                memcpy(tp, trans_with_tags, tp_len);
                tp[tp_len] = '\0';
            }
            strncpy(ts, p_trans_dog + 5, sizeof(ts) - 1);
        } else {
            strncpy(tp, trans_with_tags, sizeof(tp) - 1);
            ts[0] = '\0';
        }
        strip_dialogue_tags(tp);
        strip_dialogue_tags(ts);

        add_reassembler_entry(op, "<dog>", os, tp, "<dog>", ts, cond, scale, 0);
        return;
    }

    /* 3. Handle <strong>...</strong> */
    const char* s1 = strstr(orig, "<strong>");
    const char* s2 = s1 ? strstr(s1, "</strong>") : NULL;
    if (s1 && s2 && s2 > s1 + 8) {
        char op[1024] = { 0 };
        char om[1024] = { 0 };
        char os[1024] = { 0 };
        size_t op_len = (size_t)(s1 - orig);
        if (op_len < sizeof(op)) {
            memcpy(op, orig, op_len);
            op[op_len] = '\0';
        }
        size_t om_len = (size_t)(s2 - (s1 + 8));
        if (om_len < sizeof(om)) {
            memcpy(om, s1 + 8, om_len);
            om[om_len] = '\0';
        }
        strncpy(os, s2 + 9, sizeof(os) - 1);

        char tp[2048] = { 0 };
        char tm[2048] = { 0 };
        char ts[2048] = { 0 };
        const char* t1 = strstr(trans_with_tags, "<strong>");
        const char* t2 = t1 ? strstr(t1, "</strong>") : NULL;
        if (t1 && t2 && t2 > t1 + 8) {
            size_t tp_len = (size_t)(t1 - trans_with_tags);
            if (tp_len < sizeof(tp)) {
                memcpy(tp, trans_with_tags, tp_len);
                tp[tp_len] = '\0';
            }
            size_t tm_len = (size_t)(t2 - (t1 + 8));
            if (tm_len < sizeof(tm)) {
                memcpy(tm, t1 + 8, tm_len);
                tm[tm_len] = '\0';
            }
            strncpy(ts, t2 + 9, sizeof(ts) - 1);
        } else {
            strncpy(tp, trans_with_tags, sizeof(tp) - 1);
        }
        strip_dialogue_tags(tp);
        strip_dialogue_tags(tm);
        strip_dialogue_tags(ts);

        add_reassembler_entry(op, om, os, tp, tm, ts, cond, scale, 1);
        if (om[0] != '\0' && tm[0] != '\0') {
            insert_translation_ex(om, cond, scale, tm, FALSE);
        }
        return;
    }
}

static void tokenize_and_insert_tags(const char* orig_in, const char* trans_in, const char* cond, float scale, int* p_loaded)
{
    if (!orig_in || !trans_in || *orig_in == '\0' || *trans_in == '\0') return;

    /* 1. Tokenize <strong>...</strong> (Highlighted terms in dialogue) - Only index highlighted keywords */
    if (strstr(orig_in, "<strong>") && strstr(trans_in, "<strong>")) {
        const char* p_orig = orig_in;
        const char* p_trans = trans_in;
        while (p_orig && p_trans) {
            const char* s1 = strstr(p_orig, "<strong>");
            const char* t1 = strstr(p_trans, "<strong>");
            if (!s1 || !t1) break;
            const char* s2 = strstr(s1, "</strong>");
            const char* t2 = strstr(t1, "</strong>");
            if (!s2 || !t2) break;

            size_t k_mid_len = s2 - (s1 + 8);
            size_t v_mid_len = t2 - (t1 + 8);
            if (k_mid_len >= 6 && k_mid_len < 4096 && v_mid_len > 0 && v_mid_len < 4096) {
                char k_mid[4096] = { 0 };
                char v_mid[4096] = { 0 };
                memcpy(k_mid, s1 + 8, k_mid_len);
                memcpy(v_mid, t1 + 8, v_mid_len);
                trim_str(k_mid);
                trim_str(v_mid);
                if (k_mid[0] != '\0' && v_mid[0] != '\0') {
                    insert_translation_ex(k_mid, cond, scale, v_mid, FALSE);
                    (*p_loaded)++;
                }
            }

            p_orig = s2 + 9;
            p_trans = t2 + 9;
        }
    }

    /* 2. Tokenize <c ...>...</c> (Color tags in text) - Only index highlighted keywords */
    if (strstr(orig_in, "<c ") && strstr(orig_in, "</c>") && strstr(trans_in, "</c>")) {
        const char* s1 = strstr(orig_in, "<c ");
        const char* s1_close = s1 ? strchr(s1, '>') : NULL;
        const char* s2 = s1_close ? strstr(s1_close, "</c>") : NULL;

        const char* t1 = strstr(trans_in, "<c ");
        const char* t1_close = t1 ? strchr(t1, '>') : NULL;
        const char* t2 = t1_close ? strstr(t1_close, "</c>") : NULL;

        if (s1_close && s2 && t1_close && t2) {
            size_t k_mid_len = s2 - (s1_close + 1);
            size_t v_mid_len = t2 - (t1_close + 1);
            if (k_mid_len >= 6 && k_mid_len < 4096 && v_mid_len > 0 && v_mid_len < 4096) {
                char k_mid[4096] = { 0 };
                char v_mid[4096] = { 0 };
                memcpy(k_mid, s1_close + 1, k_mid_len);
                memcpy(v_mid, t1_close + 1, v_mid_len);
                trim_str(k_mid);
                trim_str(v_mid);
                if (k_mid[0] != '\0' && v_mid[0] != '\0') {
                    insert_translation_ex(k_mid, cond, scale, v_mid, FALSE);
                    (*p_loaded)++;
                }
            }
        }
    }

    /* 3. Tokenize <cmd ...> (Prompt after controller button icons) - Exclude short particles/punctuation */
    const char* cmd_pos = strstr(orig_in, "<cmd");
    if (cmd_pos) {
        const char* last_gt = strrchr(cmd_pos, '>');
        if (last_gt && *(last_gt + 1) != '\0') {
            char k_cmd_post[4096] = { 0 };
            strncpy(k_cmd_post, last_gt + 1, sizeof(k_cmd_post) - 1);
            trim_str(k_cmd_post);
            /* Only index meaningful phrases (at least 6 bytes), never bare particles like で、, か, で, に, etc. */
            if (strlen(k_cmd_post) >= 6 &&
                strcmp(k_cmd_post, "で、") != 0 &&
                strcmp(k_cmd_post, "か") != 0 &&
                strcmp(k_cmd_post, "で") != 0 &&
                strcmp(k_cmd_post, "に") != 0 &&
                strcmp(k_cmd_post, "を") != 0 &&
                strcmp(k_cmd_post, "は") != 0 &&
                strcmp(k_cmd_post, "と") != 0) {
                const char* trans_cmd = strstr(trans_in, "<cmd");
                const char* trans_last_gt = trans_cmd ? strrchr(trans_cmd, '>') : NULL;
                const char* v_after = trans_last_gt ? (trans_last_gt + 1) : trans_in;
                char v_cmd_post[4096] = { 0 };
                strncpy(v_cmd_post, v_after, sizeof(v_cmd_post) - 1);
                trim_str(v_cmd_post);
                if (v_cmd_post[0] != '\0') {
                    insert_translation_ex(k_cmd_post, cond, scale, v_cmd_post, FALSE);
                    (*p_loaded)++;
                }
            }
        }
    }
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
        char* p = line;
        while (*p == ' ' || *p == '\t') p++;
        if (*p == '#' || *p == ';' || *p == '\r' || *p == '\n' || *p == '\0') continue;
        if (p[0] == '/' && p[1] == '/') continue;

        char* sep = strchr(p, '=');
        if (!sep) continue;

        *sep = '\0';
        char* orig_raw = p;
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

        char trans_with_tags[16384];
        strncpy(trans_with_tags, trans, sizeof(trans_with_tags) - 1);
        trans_with_tags[sizeof(trans_with_tags) - 1] = '\0';
        strip_br_tags(trans_with_tags);

        strip_br_tags(trans);
        strip_dialogue_tags(trans);

        char cond[256] = { 0 };
        float scale = 1.0f;

        /* Extract leading [ANCHOR] if present, e.g. [設定を初期状態に戻します] うん */
        if (orig[0] == '[' && strncmp(orig, "[SCALE:", 7) != 0 && strncmp(orig, "[IF:", 4) != 0) {
            char* tag_end = strchr(orig, ']');
            if (tag_end && *(tag_end + 1) != '\0') {
                size_t clen = tag_end - (orig + 1);
                if (clen > 0 && clen < sizeof(cond)) {
                    memcpy(cond, orig + 1, clen);
                    cond[clen] = '\0';
                }
                char* after = tag_end + 1;
                while (*after == ' ' || *after == '\t') after++;
                memmove(orig, after, strlen(after) + 1);
            }
        }

        /* Extract [IF:...] condition */
        char* if_tag = strstr(orig, "[IF:");
        if (if_tag) {
            char* tag_end = strchr(if_tag, ']');
            if (tag_end) {
                size_t clen = tag_end - (if_tag + 4);
                if (clen > 0 && clen < sizeof(cond)) {
                    memcpy(cond, if_tag + 4, clen);
                    cond[clen] = '\0';
                }
                memset(if_tag, ' ', (tag_end - if_tag + 1));
            }
        }

        /* Extract [SCALE:...] factor */
        char* sc_tag = strstr(orig, "[SCALE:");
        if (sc_tag) {
            char* tag_end = strchr(sc_tag, ']');
            if (tag_end) {
                float sc = (float)atof(sc_tag + 7);
                if (sc > 0.05f && sc < 10.0f) {
                    scale = sc;
                }
                memset(sc_tag, ' ', (tag_end - sc_tag + 1));
            }
        }

        /* Trim trailing whitespace from orig after stripping tags */
        int orig_len = (int)strlen(orig);
        while (orig_len > 0 && (orig[orig_len - 1] == ' ' || orig[orig_len - 1] == '\t')) {
            orig[orig_len - 1] = '\0';
            orig_len--;
        }

        if (orig[0] == '\0') continue;

        insert_translation(orig, cond[0] != '\0' ? cond : NULL, scale, trans);
        loaded++;

        /* Register in Smart Sentence Reassembler (<player>, <dog>, <strong>) */
        register_reassembler_entry(orig, trans_with_tags, cond[0] != '\0' ? cond : NULL, scale);

        /* Auto-tokenize and index tags: <strong>, <c>, <player>, <cmd> */
        tokenize_and_insert_tags(orig, trans_with_tags, cond[0] != '\0' ? cond : NULL, scale, &loaded);

        /* Dual indexing: If orig has tags (e.g. <cmd ...>で、目の前にある), also index clean text */
        if (strchr(orig, '<') && strchr(orig, '>')) {
            char clean_orig[16384];
            strip_xml_tags(clean_orig, orig, sizeof(clean_orig));
            char* co_p = clean_orig;
            while (*co_p == ' ' || *co_p == '\t') co_p++;
            int co_len = (int)strlen(co_p);
            while (co_len > 0 && (co_p[co_len - 1] == ' ' || co_p[co_len - 1] == '\t')) {
                co_p[co_len - 1] = '\0';
                co_len--;
            }
            if (co_len > 0 && strcmp(co_p, orig) != 0) {
                char clean_trans[16384];
                strip_xml_tags(clean_trans, trans, sizeof(clean_trans));
                insert_translation(co_p, cond[0] != '\0' ? cond : NULL, scale, clean_trans);
                loaded++;
            }
        }
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
    log_msg("Loaded %d translation entries, %d reassembler entries (translation.txt and translations folder)", loaded, g_reassembler_count);
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

    update_name_screen_state_and_hotkeys(str);

    EnterCriticalSection(&g_cs);
    g_total_calls++;
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
            unsigned char b2 = *(p + 2);
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
        } else if (*p == 0xEF) {
            unsigned char b1 = *(p + 1);
            unsigned char b2 = *(p + 2);
            if (b1 != 0 && b2 != 0) {
                /* Fullwidth & Halfwidth Forms U+FF00..U+FFEF (excludes PUA 0xEF 0x80..0xA3) */
                if (b1 >= 0xBC && b1 <= 0xBF && b2 >= 0x80 && b2 <= 0xBF) return TRUE;
                p += 2;
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
    (void)source;
    if (!is_safe_str(str, 8192)) return;

    EnterCriticalSection(&g_cs);
    if (!is_missing_seen_or_insert(str)) {
        g_missing_count++;
        if (!g_fmissing_latest) {
            g_fmissing_latest = _wfopen(g_dump_missing_path_w, L"a+");
        }
        char escaped[8192];
        escape_string_for_dump(escaped, sizeof(escaped), str);

        SYSTEMTIME st;
        GetLocalTime(&st);
        if (g_fmissing_latest) {
            fprintf(g_fmissing_latest, "[%04d-%02d-%02d %02d:%02d:%02d] %s\n",
                    st.wYear, st.wMonth, st.wDay,
                    st.wHour, st.wMinute, st.wSecond,
                    escaped);
            fflush(g_fmissing_latest);
        }
        log_msg("[MISSING TEXT] [%04d-%02d-%02d %02d:%02d:%02d] %s",
                st.wYear, st.wMonth, st.wDay,
                st.wHour, st.wMinute, st.wSecond,
                escaped);
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

    /* 1d. Mods\TextDump\database\<basename> */
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
                BOOL found = find_override_file_w(g_fad_runtime_subfiles[i].filename, override_path_w, MAX_PATH, &ext_size);
                if (!found && g_fad_runtime_subfiles[i].alt_filename) {
                    found = find_override_file_w(g_fad_runtime_subfiles[i].alt_filename, override_path_w, MAX_PATH, &ext_size);
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

/* ==================================================================
 * Dynamic Word Replacements in RAM (Village Name Normalization)
 * ================================================================== */
typedef struct {
    const char* pattern;
    size_t pattern_len;
    const char* replacement;
    size_t replacement_len;
} DynamicWordReplacement;

static const DynamicWordReplacement kDynamicWordReplacements[] = {
    /* 1. คาเรกัตสึ -> คากัตสึ */
    { "\xe0\xb8\x84\xe0\xb8\xb2\xe0\xb9\x80\xe0\xb8\xa3\xef\x80\x80\xe0\xb8\x95\xef\x82\xb3", 18,
      "\xe0\xb8\x84\xe0\xb8\xb2\xef\x80\x80\xe0\xb8\x95\xef\x82\xb3", 12 }, /* PUA */
    { "\xe0\xb8\x84\xe0\xb8\xb2\xe0\xb9\x80\xe0\xb8\xa3\xe0\xb8\x81\xe0\xb8\xb1\xe0\xb8\x95\xe0\xb8\xaa\xe0\xb8\xb6", 21,
      "\xe0\xb8\x84\xe0\xb8\xb2\xe0\xb8\x81\xe0\xb8\xb1\xe0\xb8\x95\xe0\xb8\xaa\xe0\xb8\xb6", 15 }, /* Std */

    /* 2. คาเระกัตสึ -> คากัตสึ */
    { "\xe0\xb8\x84\xe0\xb8\xb2\xe0\xb9\x80\xe0\xb8\xa3\xe0\xb8\xb0\xef\x80\x80\xe0\xb8\x95\xef\x82\xb3", 21,
      "\xe0\xb8\x84\xe0\xb8\xb2\xef\x80\x80\xe0\xb8\x95\xef\x82\xb3", 12 }, /* PUA */
    { "\xe0\xb8\x84\xe0\xb8\xb2\xe0\xb9\x80\xe0\xb8\xa3\xe0\xb8\xb0\xe0\xb8\x81\xe0\xb8\xb1\xe0\xb8\x95\xe0\xb8\xaa\xe0\xb8\xb6", 24,
      "\xe0\xb8\x84\xe0\xb8\xb2\xe0\xb8\x81\xe0\xb8\xb1\xe0\xb8\x95\xe0\xb8\xaa\xe0\xb8\xb6", 15 }, /* Std */

    /* 3. คาเรัตสึ -> คากัตสึ */
    { "\xe0\xb8\x84\xe0\xb8\xb2\xe0\xb9\x80\xef\x80\xa2\xe0\xb8\x95\xef\x82\xb3", 15,
      "\xe0\xb8\x84\xe0\xb8\xb2\xef\x80\x80\xe0\xb8\x95\xef\x82\xb3", 12 }, /* PUA */
    { "\xe0\xb8\x84\xe0\xb8\xb2\xe0\xb9\x80\xe0\xb8\xa3\xe0\xb8\xb1\xe0\xb8\x95\xe0\xb8\xaa\xe0\xb8\xb6", 18,
      "\xe0\xb8\x84\xe0\xb8\xb2\xe0\xb8\x81\xe0\xb8\xb1\xe0\xb8\x95\xe0\xb8\xaa\xe0\xb8\xb6", 15 }, /* Std */

    /* 4. คาเระงะสึ -> คากัตสึ */
    { "\xe0\xb8\x84\xe0\xb8\xb2\xe0\xb9\x80\xe0\xb8\xa3\xe0\xb8\xb0\xe0\xb8\x87\xe0\xb8\xb0\xef\x82\xb3", 21,
      "\xe0\xb8\x84\xe0\xb8\xb2\xef\x80\x80\xe0\xb8\x95\xef\x82\xb3", 12 }, /* PUA */
    { "\xe0\xb8\x84\xe0\xb8\xb2\xe0\xb9\x80\xe0\xb8\xa3\xe0\xb8\xb0\xe0\xb8\x87\xe0\xb8\xb0\xe0\xb8\xaa\xe0\xb8\xb6", 24,
      "\xe0\xb8\x84\xe0\xb8\xb2\xe0\xb8\x81\xe0\xb8\xb1\xe0\xb8\x95\xe0\xb8\xaa\xe0\xb8\xb6", 15 }, /* Std */

    /* 5. คาเรงะสึ -> คากัตสึ */
    { "\xe0\xb8\x84\xe0\xb8\xb2\xe0\xb9\x80\xe0\xb8\xa3\xe0\xb8\x87\xe0\xb8\xb0\xef\x82\xb3", 18,
      "\xe0\xb8\x84\xe0\xb8\xb2\xef\x80\x80\xe0\xb8\x95\xef\x82\xb3", 12 }, /* PUA */
    { "\xe0\xb8\x84\xe0\xb8\xb2\xe0\xb9\x80\xe0\xb8\xa3\xe0\xb8\x87\xe0\xb8\xb0\xe0\xb8\xaa\xe0\xb8\xb6", 21,
      "\xe0\xb8\x84\xe0\xb8\xb2\xe0\xb8\x81\xe0\xb8\xb1\xe0\xb8\x95\xe0\xb8\xaa\xe0\xb8\xb6", 15 }, /* Std */

    /* 6. คางัตสึ -> คากัตสึ */
    { "\xe0\xb8\x84\xe0\xb8\xb2\xef\x80\x86\xe0\xb8\x95\xef\x82\xb3", 12,
      "\xe0\xb8\x84\xe0\xb8\xb2\xef\x80\x80\xe0\xb8\x95\xef\x82\xb3", 12 }, /* PUA */
    { "\xe0\xb8\x84\xe0\xb8\xb2\xe0\xb8\x87\xe0\xb8\xb1\xe0\xb8\x95\xe0\xb8\xaa\xe0\xb8\xb6", 15,
      "\xe0\xb8\x84\xe0\xb8\xb2\xe0\xb8\x81\xe0\xb8\xb1\xe0\xb8\x95\xe0\xb8\xaa\xe0\xb8\xb6", 15 }, /* Std */

    /* 7. คะงึสึ -> คากัตสึ */
    { "\xe0\xb8\x84\xe0\xb8\xb0\xef\x82\x90\xef\x82\xb3", 9,
      "\xe0\xb8\x84\xe0\xb8\xb2\xef\x80\x80\xe0\xb8\x95\xef\x82\xb3", 12 }, /* PUA */
    { "\xe0\xb8\x84\xe0\xb8\xb0\xe0\xb8\x87\xe0\xb8\xb6\xe0\xb8\xaa\xe0\xb8\xb6", 12,
      "\xe0\xb8\x84\xe0\xb8\xb2\xe0\xb8\x81\xe0\xb8\xb1\xe0\xb8\x95\xe0\xb8\xaa\xe0\xb8\xb6", 15 }, /* Std */
};

static const char* apply_dynamic_word_replacements(const char* str)
{
    if (!str || str[0] == '\0') return str;

    /* Fast check: all targets start with Thai 'ค' (\xe0\xb8\x84) */
    if (strstr(str, "\xe0\xb8\x84") == NULL) {
        return str;
    }

    /* Check if ANY target is actually present in str before modifying */
    BOOL found_any = FALSE;
    for (size_t i = 0; i < sizeof(kDynamicWordReplacements) / sizeof(kDynamicWordReplacements[0]); i++) {
        if (strstr(str, kDynamicWordReplacements[i].pattern) != NULL) {
            found_any = TRUE;
            break;
        }
    }
    if (!found_any) return str;

    /* Perform replacement into a round-robin buffer */
    #define NUM_REPLACE_BUFS 8
    #define REPLACE_BUF_SIZE 4096
    static char s_rep_bufs[NUM_REPLACE_BUFS][REPLACE_BUF_SIZE];
    static LONG s_rep_idx = 0;

    LONG idx = InterlockedIncrement(&s_rep_idx) & (NUM_REPLACE_BUFS - 1);
    char* dst = s_rep_bufs[idx];
    size_t dst_cap = REPLACE_BUF_SIZE - 1;
    size_t dst_len = 0;

    const char* src = str;
    while (*src && dst_len < dst_cap) {
        BOOL matched = FALSE;
        for (size_t i = 0; i < sizeof(kDynamicWordReplacements) / sizeof(kDynamicWordReplacements[0]); i++) {
            size_t pat_len = kDynamicWordReplacements[i].pattern_len;
            if (strncmp(src, kDynamicWordReplacements[i].pattern, pat_len) == 0) {
                size_t rep_len = kDynamicWordReplacements[i].replacement_len;
                if (dst_len + rep_len <= dst_cap) {
                    memcpy(dst + dst_len, kDynamicWordReplacements[i].replacement, rep_len);
                    dst_len += rep_len;
                }
                src += pat_len;
                matched = TRUE;
                break;
            }
        }
        if (!matched) {
            dst[dst_len++] = *src++;
        }
    }
    dst[dst_len] = '\0';
    return dst;
}

static void hk_putStr(void* this_ptr, const char* str)
{
    process_captured_text(str, "putStr");
    const char* orig_str = str;

    float scale = 1.0f;
    const char* rep = lookup_translation_ex(str, &scale);
    if (rep) {
        InterlockedIncrement64((volatile LONG64*)&g_total_replacements);
        str = rep;
    } else {
        if (has_japanese_utf8(str)) {
            log_missing_text(str, "putStr");
        }
    }

    str = apply_dynamic_word_replacements(str);

    call_with_auto_scale(fp_original_putStr, this_ptr, str, scale);
    record_recent_string(orig_str);
}

static void hk_putStrProp(void* this_ptr, const char* str)
{
    process_captured_text(str, "putStrProp");
    const char* orig_str = str;

    float scale = 1.0f;
    const char* rep = lookup_translation_ex(str, &scale);
    if (rep) {
        InterlockedIncrement64((volatile LONG64*)&g_total_replacements);
        str = rep;
    } else {
        if (has_japanese_utf8(str)) {
            log_missing_text(str, "putStrProp");
        }
    }

    str = apply_dynamic_word_replacements(str);

    call_with_auto_scale(fp_original_putStrProp, this_ptr, str, scale);
    record_recent_string(orig_str);
}

static void hk_putStrAlign(void* this_ptr, const char* str)
{
    process_captured_text(str, "putStrAlign");
    const char* orig_str = str;

    float scale = 1.0f;
    const char* rep = lookup_translation_ex(str, &scale);
    if (rep) {
        InterlockedIncrement64((volatile LONG64*)&g_total_replacements);
        str = rep;
    } else {
        if (has_japanese_utf8(str)) {
            log_missing_text(str, "putStrAlign");
        }
    }

    str = apply_dynamic_word_replacements(str);

    call_with_auto_scale(fp_original_putStrAlign, this_ptr, str, scale);
    record_recent_string(orig_str);
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
    swprintf(g_custom_names_ini_path_w, MAX_PATH, L"%ls\\custom_names.ini", g_mod_dir_w);

    /* Populate UTF-8 versions for display/logging if needed */
    WideCharToMultiByte(CP_UTF8, 0, g_log_path_w, -1, g_log_path, sizeof(g_log_path), NULL, NULL);
    WideCharToMultiByte(CP_UTF8, 0, g_translation_path_w, -1, g_translation_path, sizeof(g_translation_path), NULL, NULL);
    WideCharToMultiByte(CP_UTF8, 0, g_dump_missing_path_w, -1, g_dump_missing_path, sizeof(g_dump_missing_path), NULL, NULL);
    WideCharToMultiByte(CP_UTF8, 0, g_custom_names_ini_path_w, -1, g_custom_names_ini_path, sizeof(g_custom_names_ini_path), NULL, NULL);
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

    /* 4. Load translation file & saved custom names */
    load_translation_file();
    load_custom_names_ini();

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
            log_msg("Status: Unique texts=%d, Missing JP=%d, Replacements applied=%llu, Total calls=%llu",
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
        if (g_fmissing) { fclose(g_fmissing); g_fmissing = NULL; }
        if (g_fmissing_latest) { fclose(g_fmissing_latest); g_fmissing_latest = NULL; }
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
