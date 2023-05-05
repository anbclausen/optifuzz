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

make all                            # runs the whole pipeline: generates, moves,
                                    # inspects, fuzzes and analyzes

make clean                          # cleans all generated files in all steps of
                                    # the process
```

## TODO
- Skriv fuzzer færdig, lav minimal C kode
- Python script til at analysere kode
- Compile programmer med mange forskellige compile flags for at se hvilke flags, der giver problemer
- Lav liste over farlige branching instruktioner
- Lav custom værdier for tests (0, MAXINT, ...)
- Document code
- Make timing more robust
- Make classes of fuzzing inputs
- Fix visualize script
  - Output LaTeX and compile it
  - move into analyze folder

The goal of today:
  - make all: generér en LaTeX-fil + pdf med sektioner der indeholder kode, grafer, compileflags og stats: så mange ud af så mange...