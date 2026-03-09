#!/usr/bin/env python3

from playwright.sync_api import sync_playwright
import requests
import os

PAGE_URL = "https://vpitvenvivo.com/watch-live/"
PLAYLIST_FILE = "TCL.m3u"

FALLBACK = "https://raw.githubusercontent.com/benmoose39/YouTube_to_m3u/main/assets/moose_na.m3u"

TARGET_LINE = '#EXTINF:-1 tvg-logo="https://raw.githubusercontent.com/boomski/TV-LOGO/refs/heads/main/Venezuela/VPI.jpg",🇻🇪 | VPI TV'


# ===============================
# detecteer m3u8
# ===============================

def detect_stream():

    streams = []

    with sync_playwright() as p:

        browser = p.chromium.launch(
            headless=True,
            args=["--no-sandbox","--disable-dev-shm-usage"]
        )

        context = browser.new_context(user_agent="Mozilla/5.0")
        page = context.new_page()

        def handle_response(response):

            url = response.url

            if ".m3u8" in url:

                if url not in streams:

                    streams.append(url)
                    print("gevonden:", url)

        page.on("response", handle_response)

        page.goto(PAGE_URL, timeout=60000, wait_until="domcontentloaded")

        page.wait_for_timeout(15000)

        browser.close()

    if not streams:
        return None

    # ===============================
    # voorkeur voor master playlist
    # ===============================

    for s in streams:

        if "master" in s.lower():

            print("🎯 master playlist gekozen")
            return s

    # ===============================
    # check of playlist varianten bevat
    # ===============================

    for s in streams:

        try:

            r = requests.get(s, timeout=10)

            if "#EXT-X-STREAM-INF" in r.text:

                print("🎯 master playlist gedetecteerd")
                return s

        except:
            pass

    # fallback: eerste stream
    print("⚠️ eerste gevonden stream gebruikt")

    return streams[0]


# ===============================
# fallback ophalen
# ===============================

def get_fallback():

    try:

        r = requests.get(FALLBACK, timeout=15)

        lines = r.text.splitlines()

        for i,line in enumerate(lines):

            if "VPI" in line.upper():

                if i+1 < len(lines):

                    url = lines[i+1].strip()

                    if ".m3u8" in url:

                        print("fallback gevonden:", url)
                        return url

    except Exception as e:

        print("fallback fout:", e)

    return None


# ===============================
# playlist aanpassen
# ===============================

def update_playlist(stream):

    if not os.path.exists(PLAYLIST_FILE):

        print("TCL.m3u niet gevonden")
        return

    with open(PLAYLIST_FILE,"r",encoding="utf-8") as f:

        lines = f.readlines()

    for i,line in enumerate(lines):

        if TARGET_LINE in line:

            if i+1 < len(lines):

                lines[i+1] = stream+"\n"

            else:

                lines.append(stream+"\n")

            print("stream vervangen")

            break

    with open(PLAYLIST_FILE,"w",encoding="utf-8") as f:

        f.writelines(lines)

    print("TCL.m3u opgeslagen")


# ===============================
# main
# ===============================

print("Start VPI updater")

stream = detect_stream()

if not stream:

    print("geen stream gevonden, fallback gebruiken")

    stream = get_fallback()

if stream:

    update_playlist(stream)

else:

    print("geen bruikbare stream")
