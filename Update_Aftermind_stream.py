#!/usr/bin/env python3

from playwright.sync_api import sync_playwright
import requests
import re
import os

PLAYLIST_FILE = "TCL.m3u"
CHANNEL_FILE = "Aftermind_Channels.txt"

FALLBACK = "https://raw.githubusercontent.com/benmoose39/YouTube_to_m3u/main/assets/moose_na.m3u"


# ===============================
# kanalen laden
# ===============================

def load_channels():

    channels=[]

    if not os.path.exists(CHANNEL_FILE):
        print("❌ Aftermind_Channels.txt ontbreekt")
        return channels

    with open(CHANNEL_FILE,"r",encoding="utf-8") as f:

        for line in f:

            line=line.strip()

            if not line or "|" not in line:
                continue

            # split op laatste |
            extinf,page=line.rsplit("|",1)

            channels.append({
                "page":page.strip(),
                "extinf":extinf.strip()
            })

    return channels


# ===============================
# fallback zoeken
# ===============================

def get_fallback(name):

    try:

        r=requests.get(FALLBACK,timeout=20)

        lines=r.text.splitlines()

        for i,line in enumerate(lines):

            if name.lower() in line.lower():

                if i+1 < len(lines):

                    url=lines[i+1].strip()

                    if ".m3u8" in url:
                        return url

    except:
        pass

    return None


# ===============================
# stream detecteren
# ===============================

def get_stream(page_url):

    with sync_playwright() as p:

        browser=p.chromium.launch(
            headless=True,
            args=["--no-sandbox","--disable-dev-shm-usage"]
        )

        page=browser.new_page()

        try:

            page.goto(page_url,timeout=60000,wait_until="domcontentloaded")

            page.wait_for_timeout(8000)

            html=page.content()

            m=re.search(r'https://[^"\']+\.m3u8\?token=[^"\']+',html)

            if m:

                url=m.group(0)

                print("✅ Stream gevonden:",url)

                browser.close()

                return url

        except Exception as e:

            print("❌ Page error:",e)

        browser.close()

    return None


# ===============================
# playlist aanpassen
# ===============================

def update_playlist(channels):

    if not os.path.exists(PLAYLIST_FILE):

        with open(PLAYLIST_FILE,"w",encoding="utf-8") as f:
            f.write("#EXTM3U\n")

    with open(PLAYLIST_FILE,"r",encoding="utf-8") as f:

        lines=f.readlines()

    for c in channels:

        extinf=c["extinf"]

        name=extinf.split(",")[-1].strip()

        print("\n🔎 Scrapen:",name)

        stream=get_stream(c["page"])

        if not stream:

            print("⚠️ fallback gebruikt")

            stream=get_fallback(name)

        if not stream:

            print("❌ geen stream gevonden")
            continue

        found=False

        for i,line in enumerate(lines):

            if extinf in line:

                found=True

                if i+1 < len(lines):
                    lines[i+1]=stream+"\n"
                else:
                    lines.append(stream+"\n")

                print("🔄 geupdate:",name)

                break

        if not found:

            lines.append(extinf+"\n")
            lines.append(stream+"\n")

            print("➕ toegevoegd:",name)

    with open(PLAYLIST_FILE,"w",encoding="utf-8") as f:

        f.writelines(lines)

    print("\n🎵 TCL.m3u opgeslagen")


# ===============================
# main
# ===============================

print("🚀 Aftermind scraper gestart")

channels=load_channels()

print("📺 Kanalen:",len(channels))

update_playlist(channels)
