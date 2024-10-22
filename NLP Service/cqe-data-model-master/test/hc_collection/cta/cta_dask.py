import requests
import json
import time
import pandas as pd
from tqdm import tqdm

import numpy as np

tqdm.pandas()


def json_read(path: str):
    with open(path, encoding="utf-8") as fh:
        data = json.load(fh)
    return data


def test_criteria(
    project_info, criteria_name, transcript, metadata, agent_channel, file_name="test"
):
    url = "http://103.176.146.250:5005/predict/dialogue/test"
    payload = json.dumps(
        {
            "project_info": project_info,
            "transcript": transcript,
            "metadata": metadata,
            "criteria": criteria_name,
            "fileName": file_name,
            "agentChannel": agent_channel,
        }
    )
    headers = {"Content-Type": "application/json"}
    response = requests.request("POST", url, headers=headers, data=payload)
    return response


def calculate_criteira(rec, wc_project_info, criteria_name):
    while True:
        try:
            result = test_criteria(
                wc_project_info,
                criteria_name,
                rec["content"],
                rec["metadata"],
                rec["agentChannel"],
                file_name=rec["name"],
            )
            result = result.json()
            for criteria in criteria_name:
                rec[criteria] = result[criteria]["decision"]
            break
        except Exception as e:
            print(criteria)
            print(result[criteria])
            print(e)
            print(result.keys())
            print(rec["name"])
            time.sleep(10)

    return rec


if __name__ == "__main__":
    call_data = pd.read_json("calls/clean/m2_clean.json")
    project_info = json_read("project_mapping/hc_clx_m2.json")["project_info"]
    criteria_name = list(project_info.keys())
    criteria_name = [
        "callResultAI",
        "willpaySummary",
        "nopaySummary",
        "paidSummary",
        "permitToEnd",
        "informAmount",
        "informOverdue",
    ]

    result_df = call_data.progress_apply(
        lambda rec: calculate_criteira(rec, project_info, criteria_name), axis=1
    )
    result_df = result_df[["name"] + criteria_name]

    labels = pd.read_csv("report/Batch-300-call-đã-gán-nhãn_M2B_v3.csv")

    labels["criterion_name"] = labels["criterion_name"].str.lower()
    labels["audit_result"] = labels["audit_result"].str.lower()
    labels_call_result = labels[labels["criterion_name"] == "call result"][
        ["file_name", "audit_result"]
    ].rename(columns={"audit_result": "P call result"})
    labels_cai = labels[labels["criterion_name"] == "contain all information"][
        ["file_name", "audit_result"]
    ].rename(columns={"audit_result": "P Contain all information"})

    labels = labels_call_result.merge(labels_cai, on="file_name")

    default_label = ["nopay", "undefined", "paid", "willpay"]
    labels["P call result"] = labels["P call result"].progress_apply(
        lambda label: label if label in default_label else "undefined"
    )
    # labels["P call result"] = labels["P call result"].fillna("n/a")
    labels["P call result"] = (
        labels["P call result"].replace(np.nan, "na").replace("", "na")
    )

    result_all = labels.merge(result_df, left_on="file_name", right_on="name")

    result_all = result_all.drop(columns=["name"])
    result_all.to_csv("test/hc_collection/cta/cta_result.csv", index=False)
