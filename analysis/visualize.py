#!/usr/bin/env python3
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

df = pd.read_csv('result.csv', sep=",", skiprows=[0])
clocks_column = 'clock_cycles'
mean_clocks = df[clocks_column].median()
min_clocks = df[clocks_column].min()
max_clocks = df[clocks_column].max()

print(df)

print("Clocks mean:", mean_clocks)
print("Min clocks:", min_clocks)
print("Max clocks:", max_clocks)
print("Data elements over mean:", len(df[df[clocks_column] > mean_clocks]))
print("Data elements under mean:", len(df[df[clocks_column] < mean_clocks]))

fig, axes = plt.subplots(nrows=2, ncols=2)

# Box plot
df.boxplot(ax=axes[0,0], column=[clocks_column])

# Hist plot
df[clocks_column].plot.hist(ax=axes[0,1], bins=max_clocks-min_clocks)
ticks_step = int((max_clocks+1-min_clocks)/10)
axes[0,1].set_xticks(np.arange(min_clocks, max_clocks+1, ticks_step))

# Hist plot
#df[clocks_column][abs(df[clocks_column]-100) < 100].plot.hist(ax=axes[1,1], bins=10)
df[clocks_column][df[clocks_column] < 80].plot.hist(ax=axes[1,1], bins=100)
axes[1,1].set_xticks(np.arange(60, 80, 1))

manager = plt.get_current_fig_manager()
manager.full_screen_toggle()
plt.show()
