# Optifuzz
Welcome to Optifuzz! A tool for fuzzing randomly generated C code with different optimization flags to discover side-channel vulnerabilities. This tool was made for the Language-Based Security course at Aarhus University.

## Prerequisites
You should have `ocaml`, `dune`, `python3`, and all python packages in `python_requirements.txt` installed.

## Paper
We made a paper describing the tool and our findings with it. It can be found in the `paper` folder.

## Documentation
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

make visualize                      # visualizes results from fuzzing

make all pn=? md=? in=?             # runs the whole pipeline: generates, 
                                    # inspects, fuzzes and analyzes

make latexgen                       # generates results of CSVs in: 
                                    # "analysis/latex/generated_latex". Compile: 
                                    # "analysis/latex/master.tex" for a preview

make clean                          # cleans all generated files in all steps of
                                    # the process
```

## Sources
- [C operators](https://devdocs.io/c/language/operator_arithmetic): List of all arithmetic operators in C. Used as a basis for defining should-be-constant-time ASTs.

## TODO
- LaTeX
  - Write jumps: jle, je, ...
  - Ensure documentation and refactor if necessary
- Fuzzer
  - Refactor `fuzzer` - especially kernel module
  - Fix the kernel module `make clean` bug
  - Ensure documentation and refactor if necessary
- Generation
  - Generate uniformly random ASTs
  - Introduce `SmallIntLit` and `TinyIntLit`
  - Ensure documentation and refactor if necessary
- General
  - Make whole pipeline consistent with config.json
- Docs 
  - Make better list of requirements
  - Make sure `make` guide is up to date