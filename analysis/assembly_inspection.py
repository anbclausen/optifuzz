#!/usr/bin/env python3
import os
import re
import subprocess
import json

CONFIG_FILENAME = "config.json"

folder = os.path.dirname(os.path.realpath(__file__))
config_dir = parent_directory = os.path.dirname(folder)
config = json.load(open(f"{config_dir}{os.sep}{CONFIG_FILENAME}"))

flagged_folder = f"{config_dir}{os.sep}{config['flagged_programs_dir']}"

# Match all jcc instructions that is not jmp, and all loop instructions
# https://cdrdv2.intel.com/v1/dl/getContent/671200
# Table 7-4
jmp_regex = re.compile(r"\t(j(?!mp)[a-z][a-z]*)|(loop[a-z]*) ")

optimization_flags = config["compiler_flags"]
compiler = config["compiler"]


def extract_conditional_branching_instructions(s: str) -> list[str]:
    """Extracts all conditional branching instructions from a string

    Parameters
    ----------
    path : str
        The string to be searched

    Returns
    ----------
    A list of all conditional branching instructions
    """
    matches = jmp_regex.findall(s)
    jmp_matches = [x[0] for x in matches if x[0] != ""]
    loop_matches = [x[1] for x in matches if x[1] != ""]
    return jmp_matches + loop_matches


def run(args: list[str]) -> str:
    """Runs a command and returns the stdout

    Parameters
    ----------
    args : list[str]
        The command to be run

    Returns
    ----------
    The stdout of the command
    """
    return subprocess.run(args, capture_output=True, text=True).stdout


def flag_file(file: str) -> None:
    """Moves a file to the flagged folder

    Parameters
    ----------
    file : str
        The path of the file to be moved
    """
    os.makedirs(flagged_folder, exist_ok=True)
    run(["mv", file, flagged_folder])


def get_assembly_for_file(file: str) -> dict[str, str]:
    """Gets the assembly for a file for each optimization flag

    Parameters
    ----------
    file : str
        The path of the file to be analyzed

    Returns
    ----------
        A dictionary with the optimization flag as key and the assembly as value
    """
    return {
        opt_flag: run(
            [compiler, file, "-S", f"-{opt_flag}", "-w", "-c", "-o", "/dev/stdout"]
        )
        for opt_flag in optimization_flags
    }


def get_cond_branching_instructions(file: str) -> dict[str, list[str]]:
    """Gets the conditional branching instructions for a file for each optimization flag

    Parameters
    ----------
    file : str
        The path of the file to be analyzed

    Returns
    ----------
        A dictionary with the optimization flag as key and lists of conditional branching instructions as value
    """
    return {
        opt_flag: extract_conditional_branching_instructions(assembly)
        for opt_flag, assembly in get_assembly_for_file(file).items()
    }


def analyze(file: str) -> bool:
    """Analyzes a file for conditional branching instructions

    Parameters
    ----------
    file : str
        The path of the file to be analyzed

    Returns
    ----------
        `True` if any conditional branching instructions are found, `False` otherwise
    """
    cond_branching_instructions = get_cond_branching_instructions(file)

    opt_flags_with_jumps = [
        k for k, v in cond_branching_instructions.items() if v
    ]

    if opt_flags_with_jumps:
        print(f"\n> File: {file}")
        for k, v in cond_branching_instructions.items():
            print(f"  {k}: {v}")
        return True
    return False


print("Analyzing assembly instructions...")
print(f"COMPILER: {compiler}")
programs_folder = f"{config_dir}{os.sep}{config['generated_programs_dir']}"
file_amount = len(os.listdir(programs_folder))
count = 1
for dirpath, dnames, fnames in os.walk(programs_folder):
    for f in fnames:
        if f.endswith(".c"):
            print(f"\rInspecting [{count}/{file_amount}]", end="", flush=True)
            count += 1
            file_path = os.path.join(dirpath, f)
            if analyze(file_path):
                flag_file(file_path)

print("\nDone!")
