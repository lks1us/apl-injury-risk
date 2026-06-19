"""Capture README screenshots from a running local server."""
from pathlib import Path

from playwright.sync_api import sync_playwright

BASE = "https://l1ksius.pythonanywhere.com"
OUT = Path(__file__).resolve().parent.parent / "docs" / "screenshots"
OUT.mkdir(parents=True, exist_ok=True)

PAGES = [
    ("dashboard.png", f"{BASE}/"),
    ("player-list.png", f"{BASE}/players/"),
    ("player-detail.png", f"{BASE}/players/1133/"),
]


def main():
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch()
        page = browser.new_page(viewport={"width": 1440, "height": 900})
        for filename, url in PAGES:
            page.goto(url, wait_until="networkidle")
            page.screenshot(path=str(OUT / filename), full_page=True)
            print(f"Saved {OUT / filename}")
        browser.close()


if __name__ == "__main__":
    main()
