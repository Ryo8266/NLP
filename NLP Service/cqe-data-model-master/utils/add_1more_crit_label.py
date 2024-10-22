import pandas as pd

GROUND_TRUTH_FILENAME = "test/hc_collection/ground_new.csv"
OUT_FILE_NAME = "ehe.csv"
CRIT_NAME = "Permit2End"
LIST_YES_CALL = ["1673319918984_3459_750342454676_494868454", "1673491145262_3718_750908780518_500135585","1673236532477_3468_750936910969_499594872", "1673405894624_3449_750908780518_499955608","1673150763097_3651_750914145741_494524723", "1673252461935_3455_750937270689_499675139","1673227379079_3474_750902429396_494633190","1673667673703_3718_750985076167_500534180","1673492418730_3468_750936910969_500144547","1673598454903_3475_750908780518_495541636", "1673139747020_3650_750345324396_499352732","1673426001623_3611_750979042248_500061729","1673399773789_3463_750353460038_499911763", "1673265735028_02873002327_3817_494809679", "1673233312932_3472_750936910969_494677203", "1673411663066_3477_750937270689_495096664", "1673483790166_3717_750978451356_495193191", "1673399333939_3454_750825978168_495012833","1676510540274_3476_750366517972_505148163","1673233346757_3611_750819478760_494676788","1673584890870_3463_750976599256_495478019","1673407579937_3479_750915758404_495068173","1673317566602_3718_750368878553_494851328","1673226638588_3472_750835235277_499524959","1673579243414_3455_750988949414_500336812","1673251822248_3477_750981586304_494774958","1673594126611_3333_750946331978_495518429","1673234066971_3451_750947076655_494681830","1673232391299_3454_750903369221_494669788","1673252149992_3451_750333659811_494776920","1673412525788_3477_850949384918_495102374","1673230676611_3477_750353578550_494657537","1673252396030_3477_750867178456_499674952","1673148479606_3477_750961143550_499407136", "1673313743314_3481_850934032694_494824612","1673229919421_3477_8502513611228_494652252",]

ground = pd.read_csv(GROUND_TRUTH_FILENAME)

names = list(ground.file_name.unique())

# for each in names: print(each) if type(each)==float else None # debug blank file name

grouped = ground.groupby(ground.file_name)
result = pd.DataFrame()

for name in names:
    ehe = grouped.get_group(name)
    if name in LIST_YES_CALL:
        ehe.loc[len(ehe)] = [name, CRIT_NAME, "Yes", None, "Collection"]
    else:
        ehe.loc[len(ehe)] = [name, CRIT_NAME, "No", None, "Collection"]

    result = pd.concat([result, ehe])


result.to_csv(OUT_FILE_NAME, index=False)