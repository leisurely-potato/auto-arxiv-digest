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
