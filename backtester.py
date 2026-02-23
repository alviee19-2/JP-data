from __future__ import annotations

import argparse
import json
import random
from datetime import date
from pathlib import Path
from typing import Any

import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import matplotlib.ticker as mtick
import pandas as pd

from NAV_clean import nav_dict, read_nav_json
from payload import FixedIncome, fixedweight, generate_payload, try_payload, zip_payload
from src.ISIN import get_isin_data
from src.chart_utils import generate_pie_charts_data, plot_pie_chart


def _slug(text: str) -> str:
    return "".join(ch if ch.isalnum() else "_" for ch in text).strip("_").lower()


def _load_payload_file(payload_file: str | Path) -> dict[str, float]:
    with Path(payload_file).open("r", encoding="utf-8") as file:
        payload = json.load(file)

    if not isinstance(payload, dict):
        raise ValueError("Payload file must be a JSON object: {fund_name: weight}")

    normalized: dict[str, float] = {}
    for key, value in payload.items():
        try:
            normalized[str(key)] = float(value)
        except (TypeError, ValueError) as exc:
            raise ValueError(f"Invalid payload value for {key}: {value}") from exc

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


def split_payload(payload: dict[str, float]) -> tuple[dict[str, float], dict[str, float]]:
    fixed_keys = set(fixedweight.keys()) | set(FixedIncome)
    equity_part = {name: weight for name, weight in payload.items() if name not in fixed_keys}
    fixed_part = {name: weight for name, weight in payload.items() if name in fixed_keys}
    return equity_part, fixed_part


def build_returns_series(start_date: str, nav_dir: str | Path) -> dict[str, pd.Series]:
    import quantstats as qs

    read_nav_json(path=nav_dir, clear=True)
    isins, _ = get_isin_data()

    start_ts = pd.to_datetime(start_date)
    returns_series: dict[str, pd.Series] = {}

    for isin in isins:
        records = nav_dict.get(isin)
        if not records:
            continue

        series = pd.Series(
            data=[record["navPrice"] for record in records],
            index=pd.to_datetime([record["date"] for record in records]),
        ).sort_index()

        if series.empty:
            continue

        fund_returns = qs.utils.to_returns(series).dropna()
        fund_returns = fund_returns[fund_returns.index >= start_ts]

        if not fund_returns.empty:
            returns_series[isin] = fund_returns

    print(f"[backtester.py] built returns series: {len(returns_series)} funds")
    return returns_series


def load_or_build_returns_series(
    cache_file: str | Path,
    use_cache: bool,
    refresh_cache: bool,
    start_date: str,
    nav_dir: str | Path,
) -> dict[str, pd.Series]:
    cache_path = Path(cache_file)

    if use_cache and not refresh_cache and cache_path.exists():
        print(f"[backtester.py] loading returns cache: {cache_path}")
        return pd.read_pickle(cache_path)

    returns_series = build_returns_series(start_date=start_date, nav_dir=nav_dir)

    if use_cache:
        cache_path.parent.mkdir(parents=True, exist_ok=True)
        pd.to_pickle(returns_series, cache_path)
        print(f"[backtester.py] saved returns cache: {cache_path}")

    return returns_series


def quick_plot_no_box(series: pd.Series, outfile: str | Path) -> Path:
    series = pd.Series(series).dropna()
    if series.empty:
        return Path(outfile)

    series.index = pd.to_datetime(series.index)
    cumulative = (1 + series).cumprod() - 1

    fig, ax = plt.subplots(figsize=(12, 4))
    ax.plot(cumulative.index, cumulative.values, linewidth=1.4)

    ax.grid(axis="y", linestyle="--", alpha=0.5)
    ax.xaxis.set_major_locator(mdates.YearLocator())
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y"))
    ax.yaxis.set_major_formatter(mtick.PercentFormatter(1.0, decimals=0))

    for side in ["top", "right", "left", "bottom"]:
        ax.spines[side].set_visible(False)

    fig.patch.set_alpha(0.0)
    ax.patch.set_alpha(0.0)
    ax.set_facecolor("none")
    ax.set_xlabel("")

    output_path = Path(outfile)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    plt.tight_layout()
    plt.savefig(output_path, dpi=300, transparent=True, facecolor="none", bbox_inches="tight", pad_inches=0)
    plt.close(fig)
    return output_path


def _sharpe_bucket(sharpe: float) -> str:
    if sharpe >= 1.0:
        return "sharpe_over_1.0"
    if sharpe >= 0.7:
        return "sharpe_over_0.7"
    if sharpe >= 0.5:
        return "sharpe_over_0.5"
    return "sharpe_under_0.5"


def calculate_portfolio_returns(
    returns_series: dict[str, pd.Series],
    payload: dict[str, float],
    fund_name_by_isin: dict[str, str],
    start_date: str,
    end_date: str,
) -> tuple[pd.Series, list[str]]:
    idx = pd.date_range(start=start_date, end=end_date, freq="D")
    portfolio_returns = pd.Series(0.0, index=idx, name="SAA_report")

    missing_funds: list[str] = []

    for isin, fund_name in fund_name_by_isin.items():
        weight = payload.get(fund_name, 0.0)
        if weight == 0:
            continue

        fund_returns = returns_series.get(isin)
        if fund_returns is None:
            missing_funds.append(fund_name)
            continue

        portfolio_returns = portfolio_returns.add(fund_returns * weight, fill_value=0.0)

    portfolio_returns = portfolio_returns.loc[idx].fillna(0.0)
    return portfolio_returns, missing_funds


def run_backtest_once(
    start_date: str,
    end_date: str,
    returns_series: dict[str, pd.Series],
    payload: dict[str, float],
    portfolio_name: str,
    output_dir: str | Path,
    fund_name_by_isin: dict[str, str],
    research_db_path: str | Path,
    write_exposure: bool,
) -> dict[str, Any]:
    import quantstats as qs

    portfolio_returns, missing_funds = calculate_portfolio_returns(
        returns_series=returns_series,
        payload=payload,
        fund_name_by_isin=fund_name_by_isin,
        start_date=start_date,
        end_date=end_date,
    )

    sharpe = qs.stats.sharpe(portfolio_returns)
    volatility = qs.stats.volatility(portfolio_returns)

    sharpe = float(0.0 if pd.isna(sharpe) else sharpe)
    volatility = float(0.0 if pd.isna(volatility) else volatility)

    bucket = _sharpe_bucket(sharpe)
    report_dir = Path(output_dir) / bucket / f"report_on_{_slug(portfolio_name)}"
    report_dir.mkdir(parents=True, exist_ok=True)

    report_html = report_dir / f"report_on_{_slug(portfolio_name)}.html"
    curve_png = report_dir / "cumulative_returns.png"

    quick_plot_no_box(portfolio_returns, curve_png)

    qs.reports.html(
        portfolio_returns,
        output=str(report_html),
        title=f"Report on {portfolio_name}",
    )

    if write_exposure:
        total_payload_weight, sector_allocations, country_allocations = generate_pie_charts_data(
            payload,
            research_db_path=research_db_path,
        )
        equity_payload, fixed_payload = split_payload(payload)
        _, fixed_sector, fixed_country = generate_pie_charts_data(
            fixed_payload,
            research_db_path=research_db_path,
        )
        _, equity_sector, equity_country = generate_pie_charts_data(
            equity_payload,
            research_db_path=research_db_path,
        )

        plot_pie_chart(
            sector_allocations,
            "Weighted Sector Allocation",
            report_dir / "sector_exposure.png",
        )
        plot_pie_chart(
            country_allocations,
            "Weighted Country Allocation",
            report_dir / "country_exposure.png",
        )

        exposure_data = {
            "portfolio_name": portfolio_name,
            "total_payload_weight": total_payload_weight,
            "payload": payload,
            "country": country_allocations,
            "sector": sector_allocations,
            "fixed_country": fixed_country,
            "fixed_sector": fixed_sector,
            "equity_country": equity_country,
            "equity_sector": equity_sector,
            "missing_funds": missing_funds,
        }

        with (report_dir / "exposure_data.json").open("w", encoding="utf-8") as file:
            json.dump(exposure_data, file, ensure_ascii=False, indent=2)

    return {
        "portfolio_name": portfolio_name,
        "sharpe": sharpe,
        "volatility": volatility,
        "report_dir": str(report_dir),
        "report_html": str(report_html),
        "missing_funds": missing_funds,
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run SAA backtests with configurable CLI arguments.")

    parser.add_argument("--start-date", default="2014-01-01", help="Backtest start date (YYYY-MM-DD).")
    parser.add_argument(
        "--end-date",
        default=date.today().isoformat(),
        help="Backtest end date (YYYY-MM-DD).",
    )
    parser.add_argument("--iterations", type=int, default=1, help="Number of portfolios to run.")
    parser.add_argument(
        "--portfolio-name",
        default=None,
        help="Explicit portfolio name (used when iterations=1).",
    )
    parser.add_argument(
        "--portfolio-prefix",
        default="portfolio",
        help="Name prefix when running multiple iterations.",
    )

    parser.add_argument(
        "--payload-mode",
        choices=["fixed", "random", "perturbed"],
        default="fixed",
        help="How to generate payload when --payload-file is not provided.",
    )
    parser.add_argument("--payload-file", default=None, help="JSON file path for explicit payload.")
    parser.add_argument("--equity-share", type=float, default=0.6, help="Equity share for random payload mode.")
    parser.add_argument("--fi-share", type=float, default=0.4, help="Fixed income share for random payload mode.")
    parser.add_argument("--seed", type=int, default=None, help="Random seed for reproducible random payload.")

    parser.add_argument("--output-dir", default="SAA", help="Output directory for reports.")
    parser.add_argument("--research-db-path", default="research_db", help="research_db path for exposure charts.")

    parser.add_argument("--nav-dir", default="raw_data/Daily_NAV", help="Raw NAV JSON directory.")
    parser.add_argument("--cache-file", default="cache/returns_series_cache.pkl", help="Cache file for returns series.")
    parser.add_argument("--refresh-cache", action="store_true", help="Force rebuild returns cache.")
    parser.add_argument("--no-cache", action="store_true", help="Do not read/write returns cache.")

    parser.add_argument("--min-vol", type=float, default=0.1, help="Minimum volatility threshold for pass list.")
    parser.add_argument("--min-sharpe", type=float, default=0.055, help="Minimum sharpe threshold for pass list.")
    parser.add_argument("--skip-exposure", action="store_true", help="Skip exposure chart/json generation.")

    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    if args.seed is not None:
        random.seed(args.seed)

    _, fund_name_by_isin = get_isin_data()

    returns_series = load_or_build_returns_series(
        cache_file=args.cache_file,
        use_cache=not args.no_cache,
        refresh_cache=args.refresh_cache,
        start_date=args.start_date,
        nav_dir=args.nav_dir,
    )

    highest_vol = -1.0
    highest_vol_name = ""
    passing: list[str] = []

    for idx in range(args.iterations):
        if args.portfolio_name and args.iterations == 1:
            portfolio_name = args.portfolio_name
        else:
            portfolio_name = f"{args.portfolio_prefix}_{idx + 1}"

        payload = build_payload(
            mode=args.payload_mode,
            equity_share=args.equity_share,
            fi_share=args.fi_share,
            payload_file=args.payload_file,
        )

        total_weight = sum(payload.values())
        if total_weight <= 0:
            print(f"[backtester.py] skip {portfolio_name}: payload total weight <= 0")
            continue
        if total_weight > 1.0 + 1e-8:
            print(f"[backtester.py] skip {portfolio_name}: payload total weight > 1.0 ({total_weight:.6f})")
            continue

        result = run_backtest_once(
            start_date=args.start_date,
            end_date=args.end_date,
            returns_series=returns_series,
            payload=payload,
            portfolio_name=portfolio_name,
            output_dir=args.output_dir,
            fund_name_by_isin=fund_name_by_isin,
            research_db_path=args.research_db_path,
            write_exposure=not args.skip_exposure,
        )

        vol = result["volatility"]
        sharpe = result["sharpe"]

        if vol > highest_vol:
            highest_vol = vol
            highest_vol_name = portfolio_name

        if vol >= args.min_vol and sharpe >= args.min_sharpe:
            passing.append(portfolio_name)

        print(
            f"[backtester.py] {portfolio_name}: "
            f"volatility={vol:.6f}, sharpe={sharpe:.6f}, report={result['report_html']}"
        )

    print(f"[backtester.py] highest volatility portfolio: {highest_vol_name} ({highest_vol:.6f})")
    print(f"[backtester.py] pass list ({len(passing)}): {passing}")


if __name__ == "__main__":
    main()
