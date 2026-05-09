import os
import requests
from typing import Any

from src.rag.llm_client import LLMClient


class OpenAIClient(LLMClient):
    """Minimal OpenAI-compatible client using the REST API via `requests`.

    Requires environment variable `OPENAI_API_KEY` to be set. This is an example
    implementation for local testing and CI demonstration only.
    """

    def __init__(self, api_key: str | None = None, model: str = "gpt-4o-mini"):
        self.api_key = api_key or os.environ.get("OPENAI_API_KEY")
        self.model = model

    def generate(self, prompt: str) -> str:
        if not self.api_key:
            return "[OpenAI API key not provided] " + prompt

        url = "https://api.openai.com/v1/chat/completions"
        headers = {"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"}
        payload: Any = {
            "model": self.model,
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": 512,
            "temperature": 0.2,
        }

        resp = requests.post(url, headers=headers, json=payload, timeout=30)
        resp.raise_for_status()
        data = resp.json()
        # Safety: try to extract a sensible text response
        if "choices" in data and data["choices"]:
            return data["choices"][0].get("message", {}).get("content", "")
        return ""
