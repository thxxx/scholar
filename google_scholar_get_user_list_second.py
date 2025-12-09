import requests
import pandas as pd
from tqdm import tqdm

api_key = ""
url = "https://api.scrapingdog.com/google"

unis = {
    'korea.ac.kr': 1, 'yonsei': 1, 'snu': 2, 'kaist': 2, 'postech': 1
}
keywords = ["deep", "machine", "artificial intelligence", "computer"] # 각 3000명씩

datas = []

schools = ["MIT", "Stanford", "UC Berkeley", "CMU"]
surnames = {
    "kim":3.5, "park":2, "lee":2, "choi":1.5, "jung":1, "cho":1, "hwang":1
}

for school in schools:
    for surname in surnames:
        for idx in tqdm(range(1, int(50 * surnames[surname]))):
            params = {
                "api_key": api_key,
                "query": f"{school} {surname} site:https://scholar.google.com/citations",
                "country": "us",
                "page": f"{idx}",
                "advance_search": "true",
                "domain": "google.com"
            }

            response = requests.get(url, params=params)

            if response.status_code == 200:
                data = response.json()
            else:
                print(f"[{idx}] - Request failed with status code: {response.status_code}")

            try:
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
            except Exception as e:
                print(f"Error: {e}")
                continue

        pd.DataFrame(datas).to_csv('scholar_search_results_second.csv', index=False)