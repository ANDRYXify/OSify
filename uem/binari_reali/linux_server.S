/* ==============================================================================
 * OSify Real Linux ELF Application (uem/binari_reali/linux_server.S)
 * ==============================================================================
 * Binario Linux ELF 32-bit autentico con header ELF completi e syscall int 0x80.
 * ==============================================================================
 */

.global _start
.text
_start:
    /* sys_write(stdout=1, banner, len=54) */
    mov $4, %eax
    mov $1, %ebx
    mov $banner, %ecx
    mov $54, %edx
    int $0x80

    /* sys_exit(0) */
    mov $1, %eax
    xor %ebx, %ebx
    int $0x80

.data
banner:
    .ascii "OSify UEM: Linux ELF Micro-Server attivo al 100%!\n"
