
import json
import os
import sys
import plotly.express as px
import plotly.io as pio

from ISIN import ISIN, FUND_NAME
from clear import delete_research_db

FUND_info_path = "raw_data/Fund_info"
Daily_NAV_path = "raw_data/Daily_NAV"

pio.renderers.default = "browser"

fund_info = {}
def invert_dict(dictionary: dict):
    return {v: k for k, v in dictionary.items()}

input_FUND_NAME = invert_dict(FUND_NAME)


def read_data():
    print(f"讀入了{len(fund_info)}個FUND的基礎資訊")
    counter = 0
    for filename in os.listdir(FUND_info_path):
        isin = filename.split("_")[0]
        # print(isin)
        # if counter > 1:
        #     break
        if filename.endswith(".json"):
            path = os.path.join(FUND_info_path, filename)
            
            # counter += 1
            with open(path, "r", encoding="utf-8") as f:
                try:
                    data = json.load(f)
                    if data is None:
                        print("fucked")
            
                    fund_info[isin] = data
                except Exception as e:
                    print("uh")
            # print(fund_info[isin])

    print(f"讀入了{len(fund_info)}個FUND的基礎資訊")
    # print(fund_info["HK0000055597"])

def meta(isin, date):
    #基金實際大小
    AUM = fund_info[isin]["fundData"]["aum"]["value"]
    #費用
    management_fee = fund_info[isin]["fundData"]["shareClass"]["fees"]["managementFee"]
    subscription_fee = fund_info[isin]["fundData"]["shareClass"]["fees"]["subscriptionFees"]
    redemption_fee = fund_info[isin]["fundData"]["shareClass"]["fees"]["redemptionFees"]

    print(f"當前分析日期: {date} ||  基金實際大小: {AUM}")
    print(f"管理費: {management_fee} || 訂閱費用: {subscription_fee} || 贖回費用: {redemption_fee} ")

def get_date(isin):
    date = fund_info[isin]["fundData"]["aum"]["date"]
    return date

def all_country(isin, target, date):
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
        output_file = f"research_db/{isin}/{target}_country_{date}.jpg"
        os.makedirs(f"research_db/{isin}", exist_ok=True)
        fig.write_image(output_file, format = 'jpg', scale=3)
        return country
    elif fund_info[isin]["fundData"]["portfolioAnalysisByCountry"] is not None:
        country = {item["name"]: item["value"] for item in fund_info[isin]["fundData"]["portfolioAnalysisByCountry"]["data"]}
        country_name = list(country.keys())
        country_value = list(country.values())

        fig = px.pie(
            #一定要的parameters
            names = country_name,
            values = country_value,
            title = f"{target}國家圓餅圖_{date}",
            #特別可操控的param
            # hole = 0.25,
            color_discrete_sequence = px.colors.sequential.OrRd[::-1],
            # # hover_data=['value'], 
            # labels={'value':'sector'}
            # hover_name=['']
        )

        output_file = f"research_db/{isin}/{target}_country_{date}.jpg"
        os.makedirs(f"research_db/{isin}", exist_ok=True)
        fig.write_image(output_file, format = 'jpg', scale=3)
        return country
    else:
        print("100%都是那個國家")
        return "fuck my bad"

def all_sector(isin, target, date):
    if fund_info[isin]["fundData"]["portfolioAnalysisBySector"] is not None:
        sector = {item["name"]: item["value"] for item in fund_info[isin]["fundData"]["portfolioAnalysisBySector"]["data"]}

        sector_name = list(sector.keys())
        sector_value = list(sector.values())

        fig = px.pie(
            #一定要的parameters
            names = sector_name,
            values = sector_value,
            title = f"{target}產業圓餅圖_{date}",

            color_discrete_sequence = px.colors.sequential.Blues[::-1],
        )
        output_file = f"research_db/{isin}/{target}_sector_{date}.jpg"
        os.makedirs(f"research_db/{isin}", exist_ok=True)
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
            #一定要的parameters
            names = sector_name,
            values = sector_value,
            title = f"{target}產業圓餅圖_{date}",

            color_discrete_sequence = px.colors.sequential.Blues[::-1],
        )

        output_file = f"research_db/{isin}/{target}_sector_{date}.jpg"
        os.makedirs(f"research_db/{isin}", exist_ok=True)
        fig.write_image(output_file, format = 'jpg', scale = 3)
        return sector
    else:
        print(f"{isin} sector failed")
    
def all_holdings(isin, target, date):
    if fund_info[isin]["fundData"]["fundHoldings"] is not None:
        holdings = fund_info[isin]["fundData"]["fundHoldings"]["tabularDataMap"].values()
        holding_clean = {}
        if holdings is None:
            print("沒有相關資料")
        else:
            for temp in holdings:
                try:
                    percentage_in_fund = temp["cellList"][3]['displayValue']
                    company = temp["cellList"][0]['displayValue']
                    holding_clean[company] = percentage_in_fund
                    company_sector = temp["cellList"][1]['displayValue']
                    company_country = temp["cellList"][2]['displayValue']
                except(KeyError, IndexError) as e:
                    print(f"跳過{isin}的holdings, Index過長")
                    break
        holding_clean
        company_name = list(holding_clean.keys())
        company_name.append("others")
        company_percentage = [
            float(temp.rstrip('%'))
            for temp in holding_clean.values()                      
        ]
        
        company_percentage.append(100 - sum(company_percentage))
        # for temp in company_percentage:
        #     print(temp)

        # print(sum(company_percentage))

        fig = px.pie(
            names = company_name,
            values = company_percentage,
            title = f"{target}持股圓餅圖_{date}",
            color_discrete_sequence = px.colors.sequential.OrRd[::-1],
        )

        output_file = f"research_db/{isin}/{target}_holding_{date}.jpg"
        os.makedirs(f"research_db/{isin}", exist_ok=True)
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

        output_file = f"research_db/{isin}/{target}_holding_{date}.jpg"
        os.makedirs(f"research_db/{isin}", exist_ok=True)
        fig.write_image(output_file, format = 'jpg', scale=3)
        return holdings
    else:
        print(f"{isin}: holdings failed")


def main():
    read_data()
    delete_research_db()
    # target = "JPM Asia Equity Dividend Fund"
    # isin = input_FUND_NAME[target]
    #isin = "LU0210528500"
    counter = 0
    for isin in ISIN:
        target = FUND_NAME[isin]
        print(isin, '|', target)
        date = get_date(isin)
        meta(isin, date)
        counter += 1
        country = all_country(isin, target, date)
        sector = all_sector(isin, target, date)
        holding = all_holdings(isin, target, date)
        print(counter, "|", isin)
if __name__ == "__main__":
    main()
    # code = "LU1303367103"
    # target = FUND_NAME[code]
    # print(code, '|', target)
    # date = get_date(code)
    # meta(code, date)
    # print(holding = all_holdings(code, target, date))
    

#portfolio characteristic analysis
#好像只要是bond才會有這個東西
