import pandas as pd
import os
import glob

prefix = "linkedin_search_results"
pattern = f"{prefix}*.csv"
csv_files = glob.glob(pattern)

dfs = []
for path in csv_files:
    try:
        df = pd.read_csv(path)
        dfs.append(df)
    except Exception as e:
        print(e, path)
merged = pd.concat(dfs, ignore_index=True)
merged.to_csv("linkedins2.csv", index=False, encoding="utf-8-sig")
