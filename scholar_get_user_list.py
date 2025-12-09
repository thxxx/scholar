import requests
import re
import pandas as pd
import random
import os
import time

keywords = [
    "model",
    "generative",
    "llm",
    "multimodal",
    "inference",
    "image",
    "audio",
    "tts",
    "diffusion",
    "flow matching",
    "adversarial",
    "neural network",
    "representation",
    "training",
    "loss function",
    "sampling",
    "agent",
    "large model",
    "recommendation",
    "robust",
    "cnn",
    "learning",
    "rl method",
    "detection",
    "retrieval",
    "denoising",
    "language model",
    "language processing",
    "video",
    "speech",
    "reasoning",
    "policy",
    "attention",
    "supervised",
    "autoregressive",
    "speech recognition",
    "synthesis",
    "probability",
]

surnames = [
  { "surname": "Kim",   "ratio_percent": 13.5 },
  { "surname": "Lee",   "ratio_percent": 8.5 },
  { "surname": "Park",  "ratio_percent": 5.5 },
  { "surname": "Jung",  "ratio_percent": 2.5 },
  { "surname": "Jeong",  "ratio_percent": 1.5 },
  { "surname": "Choi",  "ratio_percent": 3.5 },
  { "surname": "Cho",   "ratio_percent": 2.5 },
  { "surname": "Kang",  "ratio_percent": 2.5 },
  { "surname": "Yoon",  "ratio_percent": 2.5 },
  { "surname": "Lim",   "ratio_percent": 1.5 },
  { "surname": "Jang",  "ratio_percent": 1.5 },
  { "surname": "Han",   "ratio_percent": 1.5 },
  { "surname": "Oh",    "ratio_percent": 1.5 },
  { "surname": "Seo",   "ratio_percent": 1.5 },
  { "surname": "Shin",  "ratio_percent": 1.5 },
  { "surname": "Kwon",  "ratio_percent": 1.5 },
  { "surname": "Hwang", "ratio_percent": 1.5 },
  { "surname": "Ahn",   "ratio_percent": 1.5 },
  { "surname": "Song",  "ratio_percent": 1.5 },
  { "surname": "Ryu",   "ratio_percent": 1.5 },
  { "surname": "Hong",  "ratio_percent": 1.5 },
  { "surname": "Bae",  "ratio_percent": 1.0 },
  { "surname": "Woo",  "ratio_percent": 1.0 },
  { "surname": "Yun",  "ratio_percent": 1.0 },
  { "surname": "Son",  "ratio_percent": 1.0 },
]

def sample_hap():
    names = [item["surname"] for item in surnames]
    weights = [item["ratio_percent"] for item in surnames]
    return [random.choices(keywords, k=1)[0].lower(), random.choices(names, weights=weights, k=1)[0].lower()]


api_key = ""
url = "https://api.scrapingdog.com/google_scholar"

# datas = []
pds = pd.read_csv("output_onlydog.csv").to_dict(orient="records")
datas = pds
start_time = time.time()

for count in range(800):
    rdns = sample_hap()
    k = rdns[0]
    n = rdns[1]
    indexes = random.sample([b for b in range(100)], k=10)

    for page in indexes:
        try:
            params = {
                "api_key": api_key,
                "query": f"{k} {n}",
                "results": "20",
                "page": page,
                "language": "en",
                "lr": "lang_en",
                "as_ylo": "2019",
                "as_yhi": "2026",
                "scisbd": False
            }

            response = requests.get(url, params=params)

            if response.status_code == 200:
                data = response.json()
            else:
                print(f"Request failed with status code: {response.status_code}")

            for sc in data['scholar_results']:
                try:
                    title = sc['title']
                    author_ids = [a['author_id'] for a in sc['authors']]
                    author_names = [a['name'] for a in sc['authors']]
                    matches = re.findall(r"20\d{2}", sc['displayed_link'])
                    paper_year = matches[-1]

                    citation_nums = sc['inline_links']['cited_by']['total']
                    if "Related" not in citation_nums:
                        citation_nums = citation_nums[len("Cited by "):]
                    else:
                        citation_nums = "0"

                    for ai in range(len(author_ids)):
                        datas.append({
                            "title": title,
                            "author_id": author_ids[ai],
                            "author_names": author_names[ai],
                            "paper_year": int(paper_year) if paper_year else None,
                            "citation_nums": int(citation_nums)
                        })
                except Exception as e:
                    print(f"[{k} {n} {page}] In paper error ", e)
                    continue
            
            print(f"[{k} {n} {page} = {count} = taken time : {time.time() - start_time}] Data lens : ", len(datas))
            df = pd.DataFrame(datas)
            df.to_csv("output_onlydog.csv", index=False)
            if count % 10 == 9:
                df.to_csv("output_backup.csv", index=False)
        except Exception as e:
            print(f"[{k} {n} {page}] In Out error ", e)
            continue

print("\n\nStart get new user list\n\n")

for count in range(200):
    rdns = sample_hap()
    k = rdns[0]
    n = rdns[1]
    indexes = random.sample([b for b in range(50)], k=5)

    for page in indexes:
        try:
            params = {
                "api_key": api_key,
                "query": f"{k} {n}",
                "results": "20",
                "page": page,
                "language": "en",
                "lr": "lang_en",
                "as_ylo": "2024",
                "as_yhi": "2026",
                "scisbd": False
            }

            response = requests.get(url, params=params)

            if response.status_code == 200:
                data = response.json()
            else:
                print(f"Request failed with status code: {response.status_code}")

            for sc in data['scholar_results']:
                try:
                    title = sc['title']
                    author_ids = [a['author_id'] for a in sc['authors']]
                    author_names = [a['name'] for a in sc['authors']]
                    matches = re.findall(r"20\d{2}", sc['displayed_link'])
                    paper_year = matches[-1]

                    citation_nums = sc['inline_links']['cited_by']['total']
                    if "Related" not in citation_nums:
                        citation_nums = citation_nums[len("Cited by "):]
                    else:
                        citation_nums = "0"

                    for ai in range(len(author_ids)):
                        datas.append({
                            "title": title,
                            "author_id": author_ids[ai],
                            "author_names": author_names[ai],
                            "paper_year": int(paper_year) if paper_year else None,
                            "citation_nums": int(citation_nums)
                        })
                except Exception as e:
                    print(f"[{k} {n} {page}] In paper error ", e)
                    continue
            
            print(f"[{k} {n} {page}] Data lens : ", len(datas))
            df = pd.DataFrame(datas)
            df.to_csv("output_onlydog.csv", index=False)
        except Exception as e:
            print(f"[{k} {n} {page}] In Out error ", e)
            continue
        
