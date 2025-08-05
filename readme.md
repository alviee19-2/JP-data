## 開發介紹
  
專案目的:
- 抓取NAV並分析
    1. volatility
    2. returns(month, year)
    3. MDD
    4. 現在有各種數據厚
- 抓取sector比例
    1. 組合成最後想要的portfolio
- 抓取國家比例
    1. 組合成最後想要的portfolio
- 抓取手續費
    1. 計算其他成本
--- 
資料夾簡介:
- raw_data: fetch 所有的fund 利用ISIN  
- chart: 全部的NAV
- research_db: 存研究用的資料  
---
軟體架構:
- ISIN.py: 抓取資料夾下ISIN.py的csv裡的ISIN code，存入CUSIPS(list)
- main.py: fetch
- clean.py: 清理資料
- research.py 清理完資料後，進行圓餅圖分析
- backtester.py 用quantstats回測並生成報告
---  
事前準備:
git clone https://github.com/你的帳號/jp-data.git
cd jp-data

## 1. 建 venv(第一次就好)
py -3.13 -m venv .venv

## 2. 啟動 venv
Set-ExecutionPolicy -Scope Process -ExecutionPolicy RemoteSigned  
window:  
. .\.venv\Scripts\Activate.ps1
apple:  
source .venv/bin/activate

## 3. 安裝所有套件(第一次就好)
pip install -r requirements.txt

## 4. 執行程式
python main.py

## 5. 進research.ipynb
可以做你想做的事ㄌ