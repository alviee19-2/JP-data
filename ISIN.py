import os
import json
import time
import requests
from datetime import datetime
import pandas as pd

# 讀取 CSV 檔，會回傳一個 DataFrame
#Category ,Sub-assets Class ,Fund Name ,ISIN
FUNDS_DataFrames = pd.read_csv("funds.csv")

# 若要把 DataFrame 轉成 dict 或 list：
ISIN = FUNDS_DataFrames["ISIN"].tolist()
FUND_NAME = FUNDS_DataFrames.set_index("ISIN")["Fund Name"].to_dict()

# print(FUNDS_DataFrames.head())
# print(FUND_NAME)
# # print(ISIN, "\n", type(ISIN))
# # print(FUNDS_DataFrames[""])