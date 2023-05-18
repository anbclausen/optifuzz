CFLAGS_program.o += -Os
CC_program = gcc

CFLAGS_program.o += -w
obj-m := modprog.o
modprog-objs := main.o program.o
modprog-y := program.o

KERNELDIR ?= /lib/modules/$(shell uname -r)/build
PWD := $(shell pwd)

.PHONY: all clean

all:
	$(MAKE) -C $(KERNELDIR) M=$(PWD) modules

clean:
	$(MAKE) -C $(KERNELDIR) M=$(PWD) clean


program.o: program.c
	$(CC) $(CFLAGS_program.o) -c -o $@ $<