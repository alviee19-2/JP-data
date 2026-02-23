# jp-data

這個專案用來做 J.P. Morgan 基金資料流程化處理：
- 抓取 NAV / FUND info 原始資料
- 產生標準化 `research_db`
- 回測組合並輸出報告與曝險圖
- 產生相關係數熱力圖、泡泡圖、NAV overlay

## 目前功能

1. 資料抓取（`src/fetch.py`）
- 從 JPM API 抓 NAV 與 FUND info
- 可設定 countries / versions / timeout / limit
- 產生抓取紀錄 `src/fetch_check.csv`

2. 研究資料標準化（`src/research.py`）
- 解析 country / sector / holdings / AUM
- 輸出 `research_db/<ISIN>/info.json`
- 可選擇是否輸出圖表

3. 回測（`backtester.py`）
- 支援固定權重、隨機權重、擾動權重、外部 JSON 權重
- 支援 cache、多次迭代、Sharpe/Vol 門檻篩選
- 輸出 QuantStats HTML 與曝險圖

4. 視覺化分析
- `analysis_on_all.py`: 相關係數熱力圖
- `bubble_chart.py`: 報酬/波動泡泡圖
- `NAV_clean.py`: NAV overlay 圖（HTML）

5. 一鍵 Pipeline（`main.py`）
- 可控制 clear/fetch/research 各步驟
- 所有原本手動改常數的參數已改為 CLI 參數

## 安裝

```powershell
py -3.13 -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

## 使用方法

### 1) 完整流程（清理 -> 抓取 -> 研究）

```powershell
python main.py
```

常用參數：

```powershell
python main.py --help
python main.py --fetch-limit 10 --research-limit 10
python main.py --skip-clear-raw --skip-clear-research
python main.py --skip-fetch --skip-research-charts
```

### 2) 只抓資料

```powershell
python src/fetch.py --help
python src/fetch.py --limit 20 --timeout 15
python src/fetch.py --countries hk,sg,us --versions 8.14_1753929949
python src/fetch.py --keep-raw --overwrite-fetch-check
```

### 3) 只建研究資料庫

```powershell
python src/research.py --help
python src/research.py --fund-info-path raw_data/FUND_info --research-db-path research_db
python src/research.py --limit 30 --skip-charts
```

### 4) 回測

```powershell
python backtester.py --help
python backtester.py --payload-mode fixed --start-date 2014-01-01 --end-date 2025-12-31
python backtester.py --payload-mode random --iterations 50 --seed 42
python backtester.py --payload-file my_payload.json --portfolio-name my_portfolio
python backtester.py --refresh-cache
```

### 5) 全基金相關係數熱力圖

```powershell
python analysis_on_all.py --help
python analysis_on_all.py --start-date 2018-01-01 --end-date 2025-12-31
python analysis_on_all.py --output chart/corr_heatmap.png --vmin -0.2 --vmax 1.0
```

### 6) 泡泡圖

```powershell
python bubble_chart.py --help
python bubble_chart.py --payload-mode fixed
python bubble_chart.py --payload-mode random --equity-share 0.7 --fi-share 0.3
python bubble_chart.py --payload-file my_payload.json --output chart/custom_bubble.png
```

### 7) NAV overlay 圖

```powershell
python NAV_clean.py --help
python NAV_clean.py --start-date 2010-01-01 --threshold 50
python NAV_clean.py --nav-dir raw_data/Daily_NAV --output-dir chart
python NAV_clean.py --skip-group-charts
```

## 常用工作流

1. 先更新原始資料
```powershell
python main.py --skip-research
```

2. 再生成研究資料（不重抓）
```powershell
python main.py --skip-fetch
```

3. 跑回測
```powershell
python backtester.py --payload-mode fixed
```

4. 出圖
```powershell
python analysis_on_all.py
python bubble_chart.py
python NAV_clean.py
```

## 目錄說明

- `src/`: 核心模組（fetch/research/clear/ISIN/chart_utils）
- `raw_data/`: API 原始 JSON
- `research_db/`: 研究結果（以 ISIN 分資料夾）
- `cache/`: 回測快取
- `chart/`: 一般分析圖輸出
- `SAA/`: 回測報告輸出
- `documents/`: 開發紀錄

## 重構重點（本次）

- 主流程修正：`main.py` 會正確執行 research，而不是只跑 `ISIN.py`
- 移除多數硬編碼參數，改成 `argparse`
- 修正 NAV 檔名解析與 ETF NAV 欄位讀取
- `research_db` 結構改為 `research_db/<ISIN>/info.json`
- 曝險彙總改為讀 `info.json` 的 `name` 欄位，不依賴資料夾名稱
