#!/usr/bin/env python3
import os
import re
import sys
import subprocess

folder = os.path.dirname(os.path.realpath(__file__))
flagged_folder = f"{folder}{os.sep}flagged{os.sep}"

jmp_regex = re.compile(r"\t(j[a-z]+)")

optimization_flags = ["O0", "O1", "O2", "O3", "Os"]
compiler = sys.argv[1] if len(sys.argv) > 1 else "gcc"


def tick():
    print(".", end="", flush=True)


def run(args):
    return subprocess.run(args, capture_output=True, text=True).stdout


def flag_file(file):
    os.makedirs(flagged_folder, exist_ok=True)
    run(["mv", file, flagged_folder])


def analyze(file):
    tick()
    out = {}
    for opt_flag in optimization_flags:
        # -S: compile to assembly
        # -w: disable warnings
        # -c: compile to object file
        out[opt_flag] = run(
            [compiler, file, "-S", f"-{opt_flag}", "-w", "-c", "-o", "/dev/stdout"]
        )

    for k, v in out.items():
        out[k] = jmp_regex.findall(v)

    # Flag the file if any jumps are reported for any flag (except O0)
    if [None for k, v in out.items() if k != "O0" and v]:
        flag_file(file)
        print(f"\n> File: {file}")
        for k, v in out.items():
            print(f"  {k}: {v}")


print("Analyzing assembly instructions...")
print(f"COMPILER: {compiler}")
programs_folder = f"{folder}{os.sep}..{os.sep}generator{os.sep}generated"
for dirpath, dnames, fnames in os.walk(programs_folder):
    for f in fnames:
        if f.endswith(".c"):
            analyze(os.path.join(dirpath, f))
print("Done!")
