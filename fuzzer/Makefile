CC = gcc
CFLAGS = -O2 -Wall

build-fuzzer-core: fuzzer_core.c fuzzer_core.h
	@$(CC) $(CFLAGS) -c -o fuzzer_core.o fuzzer_core.c

build-fuzzer: build-fuzzer-core fuzzer.c fuzzer_core.h
	@$(CC) $(CFLAGS) -c -o fuzzer.o fuzzer.c 

fuzz: clean build-fuzzer
	@./fuzz.py $(in)

clean-results:
	$(RM) results/*

clean-objects:
	$(RM) *.o

.PHONY : clean
clean: clean-results clean-objects
	$(MAKE) -C km_fuzzer clean