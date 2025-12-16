from bs4 import BeautifulSoup, Comment
from openai import OpenAI
from tqdm import tqdm
import pandas as pd
import requests
import json
import os
import re
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time

from utils import upload_to_huggingface, build_driver

client = OpenAI(
    api_key="",
    base_url="https://api.x.ai/v1/",
)

df = pd.read_csv("most_recent_total_detail_profiles_with_homepage.csv")
print(len(df))

def return_text(soup):
    NOISE_ID_RE = re.compile(
        r"^(actionbar|jp-|jetpack|wpgroho|grofiles|wp-emoji|comment-|bilmur|follow-bubble)",
        re.I,
    )

    GENERIC_TAGS = [
        "div", "section", "article", "main",
        "header", "footer", "nav", "span", "p"
    ]

    # Common "noisy" attributes added by frameworks/trackers/renderers
    DROP_ATTR_PREFIXES = ("data-", "aria-")
    DROP_ATTR_NAMES = {
        "role", "rel", "target", "tabindex",
        # "itemprop", "itemscope", "itemtype",
        "contenteditable", "draggable", "spellcheck",
        "loading", "decoding", "fetchpriority",
        "srcset", "sizes", "integrity", "crossorigin",
        "referrerpolicy", "nonce",
        "width", "height",
    }
    ON_EVENT_ATTR_RE = re.compile(r"^on[a-z]+$", re.I)

    def strip_noisy_nodes_and_attrs(root):
        # Remove comments
        for c in root.find_all(string=lambda s: isinstance(s, Comment)):
            c.extract()

        # Remove whole noisy tags
        for t in root.find_all(["script", "style", "noscript", "template", "svg", "canvas"]):
            t.decompose()

        # Remove noisy attributes
        for t in root.find_all(True):
            attrs = list(t.attrs.keys())
            for k in attrs:
                kl = k.lower()

                # Drop inline event handlers like onclick/onload/...
                if ON_EVENT_ATTR_RE.match(kl):
                    t.attrs.pop(k, None)
                    continue

                # Drop data-*, aria-*
                if any(kl.startswith(p) for p in DROP_ATTR_PREFIXES):
                    t.attrs.pop(k, None)
                    continue

                # Drop known noisy attributes
                if kl in DROP_ATTR_NAMES:
                    t.attrs.pop(k, None)
                    continue

    def remove_class_style_regex(html: str) -> str:
        # Remove class/style in both quote styles
        html = re.sub(r"\sclass=\"[^\"]*\"", "", html)
        html = re.sub(r"\sclass='[^']*'", "", html)
        html = re.sub(r"\sstyle=\"[^\"]*\"", "", html)
        html = re.sub(r"\sstyle='[^']*'", "", html)
        return html

    def shrink_html_tokens(html) -> str:
        # First pass: remove noisy nodes/attrs (framework/tracker bloat)
        strip_noisy_nodes_and_attrs(html)

        # Second pass: remove Jetpack/WordPress-ish noisy blocks by id/class pattern
        for t in list(html.find_all(True)):
            if t is None:
                continue

            tid = t.get("id") or ""
            if tid and NOISE_ID_RE.match(tid):
                t.decompose()
                continue

            classes = " ".join(t.get("class", [])) if t.get("class") else ""
            if classes and NOISE_ID_RE.search(classes):
                t.decompose()
                continue

        s = str(html)

        # Normalize whitespace
        s = s.replace("\t", "")
        s = re.sub(r"\n+", "\n", s)
        s = re.sub(r"[ ]{2,}", " ", s)

        # Collapse generic tags
        for tag in GENERIC_TAGS:
            s = re.sub(fr"<{tag}(\s[^>]*)?>", "<>", s)
            s = re.sub(fr"</{tag}>", "</>", s)

        # Collapse empty generic pairs
        s = re.sub(r"<>\s*</>", "<>", s)

        # Remove inter-tag whitespace
        s = re.sub(r">\s+<", "><", s)

        return s.strip()

    # Usage
    body = soup.find("body")
    sp = shrink_html_tokens(body)
    sp = remove_class_style_regex(sp)
    
    return sp

prompt = """
You are an information extraction assistant.

Below is a raw HTML document of a person's profile website.
Your task is to extract the following attributes **only if they are explicitly present in the HTML**.
Do NOT infer, guess, or hallucinate any information.

If an attribute cannot be found with reasonable certainty, return `None` for that field.

### Attributes to extract
- email: A contact email address of the owner found in the HTML (e.g., mailto links or visible text). only the owner's email address, not other people.
- related_links: a list of links that appear to be related to the exact person. (e.g. linkedin, github, cv, blog, sns, etc.). Do not include every single paper, citation, project, labs or company links.
- bio: A short biography or description text describing the person, company, or project. Write it in the first person. At leat 3 sentences, at most 6 sentences.
e.g. I am the researcher who is interested in ...
- page_type: If current html is not a profile page, return the type of the page. e.g. "company", "blog", "other", "labs", etc.
If is not a profile page, return None for all the other attributes.
- company_experiences: A list of company experiences of the owner. include the company name, title(Role), start date, end date.
ex) 
"company_experiences": [
    {
      "company_name": "Company A",
      "title": "Reseach Scientist, TTS end LLM optimization",
      "start_date": "2020-07",
      "end_date": "2021-04"
    },{
      "company_name": "Los University",
      "title": "Assistant professor",
      "start_date": "2019-10",
      "end_date": "2018-02"
    }, etc
]
- education: A list of education experiences of the owner. include the school name, degree, start date, end date. only include BS, MS, PhD. no 
ex)
"education": [
    {
      "school_name": "School A",
      "degree": "Ph.D. in Computer Science",
      "start_date": "2018-11",
      "end_date": "2022-01"
    }
]

Write date in format "YYYY-MM"

### Output format
Return a **valid JSON object** exactly in the following format:

{
  "email": string | None,
  "related_links": list[string] | None,
  "bio": string | None,
  "page_type": string,
  "company_experiences": list[dict] | None,
  "education": list[dict] | None,
}

### Rules
- Use `None` (not null, not empty string) if the value is missing
- For `related_links`, return `None` if no relevant links are found
- Do not include duplicate links
- Do not include navigation-only or irrelevant links (e.g., privacy policy, terms)
- Preserve the original text as-is (do not paraphrase)
- Do not add any explanations or extra text outside the JSON
- Only include in related_links of a list of links that appear to be related to the exact person. (e.g. linkedin, github, cv, blog, sns, etc.). Do not include every single paper, citation, project, labs or company links.

""" 

def calc_cost_with_cache(
    usage,
    input_price_per_1k,
    output_price_per_1k,
    input_price_per_cached_1k,
):
    # prompt
    total_prompt = usage.prompt_tokens
    cached = usage.prompt_tokens_details.cached_tokens or 0
    billable_prompt = max(total_prompt - cached, 0)

    # completion
    completion = usage.completion_tokens

    input_cost = billable_prompt / 1000 * input_price_per_1k + cached / 1000 * input_price_per_cached_1k
    output_cost = completion / 1000 * output_price_per_1k

    return {
        "prompt_tokens_total": total_prompt,
        "prompt_tokens_cached": cached,
        "prompt_tokens_billable": billable_prompt,
        "completion_tokens": completion,
        "input_cost_usd": input_cost,
        "output_cost_usd": output_cost,
        "total_cost_usd": input_cost + output_cost,
    }


PRICES = {
    "input": 0.0002,
    "output": 0.0005,
    "cached": 0.00005,
}

drv = build_driver()

import os
import re
import json
import time
import traceback
from datetime import datetime

import pandas as pd
from tqdm import tqdm
from bs4 import BeautifulSoup

from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


# ----------------------------
# Helpers
# ----------------------------
def now_str():
    return datetime.now().strftime("%Y_%m_%d_%H_%M_%S")


def safe_str(x):
    if x is None or (isinstance(x, float) and pd.isna(x)):
        return ""
    return str(x)


def default_output(home_link: str):
    return {
        "email": None,
        "related_links": [home_link] if home_link else [],
        "bio": None,
        "page_type": None,
        "company_experiences": [],
        "education": [],
    }


def extract_json_from_llm(text: str):
    """
    LLM이 JSON만 주면 그대로 파싱.
    JSON 앞뒤로 설명이 붙는 경우도 많아서, 가장 바깥 { ... } 혹은 [ ... ] 블록을 찾아 파싱 시도.
    """
    if text is None:
        raise ValueError("LLM output is None")

    text = text.strip()

    # 1) 그냥 JSON 파싱 시도
    try:
        return json.loads(text)
    except Exception:
        pass

    # 2) ```json ... ``` 형태 제거
    fenced = re.search(r"```(?:json)?\s*(\{.*\}|\[.*\])\s*```", text, re.DOTALL)
    if fenced:
        return json.loads(fenced.group(1))

    # 3) 가장 큰 {...} 덩어리 찾기 (greedy)
    brace = re.search(r"(\{.*\})", text, re.DOTALL)
    if brace:
        return json.loads(brace.group(1))

    # 4) 배열로 올 수도
    bracket = re.search(r"(\[.*\])", text, re.DOTALL)
    if bracket:
        return json.loads(bracket.group(1))

    raise ValueError(f"Could not parse JSON from LLM output. Head={text[:120]!r}")


def normalize_output(obj, home_link: str):
    """
    obj는 dict/str 등 다양한 형태일 수 있음.
    dict로 만들고, 키 누락 보정 + 타입 보정.
    """
    if isinstance(obj, str):
        obj = extract_json_from_llm(obj)

    if not isinstance(obj, dict):
        raise ValueError(f"Parsed output is not dict: {type(obj)}")

    out = default_output(home_link)

    # merge
    for k in out.keys():
        if k in obj:
            out[k] = obj[k]

    # 타입 보정
    if out["email"] == "" or out["email"] == "None":
        out["email"] = None

    if out["bio"] == "" or out["bio"] == "None":
        out["bio"] = None

    if out["page_type"] == "" or out["page_type"] == "None":
        out["page_type"] = None

    if out["related_links"] is None:
        out["related_links"] = []
    elif isinstance(out["related_links"], str):
        out["related_links"] = [out["related_links"]]

    if out["company_experiences"] is None:
        out["company_experiences"] = []
    if out["education"] is None:
        out["education"] = []

    # home_link는 최소 포함
    if home_link and home_link not in out["related_links"]:
        out["related_links"].append(home_link)

    return out


def dump_jsonl(path, rows):
    with open(path, "a", encoding="utf-8") as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")


# ----------------------------
# Main loop (completed)
# ----------------------------
total_dollars = 0.0
results = []          # 성공/실패 포함 전체 로그
success_rows = []     # 파싱 성공 결과만 별도
failed_rows = []      # 실패 로그만 별도

# 중간 저장 파일들
run_id = now_str()
out_dir = "outputs"
os.makedirs(out_dir, exist_ok=True)

jsonl_path = os.path.join(out_dir, f"extracted_{run_id}.jsonl")
fail_jsonl_path = os.path.join(out_dir, f"failed_{run_id}.jsonl")
csv_path = os.path.join(out_dir, f"extracted_{run_id}.csv")
cost_csv_path = os.path.join(out_dir, f"cost_{run_id}.csv")

# 비용 로그
cost_logs = []

# 이 루프 밖에 prompt 초기화가 있다면 여기선 prompt를 row마다 새로 만들거나,
# 혹은 "base_prompt"를 따로 두고 base_prompt + doc 형태로 추천.
base_prompt = prompt  # 너가 이미 만들어둔 prompt를 base로 둔다고 가정

SAVE_EVERY = 100
PAGE_LOAD_TIMEOUT_SEC = 30
AFTER_GET_SLEEP_SEC = 2
RETRY = 2

for i in tqdm(range(10, 30)):
    data = df.iloc[i]
    hl = data.get("home_link", None)

    if pd.isna(hl) or not safe_str(hl).strip():
        continue

    url = safe_str(hl).strip()

    row_meta = {
        "row_index": int(i),
        "author_id": safe_str(data.get("author_id", "")),
        "name": safe_str(data.get("name", "")),
        "home_link": url,
    }

    # LinkedIn은 스킵/별도 처리
    if "linkedin.com" in url:
        output_dict = default_output(url)
        output_dict.update({
            "page_type": "linkedin",
        })

        results.append({**row_meta, "ok": True, "output": output_dict, "error": None})
        success_rows.append({**row_meta, **output_dict, "ok": True})

        # 중간 저장
        if len(results) % SAVE_EVERY == 0:
            dump_jsonl(jsonl_path, results[-SAVE_EVERY:])
            pd.DataFrame(success_rows).to_csv(csv_path, index=False, encoding="utf-8-sig")
            pd.DataFrame(cost_logs).to_csv(cost_csv_path, index=False, encoding="utf-8-sig")
        continue

    # --- Fetch + extract with retries ---
    last_err = None
    extracted_text = None

    for attempt in range(RETRY + 1):
        try:
            drv.get(url)
            time.sleep(AFTER_GET_SLEEP_SEC)

            # body 태그 등장 대기
            WebDriverWait(drv, PAGE_LOAD_TIMEOUT_SEC).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )

            html = drv.page_source
            soup = BeautifulSoup(html, "html.parser")

            extracted_text = return_text(soup)  # 이미 있다고 가정
            if not extracted_text or len(extracted_text.strip()) < 50:
                raise ValueError("Extracted text too short (maybe blocked / empty page).")

            break  # 성공
        except Exception as e:
            last_err = e
            if attempt < RETRY:
                time.sleep(1.5 * (attempt + 1))
                continue

    if extracted_text is None:
        err_msg = f"Failed to fetch/extract after retries: {repr(last_err)}"
        fail_obj = {**row_meta, "ok": False, "stage": "fetch", "error": err_msg}
        results.append(fail_obj)
        failed_rows.append(fail_obj)
        dump_jsonl(fail_jsonl_path, [fail_obj])
        continue

    # --- Build prompt per row ---
    row_prompt = base_prompt + f"""
### owner's name
{safe_str(data.get('name', ''))}

### HTML Document
{extracted_text}
"""

    # --- LLM call + parse ---
    try:
        response = client.chat.completions.create(
            model="grok-4-1-fast-non-reasoning",
            messages=[
                {"role": "system", "content": "You are a html extractor. Return ONLY valid JSON."},
                {"role": "user", "content": row_prompt},
            ],
        )

        raw_output = response.choices[0].message.content

        # 비용 계산
        try:
            cost = calc_cost_with_cache(
                response.usage,
                PRICES["input"],
                PRICES["output"],
                PRICES["cached"],
            )
            dollars = float(cost["total_cost_usd"])
        except Exception:
            cost = None
            dollars = 0.0

        total_dollars += dollars
        cost_logs.append({
            **row_meta,
            "total_cost_usd": dollars,
            "usage": json.dumps(getattr(response, "usage", {}), ensure_ascii=False, default=str),
        })

        # 출력 정규화
        output_dict = normalize_output(raw_output, url)

        results.append({
            **row_meta,
            "ok": True,
            "output": output_dict,
            "raw_output": raw_output,
            "error": None,
        })

        # tabular로도 저장하기 쉽게 flatten
        success_rows.append({
            **row_meta,
            "ok": True,
            "email": output_dict.get("email"),
            "bio": output_dict.get("bio"),
            "page_type": output_dict.get("page_type"),
            "related_links": json.dumps(output_dict.get("related_links", []), ensure_ascii=False),
            "company_experiences": json.dumps(output_dict.get("company_experiences", []), ensure_ascii=False),
            "education": json.dumps(output_dict.get("education", []), ensure_ascii=False),
        })

        print(output_dict)

    except Exception as e:
        err_msg = f"LLM/parse failed: {repr(e)}"
        fail_obj = {
            **row_meta,
            "ok": False,
            "stage": "llm_or_parse",
            "error": err_msg,
            "traceback": traceback.format_exc(limit=3),
        }
        results.append(fail_obj)
        failed_rows.append(fail_obj)
        dump_jsonl(fail_jsonl_path, [fail_obj])
        continue

    # --- periodic save ---
    if len(results) % SAVE_EVERY == 0:
        dump_jsonl(jsonl_path, results[-SAVE_EVERY:])
        pd.DataFrame(success_rows).to_csv(csv_path, index=False, encoding="utf-8-sig")
        pd.DataFrame(cost_logs).to_csv(cost_csv_path, index=False, encoding="utf-8-sig")

# final save
dump_jsonl(jsonl_path, results)  # 전체 덤프(이미 일부 append 했어도 상관없으면 이렇게)
pd.DataFrame(success_rows).to_csv(csv_path, index=False, encoding="utf-8-sig")
pd.DataFrame(cost_logs).to_csv(cost_csv_path, index=False, encoding="utf-8-sig")

print(f"\nDONE. success={len(success_rows)}, failed={len(failed_rows)}")
print(f"Total cost (USD): {total_dollars:.6f}")
print("Saved:")
print(" -", jsonl_path)
print(" -", fail_jsonl_path)
print(" -", csv_path)
print(" -", cost_csv_path)
