#ifndef SPEEDHACK_H
#define SPEEDHACK_H

#include <windows.h>

#ifdef __cplusplus
extern "C" {
#endif

/* Install Speedhack hooks on QueryPerformanceCounter and GetTickCount via MinHook */
BOOL speedhack_install_hooks(void (*log_fn)(const char* fmt, ...));

/* Smoothly adjust the game speed multiplier (1.0 = normal, 2.0 = 2x, 0.5 = 0.5x) */
void speedhack_set_speed(double factor);

/* Get the current speed multiplier */
double speedhack_get_speed(void);

/* Restore original timing APIs */
void speedhack_cleanup(void);

#ifdef __cplusplus
}
#endif

#endif /* SPEEDHACK_H */
