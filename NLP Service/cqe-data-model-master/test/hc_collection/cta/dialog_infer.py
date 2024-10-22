from typing import Any, Dict, List

import pandas as pd
import requests
from dask.threaded import get


def call_criteria_server(
    predict_df: pd.DataFrame,
    input_field: str,
    agentChannel: str,
    meta_check: Dict[str, Any],
    criteria_name: str,
    metaDialog: dict = {},
) -> List[Dict[str, Any]]:
    """call_criteria_server -
    Call criteria server to check whether the input data satisfies the criteria,
    and return the result in the form of a list of dictionaries.

    Args:
        predict_df (pd.DataFrame): _description_
        input_field (str): _description_
        agentChannel (str): _description_
        meta_check (Dict[str, Any]): _description_
        criteria_name (str): _description_

    Returns:
        List[Dict[str, Any]]: _description_
    """
    result = requests.post(
        url=f"https://nlp-api.fpt.ai/criteria-sdk/process_criteria",
        json={
            "dialog_tracker": {
                "agentChannel": agentChannel,
                "dialog_nlu": predict_df.to_dict("records"),
                "original_field": input_field,
            },
            "checker": meta_check,
            "criteria_name": criteria_name,
        },
    )

    if result.status_code != 200:
        return {"error": result.text}

    result_json = result.json()
    if len(metaDialog) != 0 and len(result_json.get("slots", {})) > 0:
        result = requests.post(
            url=f"https://nlp-api.fpt.ai/criteria-sdk/postprocess",
            json={
                "metadata": metaDialog,
                "criteria_result": result_json,
                "criteria_name": criteria_name,
            },
        )

    if result.status_code == 200:
        return result.json()
    else:
        return result_json


def process_criteria(
    input_field,
    predict_df,
    agentChannel,
    meta_check,
    criteria_name,
    metaDialog={},
):
    dialog_tracker = predict_df

    result_criterias = call_criteria_server(
        dialog_tracker, input_field, agentChannel, meta_check, criteria_name, metaDialog
    )

    return result_criterias


def criteria_result(criterias, sequence_of_criterias):
    return {
        criteria: result_criteria
        for criteria, result_criteria in zip(criterias, sequence_of_criterias)
    }


def predict_criterias(
    criterias: list,
    original_field: list,
    predict_df: pd.DataFrame,
    agentChannel: int,
    project_info: dict,
    metaDialog: dict = {},
) -> dict:
    input_field = original_field
    result_criterias = {}
    dsk = {
        "criteria-"
        + criteria: (
            process_criteria,
            input_field,
            predict_df,
            agentChannel,
            project_info[criteria],
            criteria,
            metaDialog,
        )
        for criteria in criterias
    }
    dsk["result"] = (
        criteria_result,
        criterias,
        ["criteria-" + criteria for criteria in criterias],
    )
    result_criterias = get(dsk, "result", num_workers=4)

    return result_criterias
