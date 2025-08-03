import os
import glob
import json
import pandas as pd
import plotly.express as px

from ISIN import ISIN, FUND_NAME

# 全域存放 NAV 原始資料
nav_dict = {}

def read_nav_json(path: str = "raw_data/Daily_NAV") -> None:
    """
    讀所有 JSON，存到 nav_dict 中 raw list
    nav_dict[isin] = [
        {"date": "YYYY-MM-DD", "navPrice": float},
        ...
    ]
    """
    # nav_dict.clear()
    for filepath in glob.glob(os.path.join(path, "*.json")):
        isin = os.path.basename(filepath).split("_")[0]
        with open(filepath, encoding="utf-8") as f:
            data = json.load(f)
        nav_dict[isin] = [
            {"date": item["date"], "navPrice": item["navPrice"]}
            for item in data.get("historicalNAVList", [])
            if item.get("date") and item.get("navPrice") is not None
        ]
    print(f"已讀取 {len(nav_dict)} 支基金 NAV 資料")


def make_wide_df(nav_data: dict) -> pd.DataFrame:
    """
    把 nav_dict 轉成 wide DataFrame:
      index = 日期 (datetime), columns = 各 ISIN
    """
    df = pd.DataFrame({
        isin: {rec["date"]: rec["navPrice"] for rec in recs}
        for isin, recs in nav_data.items()
        if isin != "LU0513027705"
    })
    df.index = pd.to_datetime(df.index)
    df.sort_index(inplace=True)
    return df


def filter_by_date(df: pd.DataFrame, start: str = None, end: str = None) -> pd.DataFrame:
    """依日期區間過濾 wide DataFrame"""
    if start:
        df = df[df.index >= start]
    if end:
        df = df[df.index <= end]
    return df


def split_by_initial(df: pd.DataFrame, threshold: float = 50.0) -> dict:
    """
    依照每支基金「第一筆有效 NAV」是否 < threshold 分組，
    回傳 {"below": [...], "above": [...]}
    """
    first_row = df.ffill().iloc[0]
    return {
        "below": first_row[first_row < threshold].index.tolist(),
        "above": first_row[first_row >= threshold].index.tolist(),
    }


def draw_overlay(df: pd.DataFrame, title: str, filename: str) -> None:
    
    df_reset = df.reset_index().rename(columns={"index": "date"})
    df_reset["date"] = pd.to_datetime(df_reset["date"])
    """一張圖 overlay 所有欄位"""
    df_long = df.reset_index().melt(
        id_vars="index", var_name="ISIN", value_name="NAV"
    )
    df_long["Display Name"] = df_long["ISIN"].map(FUND_NAME).fillna(df_long["ISIN"])
    df_long["index"] = pd.to_datetime(df_long["index"]).dt.strftime("%Y-%m-%d")
    fig = px.line(
        df_long,
        x="index", y="NAV", color="Display Name",
        title=title,
        labels={"index": "Date", "NAV": "NAV Price"}
    )
    fig.update_layout(
        legend=dict(
            orientation="h",
            yanchor="bottom", y=1.02,
            xanchor="left", x=0,
            font=dict(size=8)
        ),
        legend_itemclick="toggleothers"
    )
    fig.show()
    # os.makedirs("chart", exist_ok=True)
    # out_path = os.path.join("chart", f"{filename}.jpg")
    # fig.write_image(out_path, format="jpg", scale=2)

def main():
    # 1. 讀原始 JSON
    read_nav_json()

    # 2. 轉 wide table & 過濾日期
    df_all = make_wide_df(nav_dict)
    df = filter_by_date(df_all, start="2010-01-01")

    # 3. 計算初始 NAV 分組
    groups = split_by_initial(df, threshold=50.0)

    # 4. 繪圖：一張全部 Overlay
    draw_overlay(df, title="All Funds NAV (2010+)", filename="All Funds NAV (2010+)")

    # 5. 繪圖：初始 NAV <50 的 Overlay
    if groups["below"]:
        df_below = df[groups["below"]]
        draw_overlay(df_below, title="Funds NAV Overlay (initial < 50)", filename="Funds NAV Overlay (initial smaller 50)")

    # 6. 繪圖：初始 NAV ≥50 的 Overlay
    if groups["above"]:
        df_above = df[groups["above"]]
        draw_overlay(df_above, title="Funds NAV Overlay (initial ≥ 50)", filename="Funds NAV Overlay (initial bigger 50)")
    

if __name__ == "__main__":
    main()
    # read_nav_json()
    # isin = ISIN[50]
    # print(FUND_NAME[isin])
    # print((nav_dict[isin][0]))