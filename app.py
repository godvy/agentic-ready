"""Agentic Ready: UserTesting for the Agentic Web (Streamlit UI)."""
import json
import os
from html import escape
from pathlib import Path

import openai
import requests
import streamlit as st
import streamlit.components.v1 as components

from engine.actor import MODE_LABELS
from engine.judge import CATEGORIES, CATEGORY_LABELS
from engine.llm import judge_model_name, model_name
from engine.pipeline import HEADLINE_PROFILES, audit, headline_score
from engine.scraper import PROFILE_HELP, PROFILES, fetch_html, html_to_markdown
from engine.tasks import suggest_tasks
from make_cache import CACHE_FILE, CATALOG, cache_key

MODE_SHORT = {"instruct": "Instruct", "execute": "Execute"}
ROOT_CAUSE_LABEL = {
    "hidden_from_agent": "Visible to humans, hidden from this agent",
    "missing_from_docs": "Not in the docs",
    "ambiguous": "Ambiguous wording",
    "poorly_structured": "Buried or out of order",
    "scattered": "Lives on another page",
    "agent_error": "Agent error, docs were fine",
}

st.set_page_config(page_title="Agentic Ready", page_icon=":material/fact_check:", layout="wide",
                   initial_sidebar_state="collapsed")

st.markdown("""<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600&family=Source+Serif+4:opsz,wght@8..60,500;8..60,600&family=JetBrains+Mono:wght@400&display=swap');
:root { --ink:#1C1B19; --muted:#6B6760; --line:#E4E1DA; --surface:#F2F0EB; --accent:#2B4A6F;
        --good:#2F6B4F; --warn:#9A6A2A; --bad:#A33A2B; }
html, body, .stApp, .stApp p, .stApp li, .stApp label, .stApp input, .stApp textarea, .stApp button,
.stApp [data-baseweb="select"], .stApp [data-baseweb="tab"] { font-family: 'Inter', sans-serif !important; }
code, pre, .stCode { font-family: 'JetBrains Mono', monospace !important; }
h1, h2, h3, h4 { font-family: 'Source Serif 4', Georgia, serif !important; font-weight: 600 !important;
                 letter-spacing: -0.01em; color: var(--ink); }
.block-container { max-width: 1120px; padding-top: 3rem; }
header[data-testid="stHeader"] { background: #FBFAF8; }
.stApp div[class^="ar-"], .stApp p[class^="ar-"] { font-family: 'Inter', sans-serif; }
.stApp p.ar-title { font-family: 'Source Serif 4', Georgia, serif !important; font-size: 2.4rem; font-weight: 600;
            letter-spacing: -0.02em; line-height: 1.15; margin: 0; color: var(--ink); }
.stApp p.ar-sub { color: var(--muted); font-size: 1.02rem; margin: .4rem 0 1.6rem; max-width: 680px; line-height: 1.55; }
.ar-label { text-transform: uppercase; letter-spacing: .08em; font-size: .72rem; color: var(--muted); font-weight: 600; }
.ar-card { border: 1px solid var(--line); border-radius: 10px; padding: 1.4rem 1.5rem; background: #fff; }
.stApp div.ar-score { font-family: 'Source Serif 4', Georgia, serif; font-size: 3.6rem; line-height: 1; font-weight: 600;
            margin: .5rem 0 .25rem; color: var(--ink); }
.ar-score span { font-size: 1.1rem; color: var(--muted); font-weight: 500; margin-left: .2rem; }
.ar-band { font-size: .85rem; font-weight: 500; }
.ar-profiles { display: flex; flex-wrap: wrap; gap: 1.6rem; margin-top: 1.2rem; padding-top: 1rem; border-top: 1px solid var(--line); }
.ar-profiles div { font-size: .82rem; color: var(--muted); }
.ar-profiles i { font-style: normal; opacity: .7; }
.ar-profiles b { display: block; font-size: 1.15rem; color: var(--ink); font-weight: 600; margin-top: .15rem; }
.ar-delta { color: var(--ink); font-size: 1rem; margin: .4rem 0 1.4rem; }
.ar-delta b { color: var(--good); }
.ar-bars { display: grid; grid-template-columns: repeat(auto-fit, minmax(150px, 1fr)); gap: 1.2rem; margin: .8rem 0 1.4rem; }
.ar-bar-top { display: flex; justify-content: space-between; font-size: .8rem; color: var(--muted); margin-bottom: .35rem; }
.ar-bar-top b { color: var(--ink); font-weight: 600; }
.ar-track { height: 4px; background: var(--line); border-radius: 2px; overflow: hidden; }
.ar-fill { height: 100%; background: var(--accent); }
.ar-verdict { color: var(--ink); margin: .2rem 0 .4rem; line-height: 1.55; }
.ar-fail { border-left: 3px solid var(--line); padding: .2rem 0 .2rem 1.1rem; margin: 0 0 1.6rem; }
.ar-fail.critical { border-color: var(--bad); } .ar-fail.major { border-color: var(--warn); }
.ar-fail-head { font-weight: 500; color: var(--ink); line-height: 1.5; }
.ar-sev { font-size: .68rem; letter-spacing: .08em; text-transform: uppercase; font-weight: 600; margin-right: .5rem; }
.ar-sev.critical { color: var(--bad); } .ar-sev.major { color: var(--warn); } .ar-sev.minor { color: var(--muted); }
.ar-cause { color: var(--muted); font-size: .85rem; margin: .25rem 0 .6rem; }
.stApp div.ar-evidence { font-family: 'JetBrains Mono', monospace; font-size: .8rem; background: var(--surface);
               border-radius: 6px; padding: .6rem .8rem; color: var(--ink); white-space: pre-wrap; margin-bottom: .6rem; }
.ar-fix { font-size: .92rem; line-height: 1.5; } .ar-fix span { color: var(--good); font-weight: 600; margin-right: .35rem; }
.ar-note { color: var(--muted); font-size: .88rem; }
.ar-task { background: var(--surface); border-radius: 8px; padding: .8rem 1rem; margin: .6rem 0 1rem; line-height: 1.5; }
</style>""", unsafe_allow_html=True)


def html(s: str) -> None:
    st.markdown(s, unsafe_allow_html=True)


# ---------- engine calls (cached so reruns don't burn credits) ----------

@st.cache_data(show_spinner=False)
def cached_audit(source: str, task: str, mode: str, html_text: str | None, reference: str | None) -> dict:
    return audit(source, task, mode, html=html_text, reference=reference)


@st.cache_data(show_spinner=False)
def cached_suggest(text: str) -> dict:
    return suggest_tasks(text)


@st.cache_data(show_spinner=False)
def offline_cache() -> dict:
    path = Path(CACHE_FILE)
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}


def sample_audit(guide: str, version: str, mode: str, offline: bool) -> dict:
    """Audit a bundled sample, live or from the offline cache (with automatic fallback)."""
    g = CATALOG[guide]
    cached = offline_cache().get(cache_key(guide, version, mode))
    if offline and cached:
        result = dict(cached)
    else:
        try:
            result = cached_audit(g[version], g["tasks"][mode], mode, None, g["reference"])
        except Exception as e:
            if not cached:
                raise
            st.toast(f"Live run failed, showing cached result. {friendly_error(e)}")
            result = dict(cached)
    result["html"] = Path(g[version]).read_text(encoding="utf-8")
    return result


def friendly_error(e: Exception) -> str:
    if isinstance(e, openai.AuthenticationError):
        return "OpenAI rejected the API key. Check `OPENAI_API_KEY` in `.env` (or Streamlit secrets)."
    if isinstance(e, openai.RateLimitError):
        return "OpenAI rate limit or credits exhausted. Wait a moment, or use offline mode for the demo."
    if isinstance(e, openai.APIConnectionError):
        return "Couldn't reach OpenAI (network issue). Try offline mode for the demo."
    if isinstance(e, requests.RequestException):
        return f"Couldn't fetch that page ({e.__class__.__name__}). Try pasting the content instead."
    return f"Something went wrong: {e}"


# ---------- rendering ----------

def band(score: int) -> tuple[str, str]:
    if score >= 80:
        return "Agent-ready", "var(--good)"
    if score >= 50:
        return "Needs work", "var(--warn)"
    return "Agent-hostile", "var(--bad)"


def profile_value(p: dict) -> str:
    if p["available"]:
        return str(p["report"]["score"])
    return "Buried" if p.get("buried") else "—"


def render_overview(result: dict, title: str = "AIO Score") -> None:
    score = headline_score(result["profiles"])  # recomputed so older cached results follow the current rule
    label, color = band(score)
    profiles = "".join(
        f"<div title='{escape(PROFILE_HELP[k])}'>{escape(p['label'])}"
        f"{'' if k in HEADLINE_PROFILES else ' <i>(not in score)</i>'}<b>{profile_value(p)}</b></div>"
        for k, p in result["profiles"].items())
    html(f"<div class='ar-card'><div class='ar-label'>{escape(title)}</div>"
         f"<div class='ar-score'>{score}<span>/ 100</span></div>"
         f"<div class='ar-band' style='color:{color}'>{label}</div>"
         f"<div class='ar-profiles'>{profiles}</div></div>")


def pick(label: str, options: list, fmt, key: str):
    """Segmented control that always has a selection."""
    choice = st.segmented_control(label, options, format_func=fmt, default=options[0], key=key)
    return choice or options[0]


def render_details(result: dict, key: str) -> None:
    available = [k for k, p in result["profiles"].items() if p["available"]]
    missing = [p for p in result["profiles"].values() if not p["available"] and not p.get("buried")]
    for p in result["profiles"].values():
        if p.get("buried"):
            html(f"<div class='ar-fail major'><div class='ar-fail-head'><span class='ar-sev major'>major</span>"
                 f"{escape(p['label'])} never reached the content</div>"
                 f"<div class='ar-cause'>Buried under page chrome</div>"
                 f"<div class='ar-evidence'>{escape(p['note'])}.</div>"
                 f"<div class='ar-fix'><span>Fix</span>Move the article earlier in the HTML, slim down or lazy-load "
                 f"the navigation, or publish a Markdown / llms.txt version. Agents that fetch the raw page and "
                 f"truncate it, like terminal coding agents using curl, see only menus here.</div></div>")
    if not available:
        return
    profile = pick("Agent", available, PROFILES.get, f"profile_{key}")
    p = result["profiles"][profile]
    r = p["report"]

    html(f"<p class='ar-verdict'>{escape(r.get('verdict', ''))}</p>")
    bars = "".join(
        f"<div><div class='ar-bar-top'>{CATEGORY_LABELS[n]}<b>{r['categories'].get(n, 0)}/{cap}</b></div>"
        f"<div class='ar-track'><div class='ar-fill' style='width:{100 * r['categories'].get(n, 0) / cap:.0f}%'>"
        f"</div></div></div>" for n, cap in CATEGORIES.items())
    html(f"<div class='ar-bars'>{bars}</div>")

    failures = r["failures"]
    t1, t2, t3, t4 = st.tabs([f"Failures ({len(failures)})", "Agent output", "What the agent saw", "Original page"])
    with t1:
        if not failures:
            html("<p class='ar-note'>No failures. This agent can complete the task from this page as written.</p>")
        for f in failures:
            sev = f.get("severity", "minor")
            evidence = f"<div class='ar-evidence'>{escape(f['doc_evidence'])}</div>" if f.get("doc_evidence") else ""
            html(f"<div class='ar-fail {sev}'>"
                 f"<div class='ar-fail-head'><span class='ar-sev {sev}'>{sev}</span>{escape(f.get('what_broke', ''))}</div>"
                 f"<div class='ar-cause'>{ROOT_CAUSE_LABEL.get(f.get('root_cause'), escape(str(f.get('root_cause', ''))))}</div>"
                 f"{evidence}<div class='ar-fix'><span>Fix</span>{escape(f.get('fix', ''))}</div></div>")
    with t2:
        st.markdown(p["output"])
    with t3:
        html(f"<p class='ar-note'>{escape(PROFILE_HELP[profile])} {escape(p['note'])}.</p>")
        st.code(p["view"], language="html" if profile == "raw_html" else "markdown", wrap_lines=True)
    with t4:
        html("<p class='ar-note'>The page as a human sees it. Hover the info icons and click the tabs.</p>")
        page = result["html"]
        if result["source"].startswith(("http://", "https://")):
            # resolve the page's relative CSS/image paths against its real URL
            page = f'<base href="{result["source"]}">' + page
        components.html(page, height=520, scrolling=True)
    for m in missing:
        html(f"<p class='ar-note'>{escape(m['label'])}: {escape(m['note'])}</p>")


# ---------- page ----------

html("<p class='ar-title'>Agentic Ready</p>"
     "<p class='ar-sub'>Usability testing for the agentic web. AI agents read your documentation the way real "
     "assistants fetch it, attempt a task, and a judge shows what they got wrong and why.</p>")

has_key = bool(os.getenv("OPENAI_API_KEY"))  # Streamlit Cloud exposes secrets as env vars
with st.sidebar:
    st.markdown("#### Settings")
    offline = st.toggle("Offline mode", value=not has_key,
                        help="Replay pre-computed results for the sample guides. Stable numbers, no network needed.")
    html(f"<p class='ar-note'>Actor model: {model_name()}<br>Judge model: {judge_model_name()}</p>")
    if not has_key:
        st.warning("No OPENAI_API_KEY found. Samples run from cache.")
    st.markdown("#### Agent profiles")
    for k, label in PROFILES.items():
        html(f"<p class='ar-note'><b style='color:var(--ink)'>{label}</b><br>{escape(PROFILE_HELP[k])}</p>")

demo_tab, audit_tab = st.tabs(["Demo", "Audit a page"])

with demo_tab:
    c1, c2 = st.columns([3, 2], vertical_alignment="bottom")
    guide = c1.selectbox("Sample guide", list(CATALOG),
                         format_func=lambda g: f"{CATALOG[g]['title']} ({CATALOG[g]['domain']})")
    with c2:
        mode = pick("Mode", list(MODE_SHORT), MODE_SHORT.get, "demo_mode")
    html(f"<div class='ar-task'><div class='ar-label'>Task</div>{escape(CATALOG[guide]['tasks'][mode])}</div>")
    if st.button("Run agents on both versions", type="primary"):
        try:
            with st.spinner("Agents are reading the docs and working on the task…"):
                st.session_state.demo = {v: sample_audit(guide, v, mode, offline) for v in ("bad", "good")}
        except Exception as e:
            st.error(friendly_error(e))
    html("<p class='ar-note'>Both versions contain the same facts. The typical version keeps some of them in "
         "tooltips, screenshots, hidden tabs and JavaScript, as many real docs do.</p>")

    demo = st.session_state.get("demo")
    if demo:
        bad, good = demo["bad"], demo["good"]
        hidden = sum(f.get("root_cause") == "hidden_from_agent"
                     for p in bad["profiles"].values() if p["available"] for f in p["report"]["failures"])
        st.divider()
        html(f"<p class='ar-delta'><b>+{headline_score(good['profiles']) - headline_score(bad['profiles'])} points</b> when the same facts are written "
             f"as plain text. {hidden} failures came from content only humans could see.</p>")
        left, right = st.columns(2, gap="medium")
        with left:
            render_overview(bad, "Typical version")
        with right:
            render_overview(good, "Agent-ready version")
        st.markdown("### Report: typical version")
        render_details(bad, "bad")
        with st.expander("Report: agent-ready version"):
            render_details(good, "good")

with audit_tab:
    src_mode = pick("Source", ["URL", "Paste content"], str, "src_mode")
    if src_mode == "URL":
        st.text_input("Docs page URL", key="url", placeholder="https://docs.yourproduct.com/getting-started")
    else:
        st.text_area("Page HTML or text", key="pasted", height=180)

    def on_suggest():
        try:
            if src_mode == "URL":
                text = html_to_markdown(fetch_html(st.session_state.get("url", "").strip()))
            else:
                text = st.session_state.get("pasted", "")
            tasks = cached_suggest(text)
            st.session_state.task_instruct = tasks.get("instruct", "")
            st.session_state.task_execute = tasks.get("execute", "")
        except Exception as e:
            st.session_state.suggest_error = friendly_error(e)

    a_mode = pick("Mode", list(MODE_SHORT), MODE_SHORT.get, "audit_mode")
    st.text_area(MODE_LABELS[a_mode], key=f"task_{a_mode}", height=80,
                 placeholder="How do I set up X on Windows?" if a_mode == "instruct"
                 else "Install X, configure it for Y, and verify it works.")
    b1, b2, _ = st.columns([1, 1, 4])
    run = b1.button("Run audit", type="primary", disabled=offline, use_container_width=True)
    b2.button("Suggest tasks", on_click=on_suggest, disabled=offline, use_container_width=True)
    if err := st.session_state.pop("suggest_error", None):
        st.error(err)
    if offline:
        html("<p class='ar-note'>Turn off offline mode in the sidebar to audit your own docs.</p>")

    if run:
        task = st.session_state.get(f"task_{a_mode}", "").strip()
        url = st.session_state.get("url", "").strip() if src_mode == "URL" else ""
        pasted = st.session_state.get("pasted", "") if src_mode != "URL" else None
        if not task or (src_mode == "URL" and not url) or (pasted is not None and not pasted.strip()):
            st.warning("Add the docs (URL or pasted content) and a task first.")
        else:
            try:
                with st.spinner("Agents are reading the docs and working on the task…"):
                    st.session_state.audit = cached_audit(url or "pasted content", task, a_mode, pasted, None)
            except Exception as e:
                st.session_state.pop("audit", None)
                st.error(friendly_error(e))

    result = st.session_state.get("audit")
    if result:
        st.divider()
        reader = result["profiles"].get("reader", {})
        if reader.get("available") and len(reader.get("view", "")) < 200:
            st.warning("Reader-mode agents saw almost no text. The page is probably rendered by JavaScript, "
                       "which is itself an AIO problem. Try pasting the rendered HTML.")
        render_overview(result)
        st.markdown("### Report")
        render_details(result, "audit")
