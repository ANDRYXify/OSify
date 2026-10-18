/* ==============================================================================
 * OSify Virtual Capture Card Subsystem (osify_capture_card.h)
 * ==============================================================================
 * Ingegnerizzato da Andrea Taliento (ANDRYXify) per OSify
 * Scheda di Acquisizione Video Integrata Diretta (Senza Hardware Esterno):
 * cattura il Framebuffer lineare al silicio a 60 FPS con ring-buffer DMA
 * per streaming, registrazione lossless e loopback a latenza zero.
 * ==============================================================================
 */

#ifndef OSIFY_CAPTURE_CARD_H
#define OSIFY_CAPTURE_CARD_H

#include <stdint.h>
#include <stdbool.h>
#include <stddef.h>
#include "osify_kernel.h"

/* Configurazione e Stato della Scheda di Acquisizione Virtuale */
typedef struct {
    bool     is_active;             /* Se l'acquisizione e in corso */
    uint32_t width;                 /* Risoluzione orizzontale */
    uint32_t height;                /* Risoluzione verticale */
    uint32_t fps;                   /* Frame rate target (es. 60 FPS) */
    uint64_t total_frames_captured; /* Contatore cumulativo frame */
    uint64_t total_bytes_streamed;  /* Byte generati */
    uint32_t bitrate_mbps;          /* Bitrate istantaneo calcolato */
    uint32_t drop_frames;           /* Frame persi (0 in modalita DMA) */
    bool     is_streaming_loopback; /* Stream verso stack di rete / UEM */
} osify_capture_state_t;

/* Inizializzazione della Scheda di Acquisizione Virtuale */
void osify_capture_init(uint32_t width, uint32_t height, uint32_t fps);

/* Controllo Acquisizione */
bool osify_capture_start(void);
void osify_capture_stop(void);

/* Tap di acquisizione: invocato a ogni ciclo di frame del Display Server */
void osify_capture_process_frame(const osify_framebuffer_t *fb);

/* Accesso allo Stato */
const osify_capture_state_t *osify_capture_get_state(void);

#endif /* OSIFY_CAPTURE_CARD_H */
