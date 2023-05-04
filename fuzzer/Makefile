CC = gcc
CFLAGS = -O2

build-fuzzer: fuzzer.c
	@$(CC) $(CFLAGS) -c -o fuzzer.o fuzzer.c

fuzz: build-fuzzer
	@./fuzz.sh 1000000

clean-results:
	@rm results/* 1>/dev/null 2>&1; true

clean-objects:
	@rm *.o

.PHONY : clean
clean: clean-results clean-objects