import json


BOT_NAME = input("Enter json file name to convert, without .json: ")
BOT_NAME = BOT_NAME.replace(".json", "")
with open(BOT_NAME + ".json", "r", encoding="utf-8") as fi:
    data = json.load(fi)

with open(BOT_NAME + "_beautify.json", "w", encoding="utf8") as fo:
    json.dump(data, fo, ensure_ascii=False)
