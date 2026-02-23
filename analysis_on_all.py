from __future__ import annotations

import argparse
from datetime import date
from pathlib import Path

import numpy as np
import pandas as pd

from src.ISIN import get_isin_data


_, FUND_NAME = get_isin_data()


def build_correlation_frame(data: pd.DataFrame, start: str, end: str, grace_days: int = 5) -> pd.DataFrame:
    if not isinstance(data.index, pd.DatetimeIndex):
        data = data.copy()
        data.index = pd.to_datetime(data.index, errors="coerce")
    data = data.sort_index()

    start_ts = pd.to_datetime(start)
    end_ts = pd.to_datetime(end)

    sliced = data.loc[start_ts:end_ts]
    if sliced.empty:
        return pd.DataFrame()

    start_idx = sliced.index.searchsorted(start_ts, side="left")
    if start_idx >= len(sliced.index):
        return pd.DataFrame()

    window_end = min(start_idx + grace_days, len(sliced.index) - 1)
    window = sliced.iloc[start_idx : window_end + 1]
    valid_cols = window.columns[window.notna().any(axis=0)]

    sliced = sliced[valid_cols]
    if sliced.shape[1] < 2:
        return pd.DataFrame()

    return sliced.corr(method="pearson")


def is_bond_or_income(name: str) -> bool:
    lower_name = name.lower()
    return "bond" in lower_name or "income" in lower_name


def sort_correlation_matrix(df: pd.DataFrame, group_bond_income: bool = True) -> pd.DataFrame:
    return sort_correlation_matrix_with_method(
        df=df,
        sort_method="score",
        group_bond_income=group_bond_income,
        cluster_linkage="average",
    )


def sort_correlation_matrix_with_method(
    df: pd.DataFrame,
    sort_method: str = "cluster",
    group_bond_income: bool = False,
    cluster_linkage: str = "average",
) -> pd.DataFrame:
    if df.empty:
        return df

    order: list[str]
    corr = df.fillna(0).copy()

    if sort_method == "alphabetical":
        order = sorted(corr.columns.tolist())
    elif sort_method == "score":
        scores = corr.copy()
        np.fill_diagonal(scores.values, 0)
        order = scores.sum(axis=0).sort_values(ascending=False).index.tolist()
    elif sort_method == "cluster":
        try:
            from scipy.cluster.hierarchy import leaves_list, linkage
            from scipy.spatial.distance import squareform

            np.fill_diagonal(corr.values, 1.0)
            distance = (1 - corr).clip(lower=0)
            np.fill_diagonal(distance.values, 0.0)
            condensed = squareform(distance.values, checks=False)
            linkage_matrix = linkage(condensed, method=cluster_linkage)
            ordered_idx = leaves_list(linkage_matrix)
            order = [corr.index[i] for i in ordered_idx]
        except Exception as error:
            print(f"[analysis_on_all.py] cluster sort failed, fallback to score sort: {error}")
            scores = corr.copy()
            np.fill_diagonal(scores.values, 0)
            order = scores.sum(axis=0).sort_values(ascending=False).index.tolist()
    else:
        raise ValueError(f"Unsupported sort method: {sort_method}")

    if group_bond_income:
        non_bond = [name for name in order if not is_bond_or_income(name)]
        bond = [name for name in order if is_bond_or_income(name)]
        order = non_bond + bond

    return df.loc[order, order]


def plot_heatmap(
    correlation_df: pd.DataFrame,
    output_path: str | Path,
    vmin: float,
    vmax: float,
    dpi: int,
) -> Path:
    import matplotlib.pyplot as plt
    import seaborn as sns

    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)

    if correlation_df.empty:
        raise ValueError("Correlation dataframe is empty, no chart generated.")

    fund_count = correlation_df.shape[0]
    figure_size = max(12, min(24, int(fund_count * 0.45)))
    annotation_font_size = 4 if fund_count >= 30 else 6 if fund_count >= 20 else 8
    label_font_size = 5 if fund_count >= 30 else 7 if fund_count >= 20 else 9

    plt.figure(figsize=(figure_size, figure_size))
    sns.heatmap(
        correlation_df,
        annot=True,
        fmt=".2f",
        cmap="coolwarm",
        cbar=True,
        vmin=vmin,
        vmax=vmax,
        square=True,
        annot_kws={"size": annotation_font_size},
    )

    axis = plt.gca()
    axis.set_xticklabels(axis.get_xticklabels(), rotation=45, ha="right", fontsize=label_font_size)
    axis.set_yticklabels(axis.get_yticklabels(), rotation=0, fontsize=label_font_size)
    # Flip Y axis so the correlation diagonal runs from bottom-left to top-right.
    axis.invert_yaxis()
    axis.set_xlabel("Funds")
    axis.set_ylabel("Funds")
    plt.title("Fund Correlation Heatmap")

    plt.tight_layout()
    plt.savefig(output, dpi=dpi, bbox_inches="tight", transparent=True)
    plt.close()
    return output


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Generate cross-fund correlation heatmap from returns cache.")
    parser.add_argument("--cache-file", default="cache/returns_series_cache.pkl", help="returns_series cache file path.")
    parser.add_argument("--start-date", default="2015-01-01", help="Analysis start date (YYYY-MM-DD).")
    parser.add_argument(
        "--end-date",
        default=date.today().isoformat(),
        help="Analysis end date (YYYY-MM-DD).",
    )
    parser.add_argument("--grace-days", type=int, default=5, help="Grace days window for valid columns.")
    parser.add_argument("--output", default="chart/corr_heatmap.png", help="Output PNG path.")
    parser.add_argument("--vmin", type=float, default=-0.15, help="Heatmap minimum color value.")
    parser.add_argument("--vmax", type=float, default=0.95, help="Heatmap maximum color value.")
    parser.add_argument("--dpi", type=int, default=900, help="Output image DPI.")
    parser.add_argument(
        "--no-group-bond-income",
        action="store_true",
        help="Do not move bond/income funds to the end of sort order.",
    )
    parser.add_argument(
        "--sort-method",
        choices=["cluster", "score", "alphabetical"],
        default="cluster",
        help="Matrix sort method.",
    )
    parser.add_argument(
        "--cluster-linkage",
        choices=["single", "complete", "average", "weighted"],
        default="average",
        help="Linkage method used when --sort-method=cluster.",
    )
    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    cache_path = Path(args.cache_file)
    if not cache_path.exists():
        raise FileNotFoundError(f"Cache file not found: {cache_path}")

    returns_series = pd.read_pickle(cache_path)
    frame = pd.DataFrame(returns_series)
    frame = frame.rename(columns=FUND_NAME)

    correlation = build_correlation_frame(
        frame,
        start=args.start_date,
        end=args.end_date,
        grace_days=args.grace_days,
    )
    correlation = sort_correlation_matrix_with_method(
        correlation,
        sort_method=args.sort_method,
        group_bond_income=not args.no_group_bond_income,
        cluster_linkage=args.cluster_linkage,
    )

    output_path = plot_heatmap(
        correlation,
        output_path=args.output,
        vmin=args.vmin,
        vmax=args.vmax,
        dpi=args.dpi,
    )
    print(f"[analysis_on_all.py] heatmap saved: {output_path}")


if __name__ == "__main__":
    main()
