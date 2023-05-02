import os
import re 

jmp_regex = re.compile(r"\t(j[a-z]+)")
compiler = "gcc"
optimization_flags = ["O0", "O1", "O2", "O3"]


def analyze(file):
    out = {}
    for opt_flag in optimization_flags:
        out[opt_flag] = os.popen(f"{compiler} {file} -{opt_flag} -S -w -c -o /dev/stdout").read()

    for k, v in out.items():
        out[k] = jmp_regex.findall(v)
    
    if not (out["O0"] == out["O1"] == out["O2"] == out["O3"]):
        print(f"> File: {file}")
        for k, v in out.items():
            print(f"  {k}: {v}")

print("Analyzing assembly instructions...")
print(f"COMPILER: {compiler}")

folder = os.path.dirname(os.path.realpath(__file__))
programs = f"{folder}{os.sep}programs"
for dirpath, dnames, fnames in os.walk(programs):
    for f in fnames:
        if f.endswith(".c"):
            analyze(os.path.join(dirpath, f))
print("Done!")
