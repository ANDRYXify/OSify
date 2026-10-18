#include <windows.h>

/* ==============================================================================
 * OSify Real Windows PE Application (uem/binari_reali/win_compat.c)
 * ==============================================================================
 * Binario Windows PE32 autentico compilato con MinGW-w64.
 * Header MZ, PE Signature, sezioni .text, .rdata, .data, tabella import USER32/KERNEL32.
 * ==============================================================================
 */

int WINAPI WinMain(HINSTANCE hInstance, HINSTANCE hPrevInstance, LPSTR lpCmdLine, int nCmdShow) {
    (void)hInstance;
    (void)hPrevInstance;
    (void)lpCmdLine;
    (void)nCmdShow;

    const char *title = "OSify UEM — Windows NT Subsystem";
    const char *msg = "OSify Universal Execution Module\n\n"
                      "Binario Windows PE32 autentico in esecuzione!\n"
                      "Kernel: OSify Sovereign Hybrid Core\n"
                      "Subsystem: Win32 PE GUI (Kernel32.dll / User32.dll)\n"
                      "Architettura: x86_32 / x86_64\n"
                      "Stato: Operativo al 100% senza emulatori terzi.";

    MessageBoxA(NULL, msg, title, MB_OK | MB_ICONINFORMATION);
    return 0;
}
