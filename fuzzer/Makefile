CC = gcc
CFLAGS = -O2

build-fuzzer: fuzzer.c
	@$(CC) $(CFLAGS) -c -o fuzzer.o fuzzer.c

fuzz: clean build-fuzzer
	@./fuzz.py $(in)

clean-results:
	@-rm results/* 1>/dev/null 2>&1

clean-objects:
	@-rm *.o 1>/dev/null 2>&1

.PHONY : clean
clean: clean-results clean-objects
	$(MAKE) -C km_fuzzer clean