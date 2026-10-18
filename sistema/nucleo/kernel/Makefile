# ==============================================================================
# Makefile del Kernel Nativo OSify (sistema/nucleo/kernel/Makefile)
# ==============================================================================
# Ingegnerizzato da Andrea Taliento (ANDRYXify) per OSify
# Compila l'esoscheletro del Micro-Core, PMM/VMM, Sicurezza SIP/Seatbelt,
# Motore Tipografico Dark Glass, Input PS/2 e Ponte di Compatibilita Universale.
# ==============================================================================

CC ?= gcc
CFLAGS ?= -Wall -Wextra -O2 -Iinclude -std=c99
AR ?= ar

SRC_CORE = core/osify_skin_core.c core/osify_memory.c core/osify_level0_security.c \
           core/osify_kstring.c core/osify_idt.c core/osify_main.c core/osify_syscall.c core/osify_synch.c \
           core/osify_hetero_dispatch.c
SRC_SEC  = security/osify_anticheat_guard.c
SRC_DRV  = drivers/osify_native_graphics.c drivers/osify_font.c drivers/osify_ps2_input.c \
           drivers/osify_storage.c drivers/osify_desktop_wm.c \
           drivers/osify_net.c drivers/osify_audio.c drivers/osify_installer.c \
           drivers/osify_capture_card.c
SRC_COMP = compat/osify_universal_bridge.c compat/osify_path_unifier.c
SRC_LOAD = loaders/osify_binary_loader.c

SRC_ALL  = $(SRC_CORE) $(SRC_SEC) $(SRC_DRV) $(SRC_COMP) $(SRC_LOAD)
OBJ_ALL  = $(SRC_ALL:.c=.o)
LIB_OUT  = libosify_kernel.a
TEST_OUT = test_osify_kernel

.PHONY: all clean test

all: $(LIB_OUT) test

$(LIB_OUT): $(OBJ_ALL)
	$(AR) rcs $@ $^

%.o: %.c
	$(CC) $(CFLAGS) -c $< -o $@

test: $(LIB_OUT) tests/test_kernel_skin.c
	$(CC) $(CFLAGS) tests/test_kernel_skin.c -L. -losify_kernel -o $(TEST_OUT)
	./$(TEST_OUT)

clean:
	rm -f $(OBJ_ALL) $(LIB_OUT) $(TEST_OUT)
