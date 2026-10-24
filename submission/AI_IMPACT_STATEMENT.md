# AI Impact Statement: Agentic Ready

**What the AI does.** Agentic Ready automates documentation usability testing. Simulated AI agents read a docs page the way real assistants fetch it (raw HTML, reader-mode Markdown, llms.txt) and attempt a task: answering a how-to question or planning the steps to do it themselves. A Judge model audits each attempt against the full page and explains every failure and its fix.

**Models.** OpenAI gpt-4.1-mini runs the Actors: fast, low-cost and representative of everyday assistants. gpt-4.1 runs the Judge, where accuracy matters most.

**Data provenance.** No training or fine-tuning. Audits use only the page the user submits. Demo guides are fictional, written by us and MIT-licensed.

**Hallucination and bias mitigations.** Actors are restricted to their fetched view and must label guesses. The Judge must cite page evidence and check whether the fact was visible to that agent before blaming the docs. Category scores are clamped and summed in code. Paired good/bad samples serve as a regression test. Generated commands are never executed.

**Expected outcomes.** Users: fewer broken setups when following AI help. Businesses: better AI-driven adoption and fewer support tickets. Safety: fewer agents running invented commands.
