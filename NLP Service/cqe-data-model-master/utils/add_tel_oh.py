import json
import copy

CUS_BOT = "tel_customer"
CUS_INTENT = "telesale_customer_reject"
OH_BOT = "tel_agent_oh"
OH_INTENT = "telesale_oh_general"
OH_SALE_ENTITY = "telesale_confirm_sale_oh"
# OH_ENTITIES = []
LIST_CRITERIA_OH = [
    "greet",
    "introduce_product",
    "propose_loan_total_amount",
    "propose_loan_period",
    "propose_loan_amount_per_payment",
    "propose_loan_payment_insurance",
    "card_cashback",
    "card_interest_zero_interest",
    "card_promotion",
    "propose_loan_payment_detail_source",
    "propose_loan_payment_detail_interest",
]  # should not contain entity and intent found in CUS_BOT and OH_BOT

with open("project_mapping_telesale.json", "r") as fi:
    project_mapping = json.load(fi)

mapping = project_mapping["project_info"]
print("List of criteria: ", LIST_CRITERIA_OH)
# print("List OH entities: ", OH_ENTITIES)


def declare(bot: str, intent: list, entity: list) -> dict:
    return {
        bot: {
            "entities": {each: "required" for each in entity},
            "intents": {each: "required" for each in intent},
        }
    }


def make_step(channel: str, intent: str, entity: list) -> dict:
    return {"channel": channel, "entities": entity, "intent": intent}


def make_decision(channel: str, crit: str, mapping: dict) -> list:
    decision = []
    for _, val in mapping[crit][channel].items():
        if bool(val["entities"]):
            decision.extend(
                [
                    {"steps": [make_step(channel, None, [ntt])], "title": "yes"}
                    for ntt in val["entities"].keys()
                ]
            )
        if bool(val["intents"]):
            decision.extend(
                [
                    {"steps": [make_step(channel, intent, [])], "title": "yes"}
                    for intent in val["intents"].keys()
                ]
            )

    return decision


result = dict()
for crit in LIST_CRITERIA_OH:
    if crit not in mapping:
        continue
    ohcrit = "oh_" + crit

    ###OH
    result[ohcrit] = copy.deepcopy(mapping[crit])

    # add decision if type == utter
    if mapping[crit]["type"] == "utter":
        decision = []
        decision.extend(make_decision("agent", crit, mapping))
        decision.extend(make_decision("customer", crit, mapping))

        result[ohcrit]["type"] = "dialogue"
        result[ohcrit]["decision"] = decision

    # edit declaration
    result[ohcrit]["agent"].update(declare(OH_BOT, [OH_INTENT], []))
    result[ohcrit]["customer"].update(declare(CUS_BOT, [CUS_INTENT], []))

    newSteps = []
    # edit decision, add "rejected"
    for steps in result[ohcrit]["decision"]:
        newStep = copy.deepcopy(steps)
        newStep["steps"][0]["getFirst"] = True  # add getFirst=true for first step
        newStep["steps"].append(make_step("customer", CUS_INTENT, []))

        temp = []
        for step in newStep["steps"][1:]:
            step["next_side"] = True  # add next_side=true for 1->end step
            temp.append(step)
        newStep["steps"][1:] = temp
        newStep["title"] = "rejected"
        newSteps.append(newStep)

    # edit decision, add "OH1"
    for steps in result[ohcrit]["decision"]:
        newStep = copy.deepcopy(steps)
        newStep["steps"][0]["getFirst"] = True  # add getFirst=true for first step
        newStep["steps"].append(make_step("agent", OH_INTENT, []))

        temp = []
        for step in newStep["steps"][1:]:
            step["next_side"] = True  # add next_side=true for 1->end step
            temp.append(step)
        newStep["steps"][1:] = temp
        newStep["title"] = "OH1"
        newSteps.append(newStep)

    # edit decision, add "rejected2"
    for steps in result[ohcrit]["decision"]:
        newStep = copy.deepcopy(steps)
        newStep["steps"][0]["getFirst"] = True  # add getFirst=true for first step
        newStep["steps"].append(make_step("agent", OH_INTENT, []))
        newStep["steps"].append(make_step("customer", CUS_INTENT, []))

        temp = []
        for step in newStep["steps"][1:]:
            step["next_side"] = True  # add next_side=true for 1->end step
            temp.append(step)
        newStep["steps"][1:] = temp
        newStep["title"] = "rejected2"
        newSteps.append(newStep)

    # edit decision, add "OH2"
    for steps in result[ohcrit]["decision"]:
        newStep = copy.deepcopy(steps)
        newStep["steps"][0]["getFirst"] = True  # add getFirst=true for first step
        newStep["steps"].append(make_step("agent", OH_INTENT, []))
        newStep["steps"].append(make_step("agent", OH_INTENT, []))

        temp = []
        for step in newStep["steps"][1:]:
            step["next_side"] = True  # add next_side=true for 1->end step
            temp.append(step)
        newStep["steps"][1:] = temp
        newStep["title"] = "OH2"
        newSteps.append(newStep)

    result[ohcrit]["decision"] = newSteps

    result[ohcrit]["description"] = "[OH] " + result[ohcrit]["description"]
    result[ohcrit]["zone"] = [None, None]

for crit in LIST_CRITERIA_OH:
    if crit not in mapping:
        continue
    salecrit = "confirm_sale_" + crit

    ###OH
    result[salecrit] = copy.deepcopy(mapping[crit])

    # add decision if type == utter
    if mapping[crit]["type"] == "utter":
        decision = []
        decision.extend(make_decision("agent", crit, mapping))
        decision.extend(make_decision("customer", crit, mapping))

        result[salecrit]["type"] = "dialogue"
        result[salecrit]["decision"] = decision

    # edit declaration
    result[salecrit]["agent"].update(declare(OH_BOT, [OH_INTENT], [OH_SALE_ENTITY]))

    newSteps = []

    # edit decision, add "confirm_sale"
    for steps in result[salecrit]["decision"]:
        newStep = copy.deepcopy(steps)
        newStep["steps"][0]["getFirst"] = True  # add getFirst=true for first step
        newStep["steps"].append(make_step("agent", OH_INTENT, []))
        newStep["steps"].append(make_step("agent", None, [OH_SALE_ENTITY]))

        temp = []
        for step in newStep["steps"][1:]:
            step["next_side"] = True  # add next_side=true for 1->end step
            temp.append(step)
        newStep["steps"][1:] = temp
        newStep["title"] = "confirm_sale"
        newSteps.append(newStep)

    # edit decision, add "confirm_sale" 2nd time
    for steps in result[salecrit]["decision"]:
        newStep = copy.deepcopy(steps)
        newStep["steps"][0]["getFirst"] = True  # add getFirst=true for first step
        newStep["steps"].append(make_step("agent", OH_INTENT, []))
        newStep["steps"].append(make_step("agent", OH_INTENT, []))
        newStep["steps"].append(make_step("agent", None, [OH_SALE_ENTITY]))

        temp = []
        for step in newStep["steps"][1:]:
            step["next_side"] = True  # add next_side=true for 1->end step
            temp.append(step)
        newStep["steps"][1:] = temp
        newStep["title"] = "confirm_sale"
        newSteps.append(newStep)

    result[salecrit]["decision"] = newSteps

    result[salecrit]["description"] = (
        "[Confirm Sale] " + result[salecrit]["description"]
    )
    result[salecrit]["zone"] = [None, None]


print("List of OH & rejected criteria: ", list(result.keys()))
project_mapping["project_info"] = result
project_mapping["project_id"] = project_mapping["project_id"] + "_oh"
with open("project_mapping_telesale_oh.json", "w") as fo:
    json.dump(project_mapping, fo)
