from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
import time
import re

PLAYLIST_FILE = "Cycling.m3u"
BASE_URL = "https://tiz-cycling.tv"

options = Options()
options.add_argument("--headless=new")
options.add_argument("--no-sandbox")
options.add_argument("--disable-dev-shm-usage")

driver = webdriver.Chrome(options=options)

def get_video_links():
    driver.get(BASE_URL)
    time.sleep(5)

    driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
    time.sleep(3)

    links = []
    elements = driver.find_elements(By.CSS_SELECTOR, "a[href*='/video/'], a[href*='/watch/']")

    for el in elements:
        title = el.text.strip()
        url = el.get_attribute("href")

        if title and url and (title, url) not in links:
            links.append((title, url))

    return links[:20]


def get_stream(url):
    try:
        driver.get(url)
        time.sleep(4)

        html = driver.page_source
        match = re.search(r"https?://[^\s\"']+\.m3u8", html)

        if match:
            return match.group(0)
    except:
        pass

    return None


def main():
    videos = get_video_links()
    streams = []

    for title, url in videos:
        stream = get_stream(url)
        if stream:
            streams.append((title, stream))

    with open(PLAYLIST_FILE, "w", encoding="utf-8") as f:
        f.write("#EXTM3U\n")
        for title, stream in streams:
            f.write(f"#EXTINF:-1,{title}\n{stream}\n")

    print(f"Done: {len(streams)} streams")

    driver.quit()


if __name__ == "__main__":
    main()
