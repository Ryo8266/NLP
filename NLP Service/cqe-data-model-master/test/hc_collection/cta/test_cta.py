from tqdm import tqdm
import pandas as pd


tqdm.pandas()


if __name__ == "__main__":
    result_all = pd.read_csv("test/hc_collection/cta/cta_result.csv")
    print(result_all)

    match_map = {
        "willpaySummary": "willpay",
        "nopaySummary": "nopay",
        "paidSummary": "paid",
    }

    print("=" * 30)
    print(" " * 11, "Report", " " * 11)
    print("=" * 30)

    for criteria in match_map:
        result_tmp_df = result_all[
            ["file_name", "P call result", "P Contain all information", criteria]
        ]
        result_tmp_df.to_csv(f"test/hc_collection/cta/{criteria}.csv", index=False)

        print("criteria:", criteria)
        pos_sample = result_tmp_df[
            result_tmp_df["P call result"] == match_map[criteria]
        ]
        ner_sample = result_tmp_df[
            result_tmp_df["P call result"] != match_map[criteria]
        ]

        print(
            "positive:",
            len(pos_sample[pos_sample[criteria] == "yes"]),
            ":",
            len(pos_sample),
            "=",
            round(len(pos_sample[pos_sample[criteria] == "yes"]) / len(pos_sample), 2),
        )
        print(
            "false-positive:",
            len(pos_sample[pos_sample[criteria] == "no"]),
        )
        pos_sample[pos_sample[criteria] == "no"].to_csv(
            f"test/hc_collection/cta/{criteria}-false-positive.csv", index=False
        )

        print(
            "false-nergative:",
            len(ner_sample[ner_sample[criteria] == "yes"]),
            ":",
            len(ner_sample),
            "=",
            round(len(ner_sample[ner_sample[criteria] == "yes"]) / len(ner_sample), 2),
        )
        print(
            ner_sample[ner_sample[criteria] == "yes"]["P call result"]
            .value_counts()
            .to_dict()
        )
