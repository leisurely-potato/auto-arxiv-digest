from datetime import datetime, timezone

from auto_paper.models import Paper, Topic
from auto_paper.summarizer import Summarizer


class FakeLLM:
    enabled = True

    def summarize(self, prompt):
        return {
            "summary": "中文摘要",
            "contributions": ["贡献一"],
            "keywords": ["关键词"],
            "audience": "研究者",
        }


def test_summarizer_applies_summary(tmp_path):
    prompt = tmp_path / "prompt.md"
    prompt.write_text("{{title}}", encoding="utf-8")
    paper = Paper(
        arxiv_id="1",
        title="Paper",
        authors=[],
        abstract="Abstract",
        published=datetime(2024, 1, 1, tzinfo=timezone.utc),
        updated=None,
        categories=[],
        primary_category=None,
        abs_url="https://arxiv.org/abs/1",
        pdf_url=None,
        topics=["Agents"],
    )
    summarizer = Summarizer(FakeLLM(), str(prompt), 20)
    summarizer.summarize([paper], {"Agents": Topic(name="Agents", query="x")})
    assert paper.summary == "中文摘要"
    assert paper.keywords == ["关键词"]


def test_llm_client_retries_empty_content(monkeypatch):
    from io import BytesIO

    from auto_paper.llm_client import LLMClient

    class Response:
        def __init__(self, payload):
            self.payload = payload

        def __enter__(self):
            return BytesIO(self.payload)

        def __exit__(self, exc_type, exc, tb):
            return False

    calls = iter(
        [
            b'{"choices":[{"message":{"content":""}}]}',
            b'{"choices":[{"message":{"content":"{\\"summary\\":\\"ok\\"}"}}]}',
        ]
    )
    monkeypatch.setenv("TEST_LLM_KEY", "key")
    monkeypatch.setattr("auto_paper.llm_client.time.sleep", lambda _: None)
    monkeypatch.setattr("auto_paper.llm_client.urlopen", lambda *_, **__: Response(next(calls)))

    client = LLMClient(
        {
            "enabled": True,
            "api_key_env": "TEST_LLM_KEY",
            "retries": 1,
        }
    )

    assert client.summarize("json please") == {"summary": "ok"}
