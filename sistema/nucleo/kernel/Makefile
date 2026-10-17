# ==============================================================================
# Makefile del Kernel Nativo OSify (sistema/nucleo/kernel/Makefile)
# ==============================================================================
# Ingegnerizzato da Andrea Taliento (ANDRYXify) per OSify
# Compila l'esoscheletro del Micro-Core e la suite di compatibilita universale.
# ==============================================================================

CC ?= gcc
CFLAGS ?= -Wall -Wextra -O2 -Iinclude -std=c99
AR ?= ar

SRC_CORE = core/osify_skin_core.c
SRC_DRV  = drivers/osify_native_graphics.c
SRC_COMP = compat/osify_universal_bridge.c
SRC_ALL  = $(SRC_CORE) $(SRC_DRV) $(SRC_COMP)

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
