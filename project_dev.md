# 開發日誌
---
### 2025/07/23
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
