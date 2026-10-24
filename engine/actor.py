"""The Actor: a simulated AI agent that only knows what its reading profile gave it."""
from .llm import chat

COMMON = """You have NO prior knowledge of this product. Use ONLY the documentation provided below,
exactly as your fetch tool returned it. Never invent commands, flags, settings or values.
Where the docs leave something unclear or missing, make your best guess and mark it inline with `ASSUMPTION:`.
Do not ask the user questions."""

MODES = {
    "instruct": f"""You are an AI assistant answering a user in chat.
The user asked how to do something. Give clear, numbered, step-by-step instructions a human can follow,
including prerequisites and how to confirm it worked.
{COMMON}""",
    "execute": f"""You are an autonomous AI agent that will carry out the task YOURSELF, with shell and file access.
Output the exact, ordered actions you will perform: every command to run, every file to create (with full contents),
every setting to change, and the checks you will run to confirm success. It must be complete enough to run as-is.
{COMMON}""",
}

MODE_LABELS = {"instruct": "Instruct: answer a how-to question", "execute": "Execute: do the task itself"}


def run_actor(doc_text: str, task: str, mode: str, profile_note: str) -> str:
    user = (f"## Documentation (retrieved by your fetch tool: {profile_note})\n\n{doc_text}\n\n"
            f"## Task\n\n{task}")
    return chat(MODES[mode], user)
