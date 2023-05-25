experiments = [
    {
        "compiler": "gcc",
        "compile_flags": ["O0"],
        "fuzz_classes": [
            "uniform",
            "equal",
            "max64",
            "fixed",
            "xzero",
            "yzero",
            "xlty",
            "yltx",
            "small",
        ],
        "pn": 100000,
        "md": 4,
        "in": 1000,
    },
    {
        "compiler": "gcc",
        "compile_flags": ["O1"],
        "fuzz_classes": [
            "uniform",
            "equal",
            "max64",
            "fixed",
            "xzero",
            "yzero",
            "xlty",
            "yltx",
            "small",
        ],
        "pn": 100000,
        "md": 4,
        "in": 1000,
    },
    {
        "compiler": "gcc",
        "compile_flags": ["O2"],
        "fuzz_classes": [
            "uniform",
            "equal",
            "max64",
            "fixed",
            "xzero",
            "yzero",
            "xlty",
            "yltx",
            "small",
        ],
        "pn": 100000,
        "md": 4,
        "in": 1000,
    },
    {
        "compiler": "gcc",
        "compile_flags": ["O3"],
        "fuzz_classes": [
            "uniform",
            "equal",
            "max64",
            "fixed",
            "xzero",
            "yzero",
            "xlty",
            "yltx",
            "small",
        ],
        "pn": 100000,
        "md": 4,
        "in": 1000,
    },
    {
        "compiler": "gcc",
        "compile_flags": ["Os"],
        "fuzz_classes": [
            "uniform",
            "equal",
            "max64",
            "fixed",
            "xzero",
            "yzero",
            "xlty",
            "yltx",
            "small",
        ],
        "pn": 100000,
        "md": 4,
        "in": 1000,
    },
    {
        "compiler": "gcc",
        "compile_flags": ["O0"],
        "fuzz_classes": [
            "uniform",
            "equal",
            "max64",
            "fixed",
            "xzero",
            "yzero",
            "xlty",
            "yltx",
            "small",
        ],
        "pn": 1000,
        "md": 12,
        "in": 100,
    },
    {
        "compiler": "gcc",
        "compile_flags": ["O1"],
        "fuzz_classes": [
            "uniform",
            "equal",
            "max64",
            "fixed",
            "xzero",
            "yzero",
            "xlty",
            "yltx",
            "small",
        ],
        "pn": 1000,
        "md": 12,
        "in": 100,
    },
    {
        "compiler": "gcc",
        "compile_flags": ["O2"],
        "fuzz_classes": [
            "uniform",
            "equal",
            "max64",
            "fixed",
            "xzero",
            "yzero",
            "xlty",
            "yltx",
            "small",
        ],
        "pn": 1000,
        "md": 12,
        "in": 100,
    },
    {
        "compiler": "gcc",
        "compile_flags": ["O3"],
        "fuzz_classes": [
            "uniform",
            "equal",
            "max64",
            "fixed",
            "xzero",
            "yzero",
            "xlty",
            "yltx",
            "small",
        ],
        "pn": 1000,
        "md": 12,
        "in": 100,
    },
    {
        "compiler": "gcc",
        "compile_flags": ["Os"],
        "fuzz_classes": [
            "uniform",
            "equal",
            "max64",
            "fixed",
            "xzero",
            "yzero",
            "xlty",
            "yltx",
            "small",
        ],
        "pn": 1000,
        "md": 12,
        "in": 100,
    },
    {
        "compiler": "clang",
        "compile_flags": ["O0"],
        "fuzz_classes": [
            "uniform",
            "equal",
            "max64",
            "fixed",
            "xzero",
            "yzero",
            "xlty",
            "yltx",
            "small",
        ],
        "pn": 10000,
        "md": 4,
        "in": 1000,
    },
    {
        "compiler": "clang",
        "compile_flags": ["O1"],
        "fuzz_classes": [
            "uniform",
            "equal",
            "max64",
            "fixed",
            "xzero",
            "yzero",
            "xlty",
            "yltx",
            "small",
        ],
        "pn": 10000,
        "md": 4,
        "in": 1000,
    },
    {
        "compiler": "clang",
        "compile_flags": ["O2"],
        "fuzz_classes": [
            "uniform",
            "equal",
            "max64",
            "fixed",
            "xzero",
            "yzero",
            "xlty",
            "yltx",
            "small",
        ],
        "pn": 10000,
        "md": 4,
        "in": 1000,
    },
    {
        "compiler": "clang",
        "compile_flags": ["O3"],
        "fuzz_classes": [
            "uniform",
            "equal",
            "max64",
            "fixed",
            "xzero",
            "yzero",
            "xlty",
            "yltx",
            "small",
        ],
        "pn": 10000,
        "md": 4,
        "in": 1000,
    },
    {
        "compiler": "clang",
        "compile_flags": ["Os"],
        "fuzz_classes": [
            "uniform",
            "equal",
            "max64",
            "fixed",
            "xzero",
            "yzero",
            "xlty",
            "yltx",
            "small",
        ],
        "pn": 10000,
        "md": 4,
        "in": 1000,
    },
]

small_experiments = [
    {
        "compiler": "gcc",
        "compile_flags": ["O1", "O2", "O3", "Os"],
        "fuzz_classes": ["uniform", "fixed"],
        "pn": 500,
        "md": 4,
        "in": 1000,
    },
]

import os
import json
import shutil
import datetime


now = datetime.datetime.now().strftime("%Y-%m-%d-%H-%M-%S")
print("EXPERIMENTS: ", now)
TOP_DIR = f"experiments/{now}"

number_of_experiments = len(experiments)


def run(args: str) -> str:
    return os.system(args)


for i, experiment in enumerate(small_experiments):
    print("RUNNING EXPERIMENT", i + 1, "/", number_of_experiments)
    print("  ", "making folder")
    os.makedirs(f"{TOP_DIR}/experiment{i}", exist_ok=True)
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

        run("sudo taskset --cpu-list 1 nice -n -20 make inspect") # makes this go brr
        run(f"sudo taskset --cpu-list 2 nice -n -20 make fuzz in={experiment['in']}")
        run("make latexgen")
        run("make latexcompile")
    except:
        print("  ^-", "experiment failed - salvaging results")

    print("  ", "copying results")
    shutil.copyfile("results/report.pdf", f"{TOP_DIR}/experiment{i}/report.pdf")
    shutil.copytree(
        "results/flagged_programs", f"{TOP_DIR}/experiment{i}/flagged_programs"
    )
    shutil.copytree(
        "analysis/latex/generated_latex", f"{TOP_DIR}/experiment{i}/generated_latex"
    )

    meta = experiment.copy()
    meta[
        "number_of_flagged_files"
    ] = f"{len(os.listdir('results/flagged_programs/'))}/{experiment['pn']}"

    print("  ", "writing meta")
    with open(f"{TOP_DIR}/experiment{i}/meta.json", "w") as f:
        json.dump(meta, f)
