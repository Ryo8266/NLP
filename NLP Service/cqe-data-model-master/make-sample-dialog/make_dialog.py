import pandas as pd
import requests
import json
from tqdm import tqdm
import time

tqdm.pandas()


def json_read(path: str):
    with open(path, encoding="utf-8") as fh:
        data = json.load(fh)
    return data


def raw_criteria(project, transcript, metadata, agent_channel, file_name="test", criterias=None):
    project_info = project["project_info"]
    project_id = project["project_id"]
    criterias = list(project_info.keys()) if criterias is None else criterias

    url = "http://103.176.146.250:5005/predict/dialogue/raw/"
    payload = json.dumps(
        {
            "project_id": project_id,
            "transcript": transcript,
            "metadata": metadata,
            "criteria": criterias,
            "fileName": file_name,
            "agentChannel": agent_channel,
        }
    )
    headers = {"Content-Type": "application/json"}
    response = requests.request("POST", url, headers=headers, data=payload)
    return response


def raw_criteira(rec, project):
    criterias = [
        "willpaySummary",
        "nopaySummary",
        "paidSummary",
        "permitToEnd",
        "informAmount",
        "informOverdue",
    ]
    while True:
        try:
            if rec["content"] == None:
                result = []
                break
            result = raw_criteria(
                project,
                rec["content"],
                rec["metadata"],
                rec["agentChannel"],
                file_name=rec["name"],
                criterias=criterias,
            )
            result = result.json()["data"]
            break
        except:
            print(rec["name"])
            time.sleep(10)

    data_raw = pd.DataFrame(result)
    default_col = ["index", "channel", "text"]
    app_codes = list(set(data_raw.columns) ^ set(default_col))

    data_raw = data_raw.apply(lambda rec: clean_predict(rec, app_codes), axis=1)
    data_raw = data_raw[default_col+["intent", "entities"]]

    result = data_raw.to_dict("records")
    rec["content"] = result
    return rec


def read_data(call_path, project_info_path, verbose=False):
    call_data = pd.read_json(call_path)
    project = json_read(project_info_path)

    call_path_output = call_path.split(".")[0] + "_raw.json"
    call_path_output = call_path_output.replace("_clean", "")

    if verbose:
        print("Filename:", call_path.split("/")[-1].split(".")[0])
        print("N calls:", len(call_data))

    return call_data, project, call_path_output


def clean_predict(rec, app_codes):
    intent = set()
    entities = list()
    # print(rec)
    for app_code in app_codes:
        if len(rec[app_code]["intents"]) > 0:
            tmp_intent = rec[app_code]["intents"][0]["label"]
            if tmp_intent != "[UNK]":
                intent.add(rec[app_code]["intents"][0]["label"])
            entities += rec[app_code]["entities"]
    intent = list(intent) if len(intent)>0 else ""
    rec["intent"] = intent[0] if len(intent)==1 else intent
    
    # TODO: check duplicate location
    if len(entities) > 0:
        entities = pd.DataFrame(entities)
        if "subentities" in entities.columns:
            entities = entities.drop(columns="subentities")
        entities = entities.drop_duplicates()
        entities = entities.sort_values(by=['start'])
        entities = entities.to_dict("records")
        # entities = map(dict, set(tuple(sorted(d.items())) for d in entities))
    rec["entities"] = entities


    return rec

if __name__ == "__main__":
    # call_path = input("call_path: ")
    # project_info_path = input("project_info_path: ")
    calls_dict = {
        "m1": {
            "data": "calls/data_label_cta/m1_clean.json",
            "labels": "report/Batch-đã-verify-587-calls_đã-sửa-yes-cho-tc17__v11.csv",
            "out_dir": "bots-v8/",
            "project_info": "project_mapping/hc_clx_m1.json",
        },
        "m2": {
            "data": "calls/data_label_cta/m2_clean.json",
            "labels": "report/Batch-300-call-đã-gán-nhãn_M2B_v3.csv",
            "out_dir": "bots-v8/",
            "project_info": "project_mapping/hc_clx_m2.json",
        },
        "m3": {
            "data": "calls/data_label_cta/m3_clean.json",
            "labels": "report/Batch 300 call đã gán nhãn_M3B.csv",
            "out_dir": "bots-v8/",
            "project_info": "project_mapping/hc_clx_m3.json",
        },
    }

    domains = ["m1", "m2", "m3"]
    for domain_task in domains:

        domain = calls_dict[domain_task]

        call_path = domain["data"]
        project_info_path = domain["project_info"]

        start_time = time.time()

        call_data, project, call_path_output = read_data(
            call_path=call_path,
            project_info_path=project_info_path,
            verbose=True,
        )

        call_data = call_data.progress_apply(lambda rec: raw_criteira(rec, project), axis=1)
        call_data.to_json(call_path_output, force_ascii=False, orient="records", indent=2)

        print((time.time() - start_time) / 60)
