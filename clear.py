import glob
import os

def delete_rawfile():
    for folder in ["raw_data/Daily_NAV", "raw_data/FUND_info"]:
        pattern = os.path.join(folder, "*.json")
        json_files = glob.glob(pattern)
        for fp in json_files:
            os.remove(fp)
        print(f"已刪除 {len(json_files)} 個 .json 檔：{folder}")
