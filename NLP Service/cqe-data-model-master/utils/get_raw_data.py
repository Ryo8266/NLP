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


def raw_criteria(project, transcript, metadata, agent_channel, file_name="test"):
    project_info = project["project_info"]
    project_id = project["project_id"]
    url = "http://103.176.146.250:5005/predict/dialogue/raw/"

    criterias = ["wrongNumber", "confirmSimWC", "sumWC", "identificationWC"]

    payload = json.dumps(
        {
            "project_id": project_id,
            "transcript": transcript,
            "metadata": metadata,
            # "criteria": list(project_info.keys()),
            "criteria": criterias,
            "fileName": file_name,
            "agentChannel": agent_channel,
        }
    )
    headers = {"Content-Type": "application/json"}
    response = requests.request("POST", url, headers=headers, data=payload)
    return response


def raw_criteira(rec, project):
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
            )
            result = result.json()["data"]
            break
        except:
            print(rec["name"])
            time.sleep(10)
    rec["raw"] = result
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


if __name__ == "__main__":
    # call_path = input("call_path: ")
    # project_info_path = input("project_info_path: ")

    call_path: list = [
        "calls/clean/wc_m1b_clean.json",
        # "calls/clean/fu_m1a_35_clean.json",
        # "calls/clean/fu_m1b_30_clean.json",
        # "calls/clean/fu_m2_37_clean.json",
        # "calls/clean/fu_m3_30_clean.json",
        # "calls/clean/m1_clean.json",
        # "calls/clean/m1a_105_clean.json",
        # "calls/clean/m2_370_clean.json",
        # "calls/clean/m2_clean.json",
        # "calls/clean/m3_286_clean.json",
        # "calls/clean/m3_clean.json",
        # "calls/clean/wc_m1_clean.json",
        # "calls/clean/wc_m2_clean.json",
        # "calls/clean/wc_m3_clean.json",
    ]
    # call_path = "calls/clean/wc_m1_clean.json"
    project_info_path = "project_mapping/hc_clx_m1.json"

    start_time = time.time()

    if isinstance(call_path, list):
        for path in call_path:
            call_data, project, call_path_output = read_data(
                call_path=path,
                project_info_path=project_info_path,
                verbose=True,
            )

            call_data = call_data.progress_apply(
                lambda rec: raw_criteira(rec, project), axis=1
            )
            call_data.to_json(
                call_path_output, force_ascii=False, orient="records", indent=2
            )
    else:
        call_data, project, call_path_output = read_data(
            call_path=call_path,
            project_info_path=project_info_path,
            verbose=True,
        )

        call_data = call_data.progress_apply(
            lambda rec: raw_criteira(rec, project), axis=1
        )
        call_data.to_json(
            call_path_output, force_ascii=False, orient="records", indent=2
        )

    print((time.time() - start_time) / 60)
