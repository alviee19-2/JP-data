from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd


REMOVED_ISINS = {"LU2521021324", "LU0318934451", "HK0000055662"}


def get_isin_data(funds_csv_path: str | Path | None = None) -> tuple[list[str], dict[str, str]]:
    """Return fund ISIN list and mapping from ISIN to fund name."""
    csv_path = Path(funds_csv_path) if funds_csv_path else Path(__file__).with_name("funds.csv")
    df = pd.read_csv(csv_path)

    isins = [isin for isin in df["ISIN"].tolist() if isin not in REMOVED_ISINS]
    fund_name_by_isin = {
        isin: fund_name
        for isin, fund_name in zip(df["ISIN"], df["Fund Name"])
        if isin not in REMOVED_ISINS
    }

    return isins, fund_name_by_isin


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Inspect ISIN data from funds.csv.")
    parser.add_argument("--funds-csv", default=None, help="Custom funds.csv path.")
    parser.add_argument("--show-sample", type=int, default=5, help="How many sample rows to print.")
    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    isins, fund_name_by_isin = get_isin_data(args.funds_csv)
    sample_count = max(0, args.show_sample)

    print(f"Total funds: {len(isins)}")
    for isin in isins[:sample_count]:
        print(f"{isin} -> {fund_name_by_isin[isin]}")


if __name__ == "__main__":
    main()
