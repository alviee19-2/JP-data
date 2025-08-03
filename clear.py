import glob
import os
import shutil

def delete_raw_json():
    for folder in ["raw_data/Daily_NAV", "raw_data/FUND_info"]:
        pattern = os.path.join(folder, "*.json")
        json_files = glob.glob(pattern)
        for fp in json_files:
            os.remove(fp)
        print(f"已刪除 {len(json_files)} 個 .json 檔：{folder}")

def delete_research_db():
    folder = "research_db"

    # 確保資料夾存在
    os.makedirs(folder, exist_ok=True)

    # 遍歷裡面所有項目，檔案就 os.remove，資料夾用 shutil.rmtree
    for name in os.listdir(folder):
        path = os.path.join(folder, name)
        if os.path.isdir(path):
            shutil.rmtree(path)
        else:
            os.remove(path)
