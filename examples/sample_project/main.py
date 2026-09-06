#!/usr/bin/env python3
"""Small executable used only as an audit fixture."""

import argparse
from pathlib import Path


parser = argparse.ArgumentParser()
parser.add_argument("--input", required=True, type=Path)
parser.add_argument("--output", required=True, type=Path)
args = parser.parse_args()
text = args.input.read_text(encoding="utf-8").lower()
label = "positive" if "love" in text else "negative"
args.output.parent.mkdir(parents=True, exist_ok=True)
args.output.write_text(label + "\n", encoding="utf-8")
print(label)

