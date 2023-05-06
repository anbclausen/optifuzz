#!/usr/bin/env python3
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import os
import re

# Constants for parsing
CLOCKS_COLUMN = 'clock_cycles'
RESULTS_FOLDER = 'results'
PROGRAMS_FOLDER = 'flagged'

# Output constants
NO_OF_BINS = 100
TIKZ_AXIS_DEFAULT_SETTINGS = """
axis x line=center,
axis y line=center,
scaled y ticks=base 10:-3,
ytick scale label code/.code={},
yticklabel={\\pgfmathprintnumber{\\tick} k},
xlabel={Clock Count},
ylabel={Frequency},
x label style={at={(axis description cs:0.5,-0.1)},anchor=north},
y label style={at={(axis description cs:-0.1,.5)},rotate=90,anchor=south,yshift=4mm},
area style,
ymin= 0,
"""


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
    seed = res[0]
    compiler_flag = res[1]
    return seed, compiler_flag



def gen_header(prog_id, prog_seed):
    return f"\\textbf{{Program {prog_id}}} -- \\texttt{{Seed {prog_seed}}}\n"

def gen_lstlisting(style, code):
    prog_pre = f"\\begin{{lstlisting}}[{style}]\n"
    prog_post = "\\end{lstlisting}\n"
    return prog_pre+code+prog_post


def gen_tikzpic(data, xmin, xmax, ymax, color):
    start_tikz = "\\begin{tikzpicture}[>=latex]\n"
    begin_axis = "\\begin{axis}["

    end_axis = "\\end{axis}"
    end_tikz = "\\end{tikzpicture}%\n"

    #xmin, xmax, ymax = f"xmin={xmin},\n", f"xmax={xmax},\n", f"ymax={ymax},\n"
    #start_axis = begin_axis+TIKZ_AXIS_DEFAULT_SETTINGS+xmin+xmax+ymax+"]\n"

    plot_section = f"""
    \\addplot+ [ybar interval,mark=no,
    color={color},
    fill={color}, 
    fill opacity=0.5] table {{
        {data}
    }};
    """

    whole_thing = f"""
    \\begin{{tikzpicture}}[>=latex]
    \\begin{{axis}}[
        axis x line=center,
        axis y line=center,
        scaled y ticks=base 10:-3,
        ytick scale label code/.code={{}},
        yticklabel={{\\pgfmathprintnumber{{\\tick}} k}},
        xlabel={{Clock Count}},
        ylabel={{Frequency}},
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

    return whole_thing

def gen_lrbox_wrapper(body):
    start_lrbox = "\\begin{lrbox}{\\mybox}%\n"
    end_lrbox = "\\end{lrbox}\\resizebox{\\textwidth}{!}{\\usebox{\\mybox}}\n"
    return start_lrbox+body+end_lrbox


def gen_subfig(body, width, caption):
    start_fig = f"\\begin{{subfigure}}[T]{{{width}\\textwidth}}\n"
    caption = f"\\caption*{{{caption}}}\n"
    end_fig = "\\end{subfigure}\n"
    return start_fig+caption+body+end_fig


def gen_fig(body, centering=False):
    start_fig = "\\begin{figure}[H]\n"
    centering = "\\centering\n" if centering else ""
    end_fig = "\\end{figure}\n"
    return start_fig+centering+body+end_fig


def gen_latex_doc(file, prog_id):
    """Generates all the LaTeX required for the CSV-file provided

    Parameters
    ----------
    file : str
        Path and file name to a CSV-file for fuzzing data
    prog_id : int
        Identifier of the program 
    """
    # Remove path from file-argument
    csv_filename = os.path.basename(file)
    c_prog_filename = csv_filename.replace(".csv", "")

    # Read first line of CSV containing auxiliary information
    aux_info = ""
    with open(file) as f: aux_info = f.readline()
    prog_seed, compile_flag = parse_aux_info(aux_info)

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

    # Read program
    file_reader = open(f'{PROGRAMS_FOLDER}/{c_prog_filename}', "r") 
    prog = file_reader.read()
    file_reader.close()
    # Replace first 3 lines with ...
    prog = "...\n"+prog.split("\n",3)[3]

    ################################################################
    # TODO: refactor this thing...
    # Everything above really only concerns about setting the 'prog' 
    # 'prog_seed', 'compile_flag', 'clocks' and other variables.
    # Everything below is more latex-generation related
    ################################################################

    header = gen_header(prog_id, prog_seed)
    program_lstlisting = gen_lstlisting("style=defstyle,language=C",prog)
    data = "\n".join(f"{bin} {count}" for bin, count in zip(clocks.index.tolist(), clocks.tolist()))

    # TODO: Refactor to builder pattern maybe?
    fig1 = gen_subfig(gen_lrbox_wrapper(gen_tikzpic(data, min_clock-10, max_clock+10, round(clocks.max(), -4), "firstCol")), 0.3, compile_flag)
    fig2 = gen_subfig(gen_lrbox_wrapper(gen_tikzpic(data, min_clock-10, max_clock+10, round(clocks.max(), -4), "secondCol")), 0.3, compile_flag)
    fig3 = gen_subfig(gen_lrbox_wrapper(gen_tikzpic(data, min_clock-10, max_clock+10, round(clocks.max(), -4), "thirdCol")), 0.3, compile_flag)
    figs = gen_fig(fig1+fig2+fig3, centering=True)

    # TODO Like this:
    # fig1 = gen_subfig(0.3, "GCC O0").add_lrbox()
    # fig1 = fig1.add_tikzpic(data, min_clock-10, max_clock+10, round(clocks.max(), -4), "firstCol")
    # ....
    # three_figs = gen_fig(centering=True).add_subfig(fig1).add_subfig(fig2).add_subfig(fig3).finalize()


    print(header+program_lstlisting+figs)



for filename in os.scandir(RESULTS_FOLDER):
    if filename.is_file():
        latex = gen_latex_doc(filename.path, 1)
        #print(latex)


