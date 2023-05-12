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

def remove_file_if_exists(path):
    if os.path.exists(path):
        os.remove(path)
    else:
        print(f"Trying to delete '{path}': Error: Does not exist.")


os.makedirs("results", exist_ok=True)

amount_of_programs = len(os.listdir(prog_dir))
seen_so_far = 0

if amount_of_programs == 0:
    print("No programs to fuzz.")
    exit(0)

for prog in os.listdir(prog_dir):
    prog_path = os.path.join(prog_dir, prog)
    if os.path.isfile(prog_path):
        name = os.path.basename(prog_path)
        seed = name[:-2]
        seen_so_far += 1
        print(f"Progress: {seen_so_far}/{amount_of_programs} [{seed}]\t flags: ", end="")

        for flag in optimization_flags:
            print(f"  {flag}", end="", flush=True)
            combine(prog_path, flag)
            os.system(f"./out {data_points} {flag}")
            shutil.copyfile("result-uniform.csv", f"results/{seed}-uniform_{flag}.csv")
            shutil.copyfile("result-equal.csv", f"results/{seed}-equal_{flag}.csv")
            shutil.copyfile("result-zero.csv", f"results/{seed}-zero_{flag}.csv")
            shutil.copyfile("result-max64.csv", f"results/{seed}-max64_{flag}.csv")
            shutil.copyfile("result-umax64.csv", f"results/{seed}-umax64_{flag}.csv")
        
        print()

remove_file_if_exists("out")
remove_file_if_exists("result-uniform.csv")
remove_file_if_exists("result-equal.csv")
remove_file_if_exists("result-zero.csv")
remove_file_if_exists("result-max64.csv")
remove_file_if_exists("result-umax64.csv")