/* proxy_winmm.c - Lightweight WinMM Proxy Loader for Village in the Shade Thai Mod
 * Forwards all winmm.dll functions to C:\Windows\System32\winmm.dll
 * Automatically loads Mods\TextDump\text_dump.dll on startup.
 */

#include <windows.h>
#include <stdio.h>

static void log_proxy(const wchar_t* game_dir, const char* msg)
{
    wchar_t log_path[MAX_PATH];
    swprintf(log_path, MAX_PATH, L"%ls\\winmm_proxy.log", game_dir);
    FILE* f = _wfopen(log_path, L"a+");
    if (f) {
        SYSTEMTIME st;
        GetLocalTime(&st);
        fprintf(f, "[%02d:%02d:%02d.%03d] [winmm_proxy] %s\n",
                st.wHour, st.wMinute, st.wSecond, st.wMilliseconds, msg);
        fclose(f);
    }
}

static DWORD WINAPI loader_thread(LPVOID param)
{
    (void)param;
    wchar_t exe_path[MAX_PATH];
    GetModuleFileNameW(NULL, exe_path, MAX_PATH);
    wchar_t* last_slash = wcsrchr(exe_path, L'\\');
    if (last_slash) *last_slash = L'\0';

    log_proxy(exe_path, "WinMM proxy bridge loaded.");

    /* Candidates for text_dump.dll */
    wchar_t target_dll[MAX_PATH];
    swprintf(target_dll, MAX_PATH, L"%ls\\Mods\\TextDump\\text_dump.dll", exe_path);

    if (GetFileAttributesW(target_dll) == INVALID_FILE_ATTRIBUTES) {
        /* Fallback 1: Mods\text_dump.dll */
        swprintf(target_dll, MAX_PATH, L"%ls\\Mods\\text_dump.dll", exe_path);
    }
    if (GetFileAttributesW(target_dll) == INVALID_FILE_ATTRIBUTES) {
        /* Fallback 2: text_dump.dll beside exe */
        swprintf(target_dll, MAX_PATH, L"%ls\\text_dump.dll", exe_path);
    }

    if (GetFileAttributesW(target_dll) != INVALID_FILE_ATTRIBUTES) {
        char msg[512];
        snprintf(msg, sizeof(msg), "Loading mod DLL: %ls", target_dll);
        log_proxy(exe_path, msg);

        HMODULE hMod = LoadLibraryW(target_dll);
        if (hMod) {
            snprintf(msg, sizeof(msg), "Loaded mod DLL successfully (Handle=%p)", (void*)hMod);
            log_proxy(exe_path, msg);

            typedef void (*pfn_mod_init)(void);
            pfn_mod_init init_fn = (pfn_mod_init)GetProcAddress(hMod, "mod_init");
            if (init_fn) {
                init_fn();
                log_proxy(exe_path, "Invoked mod_init()");
            }
        } else {
            DWORD err = GetLastError();
            snprintf(msg, sizeof(msg), "Failed to load mod DLL (Error=%lu)", err);
            log_proxy(exe_path, msg);
        }
    } else {
        log_proxy(exe_path, "Mod DLL not found in Mods\\TextDump, Mods, or game root.");
    }

    return 0;
}

BOOL WINAPI DllMain(HINSTANCE hinst, DWORD reason, LPVOID reserved)
{
    (void)reserved;
    if (reason == DLL_PROCESS_ATTACH) {
        DisableThreadLibraryCalls(hinst);
        /* Spawn thread so loader lock is never held */
        HANDLE hThread = CreateThread(NULL, 0, loader_thread, (LPVOID)hinst, 0, NULL);
        if (hThread) CloseHandle(hThread);
    }
    return TRUE;
}
