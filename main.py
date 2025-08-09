import sys
import os

# 將 src 資料夾添加到 Python 路徑，以便導入模組
sys.path.insert(0, os.path.abspath('src'))

from src.clear import delete_raw_json, delete_research_db
from src.fetch import run_fetch
from src.research import run_research

def main():
    """
    主執行函式，依序執行資料清理、抓取和研究分析。
    """
    print("--- 開始執行主程式 (main.py) ---")

    # 步驟 1: 清理舊的研究資料 (原始資料清理已整合到 fetch 步驟中)
    print("\n--- 執行資料清理 ---")
    delete_research_db()
    print("--- 資料清理完成 ---")

    # 步驟 2: 抓取最新的基金資料 (此步驟會先清理舊的原始資料)
    print("\n--- 執行基金資料抓取 ---")
    run_fetch()
    print("--- 基金資料抓取完成 ---")

    # 步驟 3: 執行基金研究分析
    print("\n--- 執行基金研究分析 ---")
    run_research()
    print("--- 基金研究分析完成 ---")

    print("\n--- 主程式執行完畢 (main.py) ---")

if __name__ == "__main__":
    main()
