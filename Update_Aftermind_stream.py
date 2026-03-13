#!/usr/bin/env python3

from playwright.sync_api import sync_playwright
import requests
import os

PLAYLIST_FILE = "TCL.m3u"
CHANNEL_FILE = "Aftermind_Channels.txt"

FALLBACK = "https://raw.githubusercontent.com/benmoose39/YouTube_to_m3u/main/assets/moose_na.m3u"


# ===============================
# kanalen laden
# ===============================

def load_channels():

    channels = {}

    if not os.path.exists(CHANNEL_FILE):
        print("❌ Aftermind_Channels.txt ontbreekt")
        return channels

    with open(CHANNEL_FILE,"r",encoding="utf-8") as f:

        for line in f:

            line=line.strip()

            if not line or "|" not in line:
                continue

            parts=line.split("|")

            if len(parts)!=3:
                continue

            key=parts[0].strip()

            channels[key] = {
                "page":parts[1].strip(),
                "extinf":parts[2].strip()
            }

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

                if i+1<len(lines):

                    url=lines[i+1].strip()

                    if ".m3u8" in url:

                        print("⚠️ fallback:",url)
                        return url

    except Exception as e:

        print("fallback error:",e)

    return None


# ===============================
# streams detecteren (snelle versie)
# ===============================

def detect_streams(channels):

    streams={}

    with sync_playwright() as p:

        browser=p.chromium.launch(
            headless=True,
            args=["--no-sandbox","--disable-dev-shm-usage"]
        )

        context=browser.new_context(user_agent="Mozilla/5.0")

        pages={}

        # netwerk listener
        def handle_response(response):

            url=response.url

            if ".m3u8" in url and "token=" in url:

                for key in channels:

                    if key in url and key not in streams:

                        streams[key]=url
                        print("✅ gevonden:",key)

        # pagina's openen
        for key,data in channels.items():

            page=context.new_page()

            page.on("response",handle_response)

            pages[key]=page

            print("🔎 Laden:",data["page"])

            page.goto(data["page"],timeout=60000,wait_until="domcontentloaded")

        # streams laten laden
        for page in pages.values():

            page.wait_for_timeout(8000)

        browser.close()

    return streams


# ===============================
# playlist aanpassen
# ===============================

def update_playlist(streams,channels):

    if not os.path.exists(PLAYLIST_FILE):

        with open(PLAYLIST_FILE,"w",encoding="utf-8") as f:
            f.write("#EXTM3U\n")

    with open(PLAYLIST_FILE,"r",encoding="utf-8") as f:

        lines=f.readlines()

    for key,data in channels.items():

        extinf=data["extinf"]

        name=extinf.split(",")[-1].strip()

        stream=streams.get(key)

        if not stream:

            stream=get_fallback(name)

        if not stream:

            print("❌ geen stream:",name)
            continue

        found=False

        for i,line in enumerate(lines):

            if extinf in line:

                found=True

                if i+1<len(lines):

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

    print("🎵 TCL.m3u opgeslagen")


# ===============================
# main
# ===============================

print("🚀 Start snelle Aftermind updater")

channels=load_channels()

streams=detect_streams(channels)

update_playlist(streams,channels)
