#!/usr/bin/env python3
import os
import sys
import json
import glob

CONFIG_FILENAME = "config.json"

folder = os.path.dirname(os.path.realpath(__file__))
config_dir = parent_directory = os.path.dirname(folder)
config = json.load(open(f"{config_dir}{os.sep}{CONFIG_FILENAME}"))

for dir in sys.argv[1:]:
    files = glob.glob(f"{config[dir]}*")
    for f in files:
      if os.path.isfile(f):
        os.remove(f)
