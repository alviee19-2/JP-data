import os
import json
import time
import requests
import pandas as pd
from datetime import datetime
from datetime import date
import csv

from ISIN import ISIN, FUND_NAME


NAV_URL = "https://am.jpmorgan.com/FundsMarketingHandler/historicalData"
FUND_INFO_URL = "https://am.jpmorgan.com/FundsMarketingHandler/product-data"

# NAV_original = "https://am.jpmorgan.com/FundsMarketingHandler/historicalData?cusip=HK0000038148&country=hk&role=per&userLoggedIn=false&language=en&version=8.12_1751450551"
# FUND_INFO_original = "https://am.jpmorgan.com/FundsMarketingHandler/product-data?cusip=HK0000038148&country=hk&role=per&language=en&userLoggedIn=false&version=8.12_1751450551"

def fetch_check(fund_name: str, isin: str, nav_status: str, fund_status: str):
    PATH = "fetch_check.csv"
    with open(PATH, "a", newline = "", encoding = "utf-8-sig") as file:
        writer = csv.writer(file);
        writer.writerow([fund_name, isin, nav_status, fund_status])

def fetch_NAV_json(cusip, retries=1, backoff=1):
    versions = ["8.12_1751450551", "8.13_1752481876"]
    countries = ["hk", "sg", "dk", "fi", "lu"]

    for country in countries:
        for version in versions:
            params = {
                "cusip": cusip,
                "country": country,
                "role": "per",
                "userLoggedIn": "false",
                "language": "en",
                "version": version,
            }
            try:
                print(f"[抓取]{cusip}, country = {country}, version = {version}")
                resp = requests.get(NAV_URL, params=params, timeout=10)
                resp.raise_for_status()
                return resp.json()
            except(requests.RequestException, ValueError) as e:
                print(f"[失敗]{cusip}, version = {version}, country = {country}")
                continue

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
    date_str = str(date.today())
    filename = f"{cusip}_{date_str}.json"
    #存到RAW_FOLDER/type
    dir_path = os.path.join("raw_data", type)
    full_path = os.path.join(dir_path, filename)
    # 寫入檔案
    with open(full_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"Saved: {full_path}")

def main():
    NAV_counter = 0
    for isin in ISIN:
        NAV = fetch_NAV_json(isin)
        FUND_INFO = fetch_FUND_INFO_json(isin)
        name = FUND_NAME[isin]

        if NAV is not None:    
            save_raw_json(isin, NAV, type = "Daily_NAV")
            nav_status = "success"
        else:
            NAV_counter += 1
            nav_status = "fail"
        
        if FUND_INFO is not None:
            save_raw_json(isin, FUND_INFO, type = "FUND_info")
            fund_status = "success"
        else:
            fund_status = "fail"
        fetch_check(name, isin, nav_status, fund_status)
    print(f"NAV抓取失敗數量{NAV_counter}")

if __name__ == "__main__":
    main()