CC = gcc
CFLAGS = -O2 -Wall
CONFIG_PATH="../config.json"
KERNEL_MODE = $(shell python3 -c "import json; print(json.load(open('$(CONFIG_PATH)'))['kernel_mode'])")

build-fuzzer-core: fuzzer_core.c fuzzer_core.h
	@$(CC) $(CFLAGS) -c -o fuzzer_core.o fuzzer_core.c

build-fuzzer: build-fuzzer-core fuzzer.c fuzzer_core.h
	@$(CC) $(CFLAGS) -c -o fuzzer.o fuzzer.c 

fuzz: clean build-fuzzer
	@./fuzz.py $(in)

clean-objects:
	$(RM) *.o

.PHONY : clean
clean: clean-objects
	@if [ "$(KERNEL_MODE)" = "True" ]; then \
		$(MAKE) -C km_fuzzer clean; \
	fi
	