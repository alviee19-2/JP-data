import os
import json
import time
import requests
from datetime import datetime
import pandas as pd

# 讀取 CSV 檔，會回傳一個 DataFrame
df = pd.read_csv("funds.csv")

# 看前五筆
print(df.head())

ISIN_map = df.set_index("ISIN")["Fund Name"].to_dict()

# 若要把 DataFrame 轉成 dict 或 list：
CUSIPS = df["ISIN"].tolist()
