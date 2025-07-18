import os
import json
import time
import requests
import pandas as pd

from datetime import datetime

from ISIN import CUSIPS

# 你要抓的所有 fund cusip list


BASE_URL = "https://am.jpmorgan.com/FundsMarketingHandler/historicalData"
RAW_FOLDER = "raw_data"

def fetch_fund_json(cusip, retries=2, backoff=1):
    params = {
        "cusip": cusip,
        "country": "hk",
        "role": "per",
        "userLoggedIn": "false",
        "language": "en",
        "version": "8.12_1751450551",
    }
    for attempt in range(retries + 1):
        try:
            resp = requests.get(BASE_URL, params=params, timeout=10)
            resp.raise_for_status()
            return resp.json()
        except (requests.RequestException, ValueError) as e:
            if attempt < retries:
                time.sleep(backoff * (2 ** attempt))
            else:
                print(f"[Error] 抓取 {cusip} 失敗：{e}")
                return None

def save_raw_json(cusip, data):
    # 建立資料夾（若不存在）
    os.makedirs(RAW_FOLDER, exist_ok=True)
    # 用 cusip+日期命名，避免覆蓋
    date_str = datetime.utcnow().strftime("%Y%m%d")
    filename = f"{cusip}_{date_str}.json"
    path = os.path.join(RAW_FOLDER, filename)
    # 寫入檔案
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"Saved: {path}")



def main():
    for cusip in CUSIPS:
        data = fetch_fund_json(cusip)
        if data is not None:
            save_raw_json(cusip, data)

if __name__ == "__main__":
    main()
