from __future__ import annotations

import argparse
import json
from pathlib import Path

import pandas as pd

from src.ISIN import get_isin_data


ISIN, FUND_NAME = get_isin_data()
nav_dict: dict[str, list[dict[str, float | str]]] = {}
FUND_NAME_TO_ISIN = {name: isin for isin, name in FUND_NAME.items()}


def _slug(text: str) -> str:
    return "".join(ch if ch.isalnum() else "_" for ch in text).strip("_").lower()


def read_nav_json(path: str | Path = "raw_data/Daily_NAV", clear: bool = True) -> None:
    """
    Load NAV JSON into global nav_dict using fund name -> ISIN mapping.
    """
    if clear:
        nav_dict.clear()

    nav_dir = Path(path)
    if not nav_dir.exists():
        print(f"[NAV_clean.py] nav directory not found: {nav_dir}")
        return

    for file_path in sorted(nav_dir.glob("*.json")):
        fund_name = file_path.stem.rsplit("_", 1)[0]
        isin = FUND_NAME_TO_ISIN.get(fund_name)

        if not isin:
            print(f"[NAV_clean.py] skip file without ISIN mapping: {file_path.name}")
            continue

        try:
            with file_path.open("r", encoding="utf-8") as file:
                payload = json.load(file)
        except Exception as exc:
            print(f"[NAV_clean.py] failed to read {file_path}: {exc}")
            continue

        records: list[dict[str, float | str]] = []

        for item in payload.get("historicalNAVList") or []:
            date_value = item.get("date")
            nav_price = item.get("navPrice")
            if date_value and nav_price is not None:
                records.append({"date": date_value, "navPrice": float(nav_price)})

        if not records:
            for item in payload.get("historicalETFNAVMarketPriceList") or []:
                date_value = item.get("date")
                nav_price = item.get("marketValueNavPrice")
                if date_value and nav_price is not None:
                    records.append({"date": date_value, "navPrice": float(nav_price)})

        if records:
            nav_dict[isin] = sorted(records, key=lambda x: str(x["date"]))

    print(f"[NAV_clean.py] loaded NAV series count: {len(nav_dict)}")


def make_wide_df(nav_data: dict[str, list[dict[str, float | str]]], exclude_isins: set[str] | None = None) -> pd.DataFrame:
    exclude_isins = exclude_isins or set()
    frame = pd.DataFrame(
        {
            isin: {record["date"]: record["navPrice"] for record in records}
            for isin, records in nav_data.items()
            if isin not in exclude_isins
        }
    )

    if frame.empty:
        return frame

    frame.index = pd.to_datetime(frame.index)
    frame.sort_index(inplace=True)
    return frame


def filter_by_date(df: pd.DataFrame, start: str | None = None, end: str | None = None) -> pd.DataFrame:
    if start:
        df = df[df.index >= pd.to_datetime(start)]
    if end:
        df = df[df.index <= pd.to_datetime(end)]
    return df


def split_by_initial(df: pd.DataFrame, threshold: float = 50.0) -> dict[str, list[str]]:
    if df.empty:
        return {"below": [], "above": []}

    first_row = df.ffill().iloc[0]
    return {
        "below": first_row[first_row < threshold].index.tolist(),
        "above": first_row[first_row >= threshold].index.tolist(),
    }


def draw_overlay(df: pd.DataFrame, title: str, filename: str, output_dir: str | Path = "chart") -> Path:
    import plotly.express as px

    output_folder = Path(output_dir)
    output_folder.mkdir(parents=True, exist_ok=True)

    if df.empty:
        output_path = output_folder / f"{filename}.html"
        output_path.write_text("<html><body><h1>No data</h1></body></html>", encoding="utf-8")
        return output_path

    df_long = df.reset_index().melt(id_vars="index", var_name="ISIN", value_name="NAV")
    df_long["Display Name"] = df_long["ISIN"].map(FUND_NAME).fillna(df_long["ISIN"])
    df_long["index"] = pd.to_datetime(df_long["index"]).dt.strftime("%Y-%m-%d")

    fig = px.line(
        df_long,
        x="index",
        y="NAV",
        color="Display Name",
        title=title,
        labels={"index": "Date", "NAV": "NAV Price"},
    )
    fig.update_layout(
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="left",
            x=0,
            font=dict(size=8),
        ),
        legend_itemclick="toggleothers",
    )

    output_path = output_folder / f"{filename}.html"
    fig.write_html(str(output_path), auto_open=False)
    print(f"[NAV_clean.py] chart saved: {output_path}")
    return output_path


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Build NAV overlay charts from raw NAV JSON.")
    parser.add_argument("--nav-dir", default="raw_data/Daily_NAV", help="Path to NAV JSON directory.")
    parser.add_argument("--start-date", default="2010-01-01", help="Filter start date (YYYY-MM-DD).")
    parser.add_argument("--end-date", default=None, help="Filter end date (YYYY-MM-DD).")
    parser.add_argument("--threshold", type=float, default=50.0, help="Initial NAV threshold for grouping.")
    parser.add_argument("--output-dir", default="chart", help="Output directory for HTML charts.")
    parser.add_argument(
        "--exclude-isins",
        default="LU0513027705",
        help="Comma-separated ISINs to exclude.",
    )
    parser.add_argument(
        "--skip-group-charts",
        action="store_true",
        help="Only generate the all-funds overlay chart.",
    )
    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    exclude_isins = {item.strip() for item in args.exclude_isins.split(",") if item.strip()}

    read_nav_json(path=args.nav_dir, clear=True)
    df_all = make_wide_df(nav_dict, exclude_isins=exclude_isins)
    df = filter_by_date(df_all, start=args.start_date, end=args.end_date)

    groups = split_by_initial(df, threshold=args.threshold)

    draw_overlay(
        df,
        title="All Funds NAV",
        filename=_slug("all_funds_nav"),
        output_dir=args.output_dir,
    )

    if not args.skip_group_charts:
        if groups["below"]:
            draw_overlay(
                df[groups["below"]],
                title=f"Funds NAV Overlay (initial < {args.threshold})",
                filename=_slug("funds_nav_overlay_initial_below_threshold"),
                output_dir=args.output_dir,
            )

        if groups["above"]:
            draw_overlay(
                df[groups["above"]],
                title=f"Funds NAV Overlay (initial >= {args.threshold})",
                filename=_slug("funds_nav_overlay_initial_above_threshold"),
                output_dir=args.output_dir,
            )


if __name__ == "__main__":
    main()
