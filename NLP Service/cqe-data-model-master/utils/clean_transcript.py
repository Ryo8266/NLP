import pandas as pd


def clean_content(content):
    if len(content) == 0:
        return None
    content_df = pd.DataFrame(content)[["channel", "text"]]
    return content_df.to_dict("records")


def clean_meta(metadata):
    metadata = eval(
        metadata.replace("true", "True")
        .replace("false", "False")
        .replace("null", "None")
    )["public"]
    return metadata


if __name__ == "__main__":
    file_name = input("file_path: ")
    data_call = pd.read_json(file_name)[["name", "agentChannel", "content", "metadata"]]

    data_call["content"] = data_call["content"].apply(clean_content)
    data_call["metadata"] = data_call["metadata"].apply(clean_meta)
    data_call.to_json(
        file_name.split(".")[0] + "_clean.json",
        orient="records",
        force_ascii=False,
        indent=2,
    )
