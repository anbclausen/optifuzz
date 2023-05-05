# Optifuzz
Welcome to Optifuzz! A tool for fuzzing randomly generated C code with different optimization flags to discover side-channel vulnerabilities.

## Documentation
```
make generate pn=? md=?             # generates 'pn' programs with ASTs of a 
                                    # maximum depth of 'md'

make generate-seeded s=? md=?       # generates 1 program from seed 's' with AST
                                    # of maximum depth of 'md'

make move-generated                 # moves generated programs to the analysis
                                    # folder - prerequisite for inspect

make inspect c=?                    # compiles all programs in analysis/programs
                                    # with compiler 'c', inspects the assembly 
                                    # and flags code with jumps

make generate-inspect pn=? md=? c=? # generates, moves and inspects code

make fuzz                           # ???

make visualize                      # ???

make all pn=? md=? c=?              # runs the whole pipeline: generates, moves,
                                    # inspects, fuzzes and analyzes

make clean                          # cleans all generated files in all steps of
                                    # the process
```

## Sources
- [C operators](https://devdocs.io/c/language/operator_arithmetic): List of all arithmetic operators in C. Used as a basis for defining should-be-constant-time ASTs.

## TODO
- Fuzzer
  - Make timing more robust
  - Make classes of fuzzing inputs: custom values for tests fx (0, MAXINT, ...)
- Document code
- Fix visualize script
  - Output LaTeX and compile it
    - Include code, graphs, compile flags and stats
    