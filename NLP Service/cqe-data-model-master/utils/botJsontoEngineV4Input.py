from ast import Not
from calendar import c
import json


BOT_NAME = input("Enter json file name to convert, without .json: ")
# BOT_NAME = "bots-v7/confirmCustomer"
BOT_NAME = BOT_NAME.replace(".json", "")

with open(BOT_NAME + ".json", "r", encoding="utf-8") as fi:
    data = json.load(fi)

data = data["nlp"]
parsed = dict()

parsed["api_key"] = ""
parsed["app_code"] = BOT_NAME.split("/")[-1]
parsed["callback"] = {"error": "", "success": ""}
parsed["dictionary"] = [{"alternatives": [], "phrase": ""}]
parsed["domain"] = ""
parsed["engine"] = "nlu"
parsed["language"] = "vi"
parsed["no_accent"] = False
parsed["sub_language"] = ""

entities = []
for each in data["entities"]:
    entity = each["label"]

    type_ = "keyword & freetext"
    if each["type"] == 0:
        entities.append({"entity": entity, "type": "builtin", "values": []})
        continue

    elif each["type"] == 2:
        type_ = "keyword"

    elif each["type"] == 3:
        type_ = "freetext"

    values = []
    for kw in data["keywords"]:
        if kw["entity"] == entity:
            xpress = [each.strip('"') for each in kw["synonym"].strip("][").split(",")]
            if len(xpress) == 1 and xpress[0] == "":
                xpress = []
            values.append({"expressions": xpress, "value": kw["value"]})

    entities.append({"entity": entity, "type": type_, "values": values})

parsed["entities"] = entities

samples = []
for each in data["samples"]:
    ntties = []
    for ntt in each["entities"]:
        subntties = []
        for sub in ntt["sub_entities"]:
            subntties.append(
                {
                    "end": sub["end"],
                    "entity": sub["label"],
                    "start": sub["start"],
                    "value": sub["value"],
                }
            )

        ntties.append(
            {
                "end": ntt["end"],
                "entity": ntt["label"],
                "start": ntt["start"],
                "subentities": subntties,
                "value": ntt["value"],
            }
        )

    samples.append(
        {"text": each["content"], "intent": each["intent"], "entities": ntties}
    )

parsed["samples"] = samples

with open(BOT_NAME + "_output.json", "w", encoding="utf8") as fo:
    json.dump(parsed, fo, ensure_ascii=False)
