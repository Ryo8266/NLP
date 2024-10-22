import pandas as pd
import os, json

CSV_FILE = "test/hc_collection/ground_new.csv"
RAW_JSON_DIR = "/home/ngocbtb8/Downloads/HC_22_2/"
RESULT_FILE_NAME = "test/hc_collection/transcript_new.json"

df = pd.read_csv(CSV_FILE)
print(df["File Name"].nunique())
filename = df["File Name"].tolist()

result = []

jsonfile = [ehe for ehe in os.listdir(RAW_JSON_DIR) if ehe.endswith(".json")]
for file in jsonfile:
    with open(RAW_JSON_DIR + file, "r") as fi:
        temp = json.load(fi)
    for call in temp:
        if (call["name"] + ".mp3") in filename:
            result.append(call)

with open(RESULT_FILE_NAME, "w") as fo:
    json.dump(result, fo, ensure_ascii=False)
