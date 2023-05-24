# OptiFuzz
Welcome to OptiFuzz! A tool for fuzzing randomly generated C code with different optimization flags to discover side-channel vulnerabilities. This tool was made for the Language-Based Security course at Aarhus University.

## Prerequisites
OptiFuzz depends on a few languages and libraries:
- You should have [OCaml](https://ocaml.org/docs/up-and-running) and [Dune](https://dune.readthedocs.io/en/stable/quick-start.html) installed (used for generating the programs).
- A  [Latex](https://www.latex-project.org/) environment with appropriate libraries for generating the analysis report.
- The GNU C compiler from [GCC](https://gcc.gnu.org/) (used for some tasks) and any other C compiler you would like to analyze the output of (like [clang](https://clang.llvm.org/)).
- The [Make](https://www.gnu.org/software/make/) tool is used to build and run the different parts of the project.
- [Python3](https://www.python.org/downloads/) installed alongside all Python packages listed in `python_requirements.txt`. These can be installed with
```
$ pip install -r python_requirements.txt
```
- The fuzzer can optionally be run as a kernel module to remove noise from preempting and interrupts. **Note** that this is not the intended use of a kernel module, but it ensures more consistent timing. To use this feature, make sure you have the Linux kernel headers matching your kernel version installed. You will need root privileges to insert/remove the module (sudo is sufficient). The module has been tested on kernel version 6.3.2. To see messages from the kernel module run
```
# dmesg -w
```


## Paper
We made a paper describing the tool and our findings with it. It can be found in the `paper` folder.

## Configuration
You can configure the OptiFuzz in the `config.json` file. Here you can
- Configure what C compiler you want to use.
- Configure what optimization flags you would like to test on.
- Configure what kind of type of inputs you would like to fuzz with. We have defined a selection of "fuzzing classes":
  - `uniform`: Inputs are 64-bit uniformly random numbers.
  - `equal`: Inputs are 64-bit uniformly random numbers, but equal.
  - `max64`: One input is `INT64_MAX` while the other is uniformly random.
  - `umax64`: One input is `UINT64_MAX` while the other is uniformly random.
  - `zero`: One input is 0 while the other is uniformly random.
  - `xlty`: Inputs are 64-bit uniformly random numbers, but the first input is smaller than the second.
  - `yltx`: Inputs are 64-bit uniformly random numbers, but the second input is smaller than the first.
  - `small`: Inputs are 8-bit uniformly random numbers.
- Configure if you would like to run the fuzzing in "kernel mode" where context switching and many CPU optimizations are disabled. This will decrease the noise of your results, however, the outcome depends on your specific system.

## Documentation
`make` targets have been added for the whole pipeline. To run the whole pipeline, do `make all pn={# of random programs to generate} md={max depth of the generated ASTs} in={# of inputs the programs should be fuzzed with}`. At the end you will have a generated pdf report visualizing the results, the code, the assembly and some analysis in `analysis/latex/master.pdf`.

As an example `make all pn=1000 md=5 in=100000` will run the whole pipeline on 1000 random programs with ASTs of maximum depth 5 where each program is fuzzed with 100000 inputs.

Note that `in` describes the number of inputs a given program will be fuzzed with for _each_ fuzzing class.

For a full description of the `make` targets, see:
```
make generate pn=? md=?             # generates 'pn' programs with ASTs of a 
                                    # maximum depth of 'md'

make generate-seeded s=? md=?       # generates 1 program from seed 's' with AST
                                    # of maximum depth of 'md'

make inspect                        # compiles all programs in analysis/programs, 
                                    # inspects the assembly and flags code with 
                                    # jumps

make generate-inspect pn=? md=?     # generates and inspects code

make fuzz in=?                      # fuzzes all programs that were flagged from
                                    # the assembly inspection with 'in' inputs

make latexgen                       # generates results of CSVs in: 
                                    # "analysis/latex/generated_latex". compile: 
                                    # "analysis/latex/master.tex" for a preview

make latexcompile                   # compiles the generated LaTeX with pdflatex

make all pn=? md=? in=?             # runs the whole pipeline: generates, 
                                    # inspects, fuzzes, analyzes and visualizes

make clean                          # cleans all generated files in all steps of
                                    # the process
```

## Sources
- [C operators](https://devdocs.io/c/language/operator_arithmetic): List of all arithmetic operators in C. Used as a basis for defining should-be-constant-time ASTs.

## TODO
- LaTeX
  - Note which compiler version was used and (if kernel mode) the kernel version.
  - Write jumps: jle, je, ...
  - Ensure documentation and refactor if necessary
  - For each result page, write all the meta data (what compiler, what flags were tested, what fuzz classes were used, ...)
- Fuzzer
  - Option to set higher priority (lower niceness) to avoid too many context switches. At least when running in userland. Requires root (use setpriority).
- General
  - Compile object (.o) files once doing assembly inspection and use these for fuzzing and latex generation. No need to compile do i multiple times.
  - Make whole pipeline consistent with config.json
  - Add all folders used in the pipeline to config.json, and move them to the root folder of the project.

## Notes
- It seems like `expr << expr` and `y op (x == const)` are causing branching. Would be awesome to find some real-life examples of tricks like these being used in crypto libraries.
- OptiFuzz might be used in a CI pipeline to detect timing vulnerabilities automatically.
- We should only have a few analysis results in the appendix since including all would be overwhelming.
