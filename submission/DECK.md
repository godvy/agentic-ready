# Pitch deck: Agentic Ready (6 slides)

Paste each slide into your deck tool. Speaker notes are in italics.

---

## 1. Problem & who cares

**Your docs have a new reader. It can't see half the page.**

- Users now paste docs links into Cursor, Copilot, Claude and ChatGPT, or let agents do the setup
- Docs hide key facts in tooltips, screenshots, hidden tabs and JavaScript
- The agent invents a wrong command → the user thinks your product is broken
- Who feels it: DevRel, docs and developer-experience teams, PMs who own onboarding

*"Every company spent 20 years making docs readable for humans and Google. Nobody is checking whether AI agents can use them."*

---

## 2. Insight & why now

**SEO made sites readable for crawlers. The next decade needs AIO: AI Optimization.**

- Agents don't read pages the way humans do, and they don't all read them the same way either
- The same page can score 70 for one agent and 50 for another, purely because of how it was fetched
- Nobody measures this today: no analytics, no tests, no score
- Why now: AI assistants are becoming the main way people find and follow instructions

---

## 3. Solution demo

**UserTesting for the agentic web.** Paste a URL and a task, get an AIO Score and a fix list.

- Screenshot: two scores side by side: *Typical guide 53 vs Agent-ready 100*
- Screenshot: failure card: 🔴 *"Agent invented `ducktape connect`; the real command was only in a screenshot"* → ✅ exact sentence to add
- Three agent reading profiles · Instruct and Execute modes · ✨ auto-suggested test tasks

*Live demo: Demo tab → Ducktape → Execute → Run. Point at the +47 banner, open a failure card, then show "What this agent saw" vs "What humans see" (hover the tooltip).*

---

## 4. Tech approach

```
docs page ─► Raw HTML view ─► Actor ─► Judge ─┐
          ├► Reader view   ─► Actor ─► Judge ─┼─► AIO Score + fixes
          └► llms.txt view ─► Actor ─► Judge ─┘
```

- **Actors:** gpt-4.1-mini, restricted to exactly what their fetch method returned
- **Judge:** gpt-4.1 sees the full page (tooltips, hidden tabs, JS text), scores against a 5-part rubric (correctness, completeness, order, specificity, verification) and labels a root cause for each failure
- Python + Streamlit; profiles run in parallel; scoring is deterministic in code; paired good/bad guides act as a regression suite

---

## 5. Value & go-to-market

- **Who pays:** dev-tool, API and SaaS companies with public docs, through DevRel and docs teams
- **Model:** free single-page audit (lead magnet) → paid plans for whole-site audits, monitoring and CI checks that fail a docs PR when the AIO Score drops
- **Reach:** DevRel communities, docs-platform integrations (Mintlify, ReadMe, Docusaurus), and publishing "AIO leaderboards" of popular docs
- **ROI story:** fewer support tickets and failed onboardings caused by AI-generated wrong answers

---

## 6. Roadmap & risks

**Next:** headless-browser profile · vision Judge for screenshots · sandboxed execution of generated commands · whole-site audits · CI / GitHub integration · auto-fix PRs

**Risks & mitigations**
- LLM-judge variance → rubric clamped in code, paired regression samples, multiple runs
- Profiles approximate real tools → keep calibrating against real assistants
- Model costs → small models for Actors, caching, sampling pages
