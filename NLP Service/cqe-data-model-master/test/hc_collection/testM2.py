import json
import pandas as pd
import requests
import tqdm

FILE_DIALOG = "m2_clean.json"
FILE_GROUNDTRUTH = "m2ground.csv"
OUTPUT_PARSED_LABELS = False
PROJECT_ID = 'hc_clx_m2'
ENDPOINT = 'http://103.176.146.250:5005/predict/dialogue'

with open(FILE_DIALOG,'r') as f:
    calls = json.load(f)

callDict = dict()
for call in calls:
    callDict[call['name']] = call

labels = pd.read_csv(FILE_GROUNDTRUTH)

criterias = [
    'hc_clx_m2_oh1', 'hc_clx_m2_oh2',
    'hc_clx_m2_call_result'
]

map_criterias = {
    # 'Greeting': ['greet','agentIntroduce','companyName'],
    # 'Identification of client': ['confirmCustomer'],
    # 'Reason of the call': ['informAmount','informOverdue'],
    # 'Will you pay?': ['requestPayment'],
    # 'CustomerFB_Will': ['requestPayment'],
    # 'When': ['askPaymentDatetime'],
    # 'How much': ['askPaymentAmount'],
    # 'Where': ['askPaymentMethod'],
    # 'Summary structure': ['goodbye','thank'],
    # 'Payment receipt': ['askPaymentReceipt'],
    'Call Result': ['hc_clx_m2_call_result'],
    # 'CustomerFB_OH1': ['oh1'],
    'OH1 handle': ['hc_clx_m2_oh1'],
    'OH2 handle': ['hc_clx_m2_oh2'],
    # 'Call Result': ['callResult']
    # 'Permit2End': ["permitToEnd"]
}

# parse ground truth label to dataframe parsedDf
parsed = []
for idx, row in labels.iterrows():
    if type(row['audit_result']) != str or (row['criterion_name'] not in map_criterias):
        continue
    
    for nlp_crit in map_criterias.get(row['criterion_name']):
        parsed.append([row['file_name'], nlp_crit, row['audit_result'].lower()])

parsedDf = pd.DataFrame(parsed, columns=['file', 'crit', 'label'])
if OUTPUT_PARSED_LABELS:
    parsedDf.to_csv('parsedLabel.tsv', sep='\t', index=False)

# get predictions for every call in parsedDf
for each in tqdm.tqdm(parsedDf['file'].unique().tolist()):
    call = callDict[each]
    req_meta = {
        "project_id": PROJECT_ID,
        "fileName": each,
        "agentChannel": call.get("agentChannel"),
        "criteria": criterias,
        "metaDialog": {},
        "transcript": call.get("content"),
    }
    resp = requests.post(ENDPOINT, json=req_meta, timeout=60).json()
    if 'error' in resp:
        print(req_meta + '\n' + resp)
        continue
    call['prediction'] = resp
    callDict[each] = call

parsedDf = parsedDf.to_dict('records')

for call in parsedDf:
    if 'prediction' not in callDict[call['file']]:
        # this call aint get preded yet
        continue
    if 'call_result' in call.get('crit') or 'oh1' in call.get('crit'):
        call['pred'] = callDict[call['file']].get('prediction').get(call.get('crit')).get('decision')
    if 'oh2' in call.get('crit'):
        call['pred'] = callDict[call['file']].get('prediction').get(call.get('crit')).get('decision')

pd.DataFrame.from_records(parsedDf).to_csv("ehe.tsv", sep='\t', index=False)