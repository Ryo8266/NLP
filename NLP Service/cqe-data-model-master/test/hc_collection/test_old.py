import os
import json
import pandas as pd
import time
import tqdm
import requests

timestamp = time.strftime("%Y-%m-%d-%H:%M", time.localtime(time.time()))

# endpoint = 'http://103.160.78.77:31905/predict/dialogue'
# env = 'dev'

endpoint = 'http://103.160.76.4:5005/predict/dialogue'
env = 'a100'

ENABLE_CONCAT = False
CONCAT_ENDPOINT = 'http://10.36.2.90:8001/merge'
CONCAT_CONTINUOUS = True

OUTPUT_PARSED_LABELS = False

FILE_DIALOG = "collection_transcript.json"
FILE_GROUNDTRUTH = "collection_ground.csv"
print(f'test on {env}')

# list of criteria needed in request body
criterias = [
    #'greet','agentIntroduce','companyName',
    #'confirmCustomer',
    #'informAmount','informOverdue',
    'requestPayment',
    'askPaymentDatetime', 'askPaymentAmount', 'askPaymentMethod', 'askPaymentReceipt',
    #'goodbye','thank',
    #'callResult',
    # "permitToEnd"
]

# map ground_truth column to criteria
map_criterias = {
    # 'Greeting': ['greet','agentIntroduce','companyName'],
    # 'Identification of client': ['confirmCustomer'],
    # 'Reason of the call': ['informAmount','informOverdue'],
    # 'Will you pay?': ['requestPayment'],
    # 'When': ['askPaymentDatetime'],
    # 'How much': ['askPaymentAmount'],
    # 'Where': ['askPaymentMethod'],
    # 'Summary structure': ['goodbye','thank'],
    # 'Payment receipt': ['askPaymentReceipt'],
    # 'Contain all information': ['willpaySummary', 'nopaySummary', 'paidSummary'],
    # 'OH1 handle': ['objectHandling'],
    # 'OH2 handle': ['objectHandling'],
    'Call Result': ['callResult']
    # 'Permit2End': ["permitToEnd"]
}

# map from ground_truth reason to smaller criteria
map_reason_criteria = {
    'KB KH: Thiếu số tiền cung cấp cho KH': 'informAmount',
    'KB KH: Thiếu thông tin DPD': 'informOverdue',
    'Không chào hỏi': 'greet',
    'Không cám ơn': 'thank',
    'Không chào tạm biệt': 'goodbye',
    'Không giới thiệu tên công ty': 'companyName',
    'Không giới thiệu tên nhân viên': 'agentIntroduce',
    'Không hỏi theo quy định': 'requestPayment',
    'Không lấy được thông tin kênh thanh toán theo quy định': 'askPaymentMethod',
    'Không lấy được thông tin ngày thanh toán theo quy định': 'askPaymentDatetime',
    'Không lấy được thông tin số tiền theo quy định': 'askPaymentAmount',
    'Thiếu ý - Không xác định họ tên': 'confirmCustomer',
    'Không hỏi thông tin biên lai theo quy định': 'askPaymentReceipt',

    # 'Thiếu kiểm tra / giữ biên lai': 'paidSummary',
    # 'Thiếu thông báo tình trạng chưa nhận được tiền': 'paidSummary',
    # 'Thiếu thông tin thanh toán': 'willpaySummary',
    # 'Thiếu motivation': 'willpaySummary',
    # 'Thiếu lưu ý về tình trạng hợp đồng': 'nopaySummary',
    # 'Thiếu hướng dẫn client thanh toán sớm số tiền cần thanh toán': 'nopaySummary',
    # 'Thiếu liên hệ hotline': 'nopaySummary',

    # 'Thiếu motivation theo quy định cho group M1B': 'objectHandling',
    # 'Thiếu giải pháp theo quy định cho group M1B': 'objectHandling',
    # 'Thiếu mục tiêu theo quy định cho group M1B': 'objectHandling',
}

# read data
with open(FILE_DIALOG,'r') as f:
    dialogs = json.load(f)

df = pd.read_csv(FILE_GROUNDTRUTH)

dialogs_labelled = []
dialog_unlabelled = []

# parse label
for dialog in dialogs:
    df_dialog = df[df['file_name'] == dialog['name']]
    if len(df_dialog) == 0:
        dialog_unlabelled.append(dialog)
        continue

    # label is map{criteriaName}(yes/no)
    label = { criteria:'' for criteria in criterias }
    dialog['label'] = label
    dialogs_labelled.append(dialog)

    for row in df_dialog.iloc:
        if row['criterion_name'] not in map_criterias.keys():
            continue

        # default label to 'yes'
        # row['criterion_name'] is map_criterias's keys
        for criteria in map_criterias[row['criterion_name']]:
            label[criteria] = 'yes'
            if row['audit_result'] == 'Willpay':
                label[criteria] = 'willpay'
            if row['audit_result'] == 'Nopay':
                label[criteria] = 'nopay'
            if row['audit_result'] == 'Paid':
                label[criteria] = 'paid'
            if row['audit_result'] == 'N/A' or row['audit_result'] == '' or type(row['audit_result']) != str:
                label[criteria] = 'no'
            
            #TODO: this is manual, fix this
            if row['audit_result'] == 'No' and row['criterion_name'] in ['Identification of client', 'Will you pay?', 'When', 'How much', 'Where', 'Payment receipt', 'Permit2End']:
                label[criteria] = 'no'

        # process reason field
        # label 'no' w.r.t reason
        if row['reason'] and type(row['reason']) == str:
            reasons = row['reason'].split(';#')
            for reason in reasons:
                if reason not in map_reason_criteria:
                    breakpoint(header=reason)
                else: #map_reason_criteria[reason] not in ['willpaySummary', 'nopaySummary', 'paidSummary']:
                    label[map_reason_criteria[reason]] = 'no'

    if '' in label.values():
        breakpoint(header='\n missing label, a criteria has no label \n')

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

HEADERS = {"Authorization": "Bearer duyld10"}
PROJECT_ID = 'ngocbtb-ctv'

for sample in tqdm.tqdm(dialogs):
    transcript = sample["content"]

    if ENABLE_CONCAT:
        concatbody = {
            "agentChannel": sample["agentChannel"],
            "mergeFrom": "both",
            "continuous": CONCAT_CONTINUOUS,
            "transcript": sample["content"],
        }
        temp = requests.post(CONCAT_ENDPOINT, json=concatbody, timeout=60).json()
        transcript = [{
            "text": turn['text'].replace("[SEP]", ""),
            "channel": turn['channel']
        } for turn in temp]
        
    req_meta = {
        "project_id": PROJECT_ID,
        "fileName": sample["name"],
        "agentChannel": sample["agentChannel"],
        "criteria": criterias,
        "metaDialog": {},
        "transcript": transcript,
    }
    resp = requests.post(endpoint, json=req_meta, timeout=60).json()
    if 'error' in resp:
        breakpoint(header='error response')
    sample['prediction'] = resp



# eval
from sklearn.metrics import accuracy_score

errors = []
accList = []

for criteria in criterias:
    # gt = df[criteria].tolist()
    gt = [d['label'][criteria] for d in dialogs ]
    pred = [d['prediction'][criteria]['evaluate'] if (d['prediction'][criteria]['task'] == 'query') else d['prediction'][criteria]['decision'] for d in dialogs]

    acc = accuracy_score(gt,pred).__round__(3)

    print('\n',criteria.ljust(15),'\t', 'acc:',acc,'\t')
    accList.append(str(criteria + ': ' + str(acc) + '\n'))

    # error log for inspection
    for i in range(len(gt)):
        if gt[i] != pred[i]:
            errors.append({
                'file_name': dialogs[i]['name'],
                'criteria': criteria,
                'expected': gt[i],
                'prediction': pred[i],
                'response': dialogs[i]['prediction'][criteria],
            })

df_errors = pd.DataFrame.from_records(errors)
df_errors.sort_values(by='file_name', inplace=True)
df_errors.to_csv(f'log/{timestamp}_err_{env}.csv', index=False, encoding='utf-8-sig')
with open(f'log/{timestamp}_acc_{env}.txt', 'w') as fo:
    for each in accList:
        fo.write(each)


