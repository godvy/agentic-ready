# Agentic Ready — TODO

Current Progress: [100%] - Core MVP locked, committed and deployed

Deadline: **Sat 12:00 PM** (portal locks). Target: all submission items uploaded by 11:00 AM.
Stack: Python + Streamlit, OpenAI API (gpt-4.1-mini Actors, gpt-4.1 Judge), requests + BeautifulSoup + markdownify. Deploy: Streamlit Community Cloud.

---

## Wave 1: Core Engine [35%] ✅
- [x] Scaffold: git, requirements, `.env.example`, `.gitignore`, MIT `LICENSE`
- [x] Three reading profiles: raw HTML, reader-mode Markdown, llms.txt (`engine/scraper.py`)
- [x] Actor with Instruct / Execute modes (`engine/actor.py`)
- [x] Judge: 5-part rubric, root causes, clamped scoring (`engine/judge.py`)
- [x] Task suggester (`engine/tasks.py`), parallel pipeline (`engine/pipeline.py`)
- [x] CLI checkpoint: typical guides score 52-72, agent-ready guides 98-100

## Wave 2: Streamlit UI [40%] ✅
- [x] Demo tab: 3 sample guides × typical/agent-ready × Instruct/Execute
- [x] Audit tab: URL or paste, suggested tasks, per-profile scores, diagnostic report
- [x] Offline mode + automatic cache fallback, friendly errors

## Wave 3: Demo + Submission [25%]
- [x] README (handbook outline), AI Impact Statement, deck text (`submission/`)
- [x] MVP committed to git
- [x] Pushed to GitHub (public), deployed to Streamlit Cloud, live link in README
- [ ] You: deck slides, demo video, fill in Team section, upload to portal

## Wave 4+: Bonus
- Headless-browser profile (rendered DOM)
- Vision-based Judge for screenshots
- Sandboxed execution of generated commands
- Whole-site audits, CI integration
