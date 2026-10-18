/* ==============================================================================
 * OSify Multiboot & Bare-Metal Bootstrap (sistema/nucleo/kernel/boot/boot.S)
 * ==============================================================================
 * Ingegnerizzato da Andrea Taliento (ANDRYXify) per OSify
 * Entry point primario bare-metal compatibile con specifiche Multiboot.
 * ==============================================================================
 */

#define MB_MAGIC    0x1BADB002
#define MB_FLAGS    0x00000007 /* ALIGN (1<<0) | MEMINFO (1<<1) | VIDEO (1<<2) */
#define MB_CHECKSUM -(MB_MAGIC + MB_FLAGS)

.section .multiboot, "a", @progbits
.align 4
.long MB_MAGIC
.long MB_FLAGS
.long MB_CHECKSUM
/* Header address fields a 0 per file ELF */
.long 0, 0, 0, 0, 0
/* Video Mode Configuration: 1024x768 a 32-bit ARGB Linear Framebuffer */
.long 0          /* mode_type: 0 = Linear Graphics Mode */
.long 1024       /* width: 1024 pixel */
.long 768        /* height: 768 pixel */
.long 32         /* depth: 32 bpp */

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

    /* Abilita hardware FPU ed SSE (CR0/CR4) */
    mov %cr0, %edx
    and $0xFFFFFFFB, %edx /* Disabilita CR0.EM */
    or $0x00000022, %edx  /* Abilita CR0.MP e CR0.NE */
    mov %edx, %cr0

    mov %cr4, %edx
    or $0x00000600, %edx  /* Abilita CR4.OSFXSR (bit 9) e CR4.OSXMMEXCPT (bit 10) */
    mov %edx, %cr4
    fninit

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

/* Default Interrupt Service Routine (Anti-Triple-Fault Gate) */
.global osify_default_isr
.type osify_default_isr, @function
osify_default_isr:
    iret
.size osify_default_isr, . - osify_default_isr

/* Native System Call Interrupt Gate (int 0x80) */
.global osify_syscall_isr
.type osify_syscall_isr, @function
osify_syscall_isr:
    push %ebp
    push %edi
    push %esi
    push %edx
    push %ecx
    push %ebx

    /* Chiama il dispatcher C: osify_syscall_dispatch(eax, ebx, ecx, edx) */
    push %edx
    push %ecx
    push %ebx
    push %eax
    call osify_syscall_dispatch
    add $16, %esp

    pop %ebx
    pop %ecx
    pop %edx
    pop %esi
    pop %edi
    pop %ebp
    iret
.size osify_syscall_isr, . - osify_syscall_isr

