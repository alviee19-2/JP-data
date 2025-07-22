import os
import json
import time
import requests
import pandas as pd
from datetime import datetime

from ISIN import ISIN, FUND_NAME


NAV_URL = "https://am.jpmorgan.com/FundsMarketingHandler/historicalData"
FUND_INFO_URL = "https://am.jpmorgan.com/FundsMarketingHandler/product-data"
# NAV_original = "https://am.jpmorgan.com/FundsMarketingHandler/historicalData?cusip=HK0000038148&country=hk&role=per&userLoggedIn=false&language=en&version=8.12_1751450551"
# FUND_INFO_original = "https://am.jpmorgan.com/FundsMarketingHandler/product-data?cusip=HK0000038148&country=hk&role=per&language=en&userLoggedIn=false&version=8.12_1751450551"

RAW_FOLDER = "raw_data"

def fetch_NAV_json(cusip, retries=2, backoff=1):
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
            resp = requests.get(NAV_URL, params=params, timeout=10)
            resp.raise_for_status()

            return resp.json()
        except (requests.RequestException, ValueError) as e:
            if attempt < retries:
                time.sleep(backoff * (2 ** attempt))
            else:
                print(f"[Error] 抓取 {cusip} 失敗：{e}")
                return None

def fetch_FUND_INFO_json(cusip, retries=2, backoff=1):
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
            resp = requests.get(FUND_INFO_URL, params=params, timeout=10)
            resp.raise_for_status()
            return resp.json()
        except (requests.RequestException, ValueError) as e:
            if attempt < retries:
                time.sleep(backoff * (2 ** attempt))
            else:
                print(f"[Error] 抓取 {cusip} 失敗：{e}")
                return None

def save_raw_json(cusip, data, type: str):
    
    # 用 cusip+日期命名，避免覆蓋
    date_str = datetime.strftime("%Y%m%d")
    filename = f"{cusip}_{date_str}.json"
    #存到RAW_FOLDER/type
    path = os.path.join(RAW_FOLDER + "/" + type)
    # 寫入檔案
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"Saved: {path}")

def main():
    for cusip in ISIN:
        NAV = fetch_NAV_json(cusip)
        FUND_INFO = fetch_FUND_INFO_json(cusip)
        if NAV is not None:
            save_raw_json(cusip, NAV, type = "Daily_NAV")
        else:
            
            path = os.path.join()
        if FUND_INFO is not None:
            save_raw_json(cusip, FUND_INFO, type = "FUND_info")

if __name__ == "__main__":
    #main()