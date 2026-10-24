# AI Impact Statement: Agentic Ready

**What the AI does:** Simulated AI agents read a docs page the way real assistants fetch it (reader-mode text, llms.txt, raw HTML) and attempt a task: answering a how-to question or planning the steps to do it. A Judge model checks each attempt against the full page as humans see it, scores it, and explains every failure with a suggested fix.

**Models:** OpenAI gpt-4.1-mini runs the agents; gpt-4.1 runs the Judge, where accuracy matters. Temperature 0.

**Data:** No training or fine-tuning. We process only the page a user submits, store nothing beyond a session cache, and OpenAI does not train on API inputs by default. Demo guides are fictional and self-written.

**Guardrails:** Agents may use only their fetched text and must flag guesses. The Judge must cite page evidence and check what each agent could see before blaming the docs. Scores are computed in code, and generated commands are never executed. Humans stay in control: the report is advisory, and docs teams review each failure and its evidence before deciding what to fix. Limits: scores vary between runs, and an LLM judge can share the agents' blind spots.

**Outcomes:** Fewer broken AI-guided setups; fewer support tickets; smoother onboarding.
