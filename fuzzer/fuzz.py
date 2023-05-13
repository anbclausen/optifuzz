#!/usr/bin/env python3
import sys
import os
import shutil
import json

prog_dir = "../analysis/flagged"
config = json.load(open("../config.json"))

number_of_fuzzing_runs = sys.argv[1] if len(sys.argv) > 1 else config["number_of_fuzzing_runs"]
optimization_flags = config["compiler_flags"]
fuzzing_classes = config["fuzzing_classes"]


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
            os.system(f"./out {number_of_fuzzing_runs} {flag}")
            for fuzzing_class in fuzzing_classes:
                shutil.copyfile(f"result-{fuzzing_class}.csv", f"results/{seed}-{fuzzing_class}_{flag}.csv")
        
        print()

remove_file_if_exists("out")
for fuzzing_class in fuzzing_classes:
    remove_file_if_exists(f"result-{fuzzing_class}.csv")