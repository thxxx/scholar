import pandas as pd
import os
import glob
import argparse
from datetime import datetime
from utils import upload_to_huggingface

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--typed", type=str, default="scholar", required=True)
    args = parser.parse_args()

    typed = args.typed

    if typed == "scholar":
        prefix = "scholar_search_results"
    elif typed == "linkedin":
        prefix = "linkedin_search_results"
    else:
        raise ValueError(f"Invalid typed: {typed}")

    pattern = f"{prefix}*.csv"
    csv_files = glob.glob(pattern)

    dfs = []
    for path in csv_files:
        try:
            df = pd.read_csv(path)
            dfs.append(df)
        except Exception as e:
            print(e, path)

    now_str = datetime.now().strftime("%Y_%m_%d_%H_%M")

    merged = pd.concat(dfs, ignore_index=True)
    out_path = f"{typed}_{now_str}.csv"

    print(f"\n===Total get : {len(merged)} ===\n")
    merged = merged.drop_duplicates(subset=["linkedin_id"], keep="first")
    print(f"\n===Total unique get : {len(merged)} ===\n")
    merged.to_csv(out_path, index=False, encoding="utf-8-sig")

    original_path = "linkedins_total.csv"
    current_df = pd.read_csv(original_path)
    new_df = pd.concat([current_df, merged], ignore_index=True)
    
    new_df = new_df.drop_duplicates(subset=["linkedin_id"], keep="first")
    print(f"\n===Total new user get : {len(new_df) - len(current_df)} ===\n")
    new_df.to_csv(original_path, index=False, encoding="utf-8-sig")

    upload_to_huggingface(original_path)
    print(f"\n===Upload to Hugging Face : {original_path} ===\n")

    # 🔥 여기서 읽은 것들 전부 삭제
    for path in csv_files:
        if path != out_path:   # 혹시 겹칠 가능성 방지
            os.remove(path)
