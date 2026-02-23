from __future__ import annotations

import shutil
from pathlib import Path
from typing import Iterable


def _delete_json_files(folder: Path) -> int:
    removed = 0
    for file_path in folder.glob("*.json"):
        file_path.unlink(missing_ok=True)
        removed += 1
    return removed


def delete_raw_json(
    raw_data_root: str | Path = "raw_data",
    subfolders: Iterable[str] = ("Daily_NAV", "FUND_info"),
) -> dict[str, int]:
    """Delete JSON files under raw data subfolders."""
    root = Path(raw_data_root)
    deleted_by_folder: dict[str, int] = {}
    for subfolder in subfolders:
        target = root / subfolder
        target.mkdir(parents=True, exist_ok=True)
        deleted_count = _delete_json_files(target)
        deleted_by_folder[str(target)] = deleted_count
        print(f"[clear.py] removed {deleted_count} JSON files from: {target}")
    return deleted_by_folder


def delete_research_db(folder: str | Path = "research_db") -> int:
    """Delete all items under research_db while keeping the root folder."""
    target = Path(folder)
    target.mkdir(parents=True, exist_ok=True)

    removed = 0
    for item in target.iterdir():
        if item.is_dir():
            shutil.rmtree(item)
        else:
            item.unlink(missing_ok=True)
        removed += 1

    print(f"[clear.py] removed {removed} items from: {target}")
    return removed
