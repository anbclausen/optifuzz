#!/bin/sh

#if [ "$#" -ne 2 ]; then
#    echo "usage: $0 /path/to/fuzzer.o path/to/ast_template.c"
#fi

gcc -O3 -c -o template.o template.c

gcc -o out fuzzer.o template.o

rm template.o
