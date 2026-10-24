"""Suggest realistic test tasks for a docs page, so users don't have to write them."""
from .llm import chat_json

SYSTEM = """You design usability tests for technical documentation.
Given a docs page, propose ONE realistic task of each kind that this page should fully support:
- "instruct": a question a real user would ask an AI assistant ("How do I ...?")
- "execute": a concrete multi-step job an autonomous AI agent would be asked to carry out end to end
Make them specific (real-looking names, OS, values) and answerable only with the details on this page.
Return JSON: {"instruct": "...", "execute": "..."}"""


def suggest_tasks(page_text: str) -> dict:
    return chat_json(SYSTEM, page_text[:20_000])
