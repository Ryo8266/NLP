import os
import json
import pandas as pd
import time
import tqdm
import requests
from sklearn.metrics import accuracy_score
from mapping import criteria, map_criteria_simple, map_criteria_complex

timestamp = time.strftime("%Y-%m-%d-%H:%M", time.localtime(time.time()))

mode = 'crit'
# while mode == '':
#     mode = input("select your mode:\n->crit (evaluate labelled calls by criteria)\n->call (evaluate labelled calls by call)\n->score (calculate score for unlabelled call)\n")

ENDPOINT = 'http://103.160.76.4:5005/predict/dialogue'
ENV = 'a100'

# concat module by lannp8
ENABLE_CONCAT = False
CONCAT_ENDPOINT = 'http://10.36.2.90:8001/merge'
CONCAT_CONTINUOUS = True

# textnorm
TEXTNORM_ENDPOINT = 'http://103.160.78.77:31930/dialogue'

HEADERS = {"Authorization": "Bearer duyld10"}
PROJECT_ID = 'gofigo_telesale_testunit'

file_dialog = "transcript_new.json" #input('path to transcript file, without .json: ') + '.json'
file_gt = 'ground_new.csv'
print(f'test on {ENV}')

# read data
with open(file_dialog,'r') as f:
    dialogs = json.load(f)
    dialogs = dialogs[:1]

with open("response.json",'r') as f:
    fake_resp = json.load(f)

if mode == 'crit' or mode == 'file':
    df = pd.read_csv(file_gt)
    print("Call without transcript:\nnot yet implement uhu")

# predict
for sample in tqdm.tqdm(dialogs):        
    transcript = sample["content"] if 'content' in sample else sample["transcript"]

    if mode == 'score': # perform TEXT-NORM
        temp = requests.post(TEXTNORM_ENDPOINT, json={'transcript':transcript}, timeout=60).json()
        for i in range(len(transcript)):
            transcript[i]['text'] = temp['transcript'][i]['text']

    if ENABLE_CONCAT:
        concatbody = {
            "agentChannel": sample["agentChannel"],
            "mergeFrom": "both",
            "continuous": CONCAT_CONTINUOUS,
            "transcript": transcript,
        }
        temp = requests.post(CONCAT_ENDPOINT, json=concatbody, timeout=60).json()
        transcript = [{
            "text": turn['text'].replace("[SEP]", ""),
            "channel": turn['channel']
        } for turn in temp]
        
    req_meta = {
        "project_id": PROJECT_ID,
        "fileName": sample["name"] if 'name' in sample else sample["fileName"],
        "agentChannel": sample["agentChannel"],
        "criteria": criteria,
        "metaDialog": {},
        "transcript": transcript,
    }
    # try:
    #     resp = requests.post(ENDPOINT, json=req_meta, timeout=30).json()
    # except TimeoutError:
    #     print("TIMEOUTTTTTTTTTTTTTTTT")
    sample['prediction'] = fake_resp #resp

# eval by criteria
if mode == 'crit':
    errors = []
    accList = []

    for criterion in map_criteria_simple.keys():
        label = df[df["Criterion Name"] == criterion]["Answer Label"].tolist()
        breakpoint()

        gt = [d['label'][map_criteria_simple[criterion]] for d in dialogs]
        pred = [d['prediction'][criterion]['evaluate'] if (d['prediction'][criterion]['task'] == 'query') else d['prediction'][criterion]['decision'] for d in dialogs]

        acc = accuracy_score(gt,pred).__round__(3)

        print('\n',criterion.ljust(15),'\t', 'acc:',acc,'\t')
        accList.append(str(criterion + ': ' + str(acc) + '\n'))

        # error log for inspection
        for i in range(len(gt)):
            if gt[i] != pred[i]:
                errors.append({
                    'file_name': dialogs[i]['name'],
                    'criteria': criterion,
                    'expected': gt[i],
                    'prediction': pred[i],
                    'response': dialogs[i]['prediction'][criterion],
                })

    if len(errors)>0:
        df_errors = pd.DataFrame.from_records(errors)
        df_errors.sort_values(by='file_name', inplace=True)
        df_errors.to_csv(f'log/{timestamp}_err_{ENV}.csv', index=False, encoding='utf-8-sig')
    with open(f'log/{timestamp}_acc_{ENV}.txt', 'w') as fo:
        for each in accList:
            fo.write(each)
