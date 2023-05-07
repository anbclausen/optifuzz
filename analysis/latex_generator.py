#!/usr/bin/env python3
import string
from typing_extensions import override
import pandas as pd
import numpy as np
import os
import re
import itertools
from dataclasses import dataclass
import subprocess

# Constants for parsing
CLOCKS_COLUMN = 'clock_cycles'
RESULTS_FOLDER = '../fuzzer/results'
LATEX_FOLDER = 'latex'
LATEX_OUTPUT_FOLDER = f'{LATEX_FOLDER}/generated_latex'
FLAGGED_FOLDER = 'flagged'

# Output constants
NO_OF_BINS = 100
COLORS = ["firstCol", "secondCol", "thirdCol", "fourthCol", "fifthCol", "sixthCol"]
X_LABEL = "CPU Clocks"
Y_LABEL = "Frequency"
X_MARGIN = 1.03 # Controls margin to both sides of x-axis
Y_MARGIN = 1.05 # Controls margin to top of y-axis



class TexString:
    def __init__(self, str):
        self.str = str
    def finalize(self) -> string:
        return self.str

class TexBlock:
    def __init__(self):
        self.children = []
        self.start = None
        self.end = None

    def add_child(self, block):
        self.children.append(block)
        return self
    
    def append_string(self, str):
        self.children.append(TexString(str))

    def finalize(self) -> string:
        return "".join([x.finalize() for x in self.children])

class TexFigure(TexBlock):
    def __init__(self):
        super().__init__()
        self.start = "\\begin{figure}[H]\n"
        self.end = "\\end{figure}\n"
    
    def finalize(self) -> string:
        return self.start+super().finalize()+self.end

class TexSubFigure(TexBlock):
    def __init__(self, width, caption=None):
        super().__init__()
        self.start = f"\\begin{{subfigure}}[T]{{{width}\\textwidth}}\n"
        self.end = "\\end{subfigure}\n"
        self.caption = f"\\caption*{{{caption}}}\n" if caption is not None else ""
    
    def finalize(self) -> string:
        return self.start+self.caption+super().finalize()+self.end
    
class TexLrbox(TexBlock):
    def __init__(self):
        super().__init__()
        self.start = "\\begin{lrbox}{\\mybox}%\n"
        self.end = "\\end{lrbox}\\resizebox{\\textwidth}{!}{\\usebox{\\mybox}}\n"
    
    def finalize(self) -> string:
        return self.start+super().finalize()+self.end
    
class TexTikzPic(TexBlock):
    def __init__(self, xmin, xmax, ymax, color, data):
        super().__init__()
        self.start = None
        self.end = None
        self.tikzpic = \
        f"""\\begin{{tikzpicture}}[>=latex]
            \\begin{{axis}}[
                axis x line=center,
                axis y line=center,
                scaled y ticks=base 10:-3,
                ytick scale label code/.code={{}},
                yticklabel={{\\pgfmathprintnumber{{\\tick}} k}},
                xlabel={{{X_LABEL}}},
                ylabel={{{Y_LABEL}}},
                x label style={{at={{(axis description cs:0.5,-0.1)}},anchor=north}},
                y label style={{at={{(axis description cs:-0.1,.5)}},rotate=90,anchor=south,yshift=4mm}},
                area style,
                ymin= 0,
                xmin={xmin},
                xmax={xmax},
                ymax={ymax}
                ]
                \\addplot+ [ybar interval,mark=no,
                color={color},
                fill={color}, 
                fill opacity=0.5] table {{
                    {data}
                }};
            \\end{{axis}}
            \\end{{tikzpicture}}%
        """
        
    @override
    def add_child(self, block):
        raise Exception("It does not make sense to nest anything in a Tikzpicture yet") 

    def finalize(self) -> string:
        return self.tikzpic

class TexLstlisting(TexBlock):
    def __init__(self, style, code):
        super().__init__()
        self.start = f"\\begin{{lstlisting}}[{style}]\n"
        self.end = "\\end{lstlisting}\n"
        self.code = code
    
    def finalize(self) -> string:
        return self.start+self.code+super().finalize()+self.end



def run(args):
    return subprocess.run(args, capture_output=True, text=True).stdout

def parse_aux_info(aux):
    """Parses first line of CSV fuzzing data
    (Currently only returns used compiler flag)

    Parameters
    ----------
    aux : str
        Auxiliary information in CSV
    """
    # Find occurrences of [---] in the string
    re_brackets = re.findall(r'\[.*?\]', aux)
    # Remove brackets from each match
    res = list(map(lambda x: x.replace("[", "").replace("]", ""), re_brackets))
    compiler_flag = res[0]
    return compiler_flag


def gen_header(prog_id: str, prog_seed: str):
    """Generates a latex header for the program

    Returns
    ----------
    Header as LaTeX string
    """
    return f"\\textbf{{Program {prog_id}}} -- \\texttt{{Seed {prog_seed}}}\n"

@dataclass
class ParsedCSV:
    clocks: pd.Series
    compile_flag: str

def parse_csv(file):
    """Generates a LaTeX figure for the CSV-files provided.\n
    CPU-clocks will be plotted and colored.\n
    Assembly lstlistings will also be generated.

    Parameters
    ----------
    file : str
        File path and name to parse

    Returns
    ----------
    A ParsedCSV containing compile-flag used and all measured clocks as a pd series
    """
    # Read first line of CSV containing auxiliary information
    with open(file) as f: aux_info = f.readline()
    compile_flag = parse_aux_info(aux_info)

    # Read the rest of the CSV - skip the auxiliary line
    df = pd.read_csv(file, sep=",", skiprows=[0])

    min_clock, max_clock = df[CLOCKS_COLUMN].min(), df[CLOCKS_COLUMN].max()
    diff = max_clock-min_clock
    # Cap the bins_count to NO_OF_BINS.
    # If we have fewer than the cap, then just use that amount of bins
    bins_count = diff if diff < NO_OF_BINS else NO_OF_BINS

    # Generate labels for bins
    edges = np.linspace(min_clock, max_clock, bins_count+1).astype(int)
    labels = [edges[i]+round((edges[i+1]-edges[i])/2) for i in range(bins_count)]

    # Group into bins, receiving a list of (interval, count)
    clocks = pd.cut(df[CLOCKS_COLUMN], bins=bins_count,labels=labels).value_counts(sort=False)  

    return ParsedCSV(clocks, compile_flag)

def get_program_source(seed):
    """Retrieves source code of program.

    Parameters
    ----------
    seed : str
        Seed of fuzzed data
    """
    # Read program
    file_reader = open(f'{FLAGGED_FOLDER}/{seed}.c', "r") 
    prog = file_reader.read()
    file_reader.close()
    # Replace first 3 lines with ...
    prog = "...\n"+prog.split("\n",2)[2]
    return prog

def trim_assembly(asm):
    """Trims start and end of provided assembly.\n
    Searches specifically after .LFE0 and trims everything
    after that point. Also trims away the first 4 lines.

    Parameters
    ----------
    asm : str
        Assembly given as string
    """
    # Split to list of instructions instead and search for LFE0
    asm = asm.split("\n") 
    LFE0 = next(i for i, s in enumerate(asm) if s.startswith(".LFE0"))
    # Trim at start and end, and return the string
    asm[4] = "..."
    asm[LFE0] = "..."
    asm = '\n'.join(asm[4:LFE0+1])
    return asm

def gen_plot_asm_fig(seed, parsed_csv: list[ParsedCSV], colors):
    """Generates a LaTeX figure for the CSV-files provided.\n
    CPU-clocks will be plotted and colored.\n
    Assembly lstlistings will also be generated.

    Parameters
    ----------
    seed : str
        Seed of fuzzed data
    parsed_csv : list[ParsedCSV]
        List of parsed CSV files
    colors : str list
        List of colors to use for the plots

    Returns
    ----------
    LaTeX figure as string
    """
    if len(colors) < len(parsed_csv):
        ex = f"Not enough colors to color parsed CSVs. " \
             f"Colors: {len(colors)} - CSVs: {len(parsed_csv)}"
        raise Exception(ex)
    
    # Determine the width according to what we can fit
    # i.e. len(parse_csv) = 3  ==>  width = 0.3
    width = 1/len(parsed_csv)-0.03
    figure = TexFigure()

    # Generate tikzpictures
    for i, csv in enumerate(parsed_csv):
        data = "\n".join(f"{bin} {count}" for bin, count in zip(csv.clocks.index.tolist(), csv.clocks.tolist()))
        xmin = round(csv.clocks.index.min()*1/X_MARGIN)
        xmax = round(csv.clocks.index.max()*X_MARGIN)
        ymax = round(csv.clocks.max()*Y_MARGIN)

        lrbox = TexLrbox().add_child(TexTikzPic(xmin,xmax,ymax,colors[i], data))
        subfig = TexSubFigure(width=width, caption=csv.compile_flag).add_child(lrbox)
        figure.add_child(subfig)

    # Move the first lstlisting a little
    figure.append_string("\\hspace*{6mm}\n")
    # Generate asm lstlistings
    for i, csv in enumerate(parsed_csv):
        asm = run(
            ["gcc", f"{FLAGGED_FOLDER}/{seed}.c", "-S", f"-{csv.compile_flag}", "-w", "-c", "-o", "/dev/stdout"]
        )
        asm = trim_assembly(asm)

        lstlisting = TexLstlisting(
            style="style=defstyle,language={[x86masm]Assembler},basicstyle=\\tiny\\ttfamily,breaklines=true",
            code=asm
        )
        subfig = TexSubFigure(width=width-0.03).add_child(lstlisting)
        figure.add_child(subfig)
        # Don't add hspace after last lstlisting
        if i != len(parsed_csv)-1:
            figure.append_string("\\hspace*{8mm}\n")
    
    return figure.finalize()

def gen_latex_doc(seed, CSV_files, prog_id):
    """Generates all the LaTeX required for the CSV-files provided.

    Parameters
    ----------
    seed : str
        Seed of fuzzed data
    CSV_files : list[str]
        List of file names for the CSV files
    prog_id : int
        Identifier of the program 

    Returns
    ----------
    LaTeX doc as string
    """
    parsed_results = [parse_csv(f"{RESULTS_FOLDER}/{x}") for x in CSV_files]
    prog = get_program_source(seed)
    program_lstlisting = TexLstlisting("style=defstyle,language=C", prog).finalize()

    figure1 = gen_plot_asm_fig(seed, parsed_results[:3], COLORS[:3])
    figure2 = gen_plot_asm_fig(seed, parsed_results[3:], COLORS[3:])
    new_page = "\\newpage"

    header = gen_header(prog_id, seed)
    first_page = header+program_lstlisting+figure1+new_page
    second_page = header+figure2+new_page

    return first_page+second_page


if __name__ == '__main__':
    # Retrieve all generated seeds
    all_seeds = list(map(lambda x: x.replace(".c", ""), os.listdir(FLAGGED_FOLDER)))
    # Map seed to available results, i.e. seed -> [O0, O2, O3]
    all_fuzzing_results = itertools.groupby(sorted(os.listdir(RESULTS_FOLDER)), lambda x: re.search(r'\d+', x).group())

    # For each program/seed; create a .tex file in the output folder
    for id, (seed, CSV_files) in enumerate(all_fuzzing_results, 1):
        latex = gen_latex_doc(seed, list(CSV_files), id)
        f = open(f"{LATEX_OUTPUT_FOLDER}/prog{id}.tex", "w")
        f.write(latex)
        f.close()




