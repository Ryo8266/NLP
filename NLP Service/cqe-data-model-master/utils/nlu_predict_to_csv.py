import requests
import glob
import json
import os

DME_APP_CODE = "askPaymentInfo"
FPTAI_TOKEN_BOT = "32d9fc584cba62bd26bd1499b2d80466"
AGENT_CHANNEL = 1


def get_files():
    files = []
    for file in glob.glob("*.json"):
        files.append(file)
    return files


def call_nlu(text, url):
    HEADER = {
        "Authorization": "Bearer duyld10",
        "Content-Type": "application/json",
    }
    PARAMS = {
        "language": "vi",
        "content": text,
        "app_code": DME_APP_CODE,
        "model_file": "latest__v4_joint",
    }
    r = requests.post(url=url, headers=HEADER, json=PARAMS)
    data = r.json().get("data")
    intent = data.get("intents")[0].get("label")
    intent_confidence = data.get("intents")[0].get("confidence")
    entities = data.get("entities")
    tmp = []
    if len(entities) > 0:
        for e in entities:
            # print(text, e)
            tmp.append("{} ({})".format(e.get("entity"), e.get("real_value")))
    return "{}".format(intent), tmp


def call_nlu_pro(text, url):
    HEADER = {
        "Authorization": "Bearer " + FPTAI_TOKEN_BOT,
        "Content-Type": "application/json",
    }
    PARAMS = {"language": "vi", "content": text}
    r = requests.post(url=url, headers=HEADER, json=PARAMS)
    data = r.json().get("data")
    intent = data.get("intents")[0].get("label")
    intent_confidence = data.get("intents")[0].get("confidence")
    entities = data.get("entities")
    tmp = []
    if len(entities) > 0:
        for e in entities:
            # print(text, e)
            tmp.append("{} ({})".format(e.get("entity"), e.get("real_value")))
    return "{}".format(intent), tmp


files = get_files()
files = ["test/hc_collection/transcript_new.json"]

SAVE_TO_MANY_FILES = True

if SAVE_TO_MANY_FILES:
    for file in files:
        # dir = file.replace('.json', '')
        fi = open(file, "r", encoding="utf8")
        # fo = open(file+'.csv', 'w', encoding='utf8')
        # fo.writelines('text\tfpt.ai intent\tfpt.ai entities\ta100 intent\ta100 entities\n')
        data = json.load(fi)

        for d in data:
            dir = file.replace(".json", "")
            print(dir)
            if not os.path.exists(dir):
                os.mkdir(dir)
            fo = open("{}/{}.csv".format(dir, d.get("name")), "w", encoding="utf8")
            fo.writelines(
                "text\tfpt.ai intent\ta100 intent\tfpt.ai entities\ta100 entities\tis diff intent\n"
            )
            transcrip = d.get("content")
            call_name = d.get("name")

            agent_sent = []
            for sent in transcrip:
                is_diff_intent = 0

                if sent.get("channel") == AGENT_CHANNEL:
                    agent_sent.append(sent.get("text"))
                    if sent.get("text") is not None and len(sent.get("text")) > 0:
                        intent, entities = call_nlu(
                            sent.get("text"), "http://103.160.76.4:5005/predict/joint"
                        )
                        intent_, entities_ = call_nlu_pro(
                            sent.get("text"), "https://api-v35.fpt.ai/api/v3/predict"
                        )
                        if intent_ != intent:
                            is_diff_intent = 1
                        fo.writelines(
                            "{}\t{}\t{}\t{}\t{}\t{}\n".format(
                                sent.get("text"),
                                intent_,
                                intent,
                                entities_,
                                entities,
                                is_diff_intent,
                            )
                        )
                    # break
            # break
        break
else:  # save to one big file
    for file in files:
        dir = file.replace(".json", "")
        fi = open(file, "r", encoding="utf8")
        data = json.load(fi)
        fo = open("{}_{}.csv".format(dir, DME_APP_CODE), "w", encoding="utf8")
        fo.writelines(
            "call name\ttext\tfpt.ai intent\ta100 intent\tfpt.ai entities\ta100 entities\tis diff intent\n"
        )

        for d in data:
            print(dir)
            if not os.path.exists(dir):
                os.mkdir(dir)
            transcrip = d.get("content")
            call_name = d.get("name")

            agent_sent = []
            for sent in transcrip:
                is_diff_intent = 0

                if sent.get("channel") == AGENT_CHANNEL:
                    agent_sent.append(sent.get("text"))
                    if sent.get("text") is not None and len(sent.get("text")) > 0:
                        intent, entities = call_nlu(
                            sent.get("text"), "http://103.160.76.4:5005/predict/joint"
                        )
                        intent_, entities_ = call_nlu_pro(
                            sent.get("text"), "https://api-v35.fpt.ai/api/v3/predict"
                        )
                        if intent_ != intent:
                            is_diff_intent = 1
                        fo.writelines(
                            "{}\t{}\t{}\t{}\t{}\t{}\t{}\n".format(
                                call_name,
                                sent.get("text"),
                                intent_,
                                intent,
                                entities_,
                                entities,
                                is_diff_intent,
                            )
                        )
        break
