#!/usr/bin/env python3
import sys
import os
import shutil
import json

prog_dir = "../analysis/flagged"
config = json.load(open("../config.json"))

if len(sys.argv) < 2:
    print("Usage: python3 fuzz.py <number of fuzzing runs>")
    exit(1)

number_of_fuzzing_runs = sys.argv[1]
optimization_flags = config["compiler_flags"]
fuzzing_classes = config["fuzzing_classes"]

compiler = config["compiler"]

kernel_mode = True # FIXME - make parameter

def combine(prog_path, flag):
    os.system(f"{compiler} -{flag} -c -w -o template.o {prog_path}")
    # Use gcc to link
    os.system("gcc -o out fuzzer.o template.o -lbsd")
    os.remove("template.o")

def compile_km(prog_path, flag):
    with open("km_fuzzer/Makefile", "w") as f:
        f.write(f"CFLAGS_program.o += -{flag}\n")
        f.write(f"CC_program = {compiler}\n")
    os.system("cat km_fuzzer/MakefileTemplate >> km_fuzzer/Makefile")
    os.system(f"cp {prog_path} km_fuzzer/program.c")
    os.system("cd km_fuzzer && make >/dev/null 2>&1")

def km_extract_output(seed):
    with open('/proc/optifuzz_output', 'r') as f:
        # Initialize the variables to keep track of the current section and filename
        current_section = []
        current_filename = None
        
        # Loop through each line in the file
        for line in f:
            # If the line starts with '# FILE:', it indicates the start of a new section
            if line.startswith('# FILE:'):
                # If we have a current filename and current section, write them to a file
                if current_filename is not None and current_section:
                    with open(current_filename, 'w') as outfile:
                        outfile.writelines(current_section)
                # Extract the filename from the line and start a new section
                current_filename = line.strip().split()[-1][1:-1]
                current_section = []
            # Otherwise, append the line to the current section
            else:
                current_section.append(line)
    
        # At the end of the file, write the last section if there is one
        if current_filename is not None and current_section:
            with open(current_filename, 'w') as outfile:
                outfile.writelines(current_section)



def remove_file_if_exists(path):
    if os.path.exists(path):
        os.remove(path)
    else:
        pass # shh
        #print(f"Trying to delete '{path}': Error: Does not exist.")


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

        if kernel_mode:
            os.system("sudo -v")

        for flag in optimization_flags:
            print(f"  {flag}", end="", flush=True)
            if kernel_mode:
                compile_km(prog_path, flag)
                sudo_prefix = "sudo" if not os.getuid() == 0 else ""
                os.system(f"{sudo_prefix} insmod km_fuzzer/modprog.ko count={number_of_fuzzing_runs} flag={flag}")
                km_extract_output(name)
                os.system(f"{sudo_prefix} rmmod modprog")
            else:
                combine(prog_path, flag)
                os.system(f"./out {number_of_fuzzing_runs} {flag}")

            for fuzzing_class in fuzzing_classes:
                shutil.copyfile(f"result-{fuzzing_class}.csv", f"results/{seed}-{fuzzing_class}_{flag}.csv")
        
        print()

remove_file_if_exists("out")
for fuzzing_class in fuzzing_classes:
    remove_file_if_exists(f"result-{fuzzing_class}.csv")