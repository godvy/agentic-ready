"""Turn a docs page into what different kinds of AI agents actually read.

Agents don't all see the same page. We simulate three common reading profiles:
- raw_html: tools that pass the page source to the model, cut at a context budget
- reader:   web-fetch / copy-paste tools that run reader mode and convert to Markdown
- llms_txt: agents that look for an AI-friendly /llms-full.txt or /llms.txt first
"""
from pathlib import Path
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup
from markdownify import markdownify

HEADERS = {"User-Agent": "AgenticReady/0.2 (+docs audit)"}
NOISE_TAGS = ["script", "style", "noscript", "svg", "nav", "footer", "header", "iframe", "template"]
RAW_HTML_BUDGET = 40_000  # chars, roughly what fetch tools keep before truncating
READER_BUDGET = 40_000

PROFILES = {
    "raw_html": "Raw HTML agent",
    "reader": "Reader-mode agent",
    "llms_txt": "llms.txt agent",
}
PROFILE_HELP = {
    "raw_html": "Gets the page source, truncated to a context budget. Sees attributes, but in lots of noise.",
    "reader": "Gets reader-mode Markdown, like most web-fetch tools. Loses tooltips, hidden tabs, images and JS-loaded text.",
    "llms_txt": "Looks for /llms-full.txt or /llms.txt, the emerging standard for AI-friendly docs.",
}


def fetch_html(source: str) -> str:
    """Fetch HTML from a URL or a local file path (used for the bundled samples)."""
    if source.startswith(("http://", "https://")):
        resp = requests.get(source, headers=HEADERS, timeout=20)
        resp.raise_for_status()
        return resp.text
    return Path(source).read_text(encoding="utf-8")


def _is_hidden(tag) -> bool:
    style = (tag.get("style") or "").replace(" ", "").lower()
    return tag.has_attr("hidden") or "display:none" in style or tag.get("aria-hidden") == "true"


def html_to_markdown(html: str) -> str:
    """Reader mode: drop chrome and hidden elements, keep main content, convert to Markdown."""
    soup = BeautifulSoup(html, "html.parser")
    for tag in soup(NOISE_TAGS):
        tag.decompose()
    for tag in soup.find_all(_is_hidden):
        tag.decompose()
    for img in soup.find_all("img"):  # agents don't OCR screenshots; keep only the alt text
        img.replace_with(f"[image: {img.get('alt') or 'no description'}]")
    root = soup.find("main") or soup.find("article") or soup.body or soup
    md = markdownify(str(root), heading_style="ATX", code_language="")
    out, blank = [], False
    for line in (l.rstrip() for l in md.splitlines()):
        if not line and blank:
            continue
        out.append(line)
        blank = not line
    return "\n".join(out).strip()[:READER_BUDGET]


def raw_view(html: str) -> str:
    if len(html) <= RAW_HTML_BUDGET:
        return html
    return html[:RAW_HTML_BUDGET] + "\n<!-- [truncated by the agent's fetch tool] -->"


def content_start(html: str) -> int | None:
    """Character offset where the page's main content begins (first <main>, <article> or <h1>)."""
    lower = html.lower()
    hits = [i for i in (lower.find("<main"), lower.find("<article"), lower.find("<h1")) if i >= 0]
    return min(hits) if hits else None


def fetch_llms_txt(source: str) -> tuple[str | None, str]:
    """Return (text, note) for the site's llms-full.txt / llms.txt, if any."""
    if not source.startswith(("http://", "https://")):
        return None, "Not checked (local or pasted content)."
    origin = f"{urlparse(source).scheme}://{urlparse(source).netloc}"
    for name in ("/llms-full.txt", "/llms.txt"):
        url = urljoin(origin, name)
        try:
            resp = requests.get(url, headers=HEADERS, timeout=10)
        except requests.RequestException:
            continue
        if resp.ok and "text/html" not in resp.headers.get("content-type", ""):
            return resp.text[:READER_BUDGET], f"Found {url}"
    return None, f"No llms.txt at {origin}. Agents that look for it fall back to the HTML."


def build_views(html: str, source: str = "") -> dict:
    """Every reading profile's view of the page. `text` is None when the profile isn't available."""
    llms, llms_note = fetch_llms_txt(source)
    start = content_start(html)
    buried = start is not None and start >= RAW_HTML_BUDGET
    raw_note = f"{len(html):,} chars of HTML" + (" (truncated)" if len(html) > RAW_HTML_BUDGET else "")
    if buried:
        raw_note = (f"Only saw page chrome: the main content starts at character {start:,} of {len(html):,}, "
                    f"past the {RAW_HTML_BUDGET:,}-character fetch budget")
    return {
        # a buried page gets no Actor run: the agent would have nothing to work from
        "raw_html": {"text": None if buried else raw_view(html), "note": raw_note, "buried": buried},
        "reader": {"text": html_to_markdown(html), "note": "Reader-mode Markdown"},
        "llms_txt": {"text": llms, "note": llms_note},
    }


def scrape(source: str) -> dict:
    html = fetch_html(source)
    return {"html": html, "views": build_views(html, source)}
