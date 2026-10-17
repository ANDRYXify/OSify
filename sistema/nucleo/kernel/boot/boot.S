/* ==============================================================================
 * OSify Multiboot & Bare-Metal Bootstrap (sistema/nucleo/kernel/boot/boot.S)
 * ==============================================================================
 * Ingegnerizzato da Andrea Taliento (ANDRYXify) per OSify
 * Entry point primario bare-metal compatibile con specifiche Multiboot.
 * ==============================================================================
 */

#define MB_MAGIC    0x1BADB002
#define MB_FLAGS    0x00000003 /* ALIGN (1<<0) | MEMINFO (1<<1) */
#define MB_CHECKSUM -(MB_MAGIC + MB_FLAGS)

.section .multiboot
.align 4
.long MB_MAGIC
.long MB_FLAGS
.long MB_CHECKSUM

.section .bss
.align 16
stack_bottom:
.skip 16384 /* 16 KB Stack Kernel */
stack_top:

.section .text
.global _start
.type _start, @function

_start:
    /* Disabilita gli interrupt durante il bootstrap iniziale */
    cli

    /* Imposta lo stack pointer del kernel */
    mov $stack_top, %esp

    /* Passa magic (in EAX) e boot_info (in EBX) come parametri C */
    push %ebx
    push %eax

    /* Salto all'entry point principale C del Kernel OSify */
    call osify_kernel_main

    /* Se il kernel ritorna, arresta la CPU in modo sicuro */
halt_loop:
    cli
    hlt
    jmp halt_loop

.size _start, . - _start
