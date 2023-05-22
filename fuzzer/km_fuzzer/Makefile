# Example of arguments: comp=gcc flag=O3
CC_program = $(comp)
CFLAGS_program.o += -w -$(flag)
# Name of the kernel module
obj-m := optifuzz.o
# Build as part of the kernel module
optifuzz-y := km_fuzzer.o ../fuzzer_core.o
# Build seperately and link
optifuzz-objs := program.o
# Flags to be passed to the preprocessor like the include directive
ccflags-y := -DKERNEL_MODE

KERNELDIR ?= /lib/modules/$(shell uname -r)/build
PWD := $(shell pwd)

.PHONY: all clean

all: check_headers program.o
	$(MAKE) -C $(KERNELDIR) M=$(PWD) modules

clean: check_headers
	$(MAKE) -C $(KERNELDIR) M=$(PWD) clean
	$(RM) program.o ../fuzzer_core.o ../.fuzzer_core.o.cmd

program.o: program.c
	$(CC_program) $(CFLAGS_program.o) -c -o $@ $^

check_headers:
	@if [ ! -d "$(KERNELDIR)" ]; then \
		echo "Linux headers not found!" >&2; \
		exit 0; \
	fi