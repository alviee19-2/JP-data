from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

try:
    from src.ISIN import get_isin_data
    from src.clear import delete_research_db
except ImportError:
    from ISIN import get_isin_data
    from clear import delete_research_db


def _safe_filename(name: str) -> str:
    invalid = '<>:"/\\|?*'
    return "".join("_" if ch in invalid else ch for ch in name)


def _parse_percent(value: Any) -> float | None:
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        cleaned = value.strip().rstrip("%")
        if cleaned == "":
            return None
        try:
            return float(cleaned)
        except ValueError:
            return None
    return None


def _write_pie_chart(data: dict[str, float], title: str, output_path: Path) -> None:
    if not data:
        return

    import plotly.express as px

    names = list(data.keys())
    values = list(data.values())

    figure = px.pie(
        names=names,
        values=values,
        title=title,
        color_discrete_sequence=px.colors.sequential.OrRd[::-1],
    )

    output_path.parent.mkdir(parents=True, exist_ok=True)
    figure.write_image(str(output_path), format="jpg", scale=3)


def _extract_country(fund_data: dict[str, Any], fund_name: str) -> dict[str, float] | None:
    emea = (fund_data.get("emeaRegionalBreakdown") or {}).get("data") or []
    if emea:
        country: dict[str, float] = {}
        for item in emea:
            value = _parse_percent(item.get("value"))
            name = item.get("name")
            if not name or value is None:
                continue
            if value == 100.0:
                break
            country[name] = value
        if country:
            return country

    by_country = (fund_data.get("portfolioAnalysisByCountry") or {}).get("data") or []
    if by_country:
        country = {
            item.get("name"): _parse_percent(item.get("value"))
            for item in by_country
            if item.get("name") and _parse_percent(item.get("value")) is not None
        }
        if country:
            return {k: float(v) for k, v in country.items() if v is not None}

    fi_regions = (fund_data.get("portfolioAnalysisByFixedIncomeRegions") or {}).get("data") or []
    if fi_regions:
        country = {
            item.get("name"): _parse_percent(item.get("value"))
            for item in fi_regions
            if item.get("name") and _parse_percent(item.get("value")) is not None
        }
        if country:
            return {k: float(v) for k, v in country.items() if v is not None}

    exposure = (fund_data.get("countryExposure") or {}).get("data") or []
    if exposure:
        groups = {x.get("group") for x in exposure if x.get("group") and x.get("group") != "HEADER"}
        country = {}
        for item in exposure:
            name = item.get("name")
            value = _parse_percent(item.get("value"))
            group = item.get("group")
            if not name or value in (None, 0):
                continue
            if group == "HEADER" and name in groups:
                continue
            country[name] = float(value)
        if country:
            return country

    name_lower = fund_name.lower()
    if "america" in name_lower or " us " in f" {name_lower} ":
        return {"US": 100.0}
    if "japan" in name_lower:
        return {"Japan": 100.0}
    if "korea" in name_lower:
        return {"Korea": 100.0}
    if "china" in name_lower:
        return {"China": 100.0}
    if "taiwan" in name_lower:
        return {"Taiwan": 100.0}
    if "india" in name_lower:
        return {"India": 100.0}

    return None


def _extract_sector(fund_data: dict[str, Any]) -> dict[str, float] | None:
    by_sector = (fund_data.get("portfolioAnalysisBySector") or {}).get("data") or []
    if by_sector:
        sector = {
            item.get("name"): _parse_percent(item.get("value"))
            for item in by_sector
            if item.get("name") and _parse_percent(item.get("value")) is not None
        }
        if sector:
            return {k: float(v) for k, v in sector.items() if v is not None}

    emea_sector = (fund_data.get("emeaSectorBreakdown") or {}).get("data") or []
    if emea_sector:
        sector = {}
        for item in emea_sector:
            name = item.get("name")
            value = _parse_percent(item.get("value"))
            if not name or name == "Total" or value in (None, 0):
                continue
            sector[name] = float(value)
        if sector:
            return sector

    equity_regions = (fund_data.get("portfolioAnalysisByEquityRegions") or {}).get("data") or []
    if equity_regions:
        sector = {}
        for item in equity_regions:
            name = item.get("name")
            value = _parse_percent(item.get("value"))
            if not name or name == "Total" or value in (None, 0):
                continue
            sector[name] = float(value)
        if sector:
            return sector

    asset_alloc = (fund_data.get("assetAllocation") or {}).get("data") or []
    if asset_alloc:
        alloc: dict[str, float] = {}
        for item in asset_alloc:
            name = item.get("name")
            value = _parse_percent(item.get("value"))
            if not name or name == "Total" or value in (None, 0):
                continue
            alloc[name] = float(value)

        total = sum(alloc.values())
        if alloc and 99.5 <= total <= 100.5 and total != 100:
            scale = 100.0 / total
            alloc = {k: round(v * scale, 2) for k, v in alloc.items()}

        if alloc:
            return alloc

    exposure = (fund_data.get("sectorExposure") or {}).get("data") or []
    if exposure:
        sector = {}
        for item in exposure:
            name = item.get("name")
            value = _parse_percent(item.get("value"))
            if not name or name == "Total" or value in (None, 0):
                continue
            sector[name] = float(value)
        if sector:
            return sector

    return None


def _extract_holdings(fund_data: dict[str, Any]) -> dict[str, float] | None:
    holdings_data = (fund_data.get("fundHoldings") or {}).get("tabularDataMap") or {}
    if holdings_data:
        holdings: dict[str, float] = {}
        for row in holdings_data.values():
            cell_list = row.get("cellList") or []
            if len(cell_list) < 4:
                continue

            company = cell_list[0].get("displayValue")
            pct = _parse_percent(cell_list[3].get("displayValue"))
            if not company or pct is None:
                continue

            holdings[company] = pct

        if holdings:
            total = sum(holdings.values())
            if total < 100:
                holdings["others"] = round(100 - total, 2)
            return holdings

    emea_holdings = (fund_data.get("emeaFundHoldings") or {}).get("data") or []
    if emea_holdings:
        top = emea_holdings[:10]
        holdings: dict[str, float] = {}
        running = 0.0
        for item in top:
            company = item.get("securityDescription")
            pct = _parse_percent(item.get("marketValuePercent"))
            if not company or pct is None:
                continue
            holdings[company] = pct
            running += pct

        if holdings:
            if running < 100:
                holdings["others"] = round(100 - running, 2)
            return holdings

    return None


def _read_fund_info(fund_info_path: Path) -> dict[str, dict[str, Any]]:
    fund_info_by_name: dict[str, dict[str, Any]] = {}
    if not fund_info_path.exists():
        print(f"[research.py] fund info path not found: {fund_info_path}")
        return fund_info_by_name

    for file_path in sorted(fund_info_path.glob("*.json")):
        fund_name = file_path.stem.rsplit("_", 1)[0]
        try:
            with file_path.open("r", encoding="utf-8") as file:
                data = json.load(file)
                if isinstance(data, dict):
                    fund_info_by_name[fund_name] = data
        except Exception as exc:
            print(f"[research.py] failed to read {file_path}: {exc}")

    print(f"[research.py] loaded fund info files: {len(fund_info_by_name)}")
    return fund_info_by_name


def run_research(
    fund_info_path: str | Path = "raw_data/FUND_info",
    research_db_path: str | Path = "research_db",
    clear_existing: bool = True,
    limit: int | None = None,
    write_charts: bool = True,
) -> dict[str, Any]:
    fund_info_path = Path(fund_info_path)
    research_db_path = Path(research_db_path)

    if clear_existing:
        delete_research_db(research_db_path)
    research_db_path.mkdir(parents=True, exist_ok=True)

    fund_info_by_name = _read_fund_info(fund_info_path)
    isins, fund_name_by_isin = get_isin_data()

    if limit is not None:
        isins = isins[:limit]

    missing_fund_info: list[str] = []
    missing_country: list[str] = []
    missing_sector: list[str] = []
    missing_holdings: list[str] = []

    processed = 0

    for index, isin in enumerate(isins, start=1):
        fund_name = fund_name_by_isin[isin]
        payload = fund_info_by_name.get(fund_name) or fund_info_by_name.get(_safe_filename(fund_name))
        if not payload:
            missing_fund_info.append(fund_name)
            print(f"[research.py] ({index}/{len(isins)}) missing fund info: {fund_name}")
            continue

        fund_data = payload.get("fundData") or {}
        aum_block = fund_data.get("aum") or {}
        aum_value = aum_block.get("value")
        aum_date = str(aum_block.get("date", "unknown-date"))

        country = _extract_country(fund_data, fund_name)
        sector = _extract_sector(fund_data)
        holdings = _extract_holdings(fund_data)

        if country is None:
            missing_country.append(fund_name)
        if sector is None:
            missing_sector.append(fund_name)
        if holdings is None:
            missing_holdings.append(fund_name)

        fund_dir = research_db_path / isin
        fund_dir.mkdir(parents=True, exist_ok=True)

        output_data = {
            "isin": isin,
            "name": fund_name,
            "aum": aum_value,
            "aum_date": aum_date,
            "country": country,
            "sector": sector,
            "holdings": holdings,
        }

        info_path = fund_dir / "info.json"
        with info_path.open("w", encoding="utf-8") as file:
            json.dump(output_data, file, ensure_ascii=False, indent=2)

        if write_charts:
            safe_name = _safe_filename(fund_name)
            safe_date = _safe_filename(aum_date)
            if country:
                _write_pie_chart(
                    country,
                    f"{fund_name} Country ({aum_date})",
                    fund_dir / f"{safe_name}_country_{safe_date}.jpg",
                )
            if sector:
                _write_pie_chart(
                    sector,
                    f"{fund_name} Sector ({aum_date})",
                    fund_dir / f"{safe_name}_sector_{safe_date}.jpg",
                )
            if holdings:
                _write_pie_chart(
                    holdings,
                    f"{fund_name} Holdings ({aum_date})",
                    fund_dir / f"{safe_name}_holding_{safe_date}.jpg",
                )

        processed += 1
        print(f"[research.py] ({index}/{len(isins)}) processed: {fund_name}")

    summary = {
        "requested": len(isins),
        "processed": processed,
        "missing_fund_info": missing_fund_info,
        "missing_country": missing_country,
        "missing_sector": missing_sector,
        "missing_holdings": missing_holdings,
    }

    print(f"[research.py] summary: processed={processed}/{len(isins)}")
    print(f"[research.py] missing fund info: {len(missing_fund_info)}")
    print(f"[research.py] missing country: {len(missing_country)}")
    print(f"[research.py] missing sector: {len(missing_sector)}")
    print(f"[research.py] missing holdings: {len(missing_holdings)}")

    return summary


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Build normalized research_db from FUND info JSON.")
    parser.add_argument("--fund-info-path", default="raw_data/FUND_info", help="Directory of raw FUND info JSON.")
    parser.add_argument("--research-db-path", default="research_db", help="Research output directory.")
    parser.add_argument("--keep-existing", action="store_true", help="Do not clear existing research_db.")
    parser.add_argument("--limit", type=int, default=None, help="Limit number of funds to process.")
    parser.add_argument("--skip-charts", action="store_true", help="Skip writing pie chart images.")
    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    run_research(
        fund_info_path=args.fund_info_path,
        research_db_path=args.research_db_path,
        clear_existing=not args.keep_existing,
        limit=args.limit,
        write_charts=not args.skip_charts,
    )


if __name__ == "__main__":
    main()
