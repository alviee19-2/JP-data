
import quantstats as qs
import pandas as pd
import webbrowser
import os
import json

from ISIN import ISIN, FUND_NAME

final_sector_Series = {}

researchdb_info = {}
all_sector = ()
isin_sector_data = {}

def tprint(data):
    print(data, "|", type(data))

def load_researchdb_info():
    """
    遍歷 RESEARCH_DB_PATH 底下每個子資料夾，讀取 info.json，
    並以資料夾名稱（ISIN）當 key，回傳一個 {ISIN: json_data} 的 dict。
    """
    research_path = "research_db"
    for entry in os.listdir(research_path):
        folder_path = os.path.join(research_path, entry)
        if os.path.isdir(folder_path):
            info_path = os.path.join(folder_path, "info.json")
            if os.path.isfile(info_path):
                with open(info_path, "r", encoding="utf-8") as f:
                    try:
                        data = json.load(f)
                        researchdb_info[entry] = data
                    except json.JSONDecodeError as e:
                        print(f"❗ 無法解析 {info_path}：{e}")

def make0_final_sector_series():
    for temp in all_sector:
        final_sector_Series[temp] = 0.0

sector_set = set()
def get_all_sector_type():
    lst = list(researchdb_info.keys())
    for isin in lst:
        
        data = researchdb_info[isin]
        # print(data["aum"])
        try:
            temp = list(data["sector"].keys())
            for sector in temp:
                sector_set.add(sector)
            # all_name.add()
        except:
            print(f"{isin}這個沒有")

def turn_sector_to_pdSeries():
    for isin in ISIN:
        isin_sector_data[isin] = researchdb_info[isin]["sector"]
    # print(isin_sector_data)


def main():
    load_researchdb_info()
    get_all_sector_type()
    
    for temp in sector_set:
        print(temp)
    make0_final_sector_series()
    turn_sector_to_pdSeries()
    # tprint(final_sector_Series.keys())
if __name__ == "__main__":
    main()