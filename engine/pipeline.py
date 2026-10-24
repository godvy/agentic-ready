"""Scrape -> (Actor -> Judge) for every reading profile, in parallel."""
from concurrent.futures import ThreadPoolExecutor

from .actor import run_actor
from .judge import run_judge
from .scraper import PROFILES, build_views, fetch_html

# Raw HTML is a naive-fetch check, not how most assistants read docs, so it stays out of the headline score
HEADLINE_PROFILES = ("reader", "llms_txt")


def headline_score(profiles: dict) -> int:
    scores = [p["report"]["score"] for k, p in profiles.items() if k in HEADLINE_PROFILES and p["available"]]
    return round(sum(scores) / len(scores)) if scores else 0


def _run_profile(key: str, view: dict, html: str, task: str, mode: str, reference: str | None) -> dict:
    output = run_actor(view["text"], task, mode, view["note"])
    report = run_judge(html, view["text"], PROFILES[key], task, mode, output, reference)
    return {"available": True, "label": PROFILES[key], "note": view["note"], "view": view["text"],
            "output": output, "report": report}


def audit(source: str, task: str, mode: str, html: str | None = None, reference: str | None = None) -> dict:
    """Run a full audit. Pass `html` to skip fetching (pasted content)."""
    if html is None:
        html = fetch_html(source)
    views = build_views(html, source)
    profiles = {}
    with ThreadPoolExecutor(max_workers=len(views)) as pool:
        futures = {k: pool.submit(_run_profile, k, v, html, task, mode, reference)
                   for k, v in views.items() if v["text"]}
        for key, view in views.items():
            if key in futures:
                profiles[key] = futures[key].result()
            else:
                profiles[key] = {"available": False, "buried": view.get("buried", False),
                                 "label": PROFILES[key], "note": view["note"]}
    return {"source": source, "task": task, "mode": mode, "html": html, "profiles": profiles,
            "score": headline_score(profiles)}
