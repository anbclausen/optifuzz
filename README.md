# optimizer-fuzzer-c

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

Goal of today:
  - make all: generér en LaTeX-fil + pdf med sektioner der indeholder kode, grafer, compileflags og stats: så mange ud af så mange...