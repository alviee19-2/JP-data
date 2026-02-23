from __future__ import annotations

import json
from collections import defaultdict
from pathlib import Path

import matplotlib.pyplot as plt


def generate_pie_charts_data(
    payload_data: dict[str, float],
    research_db_path: str | Path = "research_db",
) -> tuple[float, dict[str, float], dict[str, float]]:
    """
    Compute weighted sector/country allocations using payload weights and research_db info.json.
    """
    research_db = Path(research_db_path)

    total_payload_weight = 0.0
    total_weighted_sector_allocation: defaultdict[str, float] = defaultdict(float)
    total_weighted_country_allocation: defaultdict[str, float] = defaultdict(float)

    if not research_db.exists():
        print(f"[chart_utils.py] research_db path not found: {research_db}")
        return 0.0, {}, {}

    for fund_folder in research_db.iterdir():
        if not fund_folder.is_dir():
            continue

        info_json_path = fund_folder / "info.json"
        if not info_json_path.exists():
            continue

        try:
            with info_json_path.open("r", encoding="utf-8") as file:
                info_data = json.load(file)
        except json.JSONDecodeError:
            print(f"[chart_utils.py] invalid JSON: {info_json_path}")
            continue

        fund_name = info_data.get("name")
        if not isinstance(fund_name, str):
            continue

        weight = float(payload_data.get(fund_name, 0.0))
        if weight == 0.0:
            continue

        total_payload_weight += weight

        sector_data = info_data.get("sector")
        if isinstance(sector_data, dict):
            for sector, percentage in sector_data.items():
                try:
                    total_weighted_sector_allocation[sector] += (float(percentage) / 100.0) * weight
                except (TypeError, ValueError):
                    continue

        country_data = info_data.get("country")
        if isinstance(country_data, dict):
            for country, percentage in country_data.items():
                if country in {"Other", "Total"}:
                    continue
                try:
                    total_weighted_country_allocation[country] += (float(percentage) / 100.0) * weight
                except (TypeError, ValueError):
                    continue

    final_sector_percentages: dict[str, float] = {}
    final_country_percentages: dict[str, float] = {}

    if total_payload_weight > 0:
        for sector, value in total_weighted_sector_allocation.items():
            final_sector_percentages[sector] = max(0.0, (value / total_payload_weight) * 100.0)

        for country, value in total_weighted_country_allocation.items():
            final_country_percentages[country] = max(0.0, (value / total_payload_weight) * 100.0)

    return total_payload_weight, final_sector_percentages, final_country_percentages


def plot_pie_chart(data: dict[str, float], title: str, filename: str | Path) -> None:
    if not data:
        print(f"[chart_utils.py] no data for chart: {title}")
        return

    labels = list(data.keys())
    sizes = list(data.values())

    total_percentage = sum(sizes)
    if total_percentage > 0:
        sizes = [(value / total_percentage) * 100 for value in sizes]

    fig, ax = plt.subplots(figsize=(10, 10))
    wedges, texts, autotexts = ax.pie(
        sizes,
        labels=labels,
        autopct="%1.1f%%",
        startangle=90,
        pctdistance=0.85,
        textprops={"fontsize": 10},
    )

    plt.setp(autotexts, size=8, weight="bold")
    plt.setp(texts, size=10)

    ax.axis("equal")
    plt.title(title, fontsize=14)

    output_path = Path(filename)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(output_path)
    plt.close(fig)
    print(f"[chart_utils.py] chart saved: {output_path}")
