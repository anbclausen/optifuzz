# OptiFuzz
Welcome to OptiFuzz! A tool for fuzzing randomly generated C code with different optimization flags to discover time-based side-channel vulnerabilities. This tool was made for the Language-Based Security course at Aarhus University.

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

***Note**: This runs on an Intel x86-64 processor. However, we got some bad results when fuzzing on an AMD processor. Our usage of the TSC register for timing is primarily based on how the serializing CPUID and the TSC read instructions work according to Intel's documentation. Thus, it is possible that AMD's implementation differs slightly. Your mileage may vary.*

## Paper
We made a paper describing the tool and our findings with it. It can be found in the `paper` folder.

## Configuration
You can configure the OptiFuzz in the `config.json` file. Here you can
- Configure what C compiler you want to use.
- Configure what optimization flags you would like to test on.
- Configure what kind of type of inputs you would like to fuzz with. We have defined a selection of "input classes":
  - `uniform`: Inputs are 64-bit uniformly random numbers.
  - `equal`: Inputs are 64-bit uniformly random numbers, but equal.
  - `max64`: One input is `INT64_MAX` while the other is uniformly random.
  - `xzero`: `x` is 0 while `y` is uniformly random.
  - `yzero`: `y` is 0 while `x` is uniformly random.
  - `xlty`: Inputs are 64-bit uniformly random numbers, but the first input is smaller than the second.
  - `yltx`: Inputs are 64-bit uniformly random numbers, but the second input is smaller than the first.
  - `small`: Inputs are 8-bit uniformly random numbers.
  - `fixed`: Both inputs are fixed to `0x12345678`. This input class is required for statistical analysis purposes (Welch's T-test) that automatically flags programs with timing vulnerabilities based on fuzzing. Additionally, the input class `uniform` should also be enabled for automatic statistical analysis.

###
To make the measurement more accurate (less noise), consider running fuzzing on a single thread and with decreased niceness.
In Linux this can be done like so:
```
# taskset --cpu-list {cpu index} nice -n -20 make fuzz in={number of fuzzing inputs}
```
Note that -20 niceness is the lower cap, and will drastically decrease the number of context switches and interrupts when fuzzing.

## Documentation
`make` targets have been added for the whole pipeline. To run the whole pipeline, do 
```
make all pn={# of random programs to generate} md={max depth of the generated ASTs} in={# of inputs the programs should be fuzzed with}
```
At the end you will have a generated pdf report visualizing the results, the code, the assembly and some analysis in. The saved location is specified in config.json and the default is`results/master.pdf`.

As an example `make all pn=1000 md=5 in=100000` will run the whole pipeline on 1000 random programs with ASTs of maximum depth 5 where each program is fuzzed with 100000 inputs.

Note that `in` describes the total number of inputs a given program will be fuzzed with distributed over the input classes.

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

make experiments                    # a collection of relevant experiments to 
                                    # run. WARNING: takes multiple hours and
                                    # is set up for Linux, and uses sudo
```

## Improvements
- General
  - Compile object (.o) files once doing assembly inspection and use these for fuzzing and latex generation. No need to compile do i multiple times.
  