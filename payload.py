# payload.py
import random

Equity = [
    "JPM APAC Managed Reserves Fund",
    "JPM ASEAN Equity Fund",
    # "JPM Active Bond ETF",
    # "JPM Active Growth ETF",
    "JPM America Equity Fund",
    "JPM Asia Equity Dividend Fund",
    "JPM Asia Equity High Income Fund",
    "JPM Asia Growth Fund",
    "JPM Asia Pacific Income Fund",
    # "JPM Asian Total Return Bond Fund",
    # "JPM China A-Share Opportunities Fund",
    "JPM China Fund",
    # "JPM Climate Change Solutions Active UCITS ETF",
    # "JPM Core Plus Bond ETF",
    # "JPM Equity Focus ETF",
    # "JPM Equity Premium ETF",
    "JPM Europe Dynamic Fund",
    # "JPM Global Aggregate Bond Active ETF",
    # "JPM Global Aggregate Bond Fund",
    # "JPM Global Bond Opportunities Fund",
    # "JPM Global Corporate Bond Fund",
    # "JPM Global Dividend Fund",
    # "JPM Global Equity High Income Fund",
    # "JPM Global Equity Premium Income ETF",
    "JPM Global Healthcare Fund",
    # "JPM Global High Yield Bond Fund",
    "JPM Global Income Fund",
    "JPM Global Natural Resources Fund",
    # "JPM Global Research Enhanced Index Equity ETF",
    # "JPM Global Research Enhanced Index Equity Fund",
    # "JPM Global Select Equity ETF",
    "JPM Global Select Equity Fund",
    "JPM Global Sustainable Equity Fund",
    "JPM Greater China Fund",
    # "JPM Healthcare Leaders ETF",
    # "JPM Income ETF",
    # "JPM Income Fund",
    "JPM India Fund",
    "JPM Japan Equity Fund",
    # "JPM Japan Research Enhanced Index Equity ETF",
    # "JPM Nasdaq Equity Premium Income ETF",
    "JPM Pacific Technology Fund",
    "JPM US Aggregate Bond Fund",
    "JPM US Growth Fund",
    # "JPM US Multi-Asset High Income Fund",
    # "JPM US Research Enhanced Index Equity ETF",
    # "JPM US Select Equity Plus",
    # "JPM US Tech Leaders ETF",
    "JPM US Technology Fund",
    # "JPM USD High Yield Bond Active ETF",
    # "JPM USD Ultra-Short Income ETF",
    # "JPMorgan Inflation Managed Bond ETF",
    # "JPMorgan Realty Income ETF"
]
Equity_weight = {
    #add1
    "JPM US Technology Fund": 0.12,
    "JPM Global Select Equity Fund": 0.125,
    "JPM US Growth Fund": 0.125,
    
    "JPM Europe Dynamic Fund": 0.065,
    "JPM ASEAN Equity Fund": 0.07,
    "JPM Japan Equity Fund": 0.06,
    "JPM Global Healthcare Fund": 0.06,
    "JPM Pacific Technology Fund": 0.05,
    "JPM Greater China Fund": 0.045,
    "JPM Global Sustainable Equity Fund": 0.03,
    "JPM India Fund": 0.03,
    # "JPM Climate Change Solutions Active UCITS ETF": 0.015,
}
FixedIncome = [
    "JPM Global Aggregate Bond Fund",
    "JPM Global Bond Opportunities Fund",
    "JPM Global Corporate Bond Fund",
    "JPM Global Dividend Fund",
    "JPM Global High Yield Bond Fund",
]
fixedweight = {
    "JPM US Aggregate Bond Fund": 0.03,
    "JPM Global Aggregate Bond Fund": 0.035,
    "JPM Global Corporate Bond Fund": 0.065,
    "JPM Income Fund": 0.07
}


def generate_payload(equity_share=0.6, fi_share=0.4):
    """隨機生成權重，Equity 與 FixedIncome 各自加總固定比例"""
    
    # Equity 權重
    eq_random = [random.uniform(0, 2) for _ in range(len(Equity))]
    eq_total = sum(eq_random)
    eq_weights = [num / eq_total * equity_share for num in eq_random]  # 總和 = equity_share

    # FixedIncome 權重
    fi_random = [random.uniform(0, 2) for _ in range(len(FixedIncome))]
    fi_total = sum(fi_random)
    fi_weights = [num / fi_total * fi_share for num in fi_random]  # 總和 = fi_share

    # 合併成一個 dict
    all_funds = Equity + FixedIncome
    all_weights = eq_weights + fi_weights
    # print(f"eq_weight: {sum(eq_weights)}, fi_weight: {sum(fi_weights)}")
    return dict(zip(all_funds, all_weights))

def zip_payload():
    return Equity_weight | fixedweight
def try_payload():
    # original_dict = Equity_weight | fixedweight
    original_dict = {
        "JPM US Technology Fund": 0.11229727208766423,
        "JPM US Growth Fund": 0.09385826112641164,
        "JPM Global Healthcare Fund": 0.07159845681947234,
        "JPM ASEAN Equity Fund": 0.06123294360348865,
        "JPM Japan Equity Fund": 0.07354539665458906,
        "JPM Europe Dynamic Fund": 0.07858772774944572,
        "JPM Global Sustainable Equity Fund": 0.03061788616434533,
        "JPM America Equity Fund": 0.010717966232293727,
        "JPM Pacific Technology Fund": 0.04041176466699547,
        "JPM India Fund": 0.02699555935846363,
        "JPM Greater China Fund": 0.05435103468940409,
        "JPM Global Select Equity Fund": 0.12661658512012696,
        "JPM Climate Change Solutions Active UCITS ETF": 0.014849621850765191,
        "JPM US Aggregate Bond Fund": 0.04106348358024598,
        "JPM Global Aggregate Bond Fund": 0.04243099826301135,
        "JPM Income Fund": 0.034590149361026515,
        "JPM Global Corporate Bond Fund": 0.045633589644503925
    }
    perturbed_dict = {
        name: value * (1 + random.uniform(-0.2, 0.2))
        for name, value in original_dict.items()
    }
    return perturbed_dict

def split_dict(temp:dict):
    items = list(temp.items())
    first_part = dict(items[:-4])
    last_part = dict(items[-4:])
    return first_part, last_part

# 預設先生成一組
if __name__ == "__main__":
    # payload = generate_payload()
    print(sum(Equity_weight.values()))
    temp = zip_payload()
    print(temp)
