import pandas as pd
import json
from pprint import pprint

FILE_PATH = "project_mapping/project_mapping_collection"

with open(FILE_PATH + ".json") as f:
    cx = json.load(f)


def filter_appCode(rec):
    rec["appCode"] = []
    rec["appCode"] += list(rec["agent"].keys())
    rec["appCode"] += list(rec["customer"].keys())
    rec["appCode"] = list(set(rec["appCode"]))
    return rec


from collections import ChainMap


def filter_intent_entities(rec):
    rec["intents_agent"] = [
        rec["agent"][appcode]["intents"] for appcode in rec["agent"]
    ]
    rec["intents_agent"] = dict(ChainMap(*rec["intents_agent"]))

    rec["intents_customer"] = [
        rec["customer"][appcode]["intents"] for appcode in rec["customer"]
    ]
    rec["intents_customer"] = dict(ChainMap(*rec["intents_customer"]))

    rec["entities_agent"] = [
        rec["agent"][appcode]["entities"] for appcode in rec["agent"]
    ]
    rec["entities_agent"] = dict(ChainMap(*rec["entities_agent"]))

    rec["entities_customer"] = [
        rec["customer"][appcode]["entities"] for appcode in rec["customer"]
    ]
    rec["entities_customer"] = dict(ChainMap(*rec["entities_customer"]))

    return rec


project_info_df = pd.DataFrame(cx["project_info"]).T

print(project_info_df.get("default_decision"))
project_info_df[["default_decision"]] = project_info_df[["default_decision"]].fillna(
    value="No"
)
project_info_df[["threshold"]] = project_info_df[["threshold"]].fillna(value=0.5)

project_info_df["default_decision"] = project_info_df["default_decision"].fillna("No")
project_info_df["threshold"] = project_info_df["threshold"].fillna(0.5)
project_info_df["zone"] = project_info_df["zone"].fillna("all")
project_info_df = project_info_df.apply(filter_appCode, axis=1)
project_info_df = project_info_df.apply(filter_intent_entities, axis=1)

project_info_df.to_excel(FILE_PATH + ".xlsx")
