import os
import re 
import time

jmp_regex = re.compile(r"j[a-z]+")
compiler = "gcc"


def analyze(file):
    os.popen(f"{compiler} {file} -O0 -c -o {file}_O0.o > /dev/null 2>&1")
    os.popen(f"{compiler} {file} -O1 -c -o {file}_O1.o > /dev/null 2>&1")
    os.popen(f"{compiler} {file} -O2 -c -o {file}_O2.o > /dev/null 2>&1")
    os.popen(f"{compiler} {file} -O3 -c -o {file}_O3.o > /dev/null 2>&1")
    time.sleep(0.1)
    o0out = os.popen(f"objdump -d {file}_O0.o").read()
    o1out = os.popen(f"objdump -d {file}_O1.o").read()
    o2out = os.popen(f"objdump -d {file}_O2.o").read()
    o3out = os.popen(f"objdump -d {file}_O3.o").read()
    o0out = jmp_regex.findall(o0out)
    o1out = jmp_regex.findall(o1out)
    o2out = jmp_regex.findall(o2out)
    o3out = jmp_regex.findall(o3out)
    
    if len(o0out) != len(o1out) or len(o0out) != len(o2out) or len(o0out) != len(o3out):
        print("### FOUND BRANCHING ###")
        print(f"File: {file}")
        print(f"O0 instructions: {str(o0out)}")
        print(f"O1 instructions: {str(o1out)}")
        print(f"O2 instructions: {str(o2out)}")
        print(f"O3 instructions: {str(o3out)}")
        print("########################")

print("Analyzing assembly instructions...")
print(f"COMPILER: {compiler}")
for dirpath, dnames, fnames in os.walk("programs"):
    for f in fnames:
        if f.endswith(".c"):
            analyze(os.path.join(dirpath, f))
print("Done!")
