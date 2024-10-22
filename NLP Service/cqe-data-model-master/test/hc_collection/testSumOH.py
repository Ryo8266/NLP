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

headers = {"Authorization": "Bearer duyld10"}
project_id = 'enhange_clx'

file_dialog = 'collection_transcript.json'
file_gt = 'collection_ground.csv'
print(f'train on {env}')

# read data
with open(file_dialog,'r') as f:
    transcripts = json.load(f)
callGrounds = pd.read_csv(file_gt)

#fill nan in audit_result
callGrounds = callGrounds.fillna({'audit_result':'N/A'})

criterias = ['willpaySummary', 'nopaySummary', 'paidSummary', 'callResult', 'objectHandling']

labeledCallName = set(callGrounds['file_name'])
labeledCall = []

for transcript in tqdm.tqdm(transcripts):
    if transcript['name'] not in labeledCallName:
        continue
    req_meta = {
        "project_id": project_id,
        "fileName": transcript["name"],
        "agentChannel": transcript["agentChannel"],
        "criteria": criterias,
        "metaDialog": {},
        "transcript": transcript["content"],
    }
    resp = requests.post(endpoint, json=req_meta, timeout=60).json()
    if 'error' in resp:
        breakpoint(header='error response')
    transcript['pred'] = resp
    #find columns of one call and convert its criteria to dict
    # transcript['ground']=callGrounds[callGrounds['file_name']==transcript['name']][['criterion_name','audit_result']].set_index('criterion_name').T.to_dict('records')[0]
    labeledCall.append(transcript)

# ===============================================Summary land================================================= #

map_reasons_entities = {
    'Thiếu thông tin thanh toán': 'thanhtoan4', #will
    'Thiếu motivation': 'motivation_title',#will,no
    'Thiếu thông báo tình trạng chưa nhận được tiền': 'paid_summary',#paid
    'Thiếu kiểm tra / giữ biên lai': 'receipt',#paid
    'Thiếu liên hệ hotline': 'hotline',#no,paid
    'Thiếu lưu ý về tình trạng hợp đồng': 'nopay_summary',#no
    'Thiếu hướng dẫn client thanh toán sớm số tiền cần thanh toán': 'amount'#no
}

evalResult = []#file,result,ground,pred,missing,predntt,error,success where missing and predntt are details about entities
success=0
fail=0

def setCallRes(result: dict, pred, err: str) -> dict:
    result['pred'] = pred
    result['err'] = err
    if pred=='yes' or pred=='ok': result['success'] = 1
    return result

#check summary
for call in labeledCall:
    callRes = {'file':call['name']}

    ground = callGrounds[callGrounds['file_name']==call['name']]
    groundDict = ground[['criterion_name','audit_result']].set_index('criterion_name').T.to_dict('records')[0]
    if 'Call Result' not in groundDict:
        breakpoint()
    callRes['result'] = groundDict['Call Result']
    summaryEval = groundDict['Contain all information'] #Yes,No,Partially

    #parsed ground reason to entities
    parsedReason = []
    reasons = ground.loc[ground['criterion_name']=='Contain all information','reason'].values[0]
    if type(reasons) is str:
        parsedReason = [map_reasons_entities[ntt] for ntt in reasons.split(';#')]
        callRes['missing'] = set(parsedReason)

    #take prediction entities out
    predEntities = []

    if groundDict['Call Result'] == '':
        breakpoint('et o et call result is null')
    elif groundDict['Call Result'] == 'Willpay':
        needies = ['amount', 'bring_contract_code', 'payment_datetime', 'payment_method', 'motivation_title']
        #amount, bring_contract_code, payment_datetime, payment_method là xác nhận thông tin thanh toán, motivation_title là motivation
        ntt=[utter['entities'].keys() for utter in call['pred']['willpaySummary']['position']]
        predEntities = [item for sublist in ntt for item in sublist] #flatten list of list of entity in all summary utters
        callRes['predntt'] = set(predEntities)

        if summaryEval == 'Yes':
            callRes['ground'] = 'yes'
            if len(list(set(['amount', 'bring_contract_code', 'payment_datetime', 'payment_method']) & set(predEntities))) >= 3 and 'motivation_title' in predEntities:
                callRes = setCallRes(callRes, 'yes', '')
            else:
                callRes = setCallRes(callRes, 'no', call['pred']['willpaySummary'])
        elif summaryEval == 'Partially' or summaryEval == 'No':
            callRes['ground'] = 'no'
            if ('motivation_title' in parsedReason and 'motivation_title' in predEntities) or ('motivation_title' not in parsedReason and 'motivation_title' not in predEntities):#fail for motivation
                callRes = setCallRes(callRes, 'fail', call['pred']['willpaySummary'])
            else:
                if 'thanhtoan4' in parsedReason and len(list(set(['amount', 'bring_contract_code', 'payment_datetime', 'payment_method']) & set(predEntities))) <3:
                    callRes = setCallRes(callRes, 'ok', '')
                elif 'thanhtoan4' not in parsedReason and len(list(set(['amount', 'bring_contract_code', 'payment_datetime', 'payment_method']) & set(predEntities))) >= 3:
                    callRes = setCallRes(callRes, 'ok', '')
                else:
                    callRes = setCallRes(callRes, 'fail', call['pred']['willpaySummary'])

    elif groundDict['Call Result'] == 'Nopay':
        #amount là số tiền agent đòi thanh toán sớm, motivation_title là motivation, nopay_summary là tình trạng hợp đồng (cty sẽ gọi lại, hđ chưa được thanh toán), hotline là kêu gọi tổng đài
        needies = ['amount', 'motivation_title', 'nopay_summary', 'hotline']

        ntt=[utter['entities'].keys() for utter in call['pred']['nopaySummary']['position']]
        predEntities = [item for sublist in ntt for item in sublist] #flatten list of list of entity in all summary utters
        callRes['predntt'] = set(predEntities)

        if summaryEval == 'Yes':
            callRes['ground'] = 'yes'
            if set(needies).issubset(predEntities):
                callRes = setCallRes(callRes, 'yes', '')
            else:
                callRes = setCallRes(callRes, 'no', call['pred']['nopaySummary'])
        elif summaryEval == 'Partially' or summaryEval == 'No':
            callRes['ground'] = 'no'
            shouldappear = set(needies) - set(parsedReason)
            if (shouldappear).issubset(predEntities):
                callRes = setCallRes(callRes, 'ok', '')
            else:
                callRes = setCallRes(callRes, 'fail', call['pred']['nopaySummary'])
    elif groundDict['Call Result'] == 'Paid':
        #receipt (hóa đơn), hotline (gọi hotline) và paid_summary (thông báo chưa nhận được tiền)
        needies = ['receipt', 'paid_summary', 'hotline']

        ntt=[utter['entities'].keys() for utter in call['pred']['paidSummary']['position']]
        predEntities = [item for sublist in ntt for item in sublist] #flatten list of list of entity in all summary utters
        callRes['predntt'] = set(predEntities)

        if summaryEval == 'Yes':
            callRes['ground'] = 'yes'
            if set(needies).issubset(predEntities):
                callRes = setCallRes(callRes, 'yes', '')
            else:
                callRes = setCallRes(callRes, 'no', call['pred']['paidSummary'])
        elif summaryEval == 'Partially' or summaryEval == 'No':
            callRes['ground'] = 'no'
            shouldappear = set(needies) - set(parsedReason)
            if (shouldappear).issubset(predEntities):
                callRes = setCallRes(callRes, 'ok', '')
            else:
                callRes = setCallRes(callRes, 'fail', call['pred']['paidSummary'])
    else:
        breakpoint('et o et 2')
    
    evalResult.append(callRes)


result = pd.DataFrame(evalResult)
result.to_csv(f'log/sum_{timestamp}_{env}.csv', encoding='utf-8', index=False)
scoreCount = result['success'].value_counts()
print(f"Summary score: total {len(result)}, pass {scoreCount[1]}, accuracy {scoreCount[1]/len(result)}")

# ===============================================OH land==================================================== #

evalResult = []#file,criteria,ground,pred,err is list of pandas dataframe
success=0
fail=0

map_oh1_reason = {
    'Thiếu motivation theo quy định cho group M1B': 'motivation_title',
    'Thiếu giải pháp theo quy định cho group M1B': 'oh_solution',
    'Thiếu mục tiêu theo quy định cho group M1B': 'today_tomorrow',
}

map_oh2_reason = {
    'Thiếu motivation theo quy định cho group M1B': 'motivation_title2',
    'Thiếu giải pháp theo quy định cho group M1B': 'oh_solution2',
    'Thiếu mục tiêu theo quy định cho group M1B': 'payment_datetime',
}

for call in labeledCall:
    callRes = []
    ground = callGrounds[callGrounds['file_name']==call['name']]
    oh1audit = ground.loc[ground['criterion_name']=='OH1 handle','audit_result'].values[0]#Yes/No
    oh1reasonMap = ground.loc[ground['criterion_name']=='OH1 handle','reason'].values[0]#map_oh1_reason
    oh1reason = []
    if type(oh1reasonMap) is str:
        oh1reason = [map_oh1_reason[reason] for reason in oh1reasonMap.split(';#')]

    oh2audit = ground.loc[ground['criterion_name']=='OH2 handle','audit_result'].values[0]#Yes/No
    oh2reasonMap = ground.loc[ground['criterion_name']=='OH2 handle','reason'].values[0]#map_oh2_reason
    oh2reason = []
    if type(oh2reasonMap) is str:
        oh2reason = [map_oh2_reason[reason] for reason in oh2reasonMap.split(';#')]

    ohEval = call['pred']['objectHandling']['evaluate']#yes/no
    ohNtt = []#list of all entt, with no duplication in each utter, and with duplication on the whole list(of all utter)
    if ohEval == 'yes':
        position = call['pred']['objectHandling']['position']
        uttersNtt = [list(set(utter['entities'].keys())) for utter in position]#get all entities without duplicate in each utter
        ohNtt = [ntt for utterNtt in uttersNtt for ntt in utterNtt]#merge all ntt of all utter to a list(have duplicate)

    #TODO: dai qua nhma toi met =;;= sua sau cho cho vao nhe
    #parse ground truth to callRes
    if oh1audit == 'Yes':
        callRes.append({'file':call['name'],'crit':'motivation_title','ground':'yes','pred':'no'})
        callRes.append({'file':call['name'],'crit':'oh_solution','ground':'yes','pred':'no'})
        callRes.append({'file':call['name'],'crit':'today_tomorrow','ground':'yes','pred':'no'})
    elif len(oh1reason) >0:
        if 'motivation_title' in oh1reason:
            callRes.append({'file':call['name'],'crit':'motivation_title','ground':'no','pred':'no'})
        else:
            callRes.append({'file':call['name'],'crit':'motivation_title','ground':'yes','pred':'no'})
        if 'oh_solution' in oh1reason:
            callRes.append({'file':call['name'],'crit':'oh_solution','ground':'no','pred':'no'})
        else:
            callRes.append({'file':call['name'],'crit':'oh_solution','ground':'yes','pred':'no'})
        if 'today_tomorrow' in oh1reason:
            callRes.append({'file':call['name'],'crit':'today_tomorrow','ground':'no','pred':'no'})
        else:
            callRes.append({'file':call['name'],'crit':'today_tomorrow','ground':'yes','pred':'no'})
    else:
        callRes.append({'file':call['name'],'crit':'motivation_title','ground':'no','pred':'no'})
        callRes.append({'file':call['name'],'crit':'oh_solution','ground':'no','pred':'no'})
        callRes.append({'file':call['name'],'crit':'today_tomorrow','ground':'no','pred':'no'})

    if oh2audit == 'Yes':
        callRes.append({'file':call['name'],'crit':'motivation_title2','ground':'yes','pred':'no'})
        callRes.append({'file':call['name'],'crit':'oh_solution2','ground':'yes','pred':'no'})
        callRes.append({'file':call['name'],'crit':'payment_datetime','ground':'yes','pred':'no'})
    elif len(oh2reason) >0:
        if 'motivation_title2' in oh2reason:
            callRes.append({'file':call['name'],'crit':'motivation_title2','ground':'no','pred':'no'})
        else:
            callRes.append({'file':call['name'],'crit':'motivation_title2','ground':'yes','pred':'no'})
        if 'oh_solution2' in oh2reason:
            callRes.append({'file':call['name'],'crit':'oh_solution2','ground':'no','pred':'no'})
        else:
            callRes.append({'file':call['name'],'crit':'oh_solution2','ground':'yes','pred':'no'})
        if 'payment_datetime' in oh2reason:
            callRes.append({'file':call['name'],'crit':'payment_datetime','ground':'no','pred':'no'})
        else:
            callRes.append({'file':call['name'],'crit':'payment_datetime','ground':'yes','pred':'no'})
    else:
        callRes.append({'file':call['name'],'crit':'motivation_title2','ground':'no','pred':'no'})
        callRes.append({'file':call['name'],'crit':'oh_solution2','ground':'no','pred':'no'})
        callRes.append({'file':call['name'],'crit':'payment_datetime','ground':'no','pred':'no'})
        
    callDf = pd.DataFrame(callRes, columns=['file','crit','ground','pred','error'])

    #G là oh_solution, M là motivation_title, còn T của OH1 là today_tomorrow, T của OH2 là payment_datetime ạ, thông tin phụ có thêm amount là số tiền thanh toán, prepay_percent là 75% của OH2
    solCount = 0#first oh_solution appear or not
    for each in ohNtt:
        if each == 'oh_solution' and solCount==0:
            callDf.loc[(callDf['file']==call['name']) & (callDf['crit']=='oh_solution'), 'pred'] = 'yes'
            solCount+=1
        if each == 'oh_solution' and solCount>0:
            callDf.loc[(callDf['file']==call['name']) & (callDf['crit']=='oh_solution2'), 'pred'] = 'yes'
            solCount+=1
        
        if each == 'motivation_title' and solCount<=1:
            callDf.loc[(callDf['file']==call['name']) & (callDf['crit']=='motivation_title'), 'pred'] = 'yes'
        if each == 'motivation_title' and solCount>1:
            callDf.loc[(callDf['file']==call['name']) & (callDf['crit']=='motivation_title2'), 'pred'] = 'yes'

        if each == 'today_tomorrow': 
            callDf.loc[(callDf['file']==call['name']) & (callDf['crit']=='today_tomorrow'), 'pred'] = 'yes'
        if each == 'payment_datetime' and solCount>0:
            callDf.loc[(callDf['file']==call['name']) & (callDf['crit']=='payment_datetime'), 'pred'] = 'yes'
            solCount+=1
        if each == 'prepay_percent':
            callDf.loc[(callDf['file']==call['name']) & (callDf['crit']=='oh_solution2'), 'pred'] = 'yes'
            solCount+=2
    
    evalResult.append(callDf)
    if callDf['ground'].equals(callDf['pred']) : success+=1
    else: fail+=1

pd.concat(evalResult, ignore_index=True).to_csv(f'log/oh_{timestamp}_{env}.csv',index=False)
print("OH score: ", success/(success+fail))