import os
import json
import time
import requests
import pandas as pd
import subprocess
from datetime import datetime
from datetime import date
import csv

from .ISIN import get_isin_data
from .clear import delete_raw_json


NAV_URL = "https://am.jpmorgan.com/FundsMarketingHandler/historicalData"
FUND_INFO_URL = "https://am.jpmorgan.com/FundsMarketingHandler/product-data"

def fetch_check(fund_name: str, isin: str, nav_status: str, fund_status: str):
    """
    將基金抓取狀態記錄到 fetch_check.csv。
    """
    PATH = "src/fetch_check.csv"
    with open(PATH, "a", newline = "", encoding = "utf-8-sig") as file:
        writer = csv.writer(file);
        writer.writerow([fund_name, isin, nav_status, fund_status])

def fetch_NAV_json(cusip, retries=1, backoff=1):
    """
    從 J.P. Morgan 網站抓取基金的歷史淨值資料。
    """
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
                print(f"[fetch.py] 抓取 NAV: {cusip}, country = {country}, version = {version}")
                resp = requests.get(NAV_URL, params=params, timeout=10)
                resp.raise_for_status()
                data =  resp.json()
                return data
                
            except requests.exceptions.RequestException as e:
                print(f"[fetch.py] 失敗 NAV (RequestException): {cusip}, version = {version}, country = {country}, 錯誤: {e}")
                continue
            except ValueError as e:
                print(f"[fetch.py] 失敗 NAV (ValueError - JSON 解碼): {cusip}, version = {version}, country = {country}, 錯誤: {e}")
                continue
            
            
def fetch_FUND_INFO_json(cusip, retries=2, backoff=1):
    """
    從 J.P. Morgan 網站抓取基金的基本資訊。
    """
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
                print(f"[fetch.py] 抓取 FUND INFO: {cusip}, country = {country}, version = {version}")
                resp = requests.get(FUND_INFO_URL, params=params, timeout=10)
                resp.raise_for_status()
                data =  resp.json()
                if data.get("fundData") is None or data.get("fundData", {}).get("stringValueWrapper") is None:
                    print(f"[fetch.py] 跳過 FUND_INFO: {cusip} 回傳 error 或 fundData 為空")
                    continue
                return data
                
            except requests.exceptions.RequestException as e:
                print(f"[fetch.py] 失敗 FUND_INFO (RequestException): {cusip}, version = {version}, country = {country}, 錯誤: {e}")
                continue
            except ValueError as e:
                print(f"[fetch.py] 失敗 FUND_INFO (ValueError - JSON 解碼): {cusip}, version = {version}, country = {country}, 錯誤: {e}")
                continue

def save_raw_json(cusip, data, type: str):
    # 取得當前檔案所在資料夾
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # 回到專案根目錄
    dir_path = os.path.join(base_dir, "raw_data", type)

    os.makedirs(dir_path, exist_ok=True)

    date_str = str(date.today())
    filename = f"{cusip}_{date_str}.json"
    full_path = os.path.join(dir_path, filename)

    with open(full_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    
    print(f"[fetch.py] Saved: {full_path}")

def run_fetch():
    """
    執行基金資料抓取的主要流程：清理舊資料，獲取 ISIN，然後抓取 NAV 和基金資訊。
    """
    print("[fetch.py] 開始執行 run_fetch...")
    delete_raw_json()
    
    ISIN, FUND_NAME = get_isin_data()
    print("[fetch.py] ISIN 資料獲取完畢。")
    
    NAV_counter = 0
    for isin in ISIN:
        NAV = fetch_NAV_json(isin)
        FUND_INFO = fetch_FUND_INFO_json(isin)
        name = FUND_NAME[isin]

        if NAV is not None:    
            save_raw_json(name, NAV, type = "Daily_NAV")
            nav_status = "success"
        else:
            NAV_counter += 1
            nav_status = "fail"
        
        if FUND_INFO is not None:
            save_raw_json(name, FUND_INFO, type = "FUND_info")
            fund_status = "success"
        else:
            fund_status = "fail"
        fetch_check(name, isin, nav_status, fund_status)
    print(f"[fetch.py] NAV抓取失敗數量: {NAV_counter}")
    print("[fetch.py] run_fetch 執行完畢。")

if __name__ == "__main__":
    run_fetch()
