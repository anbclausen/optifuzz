#!/usr/bin/env python3
import sys
import os
import shutil
import json

CONFIG_FILENAME = "config.json"

# Kernel Module files
KM_STATUS = '/proc/optifuzz_status'
KM_OUTPUT = '/proc/optifuzz_output'

folder = os.path.dirname(os.path.realpath(__file__))
config_dir = parent_directory = os.path.dirname(folder)
config = json.load(open(f"{config_dir}{os.sep}{CONFIG_FILENAME}"))


def absolute_path(path: str):
    """ Converts a path from config_dir to absolute 

    Parameters
    ----------
    path : str
        Relative path

    Returns
    ----------
    Absolute path
    """
    return f"{config_dir}{os.sep}{path}"


def get_config_path(entry: str):
    """ Get absolute path from path entry in config 

    Parameters
    ----------
    path : str
        The path entry in config

    Returns
    ----------
    Absolute path of config entry
    """
    return absolute_path(config[entry])


def remove_file_if_exists(path: str):
    """ Silently tries to delete a file if it exists

    Parameters
    ----------
    path : str
        Path to the file to be deleted
    """
    if os.path.exists(path):
        os.remove(path)


def compile_user(prog_path: str, compiler: str, flag: str):
    """ Compile program and link with user runtime 

    Parameters
    ----------
    prog_path : str
        Path to the program to compile and link
    compiler : str
        Compiler used for compilation of program
    flag : str
        Optimization flag (eg. "O3") to compile program
    """
    os.system(f"{compiler} -{flag} -c -w -o template.o {prog_path}")

    # Use gcc to link (no compilation happens)
    os.system("gcc -o out fuzzer.o fuzzer_core.o template.o -lbsd")
    remove_file_if_exists("template.o")


def compile_kernel(prog_path: str, compiler: str, flag: str):
    """ Compile program and link with kernel module 

    Parameters
    ----------
    prog_path : str
        Path to the program to compile and link
    compiler : str
        Compiler used for compilation of program
    flag : str
        Optimization flag (eg. "O3") to compile program
    """
    os.system(f"cp {prog_path} km_fuzzer/program.c")
    os.system(
        f"cd km_fuzzer && make comp={compiler} flag={flag}>/dev/null 2>&1")


def extract_kernel_output():
    """ Extracts the results from the kernel module and saves them in 
        the default result file for each fuzzing class
    """
    with open(KM_OUTPUT, 'r') as f:
        current_section = []
        current_filename = None

        for line in f:
            # If new section
            if line.startswith('# FILE:'):
                # Save last section
                if current_filename is not None and current_section:
                    with open(current_filename, 'w') as outfile:
                        outfile.writelines(current_section)

                current_filename = line.strip().split()[-1][1:-1]
                current_section = []
            else:
                current_section.append(line)

        # write last section
        if current_filename is not None and current_section:
            with open(current_filename, 'w') as outfile:
                outfile.writelines(current_section)


def fuzz_program_user(prog_path: str, compiler: str, flag: str):
    """ Compile and fuzz specified program in user mode 

    Parameters
    ----------
    prog_path : str
        Path to the program to fuzz
    compiler : str
        Compiler used for compilation of program
    flag : str
        Optimization flag to compile program
    """
    compile_user(prog_path, compiler, flag)
    os.system(f"./out {number_of_fuzzing_runs} {flag}")


def fuzz_program_kernel(prog_path: str, compiler: str, flag: str):
    """ Compile and fuzz specified program in kernel module mode 

    Parameters
    ----------
    prog_path : str
        Path to the program to fuzz
    compiler : str
        Compiler used for compilation of program
    flag : str
        Optimization flag to compile program
    """
    compile_kernel(prog_path, compiler, flag)

    # We need root permissions to load and unload a kernel module
    sudo_prefix = ""
    if not os.getuid() == 0:
        os.system("sudo -v")
        sudo_prefix = "sudo"

    # Load module
    os.system(
        f"{sudo_prefix} insmod km_fuzzer/optifuzz.ko count={number_of_fuzzing_runs} flag={flag}")
    # Process results
    extract_kernel_output()
    # Unoad module
    os.system(f"{sudo_prefix} rmmod optifuzz")


def save_results(seed: str, fuzzing_classes: list, flag: str, result_dir: str):
    """ Copy results to results folder and rename to reflect class and flag 

    Parameters
    ----------
    seed : str
        Seed used to generate the program
    fuzzing_classes : list
        The fuzzing classes the results come from
    flag : str
        Optimization flag used to compile program
    result_dir : str
        The directory to save the results in
    """
    for fuzzing_class in fuzzing_classes:
        shutil.copyfile(f"result-{fuzzing_class}.csv",
                        f"{result_dir}{os.sep}{seed}-{fuzzing_class}_{flag}.csv")


def fuzz(prog_dir: str, fuzzing_classes: list, optimization_flags: list, compiler: str, kernel_mode: bool, result_dir: str):
    """ Fuzz all programs for each optimization flag and fuzzing class in inspecified mode

    Parameters
    ----------
    prog_dir : str
        Directory containing the programs
    fuzzing_classes : list
        The fuzzing classes to be testet by the programs
    optimization_flags : list
        Optimization flags to compile the programs with
    compiler : str
        The compiler used to compile the programs
    kernel_mode : bool
        Specify whether or not the programs should be run as kernel modules
    result_dir : str
        The directory to save the results in
    """
    amount_of_programs = len(os.listdir(prog_dir))
    if amount_of_programs == 0:
        print("No programs to fuzz.")
        exit(0)

    seen_so_far = 0
    for prog in os.listdir(prog_dir):
        prog_path = os.path.join(prog_dir, prog)
        if os.path.isfile(prog_path):
            name = os.path.basename(prog_path)
            seed = name[:-2]
            seen_so_far += 1
            print(
                f"Progress: {seen_so_far}/{amount_of_programs} [{seed}]\t flags: ", end="")

            for flag in optimization_flags:

                if kernel_mode:
                    fuzz_program_kernel(prog_path, compiler, flag)
                else:
                    fuzz_program_user(prog_path, compiler, flag)
                print(f"  {flag}", end="", flush=True)

                save_results(seed, fuzzing_classes, flag, result_dir)

            print()


def clean(fuzzing_classes: list):
    """ Remove all temporary result files and program

    Parameters
    ----------
    fuzzing_classes : list
        All classes that has emitted result files 
    """
    remove_file_if_exists("out")
    for fuzzing_class in fuzzing_classes:
        remove_file_if_exists(f"result-{fuzzing_class}.csv")


if __name__ == '__main__':
    prog_dir = get_config_path('fuzzer_source')
    result_dir = get_config_path('fuzzer_results')

    if len(sys.argv) < 2:
        print("Usage: python3 fuzz.py <number of fuzzing runs>")
        exit(1)

    number_of_fuzzing_runs = sys.argv[1]
    optimization_flags = config["compiler_flags"]
    fuzzing_classes = config["fuzzing_classes"]

    compiler = config["compiler"]
    kernel_mode = config["kernel_mode"]

    # Ensure that we have a place to save our results
    os.makedirs(result_dir, exist_ok=True)

    fuzz(prog_dir, fuzzing_classes, optimization_flags, compiler, kernel_mode, result_dir)

    clean(fuzzing_classes)
