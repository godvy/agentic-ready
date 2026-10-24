"""Agentic Ready: UserTesting for the Agentic Web (Streamlit UI)."""
import json
import os
from pathlib import Path

import openai
import requests
import streamlit as st
import streamlit.components.v1 as components

from engine.actor import MODE_LABELS
from engine.judge import CATEGORIES, CATEGORY_LABELS
from engine.llm import judge_model_name, model_name
from engine.pipeline import audit
from engine.scraper import PROFILE_HELP, PROFILES, fetch_html, html_to_markdown
from engine.tasks import suggest_tasks
from make_cache import CACHE_FILE, CATALOG, cache_key

SEVERITY_ICON = {"critical": "🔴", "major": "🟠", "minor": "🟡"}
ROOT_CAUSE_LABEL = {
    "hidden_from_agent": "👁️ Visible to humans, hidden from this agent",
    "missing_from_docs": "🕳️ Not in the docs at all",
    "ambiguous": "❓ Ambiguous wording",
    "poorly_structured": "🧱 Buried or out of order",
    "scattered": "🔗 Lives on another page",
    "agent_error": "🤖 Agent error (docs were fine)",
}

st.set_page_config(page_title="Agentic Ready", page_icon="🦆", layout="wide")


# ---------- engine calls (cached so reruns don't burn credits) ----------

@st.cache_data(show_spinner=False)
def cached_audit(source: str, task: str, mode: str, html: str | None, reference: str | None) -> dict:
    return audit(source, task, mode, html=html, reference=reference)


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
        return f"Couldn't fetch that page ({e.__class__.__name__}). Try the **Paste content** option instead."
    return f"Something went wrong: {e}"


# ---------- rendering ----------

def band(score: int) -> tuple[str, str]:
    if score >= 80:
        return "Agent-ready", "green"
    if score >= 50:
        return "Needs work", "orange"
    return "Agent-hostile", "red"


def render_overview(result: dict, title: str | None = None) -> None:
    label, color = band(result["score"])
    if title:
        st.markdown(f"#### {title}")
    st.markdown(f"<div style='font-size:64px;font-weight:800;line-height:1'>{result['score']}"
                f"<span style='font-size:24px;opacity:.6'>/100</span></div>", unsafe_allow_html=True)
    st.markdown(f"**AIO Score** (average across agents) · :{color}[**{label}**]")
    cols = st.columns(len(PROFILES))
    for col, (key, p) in zip(cols, result["profiles"].items()):
        with col:
            value = p["report"]["score"] if p["available"] else "n/a"
            st.metric(p["label"], value, help=f"{PROFILE_HELP[key]}\n\n{p['note']}")


def render_details(result: dict, key: str) -> None:
    available = [k for k, p in result["profiles"].items() if p["available"]]
    for k, p in result["profiles"].items():
        if not p["available"]:
            st.caption(f"ℹ️ **{p['label']}**: {p['note']}")
    if not available:
        return
    pick = st.radio("Show the report for", available, format_func=lambda k: PROFILES[k],
                    horizontal=True, key=f"profile_{key}")
    p = result["profiles"][pick]
    r = p["report"]
    st.markdown(f"**{p['label']}: {r['score']}/100.** {r.get('verdict', '')}")
    bars = st.columns(len(CATEGORIES))
    for col, (name, cap) in zip(bars, CATEGORIES.items()):
        pts = r["categories"].get(name, 0)
        col.progress(pts / cap, text=f"{CATEGORY_LABELS[name]}: {pts}/{cap}")

    failures = r["failures"]
    t1, t2, t3, t4 = st.tabs([f"🩺 Where the docs failed ({len(failures)})", "🤖 What the agent produced",
                              "📄 What this agent saw", "👀 What humans see"])
    with t1:
        if not failures:
            st.success("No failures. This agent can complete the task from this page as-is. 🎉")
        for f in failures:
            sev = f.get("severity", "minor")
            with st.container(border=True):
                st.markdown(f"{SEVERITY_ICON.get(sev, '⚪')} **{sev.upper()}**: {f.get('what_broke', '')}")
                st.caption(ROOT_CAUSE_LABEL.get(f.get("root_cause"), f.get("root_cause", "")))
                if f.get("doc_evidence"):
                    st.markdown("Where the real answer was:")
                    st.code(f["doc_evidence"], language="html", wrap_lines=True)
                st.markdown(f"**✅ Fix:** {f.get('fix', '')}")
    with t2:
        st.markdown(p["output"])
    with t3:
        st.caption(f"{PROFILE_HELP[pick]} ({p['note']})")
        st.code(p["view"], language="html" if pick == "raw_html" else "markdown", wrap_lines=True)
    with t4:
        st.caption("The original page as a human sees it. Hover the ⓘ icons and click the tabs.")
        html = result["html"]
        if result["source"].startswith(("http://", "https://")):
            # resolve the page's relative CSS/image paths against its real URL
            html = f'<base href="{result["source"]}">' + html
        components.html(html, height=520, scrolling=True)


# ---------- page ----------

st.title("🦆 Agentic Ready")
st.markdown("**UserTesting for the Agentic Web.** We send AI agents to use your documentation, the way "
            "real assistants read it, then show what they got wrong and *why*.")

has_key = bool(os.getenv("OPENAI_API_KEY"))  # Streamlit Cloud exposes secrets as env vars
with st.sidebar:
    st.markdown("### How it works")
    st.markdown("1. **Fetch** the page the way 3 kinds of agents do\n"
                "2. **Actor** agents answer or perform a task using only what they saw\n"
                "3. **Judge** checks each one against the full page a human sees\n"
                "4. **AIO Score** + a fix for every failure")
    st.markdown("### Agent reading profiles")
    for k, label in PROFILES.items():
        st.markdown(f"**{label}**: {PROFILE_HELP[k]}")
    st.divider()
    offline = st.toggle("Offline mode (cached samples)", value=not has_key,
                        help="Replay pre-computed results for the samples. Stable numbers, no Wi-Fi needed.")
    st.caption(f"Actor: `{model_name()}` · Judge: `{judge_model_name()}`")
    if not has_key:
        st.warning("No OPENAI_API_KEY found. Live audits are disabled; samples run from cache.")

demo_tab, audit_tab = st.tabs(["⚡ Demo: same guide, two versions", "🔍 Audit your docs"])

with demo_tab:
    c1, c2 = st.columns([2, 1])
    guide = c1.selectbox("Sample guide", list(CATALOG),
                         format_func=lambda g: f"{CATALOG[g]['title']}  ·  {CATALOG[g]['domain']}")
    mode = c2.radio("Test mode", list(MODE_LABELS), format_func=MODE_LABELS.get, key="demo_mode")
    st.markdown(f"**Task given to the agents:** _{CATALOG[guide]['tasks'][mode]}_")
    st.caption("Both versions contain the same facts. The typical version puts some of them in tooltips, "
               "screenshots, hidden tabs and JavaScript, the way many real docs do.")
    if st.button("Run the agents on both versions", type="primary"):
        try:
            with st.spinner("Agents are reading the docs and working on the task…"):
                st.session_state.demo = {v: sample_audit(guide, v, mode, offline) for v in ("bad", "good")}
        except Exception as e:
            st.error(friendly_error(e))

    demo = st.session_state.get("demo")
    if demo:
        bad, good = demo["bad"], demo["good"]
        hidden = sum(f.get("root_cause") == "hidden_from_agent"
                     for p in bad["profiles"].values() if p["available"] for f in p["report"]["failures"])
        st.success(f"**+{good['score'] - bad['score']} points** from the same facts written as plain text. "
                   f"Agents hit **{hidden} failures** caused by content only humans could see.")
        left, right = st.columns(2)
        with left:
            render_overview(bad, "❌ Typical version")
        with right:
            render_overview(good, "✅ Agent-ready version")
        st.divider()
        st.markdown("### Diagnostic report: typical version")
        render_details(bad, "bad")
        with st.expander("Diagnostic report: agent-ready version"):
            render_details(good, "good")

with audit_tab:
    src_mode = st.radio("Docs source", ["URL", "Paste content"], horizontal=True)
    if src_mode == "URL":
        st.text_input("Docs page URL", key="url", placeholder="https://docs.yourproduct.com/getting-started")
    else:
        st.text_area("Paste the page HTML (best) or its text", key="pasted", height=200)

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

    a_mode = st.radio("Test mode", list(MODE_LABELS), format_func=MODE_LABELS.get, horizontal=True,
                      key="audit_mode")
    st.text_area("What should the agent do?", key=f"task_{a_mode}", height=80,
                 placeholder="How do I set up X on Windows?" if a_mode == "instruct"
                 else "Install X, configure it for Y, and verify it works.")
    b1, b2, _ = st.columns([1, 1, 3])
    b1.button("✨ Suggest test tasks", on_click=on_suggest, disabled=offline)
    run = b2.button("Run audit", type="primary", disabled=offline)
    if err := st.session_state.pop("suggest_error", None):
        st.error(err)
    if offline:
        st.info("Turn off offline mode in the sidebar to audit your own docs.")

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
        reader = result["profiles"].get("reader", {})
        if reader.get("available") and len(reader.get("view", "")) < 200:
            st.warning("Reader-mode agents saw almost no text. The page is probably rendered by JavaScript, "
                       "which is itself an AIO problem. Try **Paste content** with the rendered HTML.")
        render_overview(result)
        render_details(result, "audit")
