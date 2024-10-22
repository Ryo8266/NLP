import requests
import json
from tqdm import tqdm
import pandas as pd

import time

tqdm.pandas()

from pprint import pprint


def json_read(path: str):
    with open(path, encoding="utf-8") as fh:
        data = json.load(fh)
    return data


def process_criteria(dialog_tracker, checker):
    url = "http://103.176.146.250:5055/process_criteria"
    payload = json.dumps({"dialog_tracker": dialog_tracker, "checker": checker})
    headers = {"Content-Type": "application/json"}
    response = requests.request("POST", url, headers=headers, data=payload)
    return response.json()


def get_criteria_result(rec, project_info, criteria_name):
    dialog_tracker = {
        "agentChannel": int(rec["agentChannel"]),
        "dialog_nlu": rec["raw"],
        "original_field": ["index", "channel", "text"],
    }

    for criteria in criteria_name:
        rec[criteria] = process_criteria(
            dialog_tracker=dialog_tracker,
            checker=project_info[criteria],
        )["decision"]

    return rec


if __name__ == "__main__":
    project_test = {
        "m1": {
            "project": "project_mapping/hc_clx_m1.json",
            "calls": [
                "calls/raw/wc_m1b_raw.json",
                # "calls/raw/m1_raw.json",
                # "calls/raw/wc_m1_raw.json",
                # "calls/raw/fu_m1a_35_raw.json",
                # "calls/raw/fu_m1b_30_raw.json",
                # "calls/raw/fu_m2_37_raw.json",
                # "calls/raw/fu_m3_30_raw.json",
                # "calls/raw/m1a_105_raw.json",
                # "calls/raw/m2_370_raw.json",
                # "calls/raw/m3_286_raw.json",
            ],
        },
        "m2": {
            "project": "project_mapping/hc_clx_m2.json",
            "calls": [
                "calls/raw/m2_raw.json",
                "calls/raw/wc_m2_raw.json",
            ],
        },
        "m3": {
            "project": "project_mapping/hc_clx_m3.json",
            "calls": [
                "calls/raw/m3_raw.json",
                "calls/raw/wc_m3_raw.json",
            ],
        },
    }

    list_test = ["m1"]
    # list_test = ["m1", "m2", "m3"]

    for test_m in list_test:
        project = json_read(path=project_test[test_m]["project"])
        project_info = project["project_info"]

        criteria_name = list(project_info.keys())
        criteria_name = ["wrongNumber"]

        list_call = project_test[test_m]["calls"]

        for call in list_call:
            dialog = pd.read_json(call)

            result_df = dialog.progress_apply(
                lambda rec: get_criteria_result(rec, project_info, criteria_name),
                axis=1,
            )[["name"] + criteria_name]

            call = call.split("/")[-1].replace(".json", "")
            print(call)
            if "wc" in call:
                pass_call = result_df[result_df["wrongNumber"] == "yes"]
                print("WC pass:", len(pass_call))
                print("WC fail:", len(result_df) - len(pass_call))
                print("ACC:", len(pass_call) / len(result_df))
                result_df[result_df["wrongNumber"] == "no"].to_csv(
                    "tmp/report_wc_" + call + ".csv"
                )
            else:
                pass_call = result_df[result_df["wrongNumber"] == "no"]
                print("Not WC pass:", len(pass_call))
                print("Not WC fail:", len(result_df) - len(pass_call))
                print("ACC:", len(pass_call) / len(result_df))
                result_df[result_df["wrongNumber"] == "yes"].to_csv(
                    "tmp/report_wc_" + call + ".csv"
                )
