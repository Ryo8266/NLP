import json

inputFile = input("raw query .json file with directory: ")

with open(inputFile + ".json", encoding="utf8") as f:
    raw = json.load(f)

res = []
for call in raw:
    if "id" not in call:
        res.append(call)
        continue
    res.append(
        {
            "name": call["name"],
            "agentChannel": call["agentChannel"],
            "content": [
                {"text": each["text"], "channel": each["channel"]}
                for each in call["content"]
            ],
        }
    )

with open(inputFile + "_ehe.json", "w", encoding="utf8") as fo:
    json.dump(res, fo, ensure_ascii=False)
