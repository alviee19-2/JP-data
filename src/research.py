import json
import os
import sys
import plotly.express as px
import plotly.io as pio

from ISIN import get_isin_data
from clear import delete_research_db

# 定義原始資料和研究資料的路徑
FUND_info_path = "../raw_data/Fund_info"
Daily_NAV_path = "../raw_data/Daily_NAV"

pio.renderers.default = "browser"

fund_info = {}
country_check = []
sector_check = []
holdings_check = []
aum_list = []

def invert_dict(dictionary: dict):
    """
    反轉字典的鍵和值。
    """
    return {v: k for k, v in dictionary.items()}


def read_data():
    """
    讀取 raw_data/Fund_info 資料夾中的所有基金基礎資訊 JSON 檔案。
    """
    print(f"[research.py] 開始讀取基金基礎資訊...")
    counter = 0
    for filename in os.listdir(FUND_info_path):
        
        isin = filename.split("_")[0]
        
        if filename.endswith(".json"):
            path = os.path.join(FUND_info_path, filename)
            
            with open(path, "r", encoding="utf-8") as f:
                try:
                    data = json.load(f)
                    if data is None:
                        print(f"[research.py] 警告: {filename} 檔案內容為空。")
            
                    fund_info[isin] = data
                except Exception as e:
                    print(f"[research.py] 讀取 {filename} 失敗: {e}")

    print(f"[research.py] 讀入了 {len(fund_info)} 個 FUND 的基礎資訊。")

def meta(isin, date):
    """
    獲取基金的資產管理規模 (AUM) 和費用資訊。
    """
    AUM = fund_info[isin]["fundData"]["aum"]["value"]
    management_fee = fund_info[isin]["fundData"]["shareClass"]["fees"]["managementFee"]
    subscription_fee = fund_info[isin]["fundData"]["shareClass"]["fees"]["subscriptionFees"]
    redemption_fee = fund_info[isin]["fundData"]["shareClass"]["fees"]["redemptionFees"]
    os.makedirs(f"../research_db/{isin}", exist_ok=True)
    print(f"[research.py] 當前分析日期: {date} || 基金實際大小: {AUM}")
    print(f"[research.py] 管理費: {management_fee} || 訂閱費用: {subscription_fee} || 贖回費用: {redemption_fee} ")
    return AUM

def get_date(isin):
    """
    獲取基金的 AUM 日期。
    """
    date = fund_info[isin]["fundData"]["aum"]["date"]
    return date

def all_country(isin, target, date):
    """
    分析基金的國家分佈並生成圓餅圖。
    """
    print(f"[research.py] 分析 {target} 國家分佈...")
    country = {}
    if fund_info[isin]["fundData"]["emeaRegionalBreakdown"] is not None:
        temp = fund_info[isin]["fundData"]["emeaRegionalBreakdown"]["data"]
        for i in range(0, len(temp)):
            if temp[i]["value"] == 100.0:
                break
            country[temp[i]["name"]] = temp[i]["value"]
        country_name = list(country.keys())
        country_value = list(country.values())

        fig = px.pie(
            names = country_name,
            values = country_value,
            title = f"{target}國家圓餅圖_{date}",
            color_discrete_sequence = px.colors.sequential.OrRd[::-1],
        )
        output_file = f"../research_db/{isin}/{target}_country_{date}.jpg"
        os.makedirs(f"../research_db/{isin}", exist_ok=True)
        fig.write_image(output_file, format = 'jpg', scale=3)
        return country
    elif fund_info[isin]["fundData"]["portfolioAnalysisByCountry"] is not None:
        
        country = {item["name"]: item["value"] for item in fund_info[isin]["fundData"]["portfolioAnalysisByCountry"]["data"]}
        if country is None:
            if ("US" in isin) or ("America" in isin):
                country_name = "US"
                country_value = 100.0
            elif "Japan" in isin:
                country_name = "Japan"
                country_value = 100.0
            elif "Korea" in isin:
                country_name = "korea"
                country_value = 100.0
            elif "China" in isin:
                country_name = "China"
                country_value = 100.0
        else:
            country_name = list(country.keys())
            country_value = list(country.values())

        fig = px.pie(
            names = country_name,
            values = country_value,
            title = f"{target}國家圓餅圖_{date}",
            color_discrete_sequence = px.colors.sequential.OrRd[::-1],
        )

        output_file = f"../research_db/{isin}/{target}_country_{date}.jpg"
        os.makedirs(f"../research_db/{isin}", exist_ok=True)
        fig.write_image(output_file, format = 'jpg', scale=3)
        return country
    else:
        country_check.append(isin)
        print(f"[research.py] {isin} 國家分佈資料缺失。")
        return None

def all_sector(isin, target, date):
    """
    分析基金的產業分佈並生成圓餅圖。
    """
    print(f"[research.py] 分析 {target} 產業分佈...")
    if fund_info[isin]["fundData"]["portfolioAnalysisBySector"] is not None:
        sector = {item["name"]: item["value"] for item in fund_info[isin]["fundData"]["portfolioAnalysisBySector"]["data"]}

        sector_name = list(sector.keys())
        sector_value = list(sector.values())

        fig = px.pie(
            names = sector_name,
            values = sector_value,
            title = f"{target}產業圓餅圖_{date}",
            color_discrete_sequence = px.colors.sequential.Blues[::-1],
        )
        output_file = f"../research_db/{isin}/{target}_sector_{date}.jpg"
        os.makedirs(f"../research_db/{isin}", exist_ok=True)
        fig.write_image(output_file, format = 'jpg', scale=3)
        return sector
    elif fund_info[isin]["fundData"]["emeaSectorBreakdown"] is not None:
        sector = {
            item["name"]: item["value"] 
            for item in fund_info[isin]["fundData"]["emeaSectorBreakdown"]["data"]
            if item["value"] != 0 and item["name"] != "Total"
        }

        sector_name = list(sector.keys())
        sector_value = list(sector.values())

        fig = px.pie(
            names = sector_name,
            values = sector_value,
            title = f"{target}產業圓餅圖_{date}",
            color_discrete_sequence = px.colors.sequential.Blues[::-1],
        )

        output_file = f"../research_db/{isin}/{target}_sector_{date}.jpg"
        os.makedirs(f"../research_db/{isin}", exist_ok=True)
        fig.write_image(output_file, format = 'jpg', scale = 3)
        return sector
    else:
        sector_check.append(isin)
        print(f"[research.py] {isin} 產業分佈資料缺失。")
        return None
    
def all_holdings(isin, target, date):
    """
    分析基金的持股分佈並生成圓餅圖。
    """
    print(f"[research.py] 分析 {target} 持股分佈...")
    if fund_info[isin]["fundData"]["fundHoldings"] is not None:
        holdings = fund_info[isin]["fundData"]["fundHoldings"]["tabularDataMap"].values()
        holding_clean = {}
        if holdings is None:
            print("[research.py] 沒有相關持股資料。")
        else:
            for temp in holdings:
                try:
                    percentage_in_fund = temp["cellList"][3]['displayValue']
                    company = temp["cellList"][0]['displayValue']
                    holding_clean[company] = percentage_in_fund
                    company_sector = temp["cellList"][1]['displayValue']
                    company_country = temp["cellList"][2]['displayValue']
                except(KeyError, IndexError) as e:
                    print(f"[research.py] 跳過 {isin} 的 holdings, Index 過長或鍵值錯誤: {e}")
                    break
        
        company_name = list(holding_clean.keys())
        company_name.append("others")
        company_percentage = [
            float(temp.rstrip('%'))
            for temp in holding_clean.values()                      
        ]
        
        company_percentage.append(100 - sum(company_percentage))

        fig = px.pie(
            names = company_name,
            values = company_percentage,
            title = f"{target}持股圓餅圖_{date}",
            color_discrete_sequence = px.colors.sequential.OrRd[::-1],
        )

        output_file = f"../research_db/{isin}/{target}_holding_{date}.jpg"
        os.makedirs(f"../research_db/{isin}", exist_ok=True)
        fig.write_image(output_file, format = 'jpg', scale=3)
        return holding_clean
    elif fund_info[isin]["fundData"]["emeaFundHoldings"] is not None:
        holdings = {}
        total = 100
        temp = 0
        test = fund_info[isin]["fundData"]["emeaFundHoldings"]["data"]
        for i in range(0, 10):
            temp += test[i]["marketValuePercent"]
            holdings[test[i]["securityDescription"]] = test[i]["marketValuePercent"]
        
        others = round(total - temp, 1)
        holdings["others"] = others

        holdings_name = list(holdings.keys())
        holdings_percent = list(holdings.values())

        fig = px.pie(
            names = holdings_name,
            values = holdings_percent,
            title = f"{target}持股圓餅圖_{date}",
            color_discrete_sequence = px.colors.sequential.OrRd[::-1],   
        )

        output_file = f"../research_db/{isin}/{target}_holding_{date}.jpg"
        os.makedirs(f"../research_db/{isin}", exist_ok=True)
        fig.write_image(output_file, format = 'jpg', scale=3)
        return holdings
    else:
        holdings_check.append(isin)
        print(f"[research.py] {isin}: 持股資料缺失。")
        return None

def write_all_to_research(isin, target, country, sector, holdings, aum):
    """
    將基金的研究分析結果寫入 JSON 檔案。
    """
    output_data = {
        "isin": isin,
        "name": target,
        "aum": aum,
        "holdings": holdings,
        "sector": sector,
        "country": country 
    }
    
    output_path = os.path.join("../research_db", isin, "info.json") # 使用 ISIN 作為資料夾名稱
    print(f"[research.py] 寫入研究結果到: {output_path}")
    with open(output_path, "w", encoding= "utf-8") as file:
        json.dump(output_data, file, ensure_ascii=False, indent=2)
        print(f"[research.py] 已儲存至 research_db/{isin} 下。") # 打印 ISIN

def run_research():
    """
    執行基金研究分析的主要流程：讀取資料，清理舊研究資料，然後分析並儲存結果。
    """
    print("[research.py] 開始執行 run_research...")
    read_data()
    delete_research_db()
    
    # 在函式內部獲取 ISIN 和 FUND_NAME
    global ISIN, FUND_NAME, input_FUND_NAME
    ISIN, FUND_NAME = get_isin_data()
    input_FUND_NAME = invert_dict(FUND_NAME)

    counter = 0
    for isin in ISIN:
        target = FUND_NAME[isin]
        # print(target)
        print(f"[research.py] 分析基金: {isin} | {target}")
        # 檢查 fund_info 中是否有該 ISIN 的資料
        if target not in fund_info:
            print(f"[research.py] 警告: 找不到 {isin} 的基金基礎資訊，跳過分析。")
            continue

        date = get_date(target)
        aum = meta(target, date)
        counter += 1
        country = all_country(target, target, date)
        sector = all_sector(target, target, date)
        holding = all_holdings(target, target, date)
        write_all_to_research(target, target, country, sector, holding, aum)
        print(f"[research.py] 完成分析 {counter} | {target}")
    
    print("[research.py] 研究分析執行完畢。")
    print("[research.py] 國家分佈資料缺失檢查: ", country_check)
    print("[research.py] 產業分佈資料缺失檢查: ", sector_check)
    print("[research.py] 持股資料缺失檢查: ", holdings_check)

if __name__ == "__main__":
    # read_data()
    # run_research()
    print(country_check)
    print(len(country_check))
    # print(fund_info.keys())
    # print(fund_info.keys())
    