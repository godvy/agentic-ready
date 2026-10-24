# Agentic Ready: UserTesting for the Agentic Web

> Is your documentation usable by AI agents? We send agents to find out, then tell you exactly what to fix.

**Live demo:** https://agentic-ready-gqulkb5ysrtmnhtve284fz.streamlit.app/ · **Demo video:** _<link>_ · Built at AIBoomi Startup Weekend (Oct 2026)

## Problem

Developers and users no longer read docs line by line. They paste a docs link into Cursor, Copilot, Claude or ChatGPT and ask "how do I set this up?", or let an agent do it for them. Most documentation is still written for human eyes: key facts sit in tooltips, screenshots, hidden OS tabs and JavaScript-loaded callouts. The agent never sees them, confidently invents a wrong command, and the user decides the product is broken.

## Users & context

- **DevRel, docs and developer-experience teams** who own product documentation
- **Product managers** responsible for onboarding and activation
- Any company whose users increasingly arrive through AI assistants rather than search

## Solution

Agentic Ready replaces manual usability testing with **automated agent usability testing**.

1. **Input:** a docs URL (or pasted HTML) and a task. Not sure what to test? ✨ *Suggest test tasks* proposes realistic ones.
2. **Fetch, three ways:** real agents read pages differently, so we simulate three reading profiles:
   | Profile | Simulates | Typically misses |
   |---|---|---|
   | Raw HTML agent | Tools that pass page source to the model, truncated to a context budget | Screenshots, content past the cut-off, facts lost in noise |
   | Reader-mode agent | Most web-fetch tools and copy-paste into an IDE | Tooltips, hidden tabs, images, JavaScript-loaded text |
   | llms.txt agent | Agents that look for `/llms-full.txt` or `/llms.txt` first | Anything the site didn't publish there (or the whole thing, if absent) |
3. **Actor:** for each profile, an isolated agent attempts the task using only what it received, in one of two modes:
   - **Instruct:** answer a user's "how do I…?" with step-by-step instructions
   - **Execute:** carry out a multi-step task itself (exact commands, files and checks)
4. **Judge:** a stronger model audits each attempt against the full page as a human sees it (tooltips, hidden tabs, JS content, author notes on screenshots).
5. **Output:** an **AIO (AI Optimization) Score** from 0 to 100. The headline score averages the agents that represent how most assistants read docs (reader mode, plus llms.txt when the site has one). Raw HTML is reported separately as a naive-fetch check; if a page's content starts past its fetch budget, it's flagged as *buried under page chrome* instead of scored. Each agent gets its own score, plus a diagnostic report. Every failure gets a root cause (e.g. *"visible to humans, hidden from this agent"*), the evidence from the page, and the exact sentence to add to fix it.

```
docs page ─► Raw HTML view ─► Actor ─► Judge ─┐
          ├► Reader view   ─► Actor ─► Judge ─┼─► AIO Score + fixes
          └► llms.txt view ─► Actor ─► Judge ─┘
```

### Demo

Three self-written sample guides from different domains, each in a **typical** version (facts in tooltips, screenshots, hidden tabs, JS) and an **agent-ready** version (same facts, plain text):

| Sample guide | Instruct | Execute |
|---|---|---|
| Ducktape CLI: install & configure (dev tooling) | 53 → 100 | 52 → 100 |
| Pondhost: deploy a static site (DevOps) | 50 → 100 | 50 → 95 |
| Waddle: set up SAML SSO (SaaS admin) | 68 → 100 | 52 → 100 |

## Tech stack

- **Python 3.10+**, **Streamlit** UI
- **OpenAI API**: `gpt-4.1-mini` for Actors and the task suggester, `gpt-4.1` for the Judge (configurable)
- `requests`, `BeautifulSoup`, `markdownify` for fetching and reading profiles
- Agents for each profile run in parallel; results are cached; an offline mode replays pre-computed sample results

## Setup & run

```bash
git clone https://github.com/godvy/agentic-ready && cd agentic-ready
python -m venv .venv
.venv/Scripts/activate        # Windows (macOS/Linux: source .venv/bin/activate)
pip install -r requirements.txt
cp .env.example .env          # then put your OpenAI key in .env
streamlit run app.py
```

Terminal check (bad vs good sample guide):

```bash
python run_cli.py ducktape execute
```

Regenerate the offline demo cache after changing prompts: `python make_cache.py`.

**Project layout**

```
app.py               Streamlit UI
engine/scraper.py    fetching + the three reading profiles
engine/actor.py      the simulated agent (Instruct / Execute)
engine/judge.py      rubric, root causes, scoring
engine/tasks.py      test-task suggester
engine/pipeline.py   runs every profile in parallel
samples/             sample guides, catalog, offline cache
```

## Models & data

- **Models:** OpenAI `gpt-4.1-mini` (Actors: cheap, fast, representative of everyday assistants) and `gpt-4.1` (Judge: accuracy matters most here). Temperature 0, JSON mode for the Judge.
- **Data:** no training data. Audits run on the page the user submits. The sample guides (Ducktape, Pondhost, Waddle) are fictional products written for this project and released under this repo's MIT license. Screenshot images are generated by us.

## Evaluation & guardrails

- **Ground-truth separation:** Actors only see their profile's view; the Judge sees the full page, so failures can be traced to what was hidden.
- **Deterministic scoring:** the Judge returns category scores; code clamps each to its maximum and sums them, so scores always add up and stay within 0 to 100.
- **Root-cause check:** the Judge must confirm whether the correct value literally appears in the agent's view before blaming the agent rather than the docs.
- **Built-in eval set:** the bad/good sample pairs act as a regression test. Every pair must score clearly lower on the typical version (current gap: 32 to 50 points).
- **Static only:** generated commands are never executed, so audits can't harm any system.
- **Fallbacks:** offline mode and automatic cache fallback if the API or network fails.

## Known limitations & risks

- **Reading profiles are approximations** of common fetch pipelines, not exact replicas of any specific product. Raw HTML in particular is a minority path (mainly terminal agents using curl), which is why it's excluded from the headline score.
- **No headless-browser profile yet:** JavaScript-heavy pages are flagged rather than rendered.
- **LLM-as-judge variance:** individual live scores can move by roughly ±10 between runs; use the sample cache for stable demos.
- **Screenshots aren't read by the Judge directly:** for the samples, author notes describe image content; for real URLs, image-only content may be under-reported.
- Single-page audits only; multi-page journeys and running generated code in a sandbox are on the roadmap.

## Roadmap

Headless-browser profile · vision-based Judge for screenshots · sandboxed execution of generated commands · multi-page and whole-site audits · CI integration (fail a docs PR when the AIO Score drops) · "auto-fix" PRs with the suggested rewrites.

## Team

Solo build: _<your name>_ (<role>, <contact>)

## License

MIT. See [LICENSE](LICENSE).
