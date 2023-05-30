#!/usr/bin/env python3
import sys
import os
import shutil
import json

CONFIG_FILENAME = "config.json"

folder = os.path.dirname(os.path.realpath(__file__))
config_dir = parent_directory = os.path.dirname(folder)
config = json.load(open(f"{config_dir}{os.sep}{CONFIG_FILENAME}"))


def absolute_path(path: str) -> str:
    """Converts a path from config_dir to absolute

    Parameters
    ----------
    path : str
        Relative path

    Returns
    ----------
    Absolute path
    """
    return f"{config_dir}{os.sep}{path}"


def get_config_path(entry: str) -> str:
    """Get absolute path from path entry in config

    Parameters
    ----------
    path : str
        The path entry in config

    Returns
    ----------
    Absolute path of config entry
    """
    return absolute_path(config[entry])


def remove_file_if_exists(path: str) -> None:
    """Silently tries to delete a file if it exists

    Parameters
    ----------
    path : str
        Path to the file to be deleted
    """
    if os.path.exists(path):
        os.remove(path)


def compile_user(prog_path: str, compiler: str, flag: str) -> None:
    """Compile program and link with user runtime

    Parameters
    ----------
    prog_path : str
        Path to the program to compile and link
    compiler : str
        Compiler used for compilation of program
    flag : str
        Optimization flag (eg. "O3") to compile program
    """
    os.system(f"{compiler} -{flag} -c -w -o template.o '{prog_path}'")

    # Use gcc to link (no compilation happens)
    os.system("gcc -o out fuzzer.o fuzzer_core.o template.o -lbsd")
    remove_file_if_exists("template.o")


def fuzz_class_lst_to_argument(fuzzing_classes: list) -> str:
    """Convert list of fuzzing classes to a space seperated string

    Parameters
    ----------
    fuzzing_classes : list
        List of classes to fuzz

    Returns
    ----------
    Space seperated string of list items
    """
    return " ".join(fuzzing_classes)


def fuzz_program_user(
    prog_path: str, compiler: str, flag: str, fuzzing_classes: list
) -> None:
    """Compile and fuzz specified program in user mode

    Parameters
    ----------
    prog_path : str
        Path to the program to fuzz
    compiler : str
        Compiler used for compilation of program
    flag : str
        Optimization flag to compile program
    fuzzing_classes : list
        List of classes to fuzz
    """
    compile_user(prog_path, compiler, flag)
    class_arg = fuzz_class_lst_to_argument(fuzzing_classes)
    os.system(f"./out {number_of_fuzzing_runs} {flag} '{class_arg}'")


def save_results(seed: str, fuzzing_classes: list, flag: str, result_dir: str) -> None:
    """Copy results to results folder and rename to reflect class and flag

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
        shutil.copyfile(
            f"result-{fuzzing_class}.csv",
            f"{result_dir}{os.sep}{seed}-{fuzzing_class}_{flag}.csv",
        )


def fuzz(
    prog_dir: str,
    fuzzing_classes: list,
    optimization_flags: list,
    compiler: str,
    result_dir: str,
) -> None:
    """Fuzz all programs for each optimization flag and fuzzing class in inspecified mode

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
                f"Progress: {seen_so_far}/{amount_of_programs} [{seed}]\t flags: ",
                end="",
            )

            for flag in optimization_flags:
                fuzz_program_user(prog_path, compiler, flag, fuzzing_classes)
                print(f"  {flag}", end="", flush=True)

                save_results(seed, fuzzing_classes, flag, result_dir)

            print()


def clean(fuzzing_classes: list) -> None:
    """Remove all temporary result files and program

    Parameters
    ----------
    fuzzing_classes : list
        All classes that has emitted result files
    """
    remove_file_if_exists("out")
    for fuzzing_class in fuzzing_classes:
        remove_file_if_exists(f"result-{fuzzing_class}.csv")


if __name__ == "__main__":
    prog_dir = get_config_path("flagged_programs_dir")
    result_dir = get_config_path("fuzzer_results_dir")

    os.makedirs(prog_dir, exist_ok=True)
    os.makedirs(result_dir, exist_ok=True)

    if len(sys.argv) < 2:
        print("Usage: python3 fuzz.py <number of fuzzing runs>")
        exit(1)

    number_of_fuzzing_runs = sys.argv[1]
    optimization_flags = config["compiler_flags"]
    fuzzing_classes = config["fuzzing_classes"]

    compiler = config["compiler"]

    # Ensure that we have a place to save our results
    os.makedirs(result_dir, exist_ok=True)

    fuzz(
        prog_dir, fuzzing_classes, optimization_flags, compiler, result_dir
    )

    clean(fuzzing_classes)
