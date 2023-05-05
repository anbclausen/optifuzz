#!/usr/bin/env python3
import os
import re

folder = os.path.dirname(os.path.realpath(__file__))
flagged_folder = f"{folder}{os.sep}flagged{os.sep}"
optimization_flags = ["O0", "O1", "O2", "O3", "Os"]
jmp_regex = re.compile(r"\t(j[a-z]+)")
compiler = "gcc"

def flag_file(file):
    os.makedirs(flagged_folder, exist_ok=True)
    os.popen(f'mv "{file}" "{flagged_folder}"')

def analyze(file):
    out = {}
    for opt_flag in optimization_flags:
        # -S: compile to assembly
        # -w: disable warnings
        # -c: compile to object file
        out[opt_flag] = os.popen(f'{compiler} "{file}" -{opt_flag} -S -w -c -o /dev/stdout').read()

    for k, v in out.items():
        out[k] = jmp_regex.findall(v)
    
    if not (out["O0"] == out["O1"] == out["O2"] == out["O3"]):
        flag_file(file)
        print(f"> File: {file}")
        for k, v in out.items():
            print(f"  {k}: {v}")

print("Analyzing assembly instructions...")
print(f"COMPILER: {compiler}")

programs_folder = f"{folder}{os.sep}programs"
for dirpath, dnames, fnames in os.walk(programs_folder):
    for f in fnames:
        if f.endswith(".c"):
            analyze(os.path.join(dirpath, f))
print("Done!")
