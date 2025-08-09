import pandas as pd
import os

def get_isin_data():
    """
    從 funds.csv 讀取資料，處理後回傳 ISIN 列表和基金名稱字典。

    Returns:
        tuple: 包含 ISIN 列表和 FUND_NAME 字典的元組。
    """
    print("[ISIN.py] 開始獲取 ISIN 資料...")
    # 使用 os.path.join 和 os.path.dirname(__file__) 構建絕對路徑，確保在任何執行環境下都能找到 funds.csv
    funds_csv_path = os.path.join(os.path.dirname(__file__), "funds.csv")
    FUNDS_DataFrames = pd.read_csv(funds_csv_path)
    
    ISIN = FUNDS_DataFrames["ISIN"].tolist()
    remove = ["LU2521021324", "LU0318934451", "HK0000055662"]
    for bad in remove:
        if bad in ISIN:
            ISIN.remove(bad)

    FUND_NAME = FUNDS_DataFrames.set_index("ISIN")["Fund Name"].to_dict()
    for bad in remove:
        if bad in FUND_NAME:
            FUND_NAME.pop(bad)
            
    print("[ISIN.py] ISIN 資料獲取完畢。")
    return ISIN, FUND_NAME
