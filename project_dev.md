# 開發日誌
---
## 2025/07/23
現在的狀況是兩個API還沒抓(fund info, actual size of country, sector)。 
   
**比較重要的事情**
1. NAV抓不完整
    - 有大概一半抓不到 有error 不知道為啥
2. 我需要加緊腳步，其他東西都還沒抓好  
  
**處理方法**:
- 開一個csv紀錄
    1. 第一列: fund_name
    2. 第二列: ISIN code
    3. 第三列: True/False(抓取成功與否)
    4. 第四列: API連結
- Observation of Fund_info json
    - "portfolioAnalysisByCountry": 國家比例
    - "portfolioAnalysisBySector": 行業比例
    - "fundHoldings": 持有股票比例(不完整)

## 2025/07/24
測好兩個API了，準備好要抓下來，然後開一個CSV(fetch_check.csv)來確認  
Result:
- 抓到全部fund的資料了
- 寫了爆搜param的爬蟲(避免系統升級，以及國家位置locate錯)
- 存進raw_data
- 開了一個csv來監測抓取historical data、Product data的結果。
  
## 2025/7/25  
今天要把fund info的資訊用jupyter notebook寫出來，讓大家比較好操作，也可以讓大家先看到一定程度的成果  
### 目標:
- 分析fund_info資訊
    1. 債券類
    2. 股票類
    3. 原物料
- 國家組成分析
- 實際大小    
  
有時間的話
- sector組成分析
- 持有標的分析

## 2025/07/30
### 目標
- holdings分析
- venv
- 穩定性測試

- 思考一下未來要甚麼功能
    - 組成排序  
今天弄好了venv，確定大家可以在同樣的環境用同樣的python版本執行。
現在main.py運行很穩定了，fetching加了一個新機制確保json也沒有抓歪。
果然還是要loose coupling會比較好，還好之前有把save這個動作拉出去。
sector跟國家分析已經完成，現在要來做holdings，比較麻煩一點。  