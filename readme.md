## 開發介紹
  
專案目的:
- 回測JP FUND，儲存報告
- 全部基金的NAV chart
- 全部基金的產業、國家、持股比例
---  
事前準備:
git clone https://github.com/你的帳號/jp-data.git
cd jp-data  
### 1. 建 venv(第一次就好)
py -3.13 -m venv .venv

### 2. 啟動 venv
Set-ExecutionPolicy -Scope Process -ExecutionPolicy RemoteSigned  
接下來分電腦系統:  
window:  
. .\.venv\Scripts\Activate.ps1
apple:  
source .venv/bin/activate  

### 3. 安裝所有套件(第一次就好)
pip install -r requirements.txt

### 4. 執行程式  
執行:  
現在所有核心資料處理邏輯都已整合到 `src/` 資料夾中，並由 `main.py` 統一協調執行。

```bash
python main.py
```

`main.py` 會依序執行以下步驟：

*   **資料清理**: 呼叫 `src/clear.py` 中的函式，刪除舊的原始資料 (`raw_data/Daily_NAV`, `raw_data/FUND_info`) 和研究分析結果 (`research_db/`)，確保每次執行都使用最新資料。
    *   `delete_raw_json()`: 刪除原始 JSON 檔案。
    *   `delete_research_db()`: 刪除研究資料庫內容。
*   **基金資料抓取**: 呼叫 `src/fetch.py` 中的 `run_fetch()` 函式，自動執行以下操作：
    *   從 `funds.csv` 獲取 ISIN 碼和基金名稱 (透過 `src/ISIN.py` 中的 `get_isin_data()` 函式)。
    *   從 J.P. Morgan 網站抓取基金的歷史淨值 (NAV) 和基本資訊。
    *   將抓取到的原始 JSON 資料儲存到 `raw_data/` 資料夾。
    *   記錄抓取狀態到 `fetch_check.csv`。
*   **基金研究分析**: 呼叫 `src/research.py` 中的 `run_research()` 函式，自動執行以下操作：
    *   讀取 `raw_data/` 中的基金基礎資訊。
    *   分析每支基金的資產管理規模 (AUM)、國家分佈、產業分佈和持股分佈。
    *   為國家、產業和持股生成圓餅圖 (JPG 格式)。
    *   將分析結果儲存到 `research_db/` 資料夾。

其他獨立腳本：
*   `NAV_clean.py`: 儲存到 `chart` 資料夾。將 NAV 一次畫在同一張圖，清楚看到每支基金。HTML 可以直接離開 IDE 點開。
*   `backtester.py`: 回測器有兩個可調整參數，結果會儲存至 `SAA` 資料夾下面。
    1.  `start_date`: 回測日期。
    2.  `name`: **每一次都要改名子，這是回測結果的檔案位置！**
    3.  `payload{}`: 裡面是我們有的基金，用小數點來決定權重。
