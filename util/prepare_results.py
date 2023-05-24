#!/usr/bin/env python3
import os
import sys
import json

CONFIG_FILENAME = "config.json"

folder = os.path.dirname(os.path.realpath(__file__))
config_dir = parent_directory = os.path.dirname(folder)
config = json.load(open(f"{config_dir}{os.sep}{CONFIG_FILENAME}"))

for dir in sys.argv[1:]:
  os.makedirs(config[dir], exist_ok=True)
