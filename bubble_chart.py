from __future__ import annotations

import argparse
import json
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns

from payload import generate_payload, try_payload, zip_payload
from src.ISIN import get_isin_data


def _load_payload_file(payload_file: str | Path) -> dict[str, float]:
    with Path(payload_file).open("r", encoding="utf-8") as file:
        payload = json.load(file)

    if not isinstance(payload, dict):
        raise ValueError("Payload file must be a JSON object: {fund_name: weight}")

    normalized: dict[str, float] = {}
    for key, value in payload.items():
        normalized[str(key)] = float(value)
    return normalized


def build_payload(
    mode: str,
    equity_share: float,
    fi_share: float,
    payload_file: str | None = None,
) -> dict[str, float]:
    if payload_file:
        return _load_payload_file(payload_file)

    if mode == "fixed":
        return {k: float(v) for k, v in zip_payload().items()}
    if mode == "random":
        return {k: float(v) for k, v in generate_payload(equity_share=equity_share, fi_share=fi_share).items()}
    if mode == "perturbed":
        return {k: float(v) for k, v in try_payload().items()}

    raise ValueError(f"Unsupported payload mode: {mode}")


def build_bubble_data(
    returns_series: dict[str, pd.Series],
    payload: dict[str, float],
    fund_name_by_isin: dict[str, str],
) -> list[dict[str, float | str]]:
    import quantstats as qs

    name_to_isin = {name: isin for isin, name in fund_name_by_isin.items()}

    bubble_data: list[dict[str, float | str]] = []

    for fund_name, weight in payload.items():
        if weight <= 0:
            continue

        isin = name_to_isin.get(fund_name)
        if not isin:
            print(f"[bubble_chart.py] missing ISIN for fund: {fund_name}")
            continue

        fund_returns = returns_series.get(isin)
        if fund_returns is None or fund_returns.empty:
            print(f"[bubble_chart.py] missing returns for fund: {fund_name} ({isin})")
            continue

        daily_avg_return = float(fund_returns.mean())
        annual_return = (1 + daily_avg_return) ** 252 - 1
        annual_volatility = float(qs.stats.volatility(fund_returns))

        bubble_data.append(
            {
                "Fund": fund_name,
                "Returns": annual_return,
                "Volatility": annual_volatility,
                "Weight": float(weight),
            }
        )

    return bubble_data


def plot_bubble_chart(
    bubble_data: list[dict[str, float | str]],
    output_path: str | Path,
    annotate: bool,
    show_plot: bool,
    title_size: int,
    axis_label_size: int,
    tick_label_size: int,
    point_label_size: int,
) -> Path:
    if not bubble_data:
        raise ValueError("No bubble data available to plot.")

    df = pd.DataFrame(bubble_data)

    plt.figure(figsize=(12, 8))
    sns.scatterplot(
        data=df,
        x="Volatility",
        y="Returns",
        hue="Fund",
        size="Weight",
        sizes=(200, 1000),
        alpha=0.7,
        edgecolor="w",
        linewidth=1,
        legend=False,
    )

    if annotate:
        for _, row in df.iterrows():
            plt.text(
                row["Volatility"] + 0.0005,
                row["Returns"] + 0.0005,
                row["Fund"],
                fontsize=point_label_size,
                va="center",
                ha="left",
            )

    plt.title("Fund Returns vs Volatility Bubble Chart", fontsize=title_size)
    plt.xlabel("Annualized Volatility", fontsize=axis_label_size)
    plt.ylabel("Annualized Returns", fontsize=axis_label_size)
    plt.xticks(fontsize=tick_label_size)
    plt.yticks(fontsize=tick_label_size)
    plt.grid(True, linestyle="--", alpha=0.6)

    plt.tight_layout()

    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(output)

    if show_plot:
        plt.show()
    else:
        plt.close()

    return output


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Generate returns/volatility bubble chart for selected payload.")
    parser.add_argument("--cache-file", default="cache/returns_series_cache.pkl", help="returns_series cache path.")
    parser.add_argument("--output", default="chart/bubble_chart.png", help="Output chart path.")

    parser.add_argument(
        "--payload-mode",
        choices=["fixed", "random", "perturbed"],
        default="fixed",
        help="How to build payload when --payload-file is not provided.",
    )
    parser.add_argument("--payload-file", default=None, help="JSON payload file path.")
    parser.add_argument("--equity-share", type=float, default=0.6, help="Equity share for random payload mode.")
    parser.add_argument("--fi-share", type=float, default=0.4, help="FI share for random payload mode.")

    parser.add_argument("--no-annotate", action="store_true", help="Do not annotate fund names on points.")
    parser.add_argument("--show", action="store_true", help="Show chart window after save.")
    parser.add_argument("--title-size", type=int, default=22, help="Chart title font size.")
    parser.add_argument("--axis-label-size", type=int, default=16, help="X/Y axis label font size.")
    parser.add_argument("--tick-label-size", type=int, default=13, help="X/Y tick label font size.")
    parser.add_argument("--point-label-size", type=int, default=11, help="Fund text label font size.")
    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    cache_path = Path(args.cache_file)
    if not cache_path.exists():
        raise FileNotFoundError(
            f"Cache file not found: {cache_path}. Run backtester.py first to build returns cache."
        )

    returns_series = pd.read_pickle(cache_path)
    _, fund_name_by_isin = get_isin_data()

    payload = build_payload(
        mode=args.payload_mode,
        equity_share=args.equity_share,
        fi_share=args.fi_share,
        payload_file=args.payload_file,
    )

    bubble_data = build_bubble_data(returns_series=returns_series, payload=payload, fund_name_by_isin=fund_name_by_isin)
    output = plot_bubble_chart(
        bubble_data=bubble_data,
        output_path=args.output,
        annotate=not args.no_annotate,
        show_plot=args.show,
        title_size=args.title_size,
        axis_label_size=args.axis_label_size,
        tick_label_size=args.tick_label_size,
        point_label_size=args.point_label_size,
    )

    print(f"[bubble_chart.py] chart saved: {output}")


if __name__ == "__main__":
    main()
