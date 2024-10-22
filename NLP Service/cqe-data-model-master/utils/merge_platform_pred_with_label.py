import pandas as pd
import json
import tqdm
import requests
import time

timestamp = time.strftime("%m_%d_%H_%M", time.localtime(time.time()))

GROUND = "/home/ngocbtb8/Downloads/callresult_ground.csv"
TRANSCRIPT = "/home/ngocbtb8/Downloads/588calls_clean.json"
PLATPRED = "/home/ngocbtb8/Downloads/from-es.csv"

ground = pd.read_csv(GROUND)
pred = pd.read_csv(PLATPRED)

pred = pred[["file_name", "callResult_decision"]]
ground = ground[ground["criterion_name"] == "Call Result"][
    ["file_name", "audit_result"]
]

merged = pd.merge(ground, pred, on="file_name", how="outer")
merged.to_csv("merge_platform_pred_with_label.csv")

with open(TRANSCRIPT, "r") as f:
    trans = json.load(f)

PROJECT_ID = "enhange_clx"
CRITERIA = ["callResult"]
ENPOINT = "http://103.160.76.4:5005/predict/dialogue"


def getCallResult(transcript, filename, agentChannel):
    req_meta = {
        "project_id": PROJECT_ID,
        "fileName": filename,
        "agentChannel": agentChannel,
        "criteria": CRITERIA,
        "metaDialog": {},
        "transcript": transcript,
    }
    resp = requests.post(ENPOINT, json=req_meta, timeout=60).json()
    if "error" in resp:
        breakpoint(header="error response")
    return resp[CRITERIA[0]]["decision"], resp[CRITERIA[0]]["decision_position"]


for each in tqdm.tqdm(trans):
    if each["name"] in merged["file_name"].tolist():
        pred, resp = getCallResult(each["content"], each["name"], each["agentChannel"])
        merged.loc[merged["file_name"] == each["name"], "prediction"] = pred
        merged.loc[merged["file_name"] == each["name"], "decision_position"] = str(resp)

merged.to_csv(f"merge_platform_pred_with_label_{timestamp}.csv", index=False)
