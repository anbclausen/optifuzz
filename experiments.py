#!/usr/bin/env python3
small_experiments = [
    {
        "compiler": "gcc",
        "compile_flags": ["O0", "O1", "O2", "O3", "Os"],
        "fuzz_classes": [
            "uniform",
            "fixed",
            "xzero",
            "yzero",
            "xlty",
            "yltx",
            "small",
            "equal",
            "max64",
        ],
        "pn": 100,
        "md": 5,
        "in": 10000,
    },
]

import os
import json
import shutil
import datetime


now = datetime.datetime.now().strftime("%Y-%m-%d-%H-%M-%S")
print("EXPERIMENTS: ", now)
TOP_DIR = f"experiments/{now}"

number_of_experiments = len(small_experiments)


def run(args: str) -> str:
    return os.system(args)


for i, experiment in enumerate(small_experiments):
    print("RUNNING EXPERIMENT", i + 1, "/", number_of_experiments)
    print("  ", "making folder")
    os.makedirs(f"{TOP_DIR}/experiment{i+1}", exist_ok=True)
    print("  ", "changing config")
    with open("config.json", "w") as f:
        json.dump(
            {
                "compiler": experiment["compiler"],
                "compiler_flags": experiment["compile_flags"],
                "fuzzing_classes": experiment["fuzz_classes"],
                "generated_programs_dir": "results/generated_programs/",
                "flagged_programs_dir": "results/flagged_programs/",
                "fuzzer_results_dir": "results/fuzzer_results/",
                "report_dir": "results/",
            },
            f,
        )
    print("  ", "running experiment")
    try:
        run(f"make generate pn={experiment['pn']} md={experiment['md']}")
        if os.getuid() != 0:
            os.system("sudo -v")

        run("sudo taskset --cpu-list 1 nice -n -20 make inspect")  # makes this go brr
        run(f"sudo taskset --cpu-list 2 nice -n -20 make fuzz in={experiment['in']}")
        number_of_flagged = len(os.listdir("results/flagged_programs/"))
        if experiment["md"] < 7 and number_of_flagged > 0:
            run("make latexgen")
            run("make latexcompile")
    except:
        print("  ^-", "experiment failed - salvaging results")

    print("  ", "copying results")
    shutil.copytree(
        "results/flagged_programs", f"{TOP_DIR}/experiment{i+1}/flagged_programs"
    )
    if experiment["md"] < 7:
        shutil.copyfile("results/report.pdf", f"{TOP_DIR}/experiment{i+1}/report.pdf")
        shutil.copytree(
            "analysis/latex/generated_latex",
            f"{TOP_DIR}/experiment{i+1}/generated_latex",
        )
    else:
        print("  ", f"skipping report and latex since md={experiment['md']}")

    meta = experiment.copy()

    number_of_flagged = len(os.listdir("results/flagged_programs/"))
    meta[
        "number_of_flagged_files"
    ] = f"{number_of_flagged}/{experiment['pn']}: {100 * number_of_flagged / experiment['pn']:.2f}%"
    if experiment["md"] < 7 and number_of_flagged > 0:
        latex_meta = json.load(open("analysis/latex/generated_latex/meta.json"))
        for key, value in latex_meta.items():
            meta[
                f"H0_dropped_in_{key}"
            ] = f"{value}/{number_of_flagged}: {100 * value / number_of_flagged:.2f}%"

    print("  ", "writing meta")
    with open(f"{TOP_DIR}/experiment{i+1}/meta.json", "w") as f:
        json.dump(meta, f)
