import json
from tqdm import tqdm
import pandas as pd
tqdm.pandas()


def gen_data_train(sample_df, app_code):
    data_train = {
        "api_key": "",
        "app_code": app_code,
        "callback": {"error": "", "success": ""},
        "dictionary": [{"alternatives": [], "phrase": ""}],
        "domain": "",
        "engine": "nlu",
        "language": "vi",
        "no_accent": False,
        "sub_language": "",
        "entities": [],
        "samples": [],
    }

    sample_df = sample_df.rename(columns={"sample": "text", "label": "intent"})
    # entities = list({s["label"]: s for s in sample_df["entities"][0]}.values())

    data_train["entities"] = [
        {"entity": "$number", "type": "builtin", "values": []},
        {"entity": "$address", "type": "builtin", "values": []},
    ]
    # for e in entities:
    #     entity = {"entity": e["label"], "type": "freetext", "value": []}
    #     data_train["entities"].append(entity)

    data_train["samples"] = sample_df.to_dict("records")

    return data_train


def map_entity(content: pd.DataFrame, orient="both"):
    if orient == "agent":
        content = content[content["channel"] == "agent"]
        if len(content) == 0:
            return []
    text = merge_turn(content, orient)
    content["label"] = content.apply(lambda rec: rec.get("intent", "[UNK]"), axis=1)
    content["value"] = content.apply(lambda rec: rec["text"], axis=1)
    content["start"] = content.apply(lambda rec: text.find(rec["value"]), axis=1)
    content["end"] = content.apply(lambda rec: rec["start"] + len(rec["value"]), axis=1)
    content["sub_entities"] = content.apply(lambda rec: rec.get("entities", []), axis=1)

    # content = content[~((content["label"]==None) & (len(content["sub_entities"])==0))]
    content = content[~(content["label"]=="") & ~(len(content["sub_entities"])==0)]

    result = content[["label", "value", "sub_entities", "start", "end"]].to_dict(
        "records"
    )

    return result


def merge_turn(content: pd.DataFrame, orient="both"):
    """merge_turn concat utter to paragraph

    Args:
        orient (str, optional): way to merge sample with [both|agent]. Defaults to "both".
    """
    if orient == "both":
        content["combine"] = content.apply(
            lambda rec: f'<{rec["channel"]}>: {rec["text"]}', axis=1
        )
        return " [CLS] ".join(content["combine"].tolist())
    else:
        content = content[content["channel"] == orient]
        if len(content) == 0:
            content_platten = ""
        else:
            content_platten = " [CLS] ".join(content["text"].tolist())
        return content_platten


def pre_process_call(agentChannel, content, return_type="df"):
    content_df = pd.DataFrame(content)
    content_df["channel"] = content_df["channel"].apply(
        lambda channel: "agent" if channel == agentChannel else "customer"
    )
    if return_type != "df":
        return content_df.to_dict("records")
    else:
        return content_df


def apply_pre_process_call(rec, zone):
    agentChannel = rec["agentChannel"]
    content = rec["content"][zone[0] : zone[1]]
    rec["content"] = pre_process_call(agentChannel, content, return_type="dict")
    content_df = pre_process_call(agentChannel, content, return_type="df")

    rec["content_both"] = merge_turn(content_df, orient="both")
    rec["content_agent"] = merge_turn(content_df, orient="agent")

    rec["entities_both"] = map_entity(content_df, orient="both")
    rec["entities_agent"] = map_entity(content_df, orient="agent")

    return rec


def get_label(label_callresult, label_contain):
    if label_contain == "no":
        return "no"
    elif label_contain == "yes":
        return label_callresult
    elif label_contain == "partially":
        return label_callresult + "_partially"
    else:
        return "undefined"


if __name__ == "__main__":
    print("make coffee")

    calls_dict = {
        "m1": {
            "data": "./calls/data_label_cta/m1_raw.json",
            "labels": "./report/Batch-đã-verify-587-calls_đã-sửa-yes-cho-tc17__v11.csv",
            "out_dir": "./bots-v8/",
        },
        "m2": {
            "data": "./calls/data_label_cta/m2_raw.json",
            "labels": "./report/Batch-300-call-đã-gán-nhãn_M2B_v3.csv",
            "out_dir": "./bots-v8/",
        },
        "m3": {
            "data": "./calls/data_label_cta/m3_raw.json",
            "labels": "./report/Batch 300 call đã gán nhãn_M3B.csv",
            "out_dir": "./bots-v8/",
        },
    }

    zone = [-9, None]

    domain = "m1"

    calls = pd.read_json(calls_dict[domain]["data"])
    calls = calls.drop(columns=["metadata"])
    calls = calls.progress_apply(
        lambda call: apply_pre_process_call(call, zone), axis=1
    )
    # print(calls["content_both"])

    labels = pd.read_csv(calls_dict[domain]["labels"])[
        ["file_name", "criterion_name", "audit_result"]
    ]
    labels["criterion_name"] = labels["criterion_name"].str.lower()
    labels["audit_result"] = labels["audit_result"].str.lower()

    labels_callresult = labels[labels["criterion_name"] == "call result"].rename(
        columns={"audit_result": "label_callresult"}
    )
    labels_contain = labels[
        labels["criterion_name"] == "contain all information"
    ].rename(columns={"audit_result": "label_contain"})

    labels = labels_callresult.merge(labels_contain, on="file_name")[
        ["file_name", "label_callresult", "label_contain"]
    ]

    default_label = ["nopay", "undefined", "paid", "willpay"]
    labels["label_callresult"] = labels["label_callresult"].apply(
        lambda label: label if label in default_label else "undefined"
    )

    labels["label"] = labels.apply(
        lambda rec: get_label(rec["label_callresult"], rec["label_contain"]), axis=1
    )

    df = calls.merge(labels, right_on="file_name", left_on="name")

    df = df[
        [
            "content",
            "content_both",
            "content_agent",
            "label",
            "entities_both",
            "entities_agent",
        ]
    ]

    data_agent = (
        df[["content_agent", "label", "entities_agent"]]
        .rename(columns={"content_agent": "sample"})
        .rename(columns={"entities_agent": "entities"})
    )

    data_both = (
        df[["content_both", "label", "entities_both"]]
        .rename(columns={"content_both": "sample"})
        .rename(columns={"entities_both": "entities"})
    )

    bot_name = "cta" + domain + "both"
    with open(
        calls_dict[domain]["out_dir"] + bot_name + ".json", "w", encoding="utf8"
    ) as fo:
        json.dump(gen_data_train(data_both, bot_name), fo, ensure_ascii=False)

        bot_name = "cta" + domain + "agent"

    with open(
        calls_dict[domain]["out_dir"] + bot_name + ".json", "w", encoding="utf8"
    ) as fo:
        json.dump(gen_data_train(data_agent, bot_name), fo, ensure_ascii=False)
