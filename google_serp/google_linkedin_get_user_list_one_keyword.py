import requests
import pandas as pd
from tqdm import tqdm
import os
import argparse

api_key = ""
url = "https://api.scrapingdog.com/google"

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--keyword1", type=str, default="", required=True)
    args = parser.parse_args()

    keyword1 = args.keyword1

    filename = f"linkedin_search_results_{keyword1.replace(' ', '_')}.csv"
    if os.path.exists(filename):
        datas = pd.read_csv(filename).to_dict(orient="records")
    else:
        datas = []
    
    print(f"\n\nStart for {keyword1}!!\n\n")
    for idx in tqdm(range(0, int(100))):
        params = {
            "api_key": api_key,
            "query": f"{keyword1} site:linkedin.com/in",
            "country": "kr",
            "page": f"{idx}",
            "advance_search": "false",
            "domain": "google.com",
            "language": "en"
        }

        response = requests.get(url, params=params)

        if response.status_code == 200:
            data = response.json()
        else:
            print(f"[{idx}] - Request failed with status code: {response.status_code}")
            pd.DataFrame(datas).to_csv(filename, index=False)
            break

        try:
            if len(data['organic_results']) < 2:
                print(f"End For {keyword1} {idx} - {len(datas)}")
                break
            for d in data['organic_results']:
                name = d['title']
                link = d['link']
                snippet = d['snippet']

                pat = 'linkedin.com/in/'
                linkedin_id = link[link.find(pat) + len(pat):].split("/")[0]

                input_data = {
                    'name': name,
                    'snippet': snippet,
                    'link': link,
                    'linkedin_id': linkedin_id,
                }
                print(name)
                datas.append(input_data)
            
            if idx == 1:
                print(f"\nStart for total_results: {keyword1} - {data['search_information']}\n\n")
        
            print(f"Search : {keyword1} | {idx}th page - length: {len(datas)}")
        except Exception as e:
            print(f"Error [{keyword1} {idx}]: {e}")
            continue

    pd.DataFrame(datas).to_csv(filename, index=False)
    print("\n\nSAVE!!\n\n")

