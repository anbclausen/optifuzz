#!/bin/sh

if [ "$#" -ne 1 ]; then
    echo "usage: $0 path/to/prog.c"
fi

gcc -O3 -c -o template.o $1

gcc -o out fuzzer.o template.o -lbsd

rm template.o
