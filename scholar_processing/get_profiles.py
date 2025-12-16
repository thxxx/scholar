import requests
import pandas as pd
import json
import argparse
from tqdm import tqdm
import os
import time

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--idx", type=int, default=0, required=True)
    args = parser.parse_args()

    idx = args.idx

    api_key = "6933b34c7cb6bab8da12fbfd"
    url = "https://api.scrapingdog.com/google_scholar/author"

    df = pd.read_csv("from_coauthor_1211.csv")
    author_ids = df['author_id'].tolist()

    detail_profiles_filename = f"./middle_files/detail_profiles_{idx}.csv"
    extracted_authors_filename = f"./middle_files/extracted_authors_{idx}.csv"
    detail_profiles_json_filename = f"./middle_files/detail_profiles_{idx}.json"
    extracted_authors_json_filename = f"./middle_files/extracted_authors_{idx}.json"

    if os.path.exists(detail_profiles_filename):
        detail_profiles = pd.read_csv(detail_profiles_filename).to_dict(orient="records")
    else:
        detail_profiles = []

    if os.path.exists(extracted_authors_filename):
        extracted_authors = pd.read_csv(extracted_authors_filename).to_dict(orient="records")
    else:
        extracted_authors = []

    start_idx = idx * 1000
    end_idx = start_idx + 1000

    done_author_ids = set([d["author_id"] for d in detail_profiles])
    print(f"Done author ids: {len(done_author_ids)}")

    time.sleep(1)
    for aidx, author_id in tqdm(enumerate(author_ids[start_idx:end_idx])):
        try:
            if author_id in done_author_ids:
                continue

            params = {
                "api_key": api_key,
                "author_id": author_id,
                "page": 0,
            }

            response = requests.get(url, params=params)

            if response.status_code != 200:
                print(f"[author {author_id}] Request failed with status code: {response.status_code}")
                continue

            data = response.json()
            first_data = data  # co_authors, cited_by, author 정보는 첫 페이지 기준으로 사용
            all_articles = data.get("articles", []).copy()

            if len(data.get("articles", [])) == 20:
                for page in range(20, 101, 20):
                    params = {
                        "api_key": api_key,
                        "author_id": author_id,
                        "page": page,
                    }

                    response = requests.get(url, params=params)
                    if response.status_code != 200:
                        print(f"[author {author_id}] (page {page}) Request failed with status code: {response.status_code}")
                        break

                    page_data = response.json()
                    page_articles = page_data.get("articles", [])

                    if not page_articles:
                        break

                    all_articles.extend(page_articles)

                    if len(page_articles) < 20:
                        break

            author = first_data["author"]
            table = first_data["cited_by"]["table"]

            input_data = {
                "author_id": author_id,  # 원래 코드에 "author_id" 문자열이 들어가 있던 부분 수정
                "name": author.get("name"),
                "affiliations": author.get("affiliations"),
                "email": author.get("email"),
                "interests": [a["title"] for a in author.get("interests", [])],
                "image_thumbnail": author.get("thumbnail"),
                "articles": [
                    {
                        "title": d.get("title"),
                        "citation_id": d.get("citation_id"),
                        "publication": d.get("publication"),
                        "citation_count": d.get("cited_by", {}).get("value"),
                        "year": d["year"],
                    }
                    for d in all_articles if d.get("title") != ""
                ],
                "total_citation_count": table[0]["citations"]["all"] if len(table) > 0 else "",
                "since_2020_citation_count": table[0]["citations"]["since_2020"] if len(table) > 0 else "",
                "h_index": table[1]["h_index"]["all"] if len(table) > 1 else "",
            }
            detail_profiles.append(input_data)

            # co_authors도 첫 페이지 기준으로만 읽음
            co_authors = first_data.get("co_authors", [])
            if co_authors:
                for co_author in co_authors:
                    author_input_data = {
                        "from_author_id": author_id,
                        "author_id": co_author.get("author_id"),
                        "author_names": co_author.get("name"),
                        "affiliations": co_author.get("affiliations"),
                    }
                    extracted_authors.append(author_input_data)
            
            if aidx % 100 == 99:
                pd.DataFrame(detail_profiles).to_csv(detail_profiles_filename, index=False)
                pd.DataFrame(extracted_authors).to_csv(extracted_authors_filename, index=False)
        except Exception as e:
            print(f"[author {author_id}] Error: {e}")
            continue
    
    pd.DataFrame(detail_profiles).to_csv(detail_profiles_filename, index=False)
    pd.DataFrame(extracted_authors).to_csv(extracted_authors_filename, index=False)

    with open(detail_profiles_json_filename, "w") as f:
        json.dump(detail_profiles, f, indent=4)
    with open(extracted_authors_json_filename, "w") as f:
        json.dump(extracted_authors, f, indent=4)
