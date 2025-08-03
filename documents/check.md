# 幹 基金有分類的問題 json type 不一樣 要手動檢查

### 總結
有4種狀態
1. 沒問題
2. 缺holdings
3. 缺country, holdings
4. 缺country, sector, holdings  

### 關鍵字
emeafundholdings
emeaRegionalBreakdown
emeaSectorBreakdown 
fundHoldings
portfolioAnalysisByCountry
portfolioAnalysisBySector

- 全部缺的(已經處理)
    1. holdings應該都是在emeafundholdings，格式很奇怪
    2. 國家在emeaRegionalBreakdown
    3. sector都在emeaSectorBreakdown  
- 缺holdings()
- 缺country, holdings()


### 觀察
初步觀察，cachedForRole: "per"會全部都沒有
-  全部都在emea
再觀察: 全部都抓到的是"fundRange": "HKUT"。  
其他三個有問題的都是"fundRange": "SICAV"。
全部都沒有的portfolioanalysis都會是null。
基本上，缺什麼就是去emea holdings拿，我現在要分辨出來三個的狀態。
先來處理cachedForRole: "per"
---
推論: 會不會只要"fundRange": "SICAV"，都會在emea holdings裡面

### 目前有四個資訊: meta data, sector, country, holdings
HK0000151891 沒問題  
HK0000055613 沒問題  
LU0169518387 全部都沒有 !  
LU0441854154 holdings 沒有  
LU0210526637 meta, country, holdings沒有  
LU1255011170 全部都沒有 !
LU0927678507 meta, country, holdings沒有  
LU0329204464 全部都沒有  
LU0210529656 holdings 沒有  
LU0972618572 meta, country, holdings沒有  
LU0955580203 全部都沒有  
LU0210528500 meta, country, holdings沒有  
LU0210536198 meta, country, holdings沒有  
LU0210536511 全部都沒有  
LU0210528922 全部都沒有  
LU2582001959 全部都沒有  
LU0329201957 全部都沒有  
LU0070217475 holdings 沒有  
LU2402382688 全部都沒有  
HK0000055597 holdings 沒有  
LU0210533179 全部都沒有  
LU0210532957 meta, country, holdings沒有  
LU0499112034 holdings 沒有  
LU0408846375 全部都沒有  
LU0406674159 holdings 沒有  
LU0344579056 holdings 沒有  
LU0513027705 全部都沒有  
LU0210527791 全部都沒有  













