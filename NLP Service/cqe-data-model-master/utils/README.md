## add_tel_oh.py
Auto-create **Home Credit Collection** *OH* and *confirm_sale* criteria by adding OH steps to available criteria in *LIST_CRITERIA_OH*

## beatifyUnicodeInBot.py
**Beautify** newly-exported bot from bot.fpt.ai (have Vietnamese characters encoded in unicode) to view it in pretty mode (ex: I need to rename intent/entity)

## botJsontoEngineV4Input.py
**Format** newly-exported bot from bot.fpt.ai to engineV4 format (to POST to NLP CQE's DME)

## json2excel_project_mapping.py
**Export** project mapping from .json to .xlsx for prettier view

## raw_query2transcript.py
**Beautify** raw transcripts by removing unnecessary fields
Prompt field is file_name+dir_name, ex: ../test/gofingo_telesale/transcripts; the path lead to a .json file of transcripts copy from Enhance Platform

## filter_file
**Filter** call from a list of json files, call name taken from a ground_truth file

## nlu_predict_to_csv
**Support** improving CQE bots by getting prediction from bot.fpt.ai & prediction from a100 dev env