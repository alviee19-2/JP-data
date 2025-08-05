import quantstats as qs
import pandas as pd
import webbrowser
import os
import json

from NAV_clean import nav_dict, read_nav_json
from ISIN import ISIN, FUND_NAME

#每一個fund的return pd.Series, 用isin: str拿取
returns_series = {}

def turn_to_pdSeries(start_date):

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

def tprint(data):
    print(data, "|", type(data))

def backtest(start_date, returns_series: dict, payload:dict):
    path = "SAA"
    idx = pd.date_range(start=start_date, end="2025-08-01", freq="D")
    SAA_returns = pd.Series(0.0, index=idx,name="SAA_report")
    for isin, name in FUND_NAME.items():
        SAA_returns = SAA_returns.add(returns_series[isin] * payload[name], fill_value=0.0)
    
    filename = os.path.join(path, f"report on {SAA_returns.name}.html") 
    qs.reports.html(
        SAA_returns,
        output=filename,
        title = f"report on {SAA_returns.name}"
    )

    webbrowser.open(filename)

def main():
    start_date = "2010-01-01"


    payload = {
        "JPM Asia Equity Dividend Fund": 0,
        "JPM Asia Equity High Income Fund": 0.1,
        "JPM Asia Growth Fund": 0,
        "JPM Asia Pacific Equity Fund": 0,
        "JPM China Fund": 0,
        "JPM China A-Share Opportunities Fund": 0,
        "JPM Japan Equity Fund": 0.2,
        "JPM Japan Strategic Value Fund": 0,
        "JPM Emerging Markets Equity Fund": 0,
        "JPM Total Emerging Markets Income Fund": 0,
        "JPM Europe Dynamic Fund": 0,
        "JPM America Equity Fund": 0.2,
        "JPM US Growth Fund": 0,
        "JPM US Value Fund": 0,
        "JPM US Smaller Companies Fund": 0,
        "JPM Global Core Equity": 0,
        "JPM Global Dividend Fund": 0,
        "JPM Global Select Equity Fund": 0,
        "JPM Global Research Enhanced Index Equity Fund": 0,
        "JPM Asian Total Return Bond Fund": 0,
        "JPM Global Aggregate Bond Fund": 0.,
        "JPM US Aggregate Bond Fund": 0,
        "JPM Emerging Markets Debt Fund": 0,
        "JPM Global Corporate Bond Fund": 0.15,
        "JPM Global Government Bond Fund": 0,
        "JPM Global High Yield Bond Fund": 0,
        "JPM Managed Reserves Fund": 0,
        "JPM APAC Managed Reserves Fund": 0,
        "JPM Asia Pacific Income Fund": 0,
        "JPM Global Income Fund": 0,
        "JPMorgan Funds - Multi-Manager Alternatives Fund": 0,
        "JPM ASEAN Equity Fund": 0,
        "JPM Brazil Equity Fund": 0,
        "JPM India Fund": 0,
        "JPM Indonesia Fund": 0,
        "JPM Korea Equity Fund": 0,
        "JPM Latin America Equity Fund": 0,
        "JPM Taiwan Fund": 0,
        "JPM Greater China Fund": 0,
        "JPM Europe Equity Fund": 0,
        "JPM Euroland Equity Fund": 0,
        "JPM Climate Change Solutions Fund": 0,
        "JPM Global Healthcare Fund": 0,
        "JPM Global Natural Resources Fund": 0,
        "JPM Thematics - Genetic Therapies": 0,
        "JPM Sustainable Infrastructure Fund": 0,
        "JPM Pacific Technology Fund": 0.2,
        "JPM Europe Dynamic Tech Fund": 0,
        "JPM US Technology Fund": 0,
        "JPM Global Government Short Duration Bond Fund": 0.15,
        "JPM Global Short Duration Bond Fund": 0,
        "JPM US Short Duration Bond Fund": 0,
        "JPM Income Fund": 0,
        "JPM Global Bond Opportunities Fund": 0,
    }
    
    read_nav_json()
    turn_to_pdSeries(start_date)
    if sum(list(payload.values())) == 1:
        backtest(start_date, returns_series, payload)
    else:
        print("阿你也太貪心囉")

if __name__ == "__main__":
    main()