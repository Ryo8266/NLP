import os
import json
import pandas as pd
import time
import tqdm
import requests
from sklearn.metrics import accuracy_score
from mapping import criteria, map_reason_criteria

timestamp = time.strftime("%Y-%m-%d-%H:%M", time.localtime(time.time()))

mode = ''
while mode == '':
    mode = input("select your mode:\n->crit (evaluate labelled calls by criteria)\n->call (evaluate labelled calls by call)\n->score (calculate score for unlabelled call)\n")

ENDPOINT = 'http://103.160.76.4:5005/predict/dialogue'
ENV = 'a100'

# concat module by lannp8
ENABLE_CONCAT = False
CONCAT_ENDPOINT = 'http://10.36.2.90:8001/merge'
CONCAT_CONTINUOUS = True

# textnorm
TEXTNORM_ENDPOINT = 'http://103.160.78.77:31930/dialogue'

OUTPUT_PARSED_LABELS = True

HEADERS = {"Authorization": "Bearer duyld10"}
PROJECT_ID = 'gofigo_telesale_testunit'

file_dialog = input('path to transcript file, without .json: ') + '.json'
file_gt = 'ground_truth.tsv'
print(f'test on {ENV}')

# read data
with open(file_dialog,'r') as f:
    dialogs = json.load(f)

if mode != 'score':
    df = pd.read_csv(file_gt, sep="\t")

    dialogs_labelled = []
    dialog_unlabelled = []

    # parse label
    for dialog in dialogs:
        df_dialog = df[df['file_name'] == dialog['name']]
        if len(df_dialog) == 0:
            dialog_unlabelled.append(dialog)
            continue

        # label is map{criteriaName}(yes/no)
        label = { criterion:'yes' for criterion in criteria } #init with yes
        label['identification_of_needs_close_question'] = 'no'#special case
        dialog['label'] = label
        dialogs_labelled.append(dialog)

        for row in df_dialog.iloc:
            # map_reason_criteria[row['reason']] is criteria name
            # un-use criteria
            if row['reason'] not in map_reason_criteria.keys():
                # special case
                if row['reason'] == 'Sử dụng câu hỏi đóng để xác định nhu cầu':
                    label['identification_of_needs_close_question'] = 'yes'
                continue
            
            if type(map_reason_criteria[row['reason']]) == str:
                label[map_reason_criteria[row['reason']]] = 'no'
            else:
                for ehe in map_reason_criteria[row['reason']]:
                    label[ehe] = 'no'

    # report dialogs label coverage
    names_dialogs = [d['name'] for d in dialogs]
    names_dialogs_labelled = [d['name'] for d in dialogs_labelled]
    names_dialogs_unlabelled = [d['name'] for d in dialog_unlabelled]
    dialogs_without_transcript = [ d for d in set(df['file_name']) if d not in names_dialogs ]

    print(len(names_dialogs_labelled),'dialogs testing on','\n',names_dialogs_labelled,'\n')
    print(len(names_dialogs_unlabelled),'dialogs unlabelled:','\n',names_dialogs_unlabelled,'\n')
    print(len(dialogs_without_transcript),'dialogs without transcript:','\n',dialogs_without_transcript,'\n')

    if OUTPUT_PARSED_LABELS:
        with open(f'parsedLabel.csv', 'w') as fo:
            for each in dialogs_labelled:
                for k, v in each['label'].items():
                    fo.write(each['name']+'\t'+k+'\t'+v+'\n')

    dialogs = dialogs_labelled #dict_keys(['name', 'agentChannel', 'content', 'label'])

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
    resp = requests.post(ENDPOINT, json=req_meta, timeout=60).json()
    if 'error' in resp:
        breakpoint(header='error response')
    sample['prediction'] = resp

# eval by criteria
if mode == 'crit':
    errors = []
    accList = []

    for criterion in criteria:
        gt = [d['label'][criterion] for d in dialogs]
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

# eval by file
if mode == 'call':
    errors = []
    accList = []

    for d in dialogs:
        gt = list(d['label'].values())
        pred = [d['prediction'][criterion]['evaluate'] if (d['prediction'][criterion]['task'] == 'query') else d['prediction'][criterion]['decision'] for criterion in criteria]

        acc = accuracy_score(gt,pred).__round__(3)

        print('\n',d['name'].ljust(15),'\t', 'acc:',acc,'\t')
        accList.append([d['name'],acc])

        # error log for inspection
        for i in range(len(gt)):
            if gt[i] != pred[i]:
                errors.append({
                    'file_name': d['name'],
                    'criteria': criteria[i],
                    'expected': gt[i],
                    'prediction': pred[i],
                    'response': d['prediction'][criteria[i]],
                })
            
    accDf = pd.DataFrame(accList, columns=['callname', 'acc'])
    accDf.sort_values('acc').to_csv(f'log/{timestamp}_acc_by_file_{ENV}.csv', index=False)
    with open(f'log/{timestamp}_acc_by_file_{ENV}.txt', 'w') as fo:
        for each in accList:
            fo.write(each)

# eval by file
if mode == 'score':
    accList = []

    for d in dialogs:
        pred = [d['prediction'][criterion]['evaluate'] if (d['prediction'][criterion]['task'] == 'query') else d['prediction'][criterion]['decision'] for criterion in criteria]
        score = pred.count('yes')

        accList.append([
            d["name"] if 'name' in d else d["fileName"],
            score,
            ','.join([criteria[i] for i in range(len(pred)) if pred[i]=='no'])
            ])
            
    accDf = pd.DataFrame(accList, columns=['callname', 'score', 'no_criteria'])
    accDf.sort_values('score').to_csv(f'{file_dialog}_{timestamp}_{ENV}.csv', index=False)
