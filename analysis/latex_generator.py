#!/usr/bin/env python3
import string
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
COLORS = ["firstCol", "secondCol", "thirdCol", "fourthCol", "fifthCol"]
X_LABEL = "CPU Clocks"
Y_LABEL = "Frequency"


def parse_aux_info(aux):
    """Parses first line of CSV fuzzing data

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



def gen_header(prog_id, prog_seed):
    return f"\\textbf{{Program {prog_id}}} -- \\texttt{{Seed {prog_seed}}}\n"

def gen_lstlisting(style, code):
    prog_pre = f"\\begin{{lstlisting}}[{style}]\n"
    prog_post = "\\end{lstlisting}\n"
    return prog_pre+code+prog_post


def gen_tikzpic(data, xmin, xmax, ymax, color):
    tikzpic = f"""
    \\begin{{tikzpicture}}[>=latex]
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

    return tikzpic

def gen_lrbox_wrapper(body):
    start_lrbox = "\\begin{lrbox}{\\mybox}%\n"
    end_lrbox = "\\end{lrbox}\\resizebox{\\textwidth}{!}{\\usebox{\\mybox}}\n"
    return start_lrbox+body+end_lrbox


def gen_subfig(body, width, caption=None):
    start_fig = f"\\begin{{subfigure}}[T]{{{width}\\textwidth}}\n"
    caption = f"\\caption*{{{caption}}}\n" if caption is not None else ""
    end_fig = "\\end{subfigure}\n"
    return start_fig+caption+body+end_fig


def gen_fig(body, centering=False):
    start_fig = "\\begin{figure}[H]\n"
    centering = "\\centering\n" if centering else ""
    end_fig = "\\end{figure}\n"
    return start_fig+centering+body+end_fig




@dataclass
class ParsedCSV:
    clocks: pd.Series
    compile_flag: str

def parse_csv(file):
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



def run(args):
    return subprocess.run(args, capture_output=True, text=True).stdout

def get_program_source(seed):
    # Read program
    file_reader = open(f'{FLAGGED_FOLDER}/{seed}.c', "r") 
    prog = file_reader.read()
    file_reader.close()
    # Replace first 3 lines with ...
    prog = "...\n"+prog.split("\n",2)[2]
    return prog


class TexBlock:
    def __init__(self):
        self.children = []
        self.start = None
        self.end = None

    def add_child(self, block):
        self.children.append(block)
        return self

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
    
    def finalize(self) -> string:
        return self.tikzpic+super().finalize()


def gen_latex_doc(seed, CSV_files, prog_id):
    """Generates all the LaTeX required for the CSV-files provided

    Parameters
    ----------
    seed : str
        Seed of fuzzed data
    CSV_files : str list
        List of file names of CSV_files
    prog_id : int
        Identifier of the program 
    """

    # first_page_fig = figure_builder()
    # for i, csv in enum(parsed[:3])
    #   data = ...
    #   tikzpic = gen_tikzpic(data).set_color(COLOURS[i])
    #   subfig = subfig_builder(width=0.3).add_lrbox().add_tikzpic(tikzpic).finalize()
    #   first_page_fig.add_subfig(subfig)
    # first_page_fig.finalize()

    parsed_results = [parse_csv(f"{RESULTS_FOLDER}/{x}") for x in CSV_files]
    prog = get_program_source(seed)

    header = gen_header(prog_id, seed)
    program_lstlisting = gen_lstlisting("style=defstyle,language=C",prog)

    figure = TexFigure()
    for i, csv in enumerate(parsed_results[:3]):
        data = "\n".join(f"{bin} {count}" for bin, count in zip(csv.clocks.index.tolist(), csv.clocks.tolist()))
        xmin = csv.clocks.index.min()
        xmax = csv.clocks.index.max()
        ymax = round(csv.clocks.max()*1.05)

        lrbox = TexLrbox().add_child(TexTikzPic(xmin,xmax,ymax,COLORS[i], data))
        subfig = TexSubFigure(width=0.3, caption=csv.compile_flag).add_child(lrbox)
        figure.add_child(subfig)
    print(figure.finalize())
    subfigs = figure.finalize()

    #subfigs = ""
    #for i, csv in enumerate(parsed_results[:3]):
    #    data = "\n".join(f"{bin} {count}" for bin, count in zip(csv.clocks.index.tolist(), csv.clocks.tolist()))
    #    subfigs += gen_subfig(gen_lrbox_wrapper(gen_tikzpic(data, csv.clocks.index.min()-10, csv.clocks.index.max()+10, round(csv.clocks.max()*1.05), COLORS[i])), 0.3, csv.compile_flag)

        # TODO: Refactor to builder pattern maybe?
        #fig1 = gen_subfig(gen_lrbox_wrapper(gen_tikzpic(data, p.clocks.min()-10, p.clocks.max()+10, round(p.clocks.max()*1.05), "firstCol")), 0.3, p.compile_flag)
        #fig2 = gen_subfig(gen_lrbox_wrapper(gen_tikzpic(data, p.clocks.min()-10, p.clocks.max()+10, round(p.clocks.max()*1.05), "secondCol")), 0.3, p.compile_flag)
        #fig3 = gen_subfig(gen_lrbox_wrapper(gen_tikzpic(data, p.clocks.min()-10, p.clocks.max()+10, round(p.clocks.max()*1.05), "thirdCol")), 0.3, p.compile_flag)
    
    #figs = gen_fig(subfigs, centering=False)

    # TODO Like this:
    # fig1 = gen_subfig(0.3, "GCC O0").add_lrbox()
    # fig1 = fig1.add_tikzpic(data, min_clock-10, max_clock+10, round(clocks.max(), -4), "firstCol")
    # ....
    # three_figs = gen_fig(centering=True).add_subfig(fig1).add_subfig(fig2).add_subfig(fig3).finalize()

    subfigs += "\\hspace*{6mm}\n"
    for i, csv in enumerate(parsed_results[:3]):
        temp = run(
            ["gcc", f"{FLAGGED_FOLDER}/{seed}.c", "-S", f"-{csv.compile_flag}", "-w", "-c", "-o", "/dev/stdout"]
        ).split("\n") # List of instructions
        
        LFE0 = next(i for i, s in enumerate(temp) if s.startswith(".LFE0"))
        temp[4] = "..."
        temp[LFE0] = "..."
        temp = '\n'.join(temp[4:LFE0+1])
        subfigs += gen_subfig(gen_lstlisting("style=defstyle, language={[x86masm]Assembler},basicstyle=\\tiny\\ttfamily, breaklines=true",temp), 0.27)
        if i != 2:
            subfigs += "\\hspace{8mm}\n"

    asm = gen_fig(subfigs, centering=False)




    new_page = "\\newpage"

    # Second page:
    subfigs = ""
    for i, csv in enumerate(parsed_results[3:],3):
        data = "\n".join(f"{bin} {count}" for bin, count in zip(csv.clocks.index.tolist(), csv.clocks.tolist()))
        subfigs += gen_subfig(gen_lrbox_wrapper(gen_tikzpic(data, csv.clocks.index.min()-10, csv.clocks.index.max()+10, round(csv.clocks.max()*1.05), COLORS[i])), 0.3, csv.compile_flag)
    #figs2 = gen_fig(subfigs, centering=False)


    #subfigs = ""
    for i, csv in enumerate(parsed_results[3:]):
        temp = run(
            ["gcc", f"{FLAGGED_FOLDER}/{seed}.c", "-S", f"-{csv.compile_flag}", "-w", "-c", "-o", "/dev/stdout"]
        ).split("\n") # List of instructions
        
        LFE0 = next(i for i, s in enumerate(temp) if s.startswith(".LFE0"))
        temp[4] = "..."
        temp[LFE0] = "..."
        temp = '\n'.join(temp[4:LFE0+1])
        subfigs += gen_subfig(gen_lstlisting("style=defstyle, language={[x86masm]Assembler},basicstyle=\\tiny\\ttfamily,framexrightmargin=-8mm,breaklines=true",temp), 0.3)
        if i != 2:
            subfigs += "\\hspace{8mm}\n"

    asm2 = gen_fig(subfigs, centering=False)

    return header+program_lstlisting+asm+new_page+header+asm2+new_page


all_seeds = list(map(lambda x: x.replace(".c", ""), os.listdir(FLAGGED_FOLDER)))
# Groups by seed, i.e. seed -> [O0, O2, O3]
all_fuzzing_results = itertools.groupby(sorted(os.listdir(RESULTS_FOLDER)), lambda x: re.search(r'\d+', x).group())

for id, (seed, CSV_files) in enumerate(all_fuzzing_results, 1):
    latex = gen_latex_doc(seed, list(CSV_files), id)
    f = open(f"{LATEX_OUTPUT_FOLDER}/prog{id}.tex", "w")
    f.write(latex)
    f.close()




