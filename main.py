from __future__ import annotations

import argparse
from pathlib import Path

from src.clear import delete_raw_json, delete_research_db
from src.fetch import DEFAULT_COUNTRIES, DEFAULT_VERSIONS, run_fetch
from src.research import run_research


def _parse_csv_arg(value: str) -> list[str]:
    return [part.strip() for part in value.split(",") if part.strip()]


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run jp-data pipeline (clear -> fetch -> research).")

    parser.add_argument("--raw-data-root", default="raw_data", help="Raw data root directory.")
    parser.add_argument("--nav-subdir", default="Daily_NAV", help="NAV raw JSON folder name.")
    parser.add_argument("--fund-info-subdir", default="FUND_info", help="FUND info JSON folder name.")
    parser.add_argument("--research-db-path", default="research_db", help="Research database output folder.")
    parser.add_argument("--fetch-check-path", default="src/fetch_check.csv", help="Fetch status CSV path.")

    parser.add_argument("--skip-clear-raw", action="store_true", help="Skip deleting old raw JSON.")
    parser.add_argument(
        "--skip-clear-research",
        action="store_true",
        help="Skip deleting old research_db content.",
    )
    parser.add_argument("--skip-fetch", action="store_true", help="Skip fetch step.")
    parser.add_argument("--skip-research", action="store_true", help="Skip research step.")

    parser.add_argument("--fetch-limit", type=int, default=None, help="Limit fund count in fetch step.")
    parser.add_argument("--research-limit", type=int, default=None, help="Limit fund count in research step.")
    parser.add_argument(
        "--overwrite-fetch-check",
        action="store_true",
        help="Overwrite fetch_check.csv before writing new logs.",
    )
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
    parser.add_argument("--timeout", type=float, default=10.0, help="HTTP timeout for API calls.")

    parser.add_argument(
        "--skip-research-charts",
        action="store_true",
        help="Run research data extraction without generating chart images.",
    )
    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    raw_data_root = Path(args.raw_data_root)
    research_db_path = Path(args.research_db_path)

    print("[main.py] pipeline start")

    if not args.skip_clear_raw:
        delete_raw_json(raw_data_root=raw_data_root, subfolders=(args.nav_subdir, args.fund_info_subdir))

    if not args.skip_clear_research:
        delete_research_db(folder=research_db_path)

    if not args.skip_fetch:
        run_fetch(
            raw_data_root=raw_data_root,
            nav_subdir=args.nav_subdir,
            fund_info_subdir=args.fund_info_subdir,
            fetch_check_path=args.fetch_check_path,
            clear_raw=False,
            overwrite_fetch_check=args.overwrite_fetch_check,
            limit=args.fetch_limit,
            versions=_parse_csv_arg(args.versions),
            countries=_parse_csv_arg(args.countries),
            timeout=args.timeout,
        )

    if not args.skip_research:
        run_research(
            fund_info_path=raw_data_root / args.fund_info_subdir,
            research_db_path=research_db_path,
            clear_existing=False,
            limit=args.research_limit,
            write_charts=not args.skip_research_charts,
        )

    print("[main.py] pipeline done")


if __name__ == "__main__":
    main()
