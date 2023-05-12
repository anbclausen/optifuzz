# Optifuzz
Welcome to Optifuzz! A tool for fuzzing randomly generated C code with different optimization flags to discover side-channel vulnerabilities.

## Prerequisites
You should have `ocaml`, `dune`, `python3`, all python packages in `requirements.txt` installed.

## Documentation
```
make generate pn=? md=?             # generates 'pn' programs with ASTs of a 
                                    # maximum depth of 'md'

make generate-seeded s=? md=?       # generates 1 program from seed 's' with AST
                                    # of maximum depth of 'md'

make inspect c=?                    # compiles all programs in analysis/programs
                                    # with compiler 'c', inspects the assembly 
                                    # and flags code with jumps

make generate-inspect pn=? md=? c=? # generates and inspects code

make fuzz in=?                      # fuzzes all programs that were flagged from
                                    # the assembly inspection with 'in' inputs

make visualize                      # visualizes results from fuzzing

make all pn=? md=? c=? in=?         # runs the whole pipeline: generates, 
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
  - Graph that shows computation time vs. fuzz # (to detect low level CPU optimizations)
  - Write jumps: jle, je, ...
  - Visualize different fuzz classes with the rainbow technique
- Misc.
  - Describe all dependencies used for this project
    
