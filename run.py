from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException, WebDriverException, NoSuchElementException, JavascriptException
from selenium_stealth import stealth
from bs4 import BeautifulSoup
from collections import defaultdict
import pandas as pd
import csv

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                  "AppleWebKit/537.36 (KHTML, like Gecko) "
                  "Chrome/120.0.0.0 Safari/537.36",
    "Accept-Language": "ko,en;q=0.9",
}


# ---------- Selenium ----------
def build_driver(headless=True, user_agent=None):
    opts = Options()
    
    opts.add_argument('--headless')
    opts.add_argument('--no-sandbox')
    opts.add_argument('--disable-dev-shm-usage')
    
    opts.add_experimental_option('excludeSwitches', ['enable-automation', 'enable-logging'])
    opts.add_experimental_option('useAutomationExtension', False)
    
    opts.page_load_strategy = "eager"
    opts.add_argument("--disable-gpu")
    opts.add_argument("--window-size=1200,2400")
    opts.add_argument("--lang=ko-KR")

    # 리소스 최소화(이미지/CSS 차단)
    prefs = {
        "profile.managed_default_content_settings.images": 2,
        "profile.managed_default_content_settings.stylesheets": 2,
        "profile.managed_default_content_settings.cookies": 1,
        "profile.managed_default_content_settings.javascript": 1,
    }
    opts.add_experimental_option("prefs", prefs)
    if user_agent:
        opts.add_argument(f"--user-agent={user_agent}")
    driver = webdriver.Chrome(options=opts)
    try:
        driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
            "source": "Object.defineProperty(navigator,'webdriver',{get:()=>undefined});"
        })
    except Exception:
        pass
    driver.set_page_load_timeout(2)
    
    stealth(driver,
        languages=['en-US', 'en'],
        vendor='Google Inc.',
        platform='Win32',
        webgl_vendor='Intel Inc.',
        renderer='Intel Iris OpenGL Engine',
        fix_hairline=True
    )
    
    return driver

drv = build_driver()

import time
import re
import random

keywords = [
    "model",
    "generative",
    "llm",
    "multimodal",
    "inference",
    "benchmark",
    "image",
    "audio",
    "tts",
    "diffusion",
    "adversarial",
    "network",
    "representation",
    "training",
    "loss",
    "sampling",
    "agent",
    "foundation",
    "recommendation",
    "robust",
    "cnn",
    "learning",
    "rl",
    "detection",
    "retrieval",
    "denoising",
    "language",
    "video",
    "speech",
    "reasoning",
    "policy"
]

surnames = [
  { "surname": "Kim",   "ratio_percent": 13.5 },
  { "surname": "Lee",   "ratio_percent": 8.5 },
  { "surname": "Park",  "ratio_percent": 5.5 },
  { "surname": "Jung",  "ratio_percent": 3.5 },
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
  { "surname": "Hong",  "ratio_percent": 1.5 }
]

def sample_hap():
    names = [item["surname"] for item in surnames]
    weights = [item["ratio_percent"] for item in surnames]
    return [random.choices(keywords, k=1)[0].lower(), random.choices(names, weights=weights, k=1)[0].lower()]

def random_float(min_val, max_val):
    return random.uniform(min_val, max_val)

author_list = defaultdict(list)
paper_list = defaultdict(list)
searched_combs = []

pds = pd.read_csv("output.csv").to_dict(orient="records")
datas = pds

def get_titles_and_author_ids(bsoup):
    papers = bsoup.find_all("div", class_=re.compile("gs_scl"))
    for paper in papers:
        try:
            title = paper.find("h3", class_=re.compile("gs_rt")).text
            author_ids = [re.sub('&hl=en&oi=sra', '', a['href']) for a in paper.find("div", class_=re.compile("gs_a")).find_all("a")]
            author_names = [a.text for a in paper.find("div", class_=re.compile("gs_a")).find_all("a")]
            matches = re.findall(r"20\d{2}", paper.find("div", class_=re.compile("gs_a")).text)

            try:
                ctns = paper.find("div", class_=re.compile("gs_flb")).find_all("a")
                citation_nums = 0
                if len(ctns)>2:
                    cttext = ctns[2].text
                    if "Related" not in cttext:
                        cttext = cttext[len("Cited by "):]
                        if cttext.isdigit():
                            citation_nums = int(cttext)
                
                paper_year = 0
                if len(matches)>0 and matches[-1].isdigit():
                    paper_year = matches[-1]
                    paper_year = int(paper_year)
            except Exception as e:
                print("In citation number error ", e)
                citation_nums = 0
                paper_year = 0
    
            for ai in range(len(author_ids)):
                author_list[author_ids[ai]].append(title)
                datas.append({
                    "title": title,
                    "author_id": author_ids[ai],
                    "author_names": author_names[ai],
                    "paper_year": paper_year,
                    "citation_nums": citation_nums
                })
        except Exception as e:
            print("In paper error ", e)
            return False
    return True

count = len(datas)
scrape_count = 0
for i in range(100):
    rdns = sample_hap()
    k = rdns[0]
    n = rdns[1]

    indexes = random.sample([b for b in range(50)], k=15)
    for idx in indexes:
        scrape_count += 1
        searched_combs.append(f"{k}_{n}_{idx}")
        pn = idx*10
        try:
            drv.get(f"https://scholar.google.com/scholar?start={pn}?hl=en&as_sdt=0%2C5&as_ylo=2020&q={k}+{n}&btnG=")
            time.sleep(7.0)
            
            html = drv.page_source
            soup = BeautifulSoup(html, "html.parser")

            assert "solving the above CAPTCHA" not in soup.text
        except Exception as e:
            print("error ", e)
            time.sleep(3000.0)
            continue
        is_ok = get_titles_and_author_ids(soup)
        if count == len(datas):
            print("No new data found", k, n)
        print("Data lens : ", len(datas))
        df = pd.DataFrame(datas)
        df.to_csv("output.csv", index=False)
        sdf = pd.DataFrame(searched_combs)
        sdf.to_csv("searched_combs.csv", index=False)
        if not is_ok:
            time.sleep(3000.0)
        
        # 40번 크롤링 하고나면 5분간 쉬기
        if scrape_count % 30 == 29:
            print("\n\nSleeping for 5 minutes\n\n")
            time.sleep(random_float(270.0, 340.0))
        time.sleep(random_float(15.0, 24.0))
        count = len(datas)