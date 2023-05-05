#!/usr/bin/env python3
import sys
import os
import shutil

prog_dir = "../analysis/flagged"

data_points = sys.argv[1]
optimization_flags = ["O0", "O1", "O2", "O3", "Os"]


def combine(prog_path, flag):
    os.system(f"gcc -{flag} -c -w -o template.o {prog_path}")
    os.system("gcc -o out fuzzer.o template.o -lbsd")
    os.remove("template.o")


os.makedirs("results", exist_ok=True)

amount_of_programs = len(os.listdir(prog_dir))
seen_so_far = 0

for prog in os.listdir(prog_dir):
    prog_path = os.path.join(prog_dir, prog)
    if os.path.isfile(prog_path):
        name = os.path.basename(prog_path)
        seed = name[:-2]
        seen_so_far += 1
        print(f"Progress: {seen_so_far}/{amount_of_programs} [{seed}]")

        for flag in optimization_flags:
            print(f"  {flag}")
            combine(prog_path, flag)
            os.system(f"./out {data_points} {flag}")
            shutil.copyfile("result.csv", f"results/{seed}_{flag}.csv")

os.remove("out")
os.remove("result.csv")
