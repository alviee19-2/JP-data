import quantstats as qs
import pandas as pd
import webbrowser
import os
import json

from NAV_clean import nav_dict, read_nav_json
from src.ISIN import get_isin_data

#每一個fund的return pd.Series, 用isin: str拿取
returns_series = {}
ISIN, FUND_NAME = get_isin_data()

def tprint(data):
    print(data, "|", type(data))

def turn_nav_to_pdSeriesSeries(start_date):

    for isin in ISIN:
        fund_nav_dict = nav_dict[isin]
        daily_nav = [fund_nav_dict[i]["navPrice"] for i in range(0, len(fund_nav_dict))]
        daily_date = [fund_nav_dict[i]["date"] for i in range(0, len(fund_nav_dict))]
        
        fund_nav_series = pd.Series(
            data=daily_nav,
            index= pd.to_datetime(daily_date),
            name= f"{isin}的日報酬"
        )
        fund_returns_series = qs.utils.to_returns(fund_nav_series)
        fund_returns_series = fund_returns_series.loc[fund_returns_series.index >= start_date]
        returns_series[isin] = fund_returns_series

def backtest(start_date, returns_series: dict, payload:dict, name: str):
    out_path =  "SAA"
    idx = pd.date_range(start=start_date, end="2025-08-01", freq="D")
    SAA_returns = pd.Series(0.0, index=idx,name="SAA_report")
    for isin, fund_name in FUND_NAME.items():
        SAA_returns = SAA_returns.add(returns_series[isin] * payload[fund_name], fill_value=0.0)
    filename = os.path.join(out_path, f"report on {name}.html") 
    qs.reports.html(
        SAA_returns,
        output=filename,
        title = f"report on {SAA_returns.name}"
    )
    webbrowser.open(filename)

def main():
    start_date = "2019-01-01"
    enddate = "還未指定"
    name = "報告名字"

    payload = {
        "JPM Asia Equity Dividend Fund": 0,
        "JPM Asia Equity High Income Fund": 0,
        "JPM Asia Growth Fund": 0,
        "JPM Asia Pacific Equity Fund": 0.065,
        "JPM China Fund": 0,
        "JPM China A-Share Opportunities Fund": 0,
        "JPM Japan Equity Fund": 0,
        "JPM Japan Strategic Value Fund": 0.03,
        "JPM Emerging Markets Equity Fund": 0,
        "JPM Total Emerging Markets Income Fund": 0,
        "JPM Europe Dynamic Fund": 0,
        "JPM America Equity Fund": 0.08,
        "JPM US Growth Fund": 0.085,
        "JPM US Value Fund": 0,
        "JPM US Smaller Companies Fund": 0,
        "JPM Global Core Equity": 0.04,
        "JPM Global Dividend Fund": 0.07,
        "JPM Global Select Equity Fund": 0.04,
        "JPM Global Research Enhanced Index Equity Fund": 0,
        "JPM Asian Total Return Bond Fund": 0,
        "JPM Global Aggregate Bond Fund": 0,
        "JPM US Aggregate Bond Fund": 0.04,
        "JPM Emerging Markets Debt Fund": 0,
        "JPM Global Corporate Bond Fund": 0,
        "JPM Global Government Bond Fund": 0,
        "JPM Global High Yield Bond Fund": 0.01,
        "JPM Managed Reserves Fund": 0.135,
        "JPM APAC Managed Reserves Fund": 0,
        "JPM Asia Pacific Income Fund": 0,
        "JPM Global Income Fund": 0,
        "JPMorgan Funds - Multi-Manager Alternatives Fund": 0.09,
        "JPM ASEAN Equity Fund": 0,
        "JPM Brazil Equity Fund": 0,
        "JPM India Fund": 0.05,
        "JPM Indonesia Fund": 0.025,
        "JPM Korea Equity Fund": 0,
        "JPM Latin America Equity Fund": 0,
        "JPM Taiwan Fund": 0,
        "JPM Greater China Fund": 0,
        "JPM Europe Equity Fund": 0.05,
        "JPM Euroland Equity Fund": 0,
        "JPM Climate Change Solutions Fund": 0.04,
        "JPM Global Healthcare Fund": 0.055,
        "JPM Global Natural Resources Fund": 0,
        "JPM Thematics - Genetic Therapies": 0,
        "JPM Sustainable Infrastructure Fund": 0,
        "JPM Pacific Technology Fund": 0,
        "JPM Europe Dynamic Tech Fund": 0,
        "JPM US Technology Fund": 0,
        "JPM Global Government Short Duration Bond Fund": 0,
        "JPM Global Short Duration Bond Fund": 0.095,
        "JPM US Short Duration Bond Fund": 0,
        "JPM Income Fund": 0,
        "JPM Global Bond Opportunities Fund": 0,
    }
    
    cache_dir = "cache"
    os.makedirs(cache_dir, exist_ok=True) # 確保 cache 目錄存在
    cache_file = os.path.join(cache_dir, "returns_series_cache.pkl")

    if os.path.exists(cache_file):
        print("從快取載入 NAV 資料...")
        with open(cache_file, 'rb') as f:
            global returns_series
            returns_series = pd.read_pickle(f)
        print("NAV 資料載入完畢。")
    else:
        print("快取不存在，開始讀取和處理 NAV 資料...")
        read_nav_json()
        turn_nav_to_pdSeriesSeries(start_date)
        with open(cache_file, 'wb') as f:
            pd.to_pickle(returns_series, f)
        print("NAV 資料處理完畢並已儲存到快取。")

    if sum(list(payload.values())) <= 1:
        backtest(start_date, returns_series, payload, name)
    else:
        print("阿你也太貪心囉")
    print(sum(list(payload.values())))
if __name__ == "__main__":
    main()
