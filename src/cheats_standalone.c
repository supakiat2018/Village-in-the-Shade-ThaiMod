/* cheats_standalone.c - Standalone Cheats Plugin for Village in the Shade
 * Contains purely in-memory cheat engine injections and pointer locks.
 * No localization, no font hooks, no VFS.
 */

#include <windows.h>
#include <stdio.h>
#include <stdarg.h>
#include "cheats.h"

static HINSTANCE g_hinst = NULL;
static wchar_t g_dll_dir_w[MAX_PATH] = { 0 };
static wchar_t g_game_dir_w[MAX_PATH] = { 0 };
static FILE* g_flog = NULL;

static void standalone_log(const char* fmt, ...)
{
    if (!g_flog && g_dll_dir_w[0]) {
        wchar_t log_path[MAX_PATH];
        swprintf(log_path, MAX_PATH, L"%ls\\cheats.log", g_dll_dir_w);
        g_flog = _wfopen(log_path, L"a+");
    }
    if (g_flog) {
        SYSTEMTIME st;
        GetLocalTime(&st);
        fprintf(g_flog, "[%02d:%02d:%02d.%03d] ", st.wHour, st.wMinute, st.wSecond, st.wMilliseconds);
        va_list args;
        va_start(args, fmt);
        vfprintf(g_flog, fmt, args);
        va_end(args);
        fprintf(g_flog, "\n");
        fflush(g_flog);
    }
}

static DWORD WINAPI cheat_worker_thread(LPVOID param)
{
    (void)param;
    Sleep(2000); /* Wait for game executable to unpack/load PE sections */
    standalone_log("[Cheats] Standalone Cheats Plugin v1.20 initialized.");
    cheats_init(g_game_dir_w, g_dll_dir_w, standalone_log);

    while (1) {
        Sleep(1000);
        cheats_tick();
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

        /* Resolve DLL directory (Mods\Cheats) */
        wchar_t path[MAX_PATH];
        GetModuleFileNameW(hinst, path, MAX_PATH);
        wchar_t* last_slash = wcsrchr(path, L'\\');
        if (last_slash) *last_slash = L'\0';
        wcscpy(g_dll_dir_w, path);

        /* Game root directory */
        GetModuleFileNameW(NULL, path, MAX_PATH);
        last_slash = wcsrchr(path, L'\\');
        if (last_slash) *last_slash = L'\0';
        wcscpy(g_game_dir_w, path);

        HANDLE hThread = CreateThread(NULL, 0, cheat_worker_thread, NULL, 0, NULL);
        if (hThread) CloseHandle(hThread);
    } else if (reason == DLL_PROCESS_DETACH) {
        cheats_cleanup();
        if (g_flog) {
            fclose(g_flog);
            g_flog = NULL;
        }
    }
    return TRUE;
}
