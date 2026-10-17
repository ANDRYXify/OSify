/* ==============================================================================
 * OSify Bare-Metal Linker Script (sistema/nucleo/kernel/boot/kernel.ld)
 * ==============================================================================
 * Ingegnerizzato da Andrea Taliento (ANDRYXify) per OSify
 * Allinea le sezioni a 4KB e imposta l'indirizzo di caricamento a 1MB (0x100000).
 * ==============================================================================
 */

ENTRY(_start)

SECTIONS
{
    . = 1M;

    .boot : ALIGN(4K)
    {
        *(.multiboot)
    }

    .text : ALIGN(4K)
    {
        *(.text)
        *(.text.*)
    }

    .rodata : ALIGN(4K)
    {
        *(.rodata)
        *(.rodata.*)
    }

    .data : ALIGN(4K)
    {
        *(.data)
        *(.data.*)
    }

    .bss : ALIGN(4K)
    {
        *(COMMON)
        *(.bss)
        *(.bss.*)
    }

    /DISCARD/ :
    {
        *(.comment)
        *(.note.gnu.build-id)
    }
}
