"""The Judge: audits an agent's output against everything a human reader of the page would know."""
import re

from bs4 import BeautifulSoup

from .llm import chat_json, judge_model_name

MAX_SOURCE_CHARS = 60_000
MAX_SCRIPT_CHARS = 3_000

CATEGORIES = {
    "correctness": 25,
    "completeness": 25,
    "ordering": 15,
    "specificity": 20,
    "verification": 15,
}
CATEGORY_LABELS = {
    "correctness": "Correctness",
    "completeness": "Completeness",
    "ordering": "Order & dependencies",
    "specificity": "Specificity",
    "verification": "Verification & recovery",
}
ROOT_CAUSES = ["hidden_from_agent", "missing_from_docs", "ambiguous", "poorly_structured", "scattered", "agent_error"]

SYSTEM = """You are a strict documentation usability auditor. You test whether AI agents can use a docs page.
You get:
1. GROUND TRUTH: the page's full HTML as a human experiences it, including tooltips, data attributes, hidden tabs,
   JavaScript-inserted text and CSS-generated content, plus optional AUTHOR NOTES describing what images show.
2. AGENT VIEW: exactly what one AI agent received when it fetched the page.
3. The task and the MODE: "instruct" (the agent answered a how-to question for a human) or
   "execute" (the agent planned to perform the task itself with exact commands and files).
4. The agent's OUTPUT.

Judge whether following the OUTPUT would actually succeed, per the GROUND TRUTH. Be strict: a wrong or invented
command, flag, value or URL is a failure even if it looks plausible. Score each category from 0 to its max:
- correctness (max 25): commands, values, settings and facts match the ground truth; nothing invented
- completeness (max 25): no missing steps or prerequisites needed for this task
- ordering (max 15): steps are in a working order; ordering-critical warnings respected
- specificity (max 20): exact commands, values, paths and names rather than vague advice or placeholders
- verification (max 15): says how to confirm success and handles likely failures
For "execute" mode, also penalise anything that could not run as-is.

For every failure, find the ROOT CAUSE in the documentation:
- hidden_from_agent: the info is on the page for humans (tooltip, image, hidden tab, JS-loaded, CSS) but absent or
  unusable in the AGENT VIEW
- missing_from_docs: not on the page at all
- ambiguous: present but unclear
- poorly_structured: present but buried or out of order, so the agent misused it
- scattered: lives on another page the agent would have to follow
- agent_error: the AGENT VIEW had it clearly; the agent just got it wrong
Before choosing a root cause, check whether the correct value literally appears as readable text in the AGENT VIEW.
If it does not, but it is in the ground truth or author notes, the cause is hidden_from_agent, never agent_error
or ambiguous. Image data (base64) is not readable text.

Return JSON:
{
  "categories": {"correctness": int, "completeness": int, "ordering": int, "specificity": int, "verification": int},
  "verdict": "one sentence: would following this output succeed?",
  "failures": [
    {"severity": "critical|major|minor",
     "what_broke": "what the agent got wrong or left out",
     "root_cause": "one of the root causes above",
     "doc_evidence": "short snippet from the ground truth that holds the real answer (or 'not on page')",
     "fix": "the exact sentence or snippet to add to the page body as plain text"}
  ]
}
If the output is fully correct, return an empty failures list."""


def ground_truth(html: str) -> str:
    """Keep the HTML with attributes and (trimmed) scripts; drop styles and inline image payloads."""
    soup = BeautifulSoup(html, "html.parser")
    for tag in soup(["noscript", "svg"]):
        tag.decompose()
    for tag in soup("script"):
        if tag.string and len(tag.string) > MAX_SCRIPT_CHARS:
            tag.string = tag.string[:MAX_SCRIPT_CHARS] + " /* trimmed */"
    for img in soup.find_all("img", src=re.compile(r"^data:")):
        img["src"] = "data:...(inline image)"
    text = re.sub(r"\n\s*\n+", "\n", str(soup))
    return text[:MAX_SOURCE_CHARS]


def run_judge(html: str, agent_view: str, profile_label: str, task: str, mode: str, output: str,
              reference: str | None = None) -> dict:
    notes = f"\n\n## AUTHOR NOTES\n\n{reference}" if reference else ""
    user = (
        f"## GROUND TRUTH (HTML)\n\n{ground_truth(html)}{notes}\n\n"
        f"## AGENT VIEW ({profile_label})\n\n{agent_view}\n\n"
        f"## MODE\n\n{mode}\n\n## Task\n\n{task}\n\n"
        f"## Agent OUTPUT\n\n{output}"
    )
    result = chat_json(SYSTEM, user, model=judge_model_name())
    cats = result.get("categories", {})
    # clamp each category to its max, so the score always adds up to at most 100
    result["categories"] = {k: max(0, min(int(cats.get(k, 0)), cap)) for k, cap in CATEGORIES.items()}
    result["score"] = sum(result["categories"].values())
    result.setdefault("failures", [])
    return result
