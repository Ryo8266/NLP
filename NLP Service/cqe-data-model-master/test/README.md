
### requirement
`pip install pandas scikit-learn requests tqdm`


### data input
`_ground.csv`: criteria-level label, made by CQE platform team on Superset

`_transcript.json`: dialogs transcript, taken from CQE platform, project screen, inspect request response


### params
```
endpoint=
project_id=
...
```


### example result
```
49 dialogs testing on 
 ['2.mp3', '63.mp3', '64.mp3', '65.mp3', '66.mp3', '67.mp3', '68.mp3', '69.mp3', '70.mp3', '71.mp3', '72.mp3', '1_outb.mp3', '3_outb.mp3', '4_outb.mp3', '5_outb.mp3', '6_outb.mp3', '7_outb.mp3', '8_outb.mp3', '9_outb.mp3', '10_outb.mp3', '11_outb.mp3', '12_outb.mp3', '13_outb.mp3', '14_outb.mp3', '15_outb.mp3', '16_outb.mp3', '17_outb.mp3', '18_outb.mp3', '20_outb.mp3', '21_outb.mp3', '22_outb.mp3', '23_outb.mp3', '24_outb.mp3', '25_outb.mp3', '26_outb.mp3', '27_outb.mp3', '28_outb.mp3', '29_outb.mp3', '30_outb.mp3', '31_outb.mp3', '33_outb.mp3', '34_outb.mp3', '35_outb.mp3', '36_outb.mp3', '37_outb.mp3', '38_outb.mp3', '39_outb.mp3', '40_outb.mp3', '41_outb.mp3'] 

1 dialogs unlabelled: 
 ['32_outb.mp3'] 

0 dialogs without transcript: 
 [] 

100%|█████████████████████████████████████████████████████████████████████████████████████████| 49/49 [01:37<00:00,  2.00s/it]

 agentIntroduce          acc: 0.694      f1: 0.819
[[ 0 15]
 [ 0 34]]

 askPaymentAmount        acc: 0.918      f1: 0.667
[[41  2]
 [ 2  4]]

 askPaymentDatetime      acc: 0.673      f1: 0.111
[[32 13]
 [ 3  1]]

 askPaymentMethod        acc: 0.694      f1: 0.717
[[15  6]
 [ 9 19]]

 companyName             acc: 1.0        f1: 1.0
[[36  0]
 [ 0 13]]

 confirmCustomer         acc: 0.959      f1: 0.5
[[46  0]
 [ 2  1]]

 goodbye                 acc: 0.98       f1: 0.963
[[35  0]
 [ 1 13]]

 greet                   acc: 0.898      f1: 0.906
[[20  5]
 [ 0 24]]

 thank                   acc: 1.0        f1: 1.0
[[40  0]
 [ 0  9]]

 informAmount            acc: 0.735      f1: 0.435
[[31 12]
 [ 1  5]]

 informOverdue           acc: 0.939      f1: 0.824
[[39  2]
 [ 1  7]]

 requestPayment          acc: 0.755      f1: 0.625
[[27  9]
 [ 3 10]]

 askPaymentReceipt       acc: 0.939      f1: 0.968
[[ 0  3]
 [ 0 46]]

 informSummary           acc: 0.245      f1: 0.393
[[ 0 37]
 [ 0 12]]

 object_handling         acc: 0.918      f1: 0.95
[[ 7  0]
 [ 4 38]]

```

error log `log/errors_.csv`


### limitations
- informSummary: currently using informSummary for (Contain all information), where informSummaryOH, willpay_summary, nopay_summary should be used. I don't know how to deal with this yet
- 'N/A' case
- oh_motivation: 'N/A' is default to 'no', in reality, 'N/A' is the main label, so the current F1 score is unreliable
- OH: giải pháp, mục tiêu chưa đánh giá
- some 'reason' in map_reason_criteria are not completed
- ...


