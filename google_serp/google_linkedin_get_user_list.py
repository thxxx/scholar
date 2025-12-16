import requests
import pandas as pd
from tqdm import tqdm
import os
import argparse

api_key = ""
url = "https://api.scrapingdog.com/google"

keywords1 = {
    "Korea university": 1, 
    "고려대학교": 1, 
    "yonsei": 1, 
    "Yonsei university": 1, 
    "연세대학교": 1, 
    "snu": 2, 
    "Seoul National University": 2, 
    "서울대학교": 2, 
    "kaist": 0.7, 
    "카이스트": 0.7, 
    "postech": 0.2,
    "포스텍": 0.2,
}
# toss, naver, kakao
keywords2 = {
    '컴퓨터': 1,
    '공학': 1,
    'computer': 1,
    'science': 1,
    'data engineer': 1,
    'scientist': 1,
    'generative': 1,
    'engineer': 1, 
    'frontend':1, 
    'backend': 1, 
    'software': 1, 
    'deep': 1, 
    'machine': 1, 
    'researcher': 1, 
    'developer': 1, 
    'ml': 1,
    'machine learning': 1,
    'deep learning': 1,
    'founder': 1,
    'ops': 1,
    'typescript': 1,
    'python': 1,
    'java': 1,
    "product engineer": 1
}
# keywords2 = {
#     "google": 1,
#     "meta": 1,
#     "apple": 1,
#     "microsoft": 1,
#     "stanford": 1,
#     "mit": 1,
#     "berkeley": 1,
#     "cmu": 1,
# }

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
    
    for keyword2 in keywords2:
        print(f"\n\nStart for {keyword1}, {keyword2}!!\n\n")
        for idx in tqdm(range(0, int(100 * keywords2[keyword2]))):
            params = {
                "api_key": api_key,
                "query": f"{keyword1} {keyword2} site:linkedin.com/in",
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
                    print(f"End For {keyword1} {keyword2} {idx} - {len(datas)}")
                    break
                for d in data['organic_results']:
                    name = d['title']
                    link = d['link']
                    snippet = d['snippet']

                    input_data = {
                        'name': name,
                        'snippet': snippet,
                        'link': link,
                        # 'source': d['source']
                        'source': ""
                    }
                    datas.append(input_data)
                
                if idx == 1:
                    print(f"\nStart for total_results: {keyword1} {keyword2} - {data['search_information']}\n\n")
            
                print(f"Search : {keyword1} {keyword2} | {idx}th page - length: {len(datas)}")
            except Exception as e:
                print(f"Error [{keyword1} {keyword2} {idx}]: {e}")
                continue

            pd.DataFrame(datas).to_csv(filename, index=False)
        print("\n\nSAVE!!\n\n")

