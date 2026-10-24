"""Capture high-res screenshots of the running app (localhost:8501) for the pitch deck."""
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "deck" / "shots"
OUT.mkdir(parents=True, exist_ok=True)
APP = "http://localhost:8501"
PAD = 16


def union_clip(page, locators):
    boxes = [l.bounding_box() for l in locators]
    boxes = [b for b in boxes if b]
    x0 = min(b["x"] for b in boxes) - PAD
    y0 = min(b["y"] for b in boxes) - PAD
    x1 = max(b["x"] + b["width"] for b in boxes) + PAD
    y1 = max(b["y"] + b["height"] for b in boxes) + PAD
    return {"x": max(x0, 0), "y": max(y0, 0), "width": x1 - max(x0, 0), "height": y1 - max(y0, 0)}


def shot(page, name, locators):
    locators[0].scroll_into_view_if_needed()
    page.wait_for_timeout(400)
    page.screenshot(path=str(OUT / name), clip=union_clip(page, locators))
    print("saved", name)


with sync_playwright() as p:
    browser = p.chromium.launch(channel="msedge")
    page = browser.new_page(viewport={"width": 1280, "height": 1200}, device_scale_factor=2)

    # 1. Audit input form
    page.goto(APP)
    page.get_by_text("Agentic Ready", exact=True).first.wait_for(timeout=30000)
    page.wait_for_timeout(1500)
    page.get_by_label("Docs page URL").fill("https://docs.ducktape.dev/install")
    page.get_by_label("Instruct: answer a how-to question").fill(
        "How do I install Ducktape on Windows and connect it to my workspace in the EU?")
    page.keyboard.press("Tab")
    page.wait_for_timeout(500)
    shot(page, "01_audit_input.png", [page.locator(".ar-title"), page.get_by_role("button", name="Run audit")])

    # 2. Turn on offline mode so numbers match the deck
    page.locator('[data-testid="stExpandSidebarButton"], [data-testid="stSidebarCollapsedControl"] button').first.click()
    page.wait_for_timeout(600)
    page.get_by_text("Offline mode", exact=True).click()
    page.wait_for_timeout(800)
    page.keyboard.press("Escape")
    page.locator('[data-testid="stSidebarCollapseButton"] button, [data-testid="stSidebarCollapseButton"]').first.click()
    page.wait_for_timeout(600)

    # 3. Demo run
    page.get_by_role("tab", name="Demo").click()
    page.get_by_role("button", name="Run agents on both versions").click()
    page.locator(".ar-delta").wait_for(timeout=120000)
    page.wait_for_timeout(1000)
    cards = page.locator(".ar-card")
    shot(page, "02_scores.png", [page.locator(".ar-delta"), cards.nth(0), cards.nth(1)])

    # 4. Failure findings (reader-mode agent of the typical version)
    page.get_by_role("button", name="Reader-mode agent").first.click()
    page.wait_for_timeout(1200)
    fails = page.locator(".ar-fail")
    shot(page, "03_failures.png", [page.locator(".ar-verdict").first, page.locator(".ar-bars").first, fails.nth(0), fails.nth(1)])

    # 5. What the reader-mode agent saw
    page.get_by_role("tab", name="What the agent saw").first.click()
    page.wait_for_timeout(1000)
    panel = page.locator('[data-testid="stCode"]').first
    shot(page, "04_agent_view.png", [panel])

    # 6. The same page as a human sees it, tooltip open
    human = browser.new_page(viewport={"width": 900, "height": 900}, device_scale_factor=2)
    human.goto((ROOT / "samples/guides/ducktape_bad.html").as_uri())
    human.locator(".tip").first.hover()
    human.wait_for_timeout(500)
    human.screenshot(path=str(OUT / "05_human_view.png"), clip={"x": 60, "y": 20, "width": 790, "height": 820})
    print("saved 05_human_view.png")

    browser.close()
