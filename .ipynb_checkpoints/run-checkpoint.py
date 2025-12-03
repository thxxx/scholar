from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException, WebDriverException, NoSuchElementException, JavascriptException
from selenium_stealth import stealth
from bs4 import BeautifulSoup
from collections import defaultdict
import pandas as pd
import csv
import time
import re
import random
import math

def human_sleep(base: float, jitter: float = 0.5):
    """
    base 초를 기준으로, +- jitter 범위에서 살짝 흔들어주는 휴식.
    예: base=5, jitter=2 -> 3~7초 사이로 랜덤.
    """
    duration = random.uniform(base - jitter, base + jitter)
    duration = max(0.5, duration)  # 최소 0.5초는 쉬기
    time.sleep(duration)

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                  "AppleWebKit/537.36 (KHTML, like Gecko) "
                  "Chrome/120.0.0.0 Safari/537.36",
    "Accept-Language": "ko,en;q=0.9",
}

def maybe_click_random_paper(driver, prob: float = 0.1):
    """
    prob 확률로 검색 결과 중 한 개 논문 상세 페이지에 들어갔다가,
    몇 초 있다가 back() 하는 사람스러운 행동.
    """
    if random.random() >= prob:
        return

    try:
        # 검색 결과 제목 링크 <h3.gs_rt a>
        links = driver.find_elements("css selector", "div.gs_r.gs_or.gs_scl h3.gs_rt a")
        if not links:
            return

        # 상위 몇 개 중 하나 랜덤 선택 (너무 밑은 잘 안 누른다고 가정)
        idx = random.randint(0, min(len(links) - 1, 7))
        target = links[idx]

        # 화면 중앙쯤으로 스크롤
        driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", target)
        time.sleep(random.uniform(0.8, 2.0))

        # 클릭
        target.click()

        # 읽는 척 대기
        dwell = random.uniform(3.0, 10.0)
        print(f"👀 Reading paper for {dwell:.1f} seconds")
        time.sleep(dwell)

        # 뒤로가기 (검색 결과로 복귀)
        driver.back()
        time.sleep(random.uniform(2.0, 5.0))

    except Exception as e:
        print("maybe_click_random_paper error:", e)



# ---------- Selenium ----------
def build_driver(user_agent=None):
    opts = Options()
    
    opts.add_argument('--headless=new')
    opts.add_argument('--no-sandbox')
    opts.add_argument('--disable-dev-shm-usage')
    
    opts.add_experimental_option('excludeSwitches', ['enable-automation', 'enable-logging'])
    opts.add_experimental_option('useAutomationExtension', False)
    
    opts.page_load_strategy = "eager"
    opts.add_argument("--disable-gpu")
    opts.add_argument("--window-size=1210,2420")
    opts.add_argument("--lang=ko-KR")

    # 리소스 최소화(이미지/CSS 차단)
    prefs = {
        "profile.managed_default_content_settings.images": 1,
        "profile.managed_default_content_settings.stylesheets": 1,
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
    driver.set_page_load_timeout(15)
    
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

def rebuild_driver():
    global drv
    try:
        drv.quit()
    except:
        pass
    print("🔄 Rebuilding driver...")
    drv = build_driver()
    time.sleep(random.uniform(3, 6))

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
    return random.randint(int(min_val), int(max_val))

author_list = defaultdict(list)
paper_list = defaultdict(list)
searched_combs = []

pds = pd.read_csv("output.csv").to_dict(orient="records")
datas = pds

def get_titles_and_author_ids(bsoup):
    papers = bsoup.find_all("div", class_=re.compile("gs_scl"))
    new_list = []
    print("papers len : ", len(papers))
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
                new_list.append({
                    "title": title,
                    "author_id": author_ids[ai],
                    "author_names": author_names[ai],
                    "paper_year": paper_year,
                    "citation_nums": citation_nums
                })
        except Exception as e:
            print("In paper error ", e)
            return []
    return new_list

def random_step_scroll(driver):
    """
    Scroll down with random steps, then slightly scroll up.
    Gives a more 'human' pattern (scrolling too far then correcting).
    """
    total_height = driver.execute_script("return document.body.scrollHeight")
    current_y = driver.execute_script("return window.pageYOffset || document.documentElement.scrollTop")

    # Scroll down a few random steps
    steps_down = random.randint(2, 5)
    for _ in range(steps_down):
        remaining = max(total_height - current_y, 0)
        if remaining <= 0:
            break

        step = int(remaining * random.uniform(0.05, 0.2))
        current_y += step
        driver.execute_script(f"window.scrollTo(0, {current_y});")
        time.sleep(random.uniform(0.4, 1.3))

    # Small scroll up (correction)
    up_step = int(total_height * random.uniform(0.02, 0.08))
    current_y = max(current_y - up_step, 0)
    driver.execute_script(f"window.scrollTo(0, {current_y});")
    time.sleep(random.uniform(0.4, 1.0))

def human_like_scroll(driver):
    """
    - 맨 위에서 약간만 내렸다가
    - 결과 중간/하단 쪽으로 점프
    - 살짝 위로 올리기
    - 마지막에 약간의 미세 스크롤
    """
    try:
        total_height = driver.execute_script("return document.body.scrollHeight") or 2000
        # 시작 위치
        current_y = driver.execute_script("return window.pageYOffset || document.documentElement.scrollTop") or 0

        # 1) 살짝 내린다
        step1 = random.randint(100, 400)
        current_y += step1
        driver.execute_script(f"window.scrollTo(0, {current_y});")
        human_sleep(random.uniform(0.5, 1.5))

        # 2) 중간쯤 점프
        mid_y = int(total_height * random.uniform(0.3, 0.6))
        driver.execute_script(f"window.scrollTo(0, {mid_y});")
        human_sleep(random.uniform(0.8, 2.0))

        # 3) 조금 아래로 몇 번 나눠서 내리기
        steps_down = random.randint(1, 3)
        for _ in range(steps_down):
            delta = int(total_height * random.uniform(0.05, 0.12))
            mid_y = min(total_height, mid_y + delta)
            driver.execute_script(f"window.scrollTo(0, {mid_y});")
            human_sleep(random.uniform(0.5, 1.4))

        # 4) 살짝 위로 올리기
        if random.random() < 0.7:
            up_delta = int(total_height * random.uniform(0.03, 0.08))
            mid_y = max(0, mid_y - up_delta)
            driver.execute_script(f"window.scrollTo(0, {mid_y});")
            human_sleep(random.uniform(0.5, 1.3))

        # 5) 마지막 미세 스크롤 (약간씩 위아래로)
        for _ in range(random.randint(1, 3)):
            jitter = random.randint(-120, 120)
            mid_y = min(max(0, mid_y + jitter), total_height)
            driver.execute_script(f"window.scrollTo(0, {mid_y});")
            human_sleep(random.uniform(0.3, 0.9))

    except Exception as e:
        print("scroll error:", e)


scrape_count = 0
for i in range(100):
    rdns = sample_hap()
    k = rdns[0]
    n = rdns[1]

    indexes = random.sample([b for b in range(50)], k=5)
    stop_count = random.randint(27, 32)
    for idx in indexes:
        start_time = time.time()
        scrape_count += 1
        searched_combs.append(f"{k}_{n}_{idx}")
        pn = idx*10
        try:
            time.sleep(random_float(3.0, 10.0))
            drv.get(f"https://scholar.google.com/scholar?hl=en&as_sdt=0%2C5&as_ylo=2020&q={k}+{n}&btnG=&start={pn}")
            time.sleep(random_float(5.0, 12.0))
            human_like_scroll(drv)

            maybe_click_random_paper(drv, prob=0.08)
            
            html = drv.page_source
            soup = BeautifulSoup(html, "html.parser")

            if "solving the above CAPTCHA" in soup.text:
                print("solving the above CAPTCHA")
                rebuild_driver()
                time.sleep(10800.0)
                continue
        except Exception as e:
            print("error ", e)
            rebuild_driver()
            time.sleep(180.0)
            continue
        
        new_data = get_titles_and_author_ids(soup)
        if len(new_data) == 0:
            print("No new data found", k, n)
            rebuild_driver()
            time.sleep(10800.0)
            continue
        # count how many unique author_ids are in the new data
        unique_author_ids = len(set([data["author_id"] for data in new_data]))
        print(f"Unique author ids : ", unique_author_ids)

        datas.extend(new_data)
        print(f"{scrape_count}th - Data lens : {len(datas)}, \nTime taken : {time.time() - start_time} seconds\n\n")
        df = pd.DataFrame(datas)
        df.to_csv("output.csv", index=False)
        sdf = pd.DataFrame(searched_combs)
        sdf.to_csv("searched_combs.csv", index=False)
        
        # 40번 크롤링 하고나면 5분간 쉬기
        if scrape_count == stop_count:
            rebuild_driver()
            time.sleep(random_float(300.0, 420.0))
            scrape_count = 0
            stop_count = random.randint(27, 32)
        time.sleep(random_float(15.0, 24.0))

