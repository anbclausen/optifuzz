CC = gcc
CFLAGS = -O2 -Wall

build-fuzzer-core: fuzzer_core.c fuzzer_core.h
	@$(CC) $(CFLAGS) -c -o fuzzer_core.o fuzzer_core.c

build-fuzzer: build-fuzzer-core fuzzer.c fuzzer_core.h
	@$(CC) $(CFLAGS) -c -o fuzzer.o fuzzer.c 

fuzz: clean build-fuzzer
	@./fuzz.py $(in)

clean-objects:
	$(RM) *.o

clean-csv:
	$(RM) *.csv

.PHONY : clean
clean: clean-objects clean-csv