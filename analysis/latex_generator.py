#!/usr/bin/env python3
import copy
import json
import string
import pandas as pd
import numpy as np
import os
import re
import itertools
from dataclasses import dataclass
import subprocess

# Constants for parsing
MIN_CLOCKS_COLUMN = "min_clock_measured"

CONFIG_FILENAME = "config.json"
current_folder = os.path.dirname(os.path.realpath(__file__))
config_dir = os.path.dirname(current_folder)  # Parent folder
config = json.load(open(f"{config_dir}{os.sep}{CONFIG_FILENAME}"))

# config["fuzzer_results_dir"] holds the path relative to the config_dir
RESULTS_FOLDER = os.path.join(config_dir, config["fuzzer_results_dir"])
COMPILER_USED = config["compiler"]

LATEX_FOLDER = "latex"
LATEX_OUTPUT_FOLDER = f"{LATEX_FOLDER}/generated_latex"
FLAGGED_FOLDER = f"{config_dir}{os.sep}{config['flagged_programs_dir']}"
ITERATION_PREFIX = "it"
NO_OF_ITERATIONS = 10

# Output constants
NO_OF_BINS = 100
COLORS = ["firstCol", "secondCol", "thirdCol", "fourthCol", "fifthCol", "sixthCol"]
X_LABEL = "CPU Clocks"
Y_LABEL = "Frequency"
X_MARGIN = 1.03  # Controls margin to both sides of x-axis
Y_MARGIN = 1.05  # Controls margin to top of y-axis

# Match all jcc instructions that is not jmp, and all loop instructions
# https://cdrdv2.intel.com/v1/dl/getContent/671200
# Table 7-4
jmp_regex = re.compile(r"\t(j(?!mp)[a-z][a-z]*)|(loop[a-z]*) ")


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
        return self

    def finalize(self) -> string:
        return "".join([x.finalize() for x in self.children])


class TexFigure(TexBlock):
    def __init__(self):
        super().__init__()
        self.start = "\\begin{figure}[H]\n"
        self.end = "\\end{figure}\n"

    def finalize(self) -> string:
        return self.start + super().finalize() + self.end


class TexSubFigure(TexBlock):
    def __init__(self, width, caption=None):
        super().__init__()
        self.start = f"\\begin{{subfigure}}[T]{{{width}\\textwidth}}\n"
        self.end = "\\end{subfigure}\n"
        self.caption = f"\\caption*{{{caption}}}\n" if caption is not None else ""

    def set_caption(self, caption):
        self.caption = f"\\caption*{{{caption}}}\n" if caption is not None else ""

    def finalize(self) -> string:
        return self.start + self.caption + super().finalize() + self.end


class TexLrbox(TexBlock):
    def __init__(self):
        super().__init__()
        self.start = "\\begin{lrbox}{\\mybox}%\n"
        self.end = "\\end{lrbox}\\resizebox{\\textwidth}{!}{\\usebox{\\mybox}}\n"

    def finalize(self) -> string:
        return self.start + super().finalize() + self.end


class TexTikzPic(TexBlock):
    def __init__(
        self,
        xmin,
        xmax,
        ymax,
        color,
        data,
        X_LABEL=X_LABEL,
        Y_LABEL=Y_LABEL,
        ymin=0,
        time_plot=False,
        means=None,
    ):
        super().__init__()

        # ybar plot vs smooth lpot depending on time_plot argument
        def plot_settings(i):
            return (
                f"[color={COLORS[i]},mark=none,smooth]"
                if time_plot
                else f"[ybar interval,mark=no,color={color},fill={color},fill opacity=0.2]"
            )

        # Always wrap data in list
        data = data if isinstance(data, list) else [data]
        plot = "\n".join(
            [
                f"""\\addplot+ {plot_settings(i)} table {{
                    {x}
                }};"""
                for i, x in enumerate(data)
            ]
        )

        fuzz_classes = list(means.keys())
        means_table = (
            ""
            if means is None
            else f"""
            \\node[below=15mm of ax] (1) {{
                $\\begin{{aligned}}
                    \\texttt{{{fuzz_classes[0]}}}_\\mu: & \\,{means[fuzz_classes[0]]}\\\\
                    \\texttt{{{fuzz_classes[1]}}}_\\mu: & \\,{means[fuzz_classes[1]]}\\\\
                    \\texttt{{{fuzz_classes[2]}}}_\\mu: & \\,{means[fuzz_classes[2]]}
                \end{{aligned}}$
            }};
            \\node[left=4mm of 1] (2) {{
                $\\begin{{aligned}}
                    \\texttt{{{fuzz_classes[3]}}}_\\mu: & \\,{means[fuzz_classes[3]]}\\\\
                    \\texttt{{{fuzz_classes[4]}}}_\\mu: & \\,{means[fuzz_classes[4]]}
                \end{{aligned}}$
            }};
            \\node[right=4mm of 1] (3) {{
                $\\begin{{aligned}}
                    \\texttt{{{fuzz_classes[5]}}}_\\mu: & \\,{means[fuzz_classes[5]]}\\\\
                    \\texttt{{{fuzz_classes[6]}}}_\\mu: & \\,{means[fuzz_classes[6]]}\\\\
                    \\texttt{{{fuzz_classes[7]}}}_\\mu: & \\,{means[fuzz_classes[7]]}
                \end{{aligned}}$
            }};
            \\node[fit=(1)(2)(3),draw]{{}};"""
        )
        mean_lines = (
            ""
            if means is None
            else "\n".join(
                [
                    f"""\
                    \draw[color=black, line width=0.2mm, dashed] 
                    (axis cs:{m}, {-ymax*0.05}) -- (axis cs:{m}, {ymax});"""
                    for m in means.values()
                ]
            )
        )

        self.start = None
        self.end = None
        self.tikzpic = f"""\\begin{{tikzpicture}}[>=latex]
            \\begin{{axis}}[
                axis x line=center,
                axis y line=center,
                name=ax,
                scaled y ticks=base 10:-3,
                ytick scale label code/.code={{}},
                yticklabel={{\\pgfmathprintnumber{{\\tick}} k}},
                xlabel={{{X_LABEL}}},
                ylabel={{{Y_LABEL}}},
                x label style={{at={{(axis description cs:0.5,-0.1)}},anchor=north}},
                y label style={{at={{(axis description cs:-0.1,.5)}},rotate=90,anchor=south,yshift=4mm}},
                {"" if time_plot else "area style"},
                ymin={ymin},
                xmin={xmin},
                xmax={xmax},
                ymax={ymax}
                ]
                {plot}
                {mean_lines}
            \\end{{axis}} {means_table}
            \\end{{tikzpicture}}%
        """

    def add_child(self):
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
        return self.start + self.code + super().finalize() + self.end


def run(args: list[str]) -> str:
    """Runs a command and returns the stdout

    Parameters
    ----------
    args : list[str]
        The command to be run

    Returns
    ----------
    The stdout of the command
    """
    return subprocess.run(args, capture_output=True, text=True).stdout


def parse_aux_info(aux: str) -> tuple[str, str]:
    """Parses first line of CSV fuzzing data

    Parameters
    ----------
    aux : str
        Auxiliary information in CSV

    Returns
    ----------
    Tuple (a,b) where:\n
    a:
        Compiler flag used
    b:
        Fuzzing class used
    """
    re_brackets = re.findall(r"\[.*?\]", aux)
    res = list(map(lambda x: x.replace("[", "").replace("]", ""), re_brackets))
    compiler_flag = res[0]
    fuzz_class = res[1]
    return compiler_flag, fuzz_class


@dataclass
class ParsedCSV:
    min_clocks: pd.Series
    all_clocks: pd.Series
    compile_flag: str
    fuzz_class: str


def gen_header(prog_id: str, prog_seed: str) -> str:
    """Generates a latex header for the program

    Parameters
    ----------
    prog_id : str
        Identifier of the program
    prog_seed : str
        Seed of fuzzed data

    Returns
    ----------
    Header as LaTeX string
    """
    compiler = config["compiler"]
    compiler_flags = config["compiler_flags"]
    fuzzing_classes = config["fuzzing_classes"]
    kernel_mode = config["kernel_mode"]

    compiled_with = compiler + " " + " ".join(compiler_flags)
    fuzzclasses = "Classes: " + " ".join(fuzzing_classes)
    newline = "\\\\"
    return f"\\textbf{{Program {prog_id}}} -- \\texttt{{Seed {prog_seed}}} -- Kernel Mode: {kernel_mode} -- \\texttt{{{compiled_with}}}{newline}\small\\texttt{{{fuzzclasses}}}\n"


def parse_csv(file: str) -> ParsedCSV:
    """Generates a LaTeX figure for the CSV-files provided.

    CPU-clocks will be plotted and colored.

    Assembly lstlistings will also be generated.

    Parameters
    ----------
    file : str
        File path of file to parse

    Returns
    ----------
    A ParsedCSV containing compile-flag used and all measured clocks as a pd series
    """
    file = f"{RESULTS_FOLDER}/{file}"

    # Read first line of CSV containing auxiliary information
    with open(file) as f:
        aux_info = f.readline()
    compile_flag, fuzz_class = parse_aux_info(aux_info)

    # Read the rest of the CSV - skip the auxiliary line
    df = pd.read_csv(file, sep=",", skiprows=[0])

    min_clock, max_clock = df[MIN_CLOCKS_COLUMN].min(), df[MIN_CLOCKS_COLUMN].max()
    diff = max_clock - min_clock

    bins_count = diff if diff < NO_OF_BINS else NO_OF_BINS

    # If min_clock = max_clock then we have to make sure that there exist at least one bin
    bins_count = max(bins_count, 1)

    # Generate labels for bins
    edges = np.linspace(min_clock, max_clock, bins_count + 1).astype(int)
    labels = [
        edges[i] + round((edges[i + 1] - edges[i]) / 2) for i in range(bins_count)
    ]

    # Group into bins, receiving a list of (interval, count)
    min_clocks = pd.cut(
        df[MIN_CLOCKS_COLUMN], bins=bins_count, labels=labels
    ).value_counts(sort=False)
    all_clocks = pd.concat(
        [df[f"it{i}"] for i in range(1, NO_OF_ITERATIONS + 1)], axis=0
    )

    return ParsedCSV(min_clocks, all_clocks, compile_flag, fuzz_class)


def get_program_source(seed: str) -> str:
    """Retrieves source code of program.

    Parameters
    ----------
    seed : str
        Seed of fuzzed data

    Returns
    ----------
    Program source code as string
    """
    # Read program
    file_reader = open(f"{FLAGGED_FOLDER}/{seed}.c", "r")
    prog = file_reader.read()
    file_reader.close()
    # Replace first 3 lines with ...
    prog = "...\n" + prog.split("\n", 2)[2]
    return prog


def trim_assembly(asm: str) -> str:
    """Trims start and end of provided assembly.

    Trims away the first 4 lines.
    Searches specifically after .LFE0 and trims everything after that point.
    Trims all instances of ".cfi" prefix.

    Parameters
    ----------
    asm : str
        Assembly given as string

    Returns
    ----------
    Trimmed assembly as string
    """
    asm = asm.split("\n")
    LFE0 = next(i for i, s in enumerate(asm) if s.startswith(".LFE0"))

    # Trim at start and end, and return the string
    asm[4] = "..."
    asm[LFE0] = "..."
    asm = asm[4 : LFE0 + 1]

    asm = [line for line in asm if ".cfi" not in line]
    asm = "\n".join(asm)
    return asm


def extract_conditional_branching_instructions(s: str) -> list[str]:
    """Extracts all conditional branching instructions from a string

    Parameters
    ----------
    path : str
        The string to be searched

    Returns
    ----------
    A list of all conditional branching instructions
    """
    matches = jmp_regex.findall(s)
    jmp_matches = [x[0] for x in matches if x[0] != ""]
    loop_matches = [x[1] for x in matches if x[1] != ""]
    return jmp_matches + loop_matches


def gen_plot_asm_fig(
    seed: str,
    parsed_csv: dict[str, list[str]],
    colors: list[str],
    blank_indexes: list[int] = [],
) -> tuple[TexFigure, list[TexSubFigure]]:
    """Generates a LaTeX figure for the CSV-files provided.

    CPU-clocks will be plotted and colored.

    Assembly lstlistings will also be generated.

    Parameters
    ----------
    seed : str
        Seed of fuzzed data
    parsed_csv : dict[str, list[str]]
        Map from a compile flag to a list of different fuzz classes identified by file names for the CSV files
    colors : str list
        List of colors to use for the plots
    blank_indexes : int list
        Indices of which subfigures should be left blank

    Returns
    ----------
    Tuple (a,b) where:\n
    a:
        Non-finalized LaTeX figure - that is; caller can keep modifying tree
    b:
        List of placeholder LaTeX subfigures, which are empty. The caller can
        populate these at a later point.
    """
    compiler_flags = list(parsed_csv.keys())

    if len(colors) < len(parsed_csv):
        ex = (
            f"Not enough colors provided to color parsed CSVs. "
            f"Colors: {len(colors)} - CSVs: {len(parsed_csv)}"
        )
        raise Exception(ex)

    # Determine the width according to what we can fit
    # i.e. len(amount_of_subfigs) = 3  ==>  width = 0.3
    amount_of_subfigs = len(parsed_csv) + len(blank_indexes)
    width = 1 / amount_of_subfigs - 0.03
    figure = TexFigure()

    placeholder_subfigures = []
    placeholder_original = copy.copy(blank_indexes)

    # Generate tikzpictures
    i = 1
    while i <= len(parsed_csv):
        if i in blank_indexes:
            subfig = TexSubFigure(width=width, caption="")
            figure.add_child(subfig)
            placeholder_subfigures.append(subfig)
            blank_indexes.remove(i)
            continue

        # Data holds the plotting data
        # The other lists keeps track of smallest/greatest min and max for x and y
        data, xmin_list, xmax_list, ymax_list = ([] for _ in range(4))
        means = {}

        for fuzz_csv in parsed_csv[compiler_flags[i - 1]]:
            data.append(
                "\n".join(
                    f"{bin} {count}"
                    for bin, count in zip(
                        fuzz_csv.min_clocks.index.tolist(), fuzz_csv.min_clocks.tolist()
                    )
                )
            )
            xmin_list.append(round(fuzz_csv.min_clocks.index.min() * 1 / X_MARGIN))
            xmax_list.append(round(fuzz_csv.min_clocks.index.max() * X_MARGIN))
            ymax_list.append(round(fuzz_csv.min_clocks.max() * Y_MARGIN))

            # Compute the mean of CPU-clocks by dividing the
            # frequency measured by the total amount of fuzzes.
            fuzzing_sum = fuzz_csv.min_clocks.sum()
            mean = sum(
                np.array(list(fuzz_csv.min_clocks.index))
                * (np.array(list(fuzz_csv.min_clocks)) / fuzzing_sum)
            )
            means[fuzz_csv.fuzz_class] = round(mean, 0).astype(int)

        xmin, xmax, ymax = min(xmin_list), max(xmax_list), max(ymax_list)

        lrbox = TexLrbox().add_child(
            TexTikzPic(xmin, xmax, ymax, colors[i - 1], data, means=means)
        )
        subfig = TexSubFigure(width=width, caption=compiler_flags[i - 1]).add_child(
            lrbox
        )
        figure.add_child(subfig)

        i = i + 1

    # Include placeholder with indices greater than len(parsed_csv)
    for i in blank_indexes:
        subfig = TexSubFigure(width=width, caption="")
        figure.add_child(subfig)
        placeholder_subfigures.append(subfig)

    blank_indexes = copy.copy(placeholder_original)

    # Move the first lstlisting a little
    figure.append_string("\\hspace*{6mm}\n")
    # Generate asm lstlistings
    i = 1
    while i <= len(parsed_csv):
        if i in blank_indexes:
            subfig = TexSubFigure(width=width, caption="")
            figure.add_child(subfig)
            placeholder_subfigures.append(subfig)
            blank_indexes.remove(i)
            continue
        csv = parsed_csv[compiler_flags[i - 1]][3]
        assert csv.compile_flag != ""
        asm = run(
            [
                COMPILER_USED,
                f"{FLAGGED_FOLDER}/{seed}.c",
                "-S",
                f"-{csv.compile_flag}",
                "-w",
                "-c",
                "-o",
                "/dev/stdout",
            ]
        )
        asm = trim_assembly(asm)
        jumps = extract_conditional_branching_instructions(asm)
        no_jumps_str = "{\color{red} No jumps}"
        formatted_jumps_string = f"""\
        \\vspace*{{2mm}}\\tiny {no_jumps_str if len(jumps) == 0 else ", ".join(jumps)}\n
        """

        lstlisting = TexLstlisting(
            style="style=defstyle,language={[x86masm]Assembler},basicstyle=\\tiny\\ttfamily,breaklines=true",
            code=asm,
        )
        subfig = (
            TexSubFigure(width=width - 0.03)
            .append_string(formatted_jumps_string)
            .add_child(lstlisting)
        )
        figure.add_child(subfig)
        # Don't add hspace after last lstlisting
        if i != len(parsed_csv):
            figure.append_string("\\hspace*{10mm}\n")

        i = i + 1

    return figure, placeholder_subfigures


def gen_latex_doc(seed: str, csv_files: dict[str, list[str]], prog_id: int) -> str:
    """Generates all the LaTeX required for the CSV-files provided.

    Parameters
    ----------
    seed : str
        Seed of fuzzed data
    csv_files : dict[str, list[str]]
        Map from a compile flag to a list of different fuzz classes identified by file names for the CSV files
    prog_id : int
        Identifier of the program

    Returns
    ----------
    LaTeX doc as string
    """
    prog = get_program_source(seed)
    program_lstlisting = TexLstlisting("style=defstyle,language=C", prog).finalize()

    first_three = dict(itertools.islice(csv_files.items(), 0, 3))
    last_two = dict(itertools.islice(csv_files.items(), 3, 5))

    # Start by plotting a 3-width plot with corresponding asm
    figure1, _ = gen_plot_asm_fig(seed, first_three, COLORS[:3])
    # By telling to placeholder=[3], we essentially tell the function, that we want a 3-wide figure
    # as len(last_two)+len(placeholder) = 3, but where the third element
    # should only be created as an empty subfigure
    figure2, _ = gen_plot_asm_fig(seed, last_two, COLORS[3:5], blank_indexes=[3])

    # Finalize the figures
    figure1, figure2 = figure1.finalize(), figure2.finalize()
    new_page = "\\newpage\\noindent"

    header = gen_header(prog_id, seed)
    first_page = header + program_lstlisting + figure1 + new_page
    second_page = header + figure2 + new_page

    return first_page + second_page


if __name__ == "__main__":
    # Retrieve all generated seeds
    all_seeds = list(map(lambda x: x.replace(".c", ""), os.listdir(FLAGGED_FOLDER)))
    # Map seed to available results, i.e. seed.c -> [r1.csv, r2.csv, ...]
    all_fuzzing_results = itertools.groupby(
        sorted(os.listdir(RESULTS_FOLDER)), lambda x: re.search(r"\d+", x).group()
    )
    # Convert to dictionary and parse all .csv-files in the above
    all_fuzzing_results = {
        seed: [parse_csv(csv) for csv in list(csv_files)]
        for seed, csv_files in all_fuzzing_results
    }
    for csv_files in all_fuzzing_results.values():
        csv_files.sort(key=lambda x: x.compile_flag)
    # Group by compile_flag, such that seed.c -> {O0: [r1.csv, ...], O1: [r1.csv, ...]}
    all_fuzzing_results = {
        seed: {
            x: list(y)
            for x, y in itertools.groupby(csv_files, lambda x: x.compile_flag)
        }
        for seed, csv_files in all_fuzzing_results.items()
    }

    # For each program/seed; create a .tex file in the output folder
    for id, (seed, grouped_CSV_files) in enumerate(all_fuzzing_results.items(), 1):
        latex = gen_latex_doc(seed, grouped_CSV_files, id)
        f = open(f"{LATEX_OUTPUT_FOLDER}/prog{id}.tex", "w")
        f.write(latex)
        f.close()
