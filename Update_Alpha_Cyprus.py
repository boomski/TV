from playwright.sync_api import sync_playwright

URL = "https://alphacyprus.com.cy/live"


def capture_stream(page):

    stream = None

    def handle_response(response):

        nonlocal stream

        if ".m3u8" in response.url and "alphacyp" in response.url:

            stream = response.url

    page.on("response", handle_response)

    try:

        page.goto(URL, timeout=60000)

        # wacht tot player geladen is
        page.wait_for_timeout(10000)

    except Exception as e:

        print("Page error:", e)

    page.remove_listener("response", handle_response)

    return stream


def main():

    print("🚀 Alpha Cyprus scraper gestart")

    with sync_playwright() as p:

        browser = p.chromium.launch(headless=True)

        page = browser.new_page()

        stream = capture_stream(page)

        browser.close()

    if stream:

        print("✅ Stream gevonden:\n")
        print(stream)

    else:

        print("❌ Geen stream gevonden")


if __name__ == "__main__":
    main()
