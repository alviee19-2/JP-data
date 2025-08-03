import pandas as pd


def read_csv_encode(path = "funds.csv"):
    return
# 讀取 CSV 檔，會回傳一個 DataFrame
#Category ,Sub-assets Class ,Fund Name ,ISIN


FUNDS_DataFrames = pd.read_csv("funds.csv")
# 若要把 DataFrame 轉成 dict 或 list：
ISIN = FUNDS_DataFrames["ISIN"].tolist()
remove = ["LU2521021324", "LU0318934451", "HK0000055662"]
for bad in remove:
    if bad in ISIN:
        ISIN.remove(bad)

FUND_NAME = FUNDS_DataFrames.set_index("ISIN")["Fund Name"].to_dict()
# print(FUNDS_DataFrames.head())
# print(FUND_NAME)
# # print(ISIN, "\n", type(ISIN))
# # print(FUNDS_DataFrames[""])