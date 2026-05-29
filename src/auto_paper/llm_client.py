from __future__ import annotations

import json
import os
import time
from json import JSONDecodeError
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


class LLMClient:
    def __init__(self, config: dict):
        self.enabled = bool(config.get("enabled", False))
        self.base_url = config.get("base_url", "https://api.openai.com/v1/chat/completions")
        self.api_key_env = config.get("api_key_env", "OPENAI_API_KEY")
        self.model = config.get("model", "gpt-4.1-mini")
        self.timeout = int(config.get("timeout", 60))
        self.max_tokens = int(config.get("max_tokens", 2000))
        self.retries = int(config.get("retries", 2))
        self.retry_delay = float(config.get("retry_delay", 1.0))

    def summarize(self, prompt: str) -> dict:
        api_key = os.environ.get(self.api_key_env)
        if not api_key:
            raise RuntimeError(f"missing API key env var: {self.api_key_env}")
        payload = {
            "model": self.model,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.2,
            "max_tokens": self.max_tokens,
            "response_format": {"type": "json_object"},
        }
        request = Request(
            self.base_url,
            data=json.dumps(payload).encode("utf-8"),
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            method="POST",
        )
        last_error: Exception | None = None
        for attempt in range(self.retries + 1):
            try:
                with urlopen(request, timeout=self.timeout) as response:
                    data = json.loads(response.read().decode("utf-8"))
                content = data["choices"][0]["message"].get("content") or ""
                if not content.strip():
                    raise RuntimeError("LLM returned empty content")
                return json.loads(content)
            except (HTTPError, URLError) as exc:
                last_error = RuntimeError(f"LLM request failed: {exc}")
            except (KeyError, IndexError, JSONDecodeError, RuntimeError) as exc:
                last_error = exc
            if attempt < self.retries:
                time.sleep(self.retry_delay)
        raise RuntimeError(f"LLM summary failed after {self.retries + 1} attempts: {last_error}")
