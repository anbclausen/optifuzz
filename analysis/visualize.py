#!/usr/bin/env python3
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import os


def visualize(path):
    df = pd.read_csv(path, sep=",", skiprows=[0])
    clocks_column = "clock_cycles"
    min_clocks = df[clocks_column].min()
    max_clocks = df[clocks_column].max()

    _, axes = plt.subplots()
    axes.set_title(path)

    # Hist plot
    df[clocks_column].plot.hist(ax=axes, bins=max(max_clocks - min_clocks, 1))
    ticks_step = int((max_clocks + 1 - min_clocks))
    axes.set_xticks(np.arange(min_clocks, max_clocks + 1, ticks_step))


root = "../fuzzer/results"
for dirpath, dnames, fnames in os.walk(root):
    for f in fnames:
        if f.endswith(".csv"):
            print(f"Visualizing {f}")
            visualize(os.path.join(dirpath, f))

plt.show()
