/* speedhack.c - Smooth High-Precision Speedhack Hook for Village in the Shade */
#include "speedhack.h"
#include "minhook-master/include/MinHook.h"
#include <stdio.h>

typedef BOOL (WINAPI *pfn_QPC)(LARGE_INTEGER* lpPerformanceCount);
typedef DWORD (WINAPI *pfn_GTC)(void);

static pfn_QPC fp_orig_QPC = NULL;
static pfn_GTC fp_orig_GTC = NULL;

static double g_speed_factor = 1.0;
static CRITICAL_SECTION g_speed_cs;
static volatile BOOL g_speed_cs_inited = FALSE;

static LARGE_INTEGER g_qpc_base_real = { 0 };
static LARGE_INTEGER g_qpc_base_virt = { 0 };

static DWORD g_gtc_base_real = 0;
static DWORD g_gtc_base_virt = 0;

static void (*g_log)(const char* fmt, ...) = NULL;

static BOOL WINAPI hk_QueryPerformanceCounter(LARGE_INTEGER* lpPerformanceCount)
{
    if (!lpPerformanceCount) return FALSE;
    LARGE_INTEGER real;
    if (!fp_orig_QPC(&real)) return FALSE;

    if (!g_speed_cs_inited) {
        *lpPerformanceCount = real;
        return TRUE;
    }

    EnterCriticalSection(&g_speed_cs);
    if (g_speed_factor == 1.0 && g_qpc_base_real.QuadPart == 0) {
        LeaveCriticalSection(&g_speed_cs);
        *lpPerformanceCount = real;
        return TRUE;
    }

    if (g_qpc_base_real.QuadPart == 0) {
        g_qpc_base_real = real;
        g_qpc_base_virt = real;
    }

    LONGLONG real_delta = real.QuadPart - g_qpc_base_real.QuadPart;
    LONGLONG virt_delta = (LONGLONG)(real_delta * g_speed_factor);
    lpPerformanceCount->QuadPart = g_qpc_base_virt.QuadPart + virt_delta;
    LeaveCriticalSection(&g_speed_cs);

    return TRUE;
}

static DWORD WINAPI hk_GetTickCount(void)
{
    DWORD real = fp_orig_GTC();
    if (!g_speed_cs_inited) return real;

    EnterCriticalSection(&g_speed_cs);
    if (g_speed_factor == 1.0 && g_gtc_base_real == 0) {
        LeaveCriticalSection(&g_speed_cs);
        return real;
    }

    if (g_gtc_base_real == 0) {
        g_gtc_base_real = real;
        g_gtc_base_virt = real;
    }

    DWORD real_delta = real - g_gtc_base_real;
    DWORD virt_delta = (DWORD)(real_delta * g_speed_factor);
    DWORD result = g_gtc_base_virt + virt_delta;
    LeaveCriticalSection(&g_speed_cs);

    return result;
}

BOOL speedhack_install_hooks(void (*log_fn)(const char* fmt, ...))
{
    g_log = log_fn;
    if (!g_speed_cs_inited) {
        InitializeCriticalSection(&g_speed_cs);
        g_speed_cs_inited = TRUE;
    }

    HMODULE hK32 = GetModuleHandleA("kernel32.dll");
    if (!hK32) return FALSE;

    FARPROC pQPC = GetProcAddress(hK32, "QueryPerformanceCounter");
    if (pQPC) {
        if (MH_CreateHook((LPVOID)pQPC, (LPVOID)&hk_QueryPerformanceCounter, (LPVOID*)&fp_orig_QPC) == MH_OK) {
            if (MH_EnableHook((LPVOID)pQPC) == MH_OK) {
                if (g_log) g_log("[Speedhack] Hooked QueryPerformanceCounter successfully!");
            }
        }
    }

    FARPROC pGTC = GetProcAddress(hK32, "GetTickCount");
    if (pGTC) {
        if (MH_CreateHook((LPVOID)pGTC, (LPVOID)&hk_GetTickCount, (LPVOID*)&fp_orig_GTC) == MH_OK) {
            if (MH_EnableHook((LPVOID)pGTC) == MH_OK) {
                if (g_log) g_log("[Speedhack] Hooked GetTickCount successfully!");
            }
        }
    }

    return TRUE;
}

void speedhack_set_speed(double factor)
{
    if (factor <= 0.05) factor = 0.05;
    if (factor > 50.0) factor = 50.0;

    if (!g_speed_cs_inited) return;

    EnterCriticalSection(&g_speed_cs);
    LARGE_INTEGER cur_real_qpc;
    if (fp_orig_QPC && fp_orig_QPC(&cur_real_qpc)) {
        if (g_qpc_base_real.QuadPart == 0) {
            g_qpc_base_real = cur_real_qpc;
            g_qpc_base_virt = cur_real_qpc;
        } else {
            LONGLONG real_delta = cur_real_qpc.QuadPart - g_qpc_base_real.QuadPart;
            LONGLONG virt_delta = (LONGLONG)(real_delta * g_speed_factor);
            g_qpc_base_virt.QuadPart += virt_delta;
            g_qpc_base_real = cur_real_qpc;
        }
    }

    if (fp_orig_GTC) {
        DWORD cur_real_gtc = fp_orig_GTC();
        if (g_gtc_base_real == 0) {
            g_gtc_base_real = cur_real_gtc;
            g_gtc_base_virt = cur_real_gtc;
        } else {
            DWORD real_delta = cur_real_gtc - g_gtc_base_real;
            DWORD virt_delta = (DWORD)(real_delta * g_speed_factor);
            g_gtc_base_virt += virt_delta;
            g_gtc_base_real = cur_real_gtc;
        }
    }

    g_speed_factor = factor;
    LeaveCriticalSection(&g_speed_cs);
}

double speedhack_get_speed(void)
{
    return g_speed_factor;
}

void speedhack_cleanup(void)
{
    speedhack_set_speed(1.0);
    HMODULE hK32 = GetModuleHandleA("kernel32.dll");
    if (hK32) {
        FARPROC pQPC = GetProcAddress(hK32, "QueryPerformanceCounter");
        if (pQPC) MH_DisableHook((LPVOID)pQPC);
        FARPROC pGTC = GetProcAddress(hK32, "GetTickCount");
        if (pGTC) MH_DisableHook((LPVOID)pGTC);
    }
}
