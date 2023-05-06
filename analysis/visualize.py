#!/usr/bin/env python3
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import os


def visualize(paths):
    positions = {
        "O0": (0, 0),
        "O1": (0, 1),
        "O2": (0, 2),
        "O3": (1, 0),
        "Os": (1, 1),   
    }

    _, axes = plt.subplots(nrows=2, ncols=3)
    print("###")
    for path in paths:
        print(f"Visualizing {path}...")
        df = pd.read_csv(path, sep=",", skiprows=[0])
        clocks_column = "clock_cycles"
        min_clocks = df[clocks_column].min()
        max_clocks = df[clocks_column].max()

        flag = path[-6:-4]

        df[clocks_column].plot.hist(ax=axes[positions[flag]], bins=max(max_clocks - min_clocks, 1))
        ticks_step = int((max_clocks + 1 - min_clocks))
        axes[positions[flag]].set_xticks(np.arange(min_clocks, max_clocks + 1, ticks_step))
        axes[positions[flag]].set_title(flag)


root = "../fuzzer/results"
for dirpath, dnames, fnames in os.walk(root):
    csv_files = [os.path.join(dirpath, f) for f in fnames if f.endswith(".csv")]
    sorted_csv_files = sorted(csv_files)
    grouped = zip(*(iter(sorted_csv_files),) * 5)
    for group in grouped:
        visualize(group)

plt.show()
