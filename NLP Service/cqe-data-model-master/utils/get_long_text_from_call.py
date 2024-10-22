"""
author: dungca4@fpt.com
usage:
python script_name.py json_call_file_name.json
"""

import json
import pandas as pd
import argparse

# Thêm đối số cho command
parser = argparse.ArgumentParser()
parser.add_argument("filename", help="name of the file")
args = parser.parse_args()

with open(args.filename, encoding="utf-8") as f:
    data = json.load(f)

df = {"name": [], "content": [], "num_words": []}

for call in data:
    check = False
    if call["content"] is not None:
        for sentence in call["content"]:
            words = sentence["text"].split()
            num_words = len(words)
            if num_words > 35:
                check = True
                df["name"].append(call["name"])
                df["content"].append(sentence["text"])
                df["num_words"].append(num_words)

data_frame = pd.DataFrame(df)
data_frame.to_excel("output.xlsx", index=False)
