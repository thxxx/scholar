import requests
import pandas as pd
from tqdm import tqdm
import os
import argparse

api_key = ""
url = "https://api.scrapingdog.com/google"

keywords1 = {"MIT": 1, "Stanford": 1, "UC Berkeley": 1, "CMU": 1}
keywords2 = {"kim":3.5, "park":2, "lee":2, "choi":1.5, "jung":1, "cho":1, "hwang":1}

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--keyword1", type=str, default="", required=True)
    args = parser.parse_args()

    keyword1 = args.keyword1

    filename = f"scholar_search_results_second_{keyword1.replace(' ', '_')}.csv"

    if os.path.exists(filename):
        datas = pd.read_csv(filename).to_dict(orient="records")
    else:
        datas = []

    for keyword2 in keywords2:
        print(f"\n\nStart for {keyword1}, {keyword2}!!\n\n")
        for idx in tqdm(range(0, int(50 * keywords1[keyword1] * keywords2[keyword2]))):
            params = {
                "api_key": api_key,
                "query": f"{keyword1} {keyword2} site:https://scholar.google.com/citations",
                "country": "kr",
                "page": f"{idx}",
                "advance_search": "true",
                "domain": "google.com"
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
                    print(f"End For {keyword1} {keyword2} {idx} - {len(datas)}")
                    break
                for d in data['organic_results']:
                    name = d['title']
                    link = d['link']
                    author_id = link.split('/citations?user=')[1].split('&')[0]
                    snippet = d['snippet']

                    input_data = {
                        'name': name,
                        'author_id': author_id,
                        'snippet': snippet,
                        'link': link,
                        'source': d['source']
                    }
                    datas.append(input_data)
                
                if idx == 1:
                    print(f"\nStart for total_results: {data['search_information']['total_results']}\n\n")
                
                print(f"For {keyword1} {keyword2} {idx} - {len(datas)}")
            except Exception as e:
                print(f"Error [{keyword1} {keyword2} {idx}]: {e}")
                continue

        print("\n\nSAVE!!\n\n")
        pd.DataFrame(datas).to_csv(filename, index=False)