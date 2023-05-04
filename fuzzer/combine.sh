#!/bin/sh

if [ "$#" -ne 2 ]; then
    echo "usage: $0 path/to/prog.c flag"
    exit 1
fi

gcc "-$2" -c -o template.o $1
gcc -o out fuzzer.o template.o -lbsd
rm template.o
