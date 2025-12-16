from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException, WebDriverException, NoSuchElementException, JavascriptException
from selenium_stealth import stealth
from bs4 import BeautifulSoup

scraping_dog_api_key = ""
huggingface_api_key = ""
grok_api_key = ""

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
    driver.set_page_load_timeout(12)
    
    stealth(driver,
        languages=['en-US', 'en'],
        vendor='Google Inc.',
        platform='Win32',
        webgl_vendor='Intel Inc.',
        renderer='Intel Iris OpenGL Engine',
        fix_hairline=True
    )
    
    return driver

def upload_to_huggingface(file_path):
    from huggingface_hub import HfApi
    from huggingface_hub import login

    api = HfApi()
    login(token=huggingface_api_key)


    api.upload_file(
        path_or_fileobj=file_path,
        path_in_repo=file_path.split("/")[-1],
        repo_id="Daniel777/harper",
        repo_type="model",
    )
