import os
import re 
import time

jmp_regex = re.compile(r"j[a-z][a-z]")


def analyze(file):
    os.popen(f"clang {file} -O0 -c -o {file}_O0.o > /dev/null 2>&1")
    os.popen(f"clang {file} -O3 -c -o {file}_O3.o > /dev/null 2>&1")
    time.sleep(0.1)
    o0out = os.popen(f"objdump -d {file}_O0.o").read()
    o3out = os.popen(f"objdump -d {file}_O3.o").read()
    o0out = jmp_regex.findall(o0out)
    o3out = jmp_regex.findall(o3out)
    
    if len(o0out) != len(o3out):
        print("### FOUND BRANCHING ###")
        print(f"File: {file}")
        print(f"O0 instructions: {str(o0out)}")
        print(f"O3 instructions: {str(o3out)}")
        print("########################")

print("Analyzing assembly instructions...")
for dirpath, dnames, fnames in os.walk("programs"):
    for f in fnames:
        if f.endswith(".c"):
            analyze(os.path.join(dirpath, f))
print("Done!")
