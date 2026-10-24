"""Thin OpenAI wrapper shared by the Actor and the Judge."""
import json
import os

from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

_client = None


def model_name() -> str:
    return os.getenv("OPENAI_MODEL", "gpt-4.1-mini")


def judge_model_name() -> str:
    # the Judge's accuracy matters most, so it gets a stronger model by default
    return os.getenv("OPENAI_JUDGE_MODEL", "gpt-4.1")


def client() -> OpenAI:
    global _client
    if _client is None:
        _client = OpenAI()  # reads OPENAI_API_KEY
    return _client


def chat(system: str, user: str, json_mode: bool = False, model: str | None = None) -> str:
    model = model or model_name()
    kwargs = {}
    # reasoning models (o-series, gpt-5) reject a custom temperature
    if not model.startswith(("o", "gpt-5")):
        kwargs["temperature"] = 0
    if json_mode:
        kwargs["response_format"] = {"type": "json_object"}
    resp = client().chat.completions.create(
        model=model,
        messages=[{"role": "system", "content": system}, {"role": "user", "content": user}],
        **kwargs,
    )
    return resp.choices[0].message.content


def chat_json(system: str, user: str, model: str | None = None) -> dict:
    return json.loads(chat(system, user, json_mode=True, model=model))
