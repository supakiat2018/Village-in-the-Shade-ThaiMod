/* crash_doctor.c - Standalone Crash Doctor & Black Box Diagnostic Plugin
 * Designed specifically for Village in the Shade (ほのぐらしの庭)
 * Used ONLY for local debugging and diagnostic testing (NEVER distributed in release).
 *
 * Capabilities:
 * 1. Hooks ucrtbase.dll!abort to intercept 0xc0000409 / __fastfail
 * 2. Captures full 64-bit callstack with Module Name and Offset
 * 3. Intercepts CRT invalid parameter handler and pure virtual calls
 * 4. Captures Vectored and Unhandled Exceptions
 * 5. Writes human-readable crash_doctor.log and full MiniDump crash_doctor.dmp
 */

#include <windows.h>
#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
#include <dbghelp.h>

#pragma comment(lib, "dbghelp.lib")
#pragma comment(lib, "user32.lib")

static wchar_t g_game_dir_w[MAX_PATH] = { 0 };
static wchar_t g_log_path_w[MAX_PATH] = { 0 };
static wchar_t g_dmp_path_w[MAX_PATH] = { 0 };
static CRITICAL_SECTION g_doc_cs;
static BOOL g_crash_handled = FALSE;

typedef BOOL (WINAPI *pfn_MiniDumpWriteDump)(
    HANDLE hProcess,
    DWORD ProcessId,
    HANDLE hFile,
    MINIDUMP_TYPE DumpType,
    PMINIDUMP_EXCEPTION_INFORMATION ExceptionParam,
    PMINIDUMP_USER_STREAM_INFORMATION UserStreamParam,
    PMINIDUMP_CALLBACK_INFORMATION CallbackParam
);

static void write_doctor_log(const char* text)
{
    EnterCriticalSection(&g_doc_cs);
    FILE* f = _wfopen(g_log_path_w, L"a+");
    if (f) {
        SYSTEMTIME st;
        GetLocalTime(&st);
        fprintf(f, "[%02d:%02d:%02d.%03d] %s\n",
                st.wHour, st.wMinute, st.wSecond, st.wMilliseconds, text);
        fflush(f);
        fclose(f);
    }
    LeaveCriticalSection(&g_doc_cs);
}

static void log_callstack(PCONTEXT pContext, const char* reason)
{
    char header[512];
    snprintf(header, sizeof(header), "================================================================\n"
                                     "*** CRASH DOCTOR CAUGHT FATAL EVENT ***\n"
                                     "Reason: %s\n"
                                     "Process ID: %lu (0x%lX), Thread ID: %lu (0x%lX)\n"
                                     "----------------------------------------------------------------",
             reason, (unsigned long)GetCurrentProcessId(), (unsigned long)GetCurrentProcessId(),
             (unsigned long)GetCurrentThreadId(), (unsigned long)GetCurrentThreadId());
    write_doctor_log(header);

    void* stack[64];
    USHORT frames = CaptureStackBackTrace(0, 64, stack, NULL);

    write_doctor_log("Call Stack Frames (most recent first):");
    for (USHORT i = 0; i < frames; i++) {
        uintptr_t addr = (uintptr_t)stack[i];
        HMODULE hMod = NULL;
        GetModuleHandleExA(GET_MODULE_HANDLE_EX_FLAG_FROM_ADDRESS |
                           GET_MODULE_HANDLE_EX_FLAG_UNCHANGED_REFCOUNT,
                           (LPCSTR)addr, &hMod);
        char mod_name[MAX_PATH] = "UnknownModule";
        uintptr_t rva = addr;
        if (hMod) {
            GetModuleFileNameA(hMod, mod_name, sizeof(mod_name));
            char* slash = strrchr(mod_name, '\\');
            if (slash) memmove(mod_name, slash + 1, strlen(slash));
            rva = addr - (uintptr_t)hMod;
        }

        char frame_buf[512];
        snprintf(frame_buf, sizeof(frame_buf), "  [%02d] 0x%p -> %s + 0x%llX",
                 i, (void*)addr, mod_name, (unsigned long long)rva);
        write_doctor_log(frame_buf);
    }
    write_doctor_log("================================================================");
}

static void create_minidump(PEXCEPTION_POINTERS pExceptionInfo)
{
    HMODULE hDbgHelp = LoadLibraryA("dbghelp.dll");
    if (!hDbgHelp) return;

    pfn_MiniDumpWriteDump pDump = (pfn_MiniDumpWriteDump)GetProcAddress(hDbgHelp, "MiniDumpWriteDump");
    if (!pDump) {
        FreeLibrary(hDbgHelp);
        return;
    }

    HANDLE hFile = CreateFileW(g_dmp_path_w, GENERIC_WRITE, FILE_SHARE_READ, NULL,
                               CREATE_ALWAYS, FILE_ATTRIBUTE_NORMAL, NULL);
    if (hFile != INVALID_HANDLE_VALUE) {
        MINIDUMP_EXCEPTION_INFORMATION mei;
        mei.ThreadId = GetCurrentThreadId();
        mei.ExceptionPointers = pExceptionInfo;
        mei.ClientPointers = FALSE;

        BOOL ok = pDump(GetCurrentProcess(), GetCurrentProcessId(), hFile,
                        (MINIDUMP_TYPE)(MiniDumpWithDataSegs | MiniDumpWithIndirectlyReferencedMemory | MiniDumpWithProcessThreadData),
                        pExceptionInfo ? &mei : NULL, NULL, NULL);
        CloseHandle(hFile);

        if (ok) {
            write_doctor_log("[DUMP] MiniDump generated successfully: crash_doctor.dmp");
        } else {
            write_doctor_log("[DUMP] Failed to write MiniDump.");
        }
    }
    FreeLibrary(hDbgHelp);
}

/* ==================================================================
 * Detour Hook for ucrtbase.dll!abort
 * ================================================================== */
static uint8_t g_orig_abort_bytes[16] = { 0 };
static void* g_abort_addr = NULL;

static void DoctorAbortHook(void)
{
    if (!g_crash_handled) {
        g_crash_handled = TRUE;
        log_callstack(NULL, "ucrtbase.dll!abort() was called (Exception 0xc0000409 averted / captured)");
        create_minidump(NULL);

        char msg[1024];
        snprintf(msg, sizeof(msg),
                 "[CRASH DOCTOR DETECTED ABORT]\n\n"
                 "The game engine or CRT requested abort()!\n"
                 "Detailed diagnostic log saved to:\n  crash_doctor.log\n"
                 "MiniDump saved to:\n  crash_doctor.dmp\n\n"
                 "Review crash_doctor.log to identify the faulting function.");
        MessageBoxA(NULL, msg, "Village in the Shade - Crash Doctor", MB_ICONERROR | MB_OK);
    }

    /* Restore original bytes and proceed with exit */
    DWORD old_protect;
    VirtualProtect(g_abort_addr, sizeof(g_orig_abort_bytes), PAGE_EXECUTE_READWRITE, &old_protect);
    memcpy(g_abort_addr, g_orig_abort_bytes, sizeof(g_orig_abort_bytes));
    VirtualProtect(g_abort_addr, sizeof(g_orig_abort_bytes), old_protect, &old_protect);

    ExitProcess(0xc0000409);
}

/* ==================================================================
 * CRT Handlers
 * ================================================================== */
static void DoctorInvalidParamHandler(
    const wchar_t* expression,
    const wchar_t* function,
    const wchar_t* file,
    unsigned int line,
    uintptr_t pReserved)
{
    (void)pReserved;
    char buf[1024];
    snprintf(buf, sizeof(buf),
             "CRT Invalid Parameter Detected!\n  Expression: %ls\n  Function: %ls\n  File: %ls\n  Line: %u",
             expression ? expression : L"(none)",
             function ? function : L"(none)",
             file ? file : L"(none)", line);
    write_doctor_log(buf);
    log_callstack(NULL, "CRT Invalid Parameter Handler");
    create_minidump(NULL);
}

static void DoctorPureCallHandler(void)
{
    write_doctor_log("CRT Pure Virtual Function Call Detected!");
    log_callstack(NULL, "CRT Pure Virtual Call");
    create_minidump(NULL);
}

/* ==================================================================
 * Vectored Exception Handler
 * ================================================================== */
static LONG WINAPI DoctorVectoredHandler(PEXCEPTION_POINTERS pExceptionInfo)
{
    if (!pExceptionInfo || !pExceptionInfo->ExceptionRecord) return EXCEPTION_CONTINUE_SEARCH;

    DWORD code = pExceptionInfo->ExceptionRecord->ExceptionCode;

    /* Ignore benign debug / RPC exceptions */
    if (code == 0x406D1388 || /* SetThreadName */
        code == 0x000006BA || /* RPC_S_SERVER_UNAVAILABLE */
        code == 0x40010006 || /* OutputDebugString */
        code == DBG_PRINTEXCEPTION_C) {
        return EXCEPTION_CONTINUE_SEARCH;
    }

    /* Target hard crash codes */
    if (code == EXCEPTION_ACCESS_VIOLATION ||
        code == 0xC0000409 || /* STATUS_STACK_BUFFER_OVERRUN / __fastfail */
        code == EXCEPTION_ILLEGAL_INSTRUCTION ||
        code == EXCEPTION_STACK_OVERFLOW ||
        code == 0xE06D7363) { /* C++ Exception */

        /* Only report once for the primary fatal event */
        if (!g_crash_handled && code != 0xE06D7363) {
            char reason[256];
            snprintf(reason, sizeof(reason), "Exception 0x%08lX at 0x%p",
                     code, pExceptionInfo->ExceptionRecord->ExceptionAddress);
            write_doctor_log(reason);
            log_callstack(pExceptionInfo->ContextRecord, reason);
            create_minidump(pExceptionInfo);
        }
    }

    return EXCEPTION_CONTINUE_SEARCH;
}

static void hook_crt_abort(void)
{
    HMODULE hUcrt = GetModuleHandleA("ucrtbase.dll");
    if (!hUcrt) hUcrt = LoadLibraryA("ucrtbase.dll");
    if (!hUcrt) return;

    g_abort_addr = (void*)GetProcAddress(hUcrt, "abort");
    if (!g_abort_addr) return;

    DWORD old_protect;
    if (VirtualProtect(g_abort_addr, 14, PAGE_EXECUTE_READWRITE, &old_protect)) {
        memcpy(g_orig_abort_bytes, g_abort_addr, 14);

        /* 64-bit absolute jmp detour:
         * FF 25 00 00 00 00 [64-bit target address] (14 bytes)
         */
        uint8_t jmp_code[14] = {
            0xFF, 0x25, 0x00, 0x00, 0x00, 0x00
        };
        uintptr_t target = (uintptr_t)DoctorAbortHook;
        memcpy(jmp_code + 6, &target, sizeof(target));

        memcpy(g_abort_addr, jmp_code, 14);
        VirtualProtect(g_abort_addr, 14, old_protect, &old_protect);
        FlushInstructionCache(GetCurrentProcess(), g_abort_addr, 14);

        write_doctor_log("[INIT] Successfully hooked ucrtbase.dll!abort()");
    }
}

/* ==================================================================
 * Plugin Entry Point
 * ================================================================== */
BOOL WINAPI DllMain(HINSTANCE hinst, DWORD reason, LPVOID reserved)
{
    (void)hinst;
    (void)reserved;
    if (reason == DLL_PROCESS_ATTACH) {
        DisableThreadLibraryCalls(hinst);
        InitializeCriticalSection(&g_doc_cs);

        GetModuleFileNameW(NULL, g_game_dir_w, MAX_PATH);
        wchar_t* slash = wcsrchr(g_game_dir_w, L'\\');
        if (slash) *slash = L'\0';

        swprintf(g_log_path_w, MAX_PATH, L"%ls\\crash_doctor.log", g_game_dir_w);
        swprintf(g_dmp_path_w, MAX_PATH, L"%ls\\crash_doctor.dmp", g_game_dir_w);

        write_doctor_log("================================================================");
        write_doctor_log("Crash Doctor Diagnostic Plugin v1.0 Active (Dev/Testing Mode)");
        write_doctor_log("================================================================");

        /* 1. Register CRT handlers */
        _set_invalid_parameter_handler(DoctorInvalidParamHandler);
        _set_purecall_handler(DoctorPureCallHandler);

        /* 2. Hook ucrtbase.dll!abort */
        hook_crt_abort();

        /* 3. Register Vectored Exception Handler */
        AddVectoredExceptionHandler(1, DoctorVectoredHandler);

        write_doctor_log("[INIT] All diagnostic interceptors successfully registered.");
    } else if (reason == DLL_PROCESS_DETACH) {
        DeleteCriticalSection(&g_doc_cs);
    }
    return TRUE;
}
