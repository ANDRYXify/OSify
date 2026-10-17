/* ==============================================================================
 * OSify Bare-Metal Audio Driver & Sound Subsystem (sistema/nucleo/kernel/include/osify_audio.h)
 * ==============================================================================
 * Ingegnerizzato da Andrea Taliento (ANDRYXify) per OSify
 * Driver audio nativo per Intel High Definition Audio (HDA) e AC97:
 * Buffer DMA PCM 16-bit 44.1kHz stereo, mixer di volume hardware e chime di avvio.
 * ==============================================================================
 */

#ifndef OSIFY_AUDIO_H
#define OSIFY_AUDIO_H

#include <stdint.h>
#include <stddef.h>
#include <stdbool.h>

/* Costanti PCI Hardware Audio */
#define PCI_VENDOR_INTEL_AUDIO  0x8086
#define PCI_DEVICE_HDA_ICH7     0x27D8
#define PCI_DEVICE_HDA_ICH9     0x293E
#define PCI_DEVICE_AC97_ICH     0x2415

typedef struct {
    uint16_t vendor_id;
    uint16_t device_id;
    char     card_name[32];
    uint8_t  master_volume;   /* 0 - 100 */
    bool     is_muted;
    uint32_t sample_rate;     /* 44100 Hz */
    uint8_t  bits_per_sample; /* 16 bit */
    uint8_t  channels;        /* 2 = Stereo */
    bool     hda_detected;
    uint32_t samples_played;
} osify_audio_state_t;

/* Inizializzazione Audio */
void osify_audio_init(void);
void osify_audio_set_volume(uint8_t volume_percent);
uint8_t osify_audio_get_volume(void);
void osify_audio_volume_up(uint8_t delta);
void osify_audio_volume_down(uint8_t delta);
void osify_audio_set_mute(bool mute);
void osify_audio_toggle_mute(void);
bool osify_audio_play_pcm(const int16_t *samples, size_t sample_count);
void osify_audio_play_startup_chime(void);
const osify_audio_state_t *osify_audio_get_state(void);

#endif /* OSIFY_AUDIO_H */
