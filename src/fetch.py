from __future__ import annotations

import argparse
import csv
import json
from datetime import date
from pathlib import Path
from typing import Iterable

import requests

try:
    from src.ISIN import get_isin_data
    from src.clear import delete_raw_json
except ImportError:
    from ISIN import get_isin_data
    from clear import delete_raw_json


NAV_URL = "https://am.jpmorgan.com/FundsMarketingHandler/historicalData"
FUND_INFO_URL = "https://am.jpmorgan.com/FundsMarketingHandler/product-data"

DEFAULT_VERSIONS = ["8.12_1751450551", "8.13_1752481876", "8.14_1753929949"]
DEFAULT_COUNTRIES = ["hk", "sg", "dk", "fi", "lu", "gb", "ch", "us", "nl"]
DEFAULT_TIMEOUT = 10.0


def _parse_csv_arg(value: str) -> list[str]:
    return [part.strip() for part in value.split(",") if part.strip()]


def _safe_filename(name: str) -> str:
    invalid = '<>:"/\\|?*'
    return "".join("_" if ch in invalid else ch for ch in name)


def _init_fetch_check(path: Path, overwrite: bool) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)

    if overwrite and path.exists():
        path.unlink()

    if not path.exists() or path.stat().st_size == 0:
        with path.open("a", newline="", encoding="utf-8-sig") as file:
            writer = csv.writer(file)
            writer.writerow(["fund_name", "isin", "nav_status", "fund_info_status"])


def _append_fetch_check_row(
    path: Path,
    fund_name: str,
    isin: str,
    nav_status: str,
    fund_status: str,
) -> None:
    with path.open("a", newline="", encoding="utf-8-sig") as file:
        writer = csv.writer(file)
        writer.writerow([fund_name, isin, nav_status, fund_status])


def fetch_nav_json(
    cusip: str,
    versions: Iterable[str],
    countries: Iterable[str],
    timeout: float,
) -> dict | None:
    for country in countries:
        for version in versions:
            params = {
                "cusip": cusip,
                "country": country,
                "role": "per",
                "userLoggedIn": "false",
                "language": "en",
                "version": version,
            }
            try:
                print(f"[fetch.py] NAV request: isin={cusip}, country={country}, version={version}")
                resp = requests.get(NAV_URL, params=params, timeout=timeout)
                resp.raise_for_status()
                data = resp.json()

                nav_list = data.get("historicalNAVList") or []
                etf_nav_list = data.get("historicalETFNAVMarketPriceList") or []
                if nav_list or etf_nav_list:
                    return data
            except requests.exceptions.RequestException as exc:
                print(f"[fetch.py] NAV request failed: isin={cusip}, error={exc}")
            except ValueError as exc:
                print(f"[fetch.py] NAV JSON decode failed: isin={cusip}, error={exc}")

    return None


def fetch_fund_info_json(
    cusip: str,
    versions: Iterable[str],
    countries: Iterable[str],
    timeout: float,
) -> dict | None:
    for country in countries:
        for version in versions:
            params = {
                "cusip": cusip,
                "country": country,
                "role": "per",
                "userLoggedIn": "false",
                "language": "en",
                "version": version,
            }
            try:
                print(f"[fetch.py] FUND INFO request: isin={cusip}, country={country}, version={version}")
                resp = requests.get(FUND_INFO_URL, params=params, timeout=timeout)
                resp.raise_for_status()
                data = resp.json()

                if data.get("fundData"):
                    return data
            except requests.exceptions.RequestException as exc:
                print(f"[fetch.py] FUND INFO request failed: isin={cusip}, error={exc}")
            except ValueError as exc:
                print(f"[fetch.py] FUND INFO JSON decode failed: isin={cusip}, error={exc}")

    return None


def save_raw_json(fund_name: str, data: dict, output_dir: Path) -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)
    filename = f"{_safe_filename(fund_name)}_{date.today().isoformat()}.json"
    output_path = output_dir / filename

    with output_path.open("w", encoding="utf-8") as file:
        json.dump(data, file, ensure_ascii=False, indent=2)

    print(f"[fetch.py] saved: {output_path}")
    return output_path


def run_fetch(
    raw_data_root: str | Path = "raw_data",
    nav_subdir: str = "Daily_NAV",
    fund_info_subdir: str = "FUND_info",
    fetch_check_path: str | Path = "src/fetch_check.csv",
    clear_raw: bool = True,
    overwrite_fetch_check: bool = False,
    limit: int | None = None,
    versions: Iterable[str] = DEFAULT_VERSIONS,
    countries: Iterable[str] = DEFAULT_COUNTRIES,
    timeout: float = DEFAULT_TIMEOUT,
) -> dict[str, int]:
    print("[fetch.py] start run_fetch")

    raw_data_root_path = Path(raw_data_root)
    nav_output_dir = raw_data_root_path / nav_subdir
    info_output_dir = raw_data_root_path / fund_info_subdir

    if clear_raw:
        delete_raw_json(raw_data_root=raw_data_root_path, subfolders=(nav_subdir, fund_info_subdir))

    check_path = Path(fetch_check_path)
    _init_fetch_check(check_path, overwrite=overwrite_fetch_check)

    isins, fund_name_by_isin = get_isin_data()
    if limit is not None:
        isins = isins[:limit]

    nav_failures = 0
    info_failures = 0

    for index, isin in enumerate(isins, start=1):
        fund_name = fund_name_by_isin.get(isin, isin)
        print(f"[fetch.py] ({index}/{len(isins)}) fetching {fund_name} ({isin})")

        nav_data = fetch_nav_json(isin, versions=versions, countries=countries, timeout=timeout)
        info_data = fetch_fund_info_json(isin, versions=versions, countries=countries, timeout=timeout)

        nav_status = "success"
        info_status = "success"

        if nav_data is not None:
            save_raw_json(fund_name, nav_data, output_dir=nav_output_dir)
        else:
            nav_status = "fail"
            nav_failures += 1

        if info_data is not None:
            save_raw_json(fund_name, info_data, output_dir=info_output_dir)
        else:
            info_status = "fail"
            info_failures += 1

        _append_fetch_check_row(check_path, fund_name, isin, nav_status, info_status)

    print(
        "[fetch.py] finished. "
        f"fund_count={len(isins)}, nav_failures={nav_failures}, fund_info_failures={info_failures}"
    )

    return {
        "fund_count": len(isins),
        "nav_failures": nav_failures,
        "fund_info_failures": info_failures,
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Fetch JPM fund NAV/FUND info JSON from API.")
    parser.add_argument("--raw-data-root", default="raw_data", help="Raw data root directory.")
    parser.add_argument("--nav-subdir", default="Daily_NAV", help="Subdirectory for NAV JSON.")
    parser.add_argument("--fund-info-subdir", default="FUND_info", help="Subdirectory for FUND info JSON.")
    parser.add_argument(
        "--fetch-check-path",
        default="src/fetch_check.csv",
        help="CSV path for fetch status logs.",
    )
    parser.add_argument(
        "--keep-raw",
        action="store_true",
        help="Keep existing raw JSON files (skip pre-clean).",
    )
    parser.add_argument(
        "--overwrite-fetch-check",
        action="store_true",
        help="Overwrite fetch_check.csv before writing new records.",
    )
    parser.add_argument("--limit", type=int, default=None, help="Limit number of funds to fetch.")
    parser.add_argument(
        "--countries",
        default=",".join(DEFAULT_COUNTRIES),
        help="Comma-separated country list for API params.",
    )
    parser.add_argument(
        "--versions",
        default=",".join(DEFAULT_VERSIONS),
        help="Comma-separated API version list.",
    )
    parser.add_argument("--timeout", type=float, default=DEFAULT_TIMEOUT, help="HTTP timeout (seconds).")
    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    run_fetch(
        raw_data_root=args.raw_data_root,
        nav_subdir=args.nav_subdir,
        fund_info_subdir=args.fund_info_subdir,
        fetch_check_path=args.fetch_check_path,
        clear_raw=not args.keep_raw,
        overwrite_fetch_check=args.overwrite_fetch_check,
        limit=args.limit,
        versions=_parse_csv_arg(args.versions),
        countries=_parse_csv_arg(args.countries),
        timeout=args.timeout,
    )


if __name__ == "__main__":
    main()
